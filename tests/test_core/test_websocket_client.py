import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from src.core.websocket_client import WebsocketClient, StreamingError

@pytest_asyncio.fixture
async def mock_websocket_client():
    """
    Fixture to create a mock WebsocketClient instance for testing.
    """
    with patch("src.core.websocket_client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()
        mock_connect.return_value = mock_websocket
        mock_websocket.send = AsyncMock()
        mock_websocket.close = AsyncMock()
        client = WebsocketClient(
            url="wss://example.com",
            api_key="test_key",
            api_secret="test_secret",
            product_ids=["BTC-USD"],
            channels=["ticker"]
        )
        client.websocket = mock_websocket
        yield client, mock_websocket

@pytest.mark.asyncio
async def test_websocket_client_initialization(mock_websocket_client):
    """
    Test the initialization of the WebsocketClient, including connection and authentication.
    """
    client, mock_websocket = mock_websocket_client
    mock_websocket.recv.return_value = json.dumps({"type": "authenticated"})
    await client._authenticate()
    assert client.websocket is not None
    mock_websocket.send.assert_called_once()  # Authentication message sent

@pytest.mark.asyncio
async def test_websocket_client_subscription(mock_websocket_client):
    """
    Test the subscription functionality of the WebsocketClient.
    """
    client, mock_websocket = mock_websocket_client
    mock_websocket.recv.return_value = json.dumps({"type": "subscriptions"})
    await client.subscribe()
    assert mock_websocket.send.call_count == 1  # Subscription messages

@pytest.mark.asyncio
async def test_websocket_client_heartbeat(mock_websocket_client):
    """
    Test the heartbeat mechanism of the WebsocketClient.
    """
    client, mock_websocket = mock_websocket_client
    mock_websocket.send.return_value = None
    client.websocket = mock_websocket
    mock_websocket.recv.return_value = json.dumps({"type": "heartbeat"})
    await client._heartbeat_loop()
    await asyncio.sleep(1)  # Allow some time for the heartbeat to be sent
    assert mock_websocket.send.call_count >= 1  # Heartbeat messages

@pytest.mark.asyncio
async def test_websocket_client_close(mock_websocket_client):
    """
    Test the close functionality of the WebsocketClient.
    """
    client, mock_websocket = mock_websocket_client
    await client.close()
    mock_websocket.close.assert_called_once()

@pytest.mark.asyncio
async def test_websocket_client_authentication_failure(mock_websocket_client):
    """
    Test the authentication failure scenario of the WebsocketClient.
    """
    client, mock_websocket = mock_websocket_client
    mock_websocket.recv.return_value = json.dumps({"type": "error", "message": "Authentication failed"})
    with pytest.raises(StreamingError, match="Authentication failed"):
        await client._authenticate()

@pytest.mark.asyncio
async def test_websocket_client_subscription_failure(mock_websocket_client):
    """
    Test the subscription failure scenario of the WebsocketClient.
    """
    client, mock_websocket = mock_websocket_client
    mock_websocket.recv.side_effect = [
        json.dumps({"type": "authenticated"}),
        json.dumps({"type": "error", "message": "Subscription failed"})
    ]
    with pytest.raises(StreamingError, match="Subscription failed"):
        await client.subscribe()
