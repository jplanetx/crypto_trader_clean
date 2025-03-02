"""Tests for the TradingCore.get_position method."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from decimal import Decimal

from src.core.trading_core import TradingCore
from src.utils.exceptions import TradingException, ConfigurationError


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    mock = MagicMock()
    mock.config = MagicMock()
    mock.config.api_key = "test_api_key"
    mock.config.private_key = "test_private_key"
    mock.config.trading_pairs = ["BTC-USD", "ETH-USD"]
    mock.config.risk_config.max_position_size = Decimal("5.0")
    return mock


@pytest.fixture
def mock_exchange_interface():
    """Create a mock exchange interface."""
    mock = AsyncMock()
    # Setup mock for get_accounts
    mock.get_accounts = AsyncMock()
    return mock


@pytest.fixture
def trading_core(mock_config_manager, mock_exchange_interface):
    """Create a TradingCore instance with mocks."""
    with patch('src.core.trading_core.ConfigManager', return_value=mock_config_manager):
        with patch('src.core.trading_core.CoinbaseExchange', return_value=mock_exchange_interface):
            with patch('src.core.trading_core.CoinbaseStreaming'):
                tc = TradingCore(config_path='config/config.json')
                tc.exchange_interface = mock_exchange_interface
                tc.config_manager = mock_config_manager
                return tc


@pytest.mark.asyncio
async def test_get_position_btc(trading_core, mock_exchange_interface):
    """Test retrieving BTC position."""
    # Setup mock accounts response
    mock_exchange_interface.get_accounts.return_value = [
        {"currency": "BTC", "balance": "1.5"},
        {"currency": "ETH", "balance": "10.0"},
        {"currency": "USD", "balance": "5000.0"}
    ]
    
    # Setup mock current price
    trading_core.get_current_price = AsyncMock(return_value=50000.0)
    
    # Execute
    position = await trading_core.get_position("BTC-USD")
    
    # Assert
    assert position['size'] == 1.5
    assert position['current_value'] == 75000.0  # 1.5 * 50000.0
    mock_exchange_interface.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_get_position_eth(trading_core, mock_exchange_interface):
    """Test retrieving ETH position."""
    # Setup mock accounts response
    mock_exchange_interface.get_accounts.return_value = [
        {"currency": "BTC", "balance": "1.5"},
        {"currency": "ETH", "balance": "10.0"},
        {"currency": "USD", "balance": "5000.0"}
    ]
    
    # Setup mock current price
    trading_core.get_current_price = AsyncMock(return_value=3000.0)
    
    # Execute
    position = await trading_core.get_position("ETH-USD")
    
    # Assert
    assert position['size'] == 10.0
    assert position['current_value'] == 30000.0  # 10.0 * 3000.0
    mock_exchange_interface.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_get_position_no_account(trading_core, mock_exchange_interface):
    """Test retrieving position for currency with no account."""
    # Setup mock accounts response
    mock_exchange_interface.get_accounts.return_value = [
        {"currency": "BTC", "balance": "1.5"},
        {"currency": "ETH", "balance": "10.0"}
    ]
    
    # Setup mock current price
    trading_core.get_current_price = AsyncMock(return_value=1.0)
    
    # Execute
    position = await trading_core.get_position("LTC-USD")
    
    # Assert - should return default values since LTC account not found
    assert position['size'] == 0
    assert position['entry_price'] == 0
    assert position['current_value'] == 0
    mock_exchange_interface.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_get_position_api_error(trading_core, mock_exchange_interface):
    """Test error handling when API call fails."""
    # Setup mock to raise an exception
    mock_exchange_interface.get_accounts.side_effect = Exception("API error")
    
    # Execute
    position = await trading_core.get_position("BTC-USD")
    
    # Assert - should return default values with error field
    assert position['size'] == 0
    assert position['entry_price'] == 0
    assert position['current_value'] == 0
    assert 'error' in position
    assert 'API error' in position['error']
    mock_exchange_interface.get_accounts.assert_called_once()


@pytest.mark.asyncio
async def test_get_position_invalid_symbol_format(trading_core):
    """Test handling of invalid trading pair format."""
    # Execute
    position = await trading_core.get_position("BTCUSD")  # Missing hyphen
    
    # Assert - should return default values
    assert position['size'] == 0
    assert position['entry_price'] == 0
    assert position['current_value'] == 0
    # The error would be in the logs, not necessarily in the return value
