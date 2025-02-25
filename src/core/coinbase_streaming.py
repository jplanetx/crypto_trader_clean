import asyncio
import json
import logging
import os
import time
import websockets
import hmac
import hashlib
from base64 import b64encode

class CoinbaseStreaming:
    def __init__(self, api_key, api_secret, product_ids, channels):
        self.api_key = api_key
        self.api_secret = api_secret
        self.product_ids = product_ids
        self.channels = channels
        self.websocket = None
        self.logger = logging.getLogger(__name__)
        self.url = "wss://advanced-trade-ws.coinbase.com"

    async def connect(self):
        """
        Connects to the Coinbase WebSocket API and authenticates.
        """
        try:
            self.websocket = await websockets.connect(self.url)
            await self.authenticate()
            await self.subscribe()
            self.logger.info("Connected to Coinbase WebSocket API")
            return self.websocket
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise

    async def authenticate(self):
        """
        Authenticates the WebSocket connection using API key and secret.
        """
        timestamp = str(int(time.time()))
        message = timestamp + 'GET' + '/users/self/verify'
        signature = hmac.new(self.api_secret.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_b64 = b64encode(signature).decode('utf-8')

        auth_message = {
            "type": "subscribe",
            "product_ids": self.product_ids,
            "channels": self.channels,
            "signature": signature_b64,
            "key": self.api_key,
            "timestamp": timestamp
        }
        await self.websocket.send(json.dumps(auth_message))
        response = await self.websocket.recv()
        self.logger.info(f"Authentication response: {response}")

    async def subscribe(self):
        """
        Subscribes to the specified channels for the given product IDs.
        """
        subscribe_message = {
            "type": "subscribe",
            "product_ids": self.product_ids,
            "channels": self.channels,
        }
        await self.websocket.send(json.dumps(subscribe_message))
        self.logger.info(f"Subscribed to channels: {self.channels} for products: {self.product_ids}")

    async def receive_data(self):
        """
        Receives and processes data from the WebSocket stream.
        """
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.process_message(data)
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(f"Connection closed: {e}")
        except Exception as e:
            self.logger.error(f"Error receiving data: {e}")

    def process_message(self, message):
        """
        Processes incoming messages from the WebSocket.
        """
        try:
            message_type = message.get('type')
            if message_type == 'ticker':
                # Process ticker data
                product_id = message.get('product_id')
                price = message.get('price')
                self.logger.info(f"Ticker - Product: {product_id}, Price: {price}")
            elif message_type == 'snapshot':
                # Process order book snapshot
                product_id = message.get('product_id')
                # Process the snapshot data as needed
                self.logger.info(f"Snapshot received for Product: {product_id}")
            elif message_type == 'update':
                # Process order book update
                product_id = message.get('product_id')
                # Process the update data as needed
                self.logger.info(f"Update received for Product: {product_id}")
            elif message_type == 'heartbeat':
                self.logger.debug("Heartbeat received")
            else:
                self.logger.debug(f"Received: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    async def run(self):
        """
        Main method to start the WebSocket connection and data processing.
        """
        try:
            await self.connect()
            await self.receive_data()
        except Exception as e:
            self.logger.error(f"Error in run method: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()
                self.logger.info("WebSocket connection closed.")

    async def close(self):
        """
        Closes the WebSocket connection.
        """
        if self.websocket:
            await self.websocket.close()
            self.logger.info("Closing WebSocket connection")
