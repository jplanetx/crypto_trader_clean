"""
Coinbase WebSocket streaming module for real-time market data.

This module handles WebSocket connections to Coinbase's Advanced Trade API,
providing real-time market data streams with proper authentication and
error handling.
"""
import asyncio
import json
import logging
import os
import time
import websockets
import hmac
import hashlib
from typing import List, Dict, Any, Optional
from base64 import b64encode
from ..utils.exceptions import StreamingError

# Configure the module logger
logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to parent loggers

class CoinbaseStreaming:
    """
    Manages WebSocket connections to Coinbase's Advanced Trade API.
    
    Handles authentication, subscription to market data channels, and
    processing of real-time market data streams.
    """
    
    def __init__(self, api_key: str, private_key: str, product_ids: List[str], channels: List[str]):
        """
        Initialize the CoinbaseStreaming instance.
        
        Args:
            api_key (str): Coinbase API key
            private_key (str): Coinbase API private key
            product_ids (List[str]): List of product IDs to subscribe to
            channels (List[str]): List of channels to subscribe to
            
        Raises:
            StreamingError: If initialization parameters are invalid
        """
        if not api_key or not private_key:
            raise StreamingError("API key and private key are required")
        if not product_ids:
            raise StreamingError("At least one product ID is required")
        if not channels:
            raise StreamingError("At least one channel is required")
            
        self.api_key = api_key
        self.private_key = private_key
        self.product_ids = product_ids
        self.channels = channels
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.url = "wss://advanced-trade-ws.coinbase.com"
        
        logger.info(f"Initialized streaming for products: {product_ids}")

    async def connect(self) -> websockets.WebSocketClientProtocol:
        """
        Connect to the Coinbase WebSocket API and authenticate.
        
        Returns:
            WebSocketClientProtocol: Connected and authenticated WebSocket client
            
        Raises:
            StreamingError: If connection or authentication fails
        """
        try:
            logger.info("Connecting to Coinbase WebSocket API...")
            self.websocket = await websockets.connect(self.url)
            await self.authenticate()
            await self.subscribe()
            logger.info("Successfully connected and authenticated")
            return self.websocket
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise StreamingError(f"WebSocket connection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            raise StreamingError(f"Connection failed: {e}")

    async def authenticate(self) -> None:
        """
        Authenticate the WebSocket connection using API credentials.
        
        Raises:
            StreamingError: If authentication fails
        """
        try:
            timestamp = str(int(time.time()))
            method = 'GET'
            request_path = '/api/v3/brokerage/accounts'
            body = ''
            message = timestamp + method + request_path + body
            signature = hmac.new(
                self.private_key.encode('utf-8'),
                message.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_b64 = b64encode(signature).decode('utf-8')

            auth_message = {
                "type": "subscribe",
                "product_ids": self.product_ids,
                "channels": self.channels,
                "signature": signature_b64,
                "key": self.api_key,
                "timestamp": timestamp
            }
            
            logger.debug("Sending authentication message")
            await self.websocket.send(json.dumps(auth_message))
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'error':
                raise StreamingError(f"Authentication failed: {response_data.get('message')}")
                
            logger.info("Authentication successful")
            logger.debug(f"Auth response: {response}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid authentication response format: {e}")
            raise StreamingError(f"Authentication failed - invalid response: {e}")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise StreamingError(f"Authentication failed: {e}")

    async def subscribe(self) -> None:
        """
        Subscribe to specified channels for given product IDs.
        
        Raises:
            StreamingError: If subscription fails
        """
        try:
            subscribe_message = {
                "type": "subscribe",
                "product_ids": self.product_ids,
                "channels": self.channels,
            }
            
            logger.debug("Sending subscription message")
            await self.websocket.send(json.dumps(subscribe_message))
            
            # Wait for and verify subscription confirmation
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get('type') == 'error':
                raise StreamingError(f"Subscription failed: {response_data.get('message')}")
                
            logger.info(f"Successfully subscribed to channels: {self.channels}")
            logger.debug(f"Subscription confirmed for products: {self.product_ids}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid subscription response format: {e}")
            raise StreamingError(f"Subscription failed - invalid response: {e}")
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
            raise StreamingError(f"Subscription failed: {e}")

    async def receive_data(self) -> None:
        """
        Receive and process data from the WebSocket stream continuously.
        
        This method runs in a loop until the connection is closed or an error occurs.
        
        Raises:
            StreamingError: If data reception fails
        """
        if not self.websocket:
            raise StreamingError("WebSocket connection not established")
            
        try:
            logger.info("Starting data reception loop")
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid message format: {e}")
                    continue  # Skip invalid messages and continue processing
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed unexpectedly: {e}")
            raise StreamingError(f"Connection closed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during data reception: {e}")
            raise StreamingError(f"Data reception failed: {e}")

    async def process_message(self, message: Dict[str, Any]) -> None:
        """
        Process incoming messages from the WebSocket stream.
        
        Args:
            message (Dict[str, Any]): The message to process
            
        Raises:
            StreamingError: If message processing fails
        """
        try:
            message_type = message.get('type')
            
            if not message_type:
                logger.warning("Received message without type field")
                return
                
            if message_type == 'error':
                error_msg = message.get('message', 'Unknown error')
                logger.error(f"Received error message: {error_msg}")
                raise StreamingError(f"Stream error: {error_msg}")
                
            if message_type == 'ticker':
                await self._handle_ticker(message)
            elif message_type == 'snapshot':
                await self._handle_snapshot(message)
            elif message_type == 'update':
                await self._handle_update(message)
            elif message_type == 'heartbeat':
                logger.debug("Heartbeat received")
            else:
                logger.debug(f"Received unknown message type: {message_type}")
                
        except KeyError as e:
            logger.error(f"Message missing required field: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise StreamingError(f"Message processing failed: {e}")

    async def _handle_ticker(self, message: Dict[str, Any]) -> None:
        """
        Handle ticker messages containing price updates.
        
        Args:
            message (Dict[str, Any]): The ticker message to process
        """
        product_id = message.get('product_id')
        price = message.get('price')
        
        if product_id and price:
            logger.info(f"Ticker update - Product: {product_id}, Price: {price}")
            # Additional ticker processing logic here
        else:
            logger.warning("Received incomplete ticker data")
            
    async def _handle_snapshot(self, message: Dict[str, Any]) -> None:
        """
        Handle order book snapshot messages.
        
        Args:
            message (Dict[str, Any]): The snapshot message to process
        """
        product_id = message.get('product_id')
        if product_id:
            logger.info(f"Processing order book snapshot for {product_id}")
            # Additional snapshot processing logic here
        else:
            logger.warning("Received incomplete snapshot data")
            
    async def _handle_update(self, message: Dict[str, Any]) -> None:
        """
        Handle order book update messages.
        
        Args:
            message (Dict[str, Any]): The update message to process
        """
        product_id = message.get('product_id')
        if product_id:
            logger.info(f"Processing order book update for {product_id}")
            # Additional update processing logic here
        else:
            logger.warning("Received incomplete update data")
            
    async def run(self) -> None:
        """
        Main method to start the WebSocket connection and data processing.
        
        This method manages the full lifecycle of the WebSocket connection.
        
        Raises:
            StreamingError: If connection or processing fails
        """
        try:
            logger.info("Starting Coinbase streaming session")
            await self.connect()
            await self.receive_data()
        except StreamingError as e:
            logger.error(f"Streaming error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in streaming session: {e}")
            raise StreamingError(f"Streaming session failed: {e}")
        finally:
            await self.close()

    async def close(self) -> None:
        """
        Close the WebSocket connection gracefully.
        """
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("WebSocket connection closed gracefully")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")

    def get_current_price(self, trading_pair: str) -> float:
        """
        Get the current price for a given trading pair.
        """
        if trading_pair in self.price_data:
            return self.price_data[trading_pair][-1]
        else:
            return 0
