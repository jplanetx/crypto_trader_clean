"""Tests for the CoinbaseClient class."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.core.coinbase_client import CoinbaseClient, ApiError


@pytest.fixture
def client():
    """Create a CoinbaseClient instance for testing."""
    return CoinbaseClient(
        api_key="test_api_key",
        private_key="test_private_key",
        product_ids=["BTC-USD", "ETH-USD"]
    )


def test_client_initialization(client):
    """Test client initialization."""
    assert client.api_key == "test_api_key"
    assert client.private_key == "test_private_key"
    assert client.product_ids == ["BTC-USD", "ETH-USD"]
    assert client.channels == ["ticker"]
    assert client.connected is False
    assert isinstance(client.prices, dict)


@pytest.mark.asyncio
async def test_connect(client):
    """Test the connect method."""
    # Mock the websocket connection and methods
    with patch('websockets.connect', return_value=AsyncMock()) as mock_connect, \
         patch.object(client, 'authenticate', AsyncMock()) as mock_auth, \
         patch.object(client, 'subscribe', AsyncMock()) as mock_subscribe:

        websocket = await client.connect()
        
        # Verify the websocket was connected with the right URL
        mock_connect.assert_called_once_with(client.url)
        
        # Verify authentication and subscription were called
        mock_auth.assert_called_once()
        mock_subscribe.assert_called_once()
        
        # Verify client state
        assert client.websocket is not None
        assert client.connected is True
        assert client.last_heartbeat > 0


@pytest.mark.asyncio
async def test_authenticate_success(client):
    """Test successful authentication."""
    # Setup mock websocket
    client.websocket = AsyncMock()
    client.websocket.send = AsyncMock()
    client.websocket.recv = AsyncMock(return_value=json.dumps({"type": "subscriptions"}))
    
    await client.authenticate()
    
    # Verify the websocket.send was called (with any argument)
    client.websocket.send.assert_called_once()
    
    # Get the call argument
    call_arg = client.websocket.send.call_args[0][0]
    
    # Check that it's a JSON string and has the expected fields
    auth_data = json.loads(call_arg)
    assert auth_data["type"] == "subscribe"
    assert auth_data["api_key"] == client.api_key
    assert "signature" in auth_data
    assert "timestamp" in auth_data
    assert auth_data["product_ids"] == client.product_ids
    assert auth_data["channels"] == client.channels


@pytest.mark.asyncio
async def test_authenticate_failure(client):
    """Test authentication failure."""
    # Setup mock websocket with error response
    client.websocket = AsyncMock()
    client.websocket.send = AsyncMock()
    client.websocket.recv = AsyncMock(return_value=json.dumps({"type": "error", "message": "Auth failed"}))
    
    # Expect an ApiError
    with pytest.raises(ApiError, match="Authentication failed"):
        await client.authenticate()


def test_get_current_price_from_cache(client):
    """Test getting a price from the cache."""
    # Put a test price in the cache
    client.prices["BTC-USD"] = 50000.0
    
    # Get the price
    price = client.get_current_price("BTC-USD")
    
    # Verify we got the cached price
    assert price == 50000.0


@pytest.mark.asyncio
async def test_fetch_price_from_api(client):
    """Test fetching a price from the API."""
    # Setup mock response for _fetch_price_from_api
    mock_response = {"price": "45000.0"}
    with patch.object(client, '_fetch_price_from_api', AsyncMock(return_value=mock_response)):
        # Remove from cache to force API fetch
        client.prices = {}
        
        # Get the price
        price = client.get_current_price("BTC-USD")
        
        # Verify we got the expected price
        assert price == 45000.0
        
        # Verify the price was cached
        assert client.prices["BTC-USD"] == 45000.0


def test_simulate_price_update(client):
    """Test simulating a price update for paper trading."""
    # Simulate a price update
    client.simulate_price_update("BTC-USD", 55000.0)
    
    # Verify the price was updated in the cache
    assert client.prices["BTC-USD"] == 55000.0
    
    # Get the price and verify it matches
    price = client.get_current_price("BTC-USD")
    assert price == 55000.0
