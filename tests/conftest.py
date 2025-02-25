"""Common test fixtures for the trading system."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from decimal import Decimal

from src.core import TradingCore, ConfigManager
from src.utils.exceptions import TradingException

@pytest.fixture
def mock_exchange():
    """Create a mock exchange interface."""
    exchange = MagicMock()
    exchange.buy = AsyncMock()
    exchange.sell = AsyncMock()
    exchange.buy.return_value = {
        'order_id': '12345',
        'status': 'filled'
    }
    exchange.sell.return_value = {
        'order_id': '12346',
        'status': 'filled'
    }
    return exchange

@pytest.fixture
def mock_risk_manager():
    """Create a mock risk manager."""
    risk_manager = MagicMock()
    risk_manager.check_order_risk = AsyncMock(return_value=True)
    return risk_manager

@pytest.fixture
def valid_config():
    """Create a valid test configuration."""
    return {
        'trading_pairs': ['BTC-USD', 'ETH-USD'],
        'risk_management': {
            'max_position_size': 5.0,
            'stop_loss_pct': 0.05,
            'max_daily_loss': 500.0,
            'max_open_orders': 5
        },
        'paper_trading': True,
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'order_settings': {
            'default_size': 0.01,
            'min_trade_interval': 60,
            'max_slippage_pct': 0.01
        }
    }

@pytest.fixture
def config_file(tmp_path, valid_config):
    """Create a temporary configuration file."""
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(valid_config, f)
    return config_file

@pytest.fixture
def config_manager(config_file):
    """Create a ConfigManager instance with test configuration."""
    return ConfigManager(str(config_file))

@pytest.fixture
async def trading_core(mock_exchange, mock_risk_manager, config_file):
    """Create a TradingCore instance with mocked dependencies."""
    core = TradingCore(
        config_path=str(config_file),
        exchange_interface=mock_exchange,
        risk_manager=mock_risk_manager
    )
    await core.initialize()
    return core

@pytest.fixture
def sample_trade_result():
    """Create a sample trade result."""
    return {
        'order_id': '12345',
        'trading_pair': 'BTC-USD',
        'side': 'buy',
        'size': '1.0',
        'price': '50000.0',
        'status': 'filled',
        'timestamp': '2025-02-21T12:00:00Z'
    }

@pytest.fixture
def sample_position():
    """Create a sample position."""
    return {
        'size': Decimal('1.0'),
        'entry_price': Decimal('50000.0')
    }

@pytest.fixture(autouse=True)
def mock_logging(mocker):
    """Mock logging to avoid writing to log files during tests."""
    return mocker.patch('logging.getLogger')

@pytest.fixture
def make_trading_exception():
    """Factory fixture for creating TradingException instances."""
    def _make_exception(message='Test error', error_code=None):
        return TradingException(message, error_code)
    return _make_exception
