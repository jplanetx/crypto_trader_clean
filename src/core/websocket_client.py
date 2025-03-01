"""
Websocket Client for Coinbase Advanced Trade API

This module implements a refactored WebsocketClient that separates initialization and subscription procedures.
The client establishes a connection, performs authentication as per the updated API, and allows explicit subscription
to desired channels. Unit tests should validate that the refactored flow meets the new API requirements.
"""

import asyncio
import json
import logging
import time
import websockets
import hmac
import hashlib
from base64 import b64encode
from typing import List, Optional, Dict, Any
from ..utils.exceptions import StreamingError
import asyncio

logger = logging.getLogger(__name__)
logger.propagate = True

HEARTBEAT_INTERVAL = 30  # seconds

class WebsocketClient:
    def __init__(self, url: str, api_key: str, api_secret: str, product_ids: List[str], channels: List[str]):
        """
        Initialize the WebsocketClient with connection parameters and credentials.
        
        Args:
            url (str): WebSocket URL.
            api_key (str): API key.
            api_secret (str): API secret.
            product_ids (List[str]): List of products to subscribe.
            channels (List[str]): List of channels for subscription.
        """
        if not api_key or not api_secret:
            raise StreamingError("API key and secret are required")
        if not product_ids:
            raise StreamingError("At least one product ID is required")
        if not channels:
            raise StreamingError("At least one channel is required")
            
        self.url = url
        self.api_key = api_key
        self.api_secret = api_secret
        self.product_ids = product_ids
        self.channels = channels
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.heartbeat_task: Optional[asyncio.Task[None]] = None

    async def initialize(self) -> None:
        """
        Establish a websocket connection and perform authentication.
        This step only initializes the connection and handles auth.
        
        Raises:
            StreamingError: If connection or authentication fails.
        """
        try:
            logger.info("Establishing connection to WebSocket...")
            self.websocket = await websockets.connect(self.url)
            await self._authenticate()
            logger.info("Connection initialized and authenticated.")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise StreamingError(f"Initialization failed: {e}")
        
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _authenticate(self) -> None:
        """
        Internal method to authenticate the websocket connection.
        
        Raises:
            StreamingError: If authentication fails.
        """
        try:
            timestamp = str(int(time.time()))
            method = 'GET'
            request_path = '/api/v3/brokerage/accounts'
            body = ''
            message = timestamp + method + request_path + body
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                message.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_b64 = b64encode(signature).decode('utf-8')
            
            auth_payload: Dict[str, Any] = {
                "type": "authenticate",
                "key": self.api_key,
                "timestamp": timestamp,
                "signature": signature_b64
            }
            logger.debug("Sending authentication payload")
            await self.websocket.send(json.dumps(auth_payload))
            response = await self.websocket.recv()
            resp_data = json.loads(response)
            if resp_data.get("type") == "error":
                raise StreamingError(f"Authentication failed: {resp_data.get('message')}")
            logger.debug("Authentication response received: " + response)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise StreamingError(f"Authentication error: {e}")

    async def subscribe(self) -> None:
        """
        Subscribe to the desired channels for the specified products.
        
        Raises:
            StreamingError: If subscription fails.
        """
        if self.websocket is None:
            raise StreamingError("WebSocket connection is not established.")
        try:
            subscription_payload: Dict[str, Any] = {
                "type": "subscribe",
                "product_ids": self.product_ids,
                "channels": self.channels
            }
            logger.debug("Sending subscription payload")
            await self.websocket.send(json.dumps(subscription_payload))
            response = await self.websocket.recv()
            resp_data = json.loads(response)
            if resp_data.get("type") == "error":
                raise StreamingError(f"Subscription failed: {resp_data.get('message')}")
            logger.info("Subscription successful.")
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise StreamingError(f"Subscription error: {e}")

    async def _heartbeat_loop(self) -> None:
        """
        Internal method to send heartbeat messages every HEARTBEAT_INTERVAL seconds.
        """
        try:
            while True:
                try:
                    await asyncio.sleep(HEARTBEAT_INTERVAL)
                    if self.websocket and self.websocket.open:
                        heartbeat_payload: Dict[str, Any] = {"type": "heartbeat"}
                        logger.debug("Sending heartbeat")
                        await self.websocket.send(json.dumps(heartbeat_payload))
                    else:
                        logger.warning("Heartbeat loop stopped: WebSocket not connected.")
                        break  # Exit loop if WebSocket is not connected
                except KeyboardInterrupt:
                    logger.warning("Heartbeat loop interrupted by keyboard.")
                    break
                except Exception as e:
                    logger.error(f"Heartbeat loop error: {e}")
        finally:
            logging.shutdown()

    async def close(self) -> None:
        """
        Close the websocket connection gracefully.
        """
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                logger.info("Heartbeat task cancelled.")
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("WebSocket closed gracefully.")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

    async def run(self) -> None:
        """
        A helper method to demonstrate the full workflow: initialization, subscription, and listening.
        """
        try:
            await self.initialize()
            await self.subscribe()
            logger.info("Client is now ready to receive data.")
            # Listening loop can be added here if needed.
        except StreamingError as e:
            logger.error(f"Run error: {e}")
            raise
