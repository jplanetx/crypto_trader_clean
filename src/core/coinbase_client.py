"""
Coinbase API client for real-time market data.

This module provides a client for the Coinbase Advanced Trade API,
including both WebSocket streaming and REST API access.
"""
import asyncio
import json
import logging
import time
import websockets
import hmac
import hashlib
from typing import Dict, Any, List, Optional
from base64 import b64encode
import aiohttp

# Configure the module logger
logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to parent loggers

class ApiError(Exception):
    """Exception raised for errors in the API client."""
    pass

class CoinbaseClient:
    """
    Client for the Coinbase Advanced Trade API.
    
    Provides functionality for both WebSocket streaming and REST API access.
    """
    
    def __init__(
        self,
        api_key: str,
        private_key: str,
        product_ids: List[str],
        channels: List[str] = None
    ):
        """
        Initialize the CoinbaseClient instance.
        
        Args:
            api_key: Coinbase API key
            private_key: Coinbase API private key
            product_ids: List of product IDs to subscribe to
            channels: List of channels to subscribe to (default: ["ticker"])
        """
        self.api_key = api_key
        self.private_key = private_key
        self.product_ids = product_ids
        self.channels = channels or ["ticker"]
        
        # WebSocket connection
        self.websocket = None
        self.url = "wss://advanced-trade-ws.coinbase.com"
        self.connected = False
        
        # Data caches
        self.prices: Dict[str, float] = {}
        self.ticker_data: Dict[str, Dict[str, Any]] = {}
        self.last_heartbeat = 0
        
        logger.info(f"Initialized CoinbaseClient with {len(product_ids)} product IDs")

    async def connect(self):
        """
        Connect to the Coinbase WebSocket API and authenticate.
        
        Returns:
            WebSocketClientProtocol: Connected and authenticated WebSocket client
            
        Raises:
            ApiError: If connection or authentication fails
        """
        try:
            logger.info("Connecting to Coinbase WebSocket API...")
            self.websocket = await websockets.connect(self.url)
            await self.authenticate()
            await self.subscribe()
            
            self.connected = True
            self.last_heartbeat = time.time()
            logger.info("Successfully connected and authenticated")
            return self.websocket
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ApiError(f"Connection failed: {e}")

    async def authenticate(self):
        """
        Authenticate the WebSocket connection using API credentials.
        
        Raises:
            ApiError: If authentication fails
        """
        try:
            timestamp = str(int(time.time()))
            message = f"{timestamp}GET/ws/accounts"
            
            # Create signature
            signature = hmac.new(
                self.private_key.encode('utf-8'),
                message.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_b64 = b64encode(signature).decode('utf-8')
            
            # Create authentication message
            auth_message = {
                "type": "subscribe",
                "product_ids": self.product_ids,
                "channels": self.channels,
                "api_key": self.api_key,
                "timestamp": timestamp,
                "signature": signature_b64
            }
            
            # Send authentication message
            await self.websocket.send(json.dumps(auth_message))
            logger.debug("Authentication message sent")
            
            # Wait for response
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'error':
                raise ApiError(f"Authentication failed: {data.get('message')}")
                
            logger.info("Authentication successful")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise ApiError(f"Authentication failed: {e}")

    async def subscribe(self):
        """
        Subscribe to specified channels for given product IDs.
        
        Raises:
            ApiError: If subscription fails
        """
        try:
            # Create subscription message
            subscribe_message = {
                "type": "subscribe",
                "product_ids": self.product_ids,
                "channels": self.channels
            }
            
            # Send subscription message
            await self.websocket.send(json.dumps(subscribe_message))
            logger.debug(f"Subscription sent for {self.product_ids}")
            
            # Wait for subscription confirmation
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'error':
                raise ApiError(f"Subscription failed: {data.get('message')}")
                
            logger.info(f"Subscribed to {len(self.product_ids)} products")
            
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
            raise ApiError(f"Subscription failed: {e}")

    async def receive_data(self):
        """
        Receive and process data from the WebSocket stream.
        
        This method runs in a loop until the connection is closed.
        """
        if not self.websocket:
            raise ApiError("WebSocket not connected")
            
        try:
            logger.info("Starting data reception loop")
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message[:100]}...")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            self.connected = False
            logger.error(f"WebSocket connection closed: {e}")
            raise ApiError(f"Connection closed: {e}")

    async def process_message(self, message: Dict[str, Any]):
        """
        Process a message from the WebSocket stream.
        
        Args:
            message: The message to process
        """
        message_type = message.get('type')
        
        if not message_type:
            logger.warning("Received message with no type")
            return
            
        if message_type == 'ticker':
            await self._handle_ticker(message)
        elif message_type == 'heartbeat':
            self.last_heartbeat = time.time()
            logger.debug("Heartbeat received")
        elif message_type == 'error':
            logger.error(f"Error from WebSocket: {message.get('message')}")
            raise ApiError(f"Stream error: {message.get('message')}")
        else:
            logger.debug(f"Received message of type {message_type}")

    async def _handle_ticker(self, message: Dict[str, Any]):
        """
        Handle a ticker message.
        
        Args:
            message: The ticker message
        """
        product_id = message.get('product_id')
        price_str = message.get('price')
        
        if not product_id or not price_str:
            return
            
        try:
            price = float(price_str)
            
            # Update price cache
            self.prices[product_id] = price
            
            # Update ticker data
            self.ticker_data[product_id] = {
                'price': price,
                'time': message.get('time'),
                'trade_id': message.get('trade_id'),
                'volume_24h': float(message.get('volume_24h', 0))
            }
            
            logger.debug(f"Updated price for {product_id}: {price}")
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing ticker: {e}")

    async def close(self):
        """
        Close the WebSocket connection.
        """
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("WebSocket connection closed")

    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a specific trading pair.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTC-USD')
            
        Returns:
            float: The current price
            
        Raises:
            ApiError: If price data cannot be retrieved or is invalid
        """
        # First check if we have the price in our cache
        if symbol in self.prices:
            return self.prices[symbol]
        
        # If not in cache, fetch from REST API
        try:
            logger.debug(f"Price not in cache for {symbol}, fetching from REST API")
            # Use aiohttp to fetch price synchronously (not ideal but works for simple cases)
            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(self._fetch_price_from_api(symbol))
            loop.close()
            
            if not response or 'price' not in response:
                error_msg = f"Invalid response from API for {symbol}"
                logger.error(error_msg)
                raise ApiError(error_msg)
                
            price = float(response.get('price', 0))
            if price <= 0:
                error_msg = f"Invalid price received for {symbol}: {price}"
                logger.error(error_msg)
                raise ApiError(error_msg)
            
            # Update our cache
            self.prices[symbol] = price
            logger.debug(f"Updated cache with price for {symbol}: {price}")
            return price
            
        except ValueError as e:
            error_msg = f"Invalid price format for {symbol}: {e}"
            logger.error(error_msg)
            raise ApiError(error_msg)
        except Exception as e:
            error_msg = f"Error fetching price for {symbol}: {e}"
            logger.error(error_msg)
            # Return 0 instead of raising an exception to avoid breaking callers
            return 0

    async def _fetch_price_from_api(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch price data from the Coinbase REST API.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            dict: Response data
        """
        url = f"https://api.exchange.coinbase.com/products/{symbol}/ticker"
        
        # Create signature
        timestamp = str(int(time.time()))
        method = "GET"
        request_path = f"/products/{symbol}/ticker"
        message = f"{timestamp}{method}{request_path}"
        
        signature = hmac.new(
            self.private_key.encode('utf-8'),
            message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_b64 = b64encode(signature).decode('utf-8')
        
        # Set up headers
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        
        # Make the request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed: {response.status}")
                    return {}

    # Add convenience method for paper trading
    def simulate_price_update(self, symbol: str, price: float):
        """
        Simulate a price update for paper trading.
        
        Args:
            symbol: The trading pair symbol
            price: The new price
        """
        self.prices[symbol] = price
        logger.debug(f"Simulated price update for {symbol}: {price}")
