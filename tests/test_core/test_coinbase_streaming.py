"""Tests for the CoinbaseStreaming class."""
import json
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from src.core.coinbase_streaming import CoinbaseStreaming
from src.utils.exceptions import StreamingError

# Add a proper import for what we're patching
try:
    import websockets.client
except ImportError:
    # Mock for test running without websockets
    pass

@pytest.fixture
def coinbase_streaming():
    """Create a CoinbaseStreaming instance with test credentials."""
    return CoinbaseStreaming(
        api_key="test_api_key",
        private_key="test_private_key",
        product_ids=["BTC-USD", "ETH-USD"],
        channels=["ticker"]
    )


@pytest.mark.asyncio
@patch('websockets.client.connect')  # Update to proper import path
async def test_connect_success(mock_connect, coinbase_streaming):
    """Test successful WebSocket connection."""
    # Setup mock
    mock_websocket = AsyncMock()
    mock_websocket.send = AsyncMock()
    mock_websocket.recv = AsyncMock(return_value=json.dumps({"type": "subscriptions"}))
    
    # Create an awaitable coroutine that returns the mock
    async def mock_connect_coro(*args, **kwargs):
        return mock_websocket
    
    # Replace the mock's side_effect with our coroutine
    mock_connect.side_effect = mock_connect_coro

    # Execute
    result = await coinbase_streaming.connect()

    # Assert
    assert result == mock_websocket
    mock_connect.assert_called_once()
    assert coinbase_streaming.websocket is not None


@pytest.mark.asyncio
@patch('src.core.coinbase_streaming.websockets.connect')
async def test_connect_failure(mock_connect, coinbase_streaming):
    """Test WebSocket connection failure."""
    # Setup mock to raise an exception
    mock_connect.side_effect = Exception("Connection failed")

    # Execute and assert
    with pytest.raises(StreamingError) as exc_info:
        await coinbase_streaming.connect()
    
    assert "Connection failed" in str(exc_info.value)


def test_get_current_price_from_cache(coinbase_streaming):
    """Test retrieving price from cache."""
    # Setup - add a price to the cache
    symbol = "BTC-USD"
    expected_price = 50000.0
    coinbase_streaming.prices[symbol] = expected_price

    # Execute
    price = coinbase_streaming.get_current_price(symbol)

    # Assert
    assert price == expected_price


@patch('coinbase_advanced_trade.rest.RESTClient')
def test_get_current_price_from_rest_api(mock_rest_client, coinbase_streaming):
    """Test retrieving price from REST API when not in cache."""
    # Setup
    symbol = "ETH-USD"
    expected_price = 3000.0
    
    # Configure the mock
    mock_client = MagicMock()
    mock_client.get_product_ticker.return_value = {"price": str(expected_price)}
    coinbase_streaming.rest_client = mock_client

    # Execute
    price = coinbase_streaming.get_current_price(symbol)

    # Assert
    assert price == expected_price
    mock_client.get_product_ticker.assert_called_once_with(product_id=symbol)
    # Verify the price was cached
    assert coinbase_streaming.prices[symbol] == expected_price


@patch('coinbase_advanced_trade.rest.RESTClient')
def test_get_current_price_rest_api_error(mock_rest_client, coinbase_streaming):
    """Test error handling when REST API call fails."""
    # Setup
    symbol = "LTC-USD"
    
    # Configure the mock
    mock_client = MagicMock()
    mock_client.get_product_ticker.side_effect = Exception("API error")
    coinbase_streaming.rest_client = mock_client

    # Execute
    price = coinbase_streaming.get_current_price(symbol)

    # Assert
    assert price == 0  # The method returns 0 on error
    mock_client.get_product_ticker.assert_called_once_with(product_id=symbol)


@pytest.mark.asyncio
@patch('src.core.coinbase_streaming.websockets.connect')
async def test_process_message_ticker(mock_connect, coinbase_streaming):
    """Test processing ticker messages."""
    # Setup mock
    mock_websocket = AsyncMock()
    mock_connect.return_value = mock_websocket
    coinbase_streaming.websocket = mock_websocket
    
    # Create a ticker message
    ticker_message = {
        "type": "ticker",
        "product_id": "BTC-USD",
        "price": "50000.0",
        "time": "2023-01-01T00:00:00.000000Z"
    }

    # Execute
    await coinbase_streaming.process_message(ticker_message)
    
    # No assertion needed as we're just testing that it doesn't raise an exception
    # In a more comprehensive test, we'd verify the ticker data was properly processed


@pytest.mark.asyncio
@patch('src.core.coinbase_streaming.websockets.connect')
async def test_process_message_error(mock_connect, coinbase_streaming):
    """Test processing error messages."""
    # Setup mock
    mock_websocket = AsyncMock()
    mock_connect.return_value = mock_websocket
    coinbase_streaming.websocket = mock_websocket
    
    # Create an error message
    error_message = {
        "type": "error",
        "message": "Test error message"
    }

    # Execute and assert
    with pytest.raises(StreamingError) as exc_info:
        await coinbase_streaming.process_message(error_message)
    
    assert "Test error message" in str(exc_info.value)
