"""Tests for coinbase_streaming.py."""
import pytest
from src.core.coinbase_streaming import CoinbaseStreaming

def test_coinbase_streaming_initialization():
    """Test CoinbaseStreaming initialization."""
    # Create test values
    api_key = "test_api_key"
    api_secret = "test_api_secret"
    product_ids = ["BTC-USD"]
    channels = ["ticker"]
    
    # Initialize the class
    streaming = CoinbaseStreaming(api_key, api_secret, product_ids, channels)
    
    # Verify initialization
    assert streaming.api_key == api_key
    assert streaming.api_secret == api_secret
    assert streaming.product_ids == product_ids
    assert streaming.channels == channels
    assert streaming.url == "wss://advanced-trade-ws.coinbase.com"
    assert streaming.websocket is None

@pytest.mark.asyncio
async def test_coinbase_streaming_connect_websocket_exception():
    """Test WebSocket connection failure."""
    mock_api_key = "test_api_key"
    mock_api_secret = "test_api_secret"
    mock_product_ids = ["BTC-USD"]
    mock_channels = ["ticker"]

    # Mock websockets.connect to raise a WebSocketException
    with patch("websockets.connect", side_effect=websockets.exceptions.WebSocketException("Connection failed")) as mock_connect:
        streaming = CoinbaseStreaming(mock_api_key, mock_api_secret, mock_product_ids, mock_channels)
        with pytest.raises(StreamingError) as exc_info:
            await streaming.connect()
        assert "WebSocket connection failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_coinbase_streaming_connect_exception():
    """Test unexpected error during connection."""
    mock_api_key = "test_api_key"
    mock_api_secret = "test_api_secret"
    mock_product_ids = ["BTC-USD"]
    mock_channels = ["ticker"]

    # Mock websockets.connect to raise a generic Exception
    with patch("websockets.connect", side_effect=Exception("Unexpected error")) as mock_connect:
        streaming = CoinbaseStreaming(mock_api_key, mock_api_secret, mock_product_ids, mock_channels)
        with pytest.raises(StreamingError) as exc_info:
            await streaming.connect()
        assert "Connection failed" in str(exc_info.value)
