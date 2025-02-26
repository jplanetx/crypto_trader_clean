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
