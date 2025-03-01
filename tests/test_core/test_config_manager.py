"""Tests for the ConfigManager class."""
import pytest
import os
import json
from decimal import Decimal
from unittest.mock import patch, mock_open

from src.core.config_manager import ConfigManager, TradingConfig, RiskConfig
from src.utils.exceptions import ConfigurationError

@pytest.fixture
def valid_config_data():
    """Sample valid configuration data."""
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
        'private_key': 'test_private_key',
        'strategy_config': {
            'ma_window': 20,
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'short_window': 5,
            'long_window': 20
        },
        'order_settings': {
            'default_size': 0.1,
            'min_trade_interval': 60,
            'max_slippage_pct': 0.01
        },
        'logging': {
            'level': 'INFO',
            'file_path': 'logs/trading.log',
            'rotation': 'daily',
            'retention': '30 days'
        },
        'retry_settings': {
            'max_attempts': 3,
            'initial_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0
        },
        'config_version': 1
    }

@pytest.fixture
def config_file_path(tmp_path):
    """Create a temporary config file path."""
    return str(tmp_path / "test_config.json")

def test_risk_config_creation():
    """Test RiskConfig creation from dictionary."""
    data = {
        'max_position_size': 5.0,
        'stop_loss_pct': 0.05,
        'max_daily_loss': 500.0,
        'max_open_orders': 5
    }
    risk_config = RiskConfig.from_dict(data)
    
    assert risk_config.max_position_size == Decimal('5.0')
    assert abs(risk_config.stop_loss_pct - 0.05) < 1e-9
    assert risk_config.max_daily_loss == Decimal('500.0')
    assert risk_config.max_open_orders == 5

def test_risk_config_defaults():
    """Test RiskConfig default values."""
    risk_config = RiskConfig.from_dict({})
    
    assert risk_config.max_position_size == Decimal('5.0')
    assert abs(risk_config.stop_loss_pct - 0.05) < 1e-9
    assert risk_config.max_daily_loss == Decimal('500.0')
    assert risk_config.max_open_orders == 5

def test_risk_config_validation():
    """Test RiskConfig validation."""
    invalid_data = {
        'max_position_size': 'invalid',
        'stop_loss_pct': 'invalid',
        'max_daily_loss': 'invalid',
        'max_open_orders': 'invalid'
    }
    
    with pytest.raises(ConfigurationError):
        RiskConfig.from_dict({k: 'invalid' for k in invalid_data})

def test_trading_config_creation(valid_config_data):
    """Test TradingConfig creation from dictionary."""
    config = TradingConfig.from_dict(valid_config_data)
    
    assert config.trading_pairs == ['BTC-USD', 'ETH-USD']
    assert isinstance(config.risk_config, RiskConfig)
    assert config.paper_trading is True
    assert config.api_key == 'test_key'
    assert config.api_secret == 'test_secret'
    assert config.private_key == 'test_private_key'
    assert isinstance(config.strategy_config, dict)
    assert config.strategy_config['short_window'] == 5
    assert config.strategy_config['long_window'] == 20

def test_trading_config_validation():
    """Test TradingConfig validation."""
    invalid_data = {
        'trading_pairs': 'invalid',  # Should be a list
        'paper_trading': 'invalid'   # Should be boolean
    }
    
    with pytest.raises(ConfigurationError):
        TradingConfig.from_dict(invalid_data)

def test_config_manager_load_config(config_file_path, valid_config_data):
    """Test configuration loading from file."""
    # Write test config to temporary file
    with open(config_file_path, 'w') as f:
        json.dump(valid_config_data, f, indent=4)

    config_manager = ConfigManager(config_file_path)
    config = config_manager.load_config()
    
    assert isinstance(config, TradingConfig)
    assert config.trading_pairs == valid_config_data['trading_pairs']
    assert config.paper_trading == valid_config_data['paper_trading']
    assert config.strategy_config == valid_config_data['strategy_config']

def test_config_manager_missing_file():
    """Test handling of missing configuration file."""
    config_manager = ConfigManager('nonexistent.json')
    
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        config_manager.load_config()

def test_config_manager_invalid_json(config_file_path):
    """Test handling of invalid JSON in config file."""
    # Write invalid JSON to file
    with open(config_file_path, 'w') as f:
        f.write('invalid json')

    config_manager = ConfigManager(config_file_path)
    
    with pytest.raises(ConfigurationError, match="Invalid JSON"):
        config_manager.load_config()

def test_config_manager_get_test_config():
    """Test getting test configuration with explicit values."""
    config_manager = ConfigManager()
    test_config_data = {
        'trading_pairs': ['BTC-USD'],
        'risk_management': {
            'max_position_size': 1.0,
            'stop_loss_pct': 0.02,
            'max_daily_loss': 100.0,
            'max_open_orders': 3
        },
        'paper_trading': True,
        'api_key': 'test_api_key',
        'api_secret': 'test_api_secret',
        'private_key': 'test_private_key',
        'strategy_config': {
            'ma_window': 20,
            'rsi_window': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'short_window': 5,
            'long_window': 20
        },
        'order_settings': {
            'default_size': 0.1,
            'min_trade_interval': 60,
            'max_slippage_pct': 0.01
        },
        'logging': {
            'level': 'INFO',
            'file_path': 'logs/trading.log',
            'rotation': 'daily',
            'retention': '30 days'
        },
        'retry_settings': {
            'max_attempts': 3,
            'initial_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0
        },
        'config_version': 1
    }
    config_manager.set_test_config(test_config_data)
    test_config = config_manager.get_test_config()
    
    assert isinstance(test_config, TradingConfig)
    # Verify trading configuration
    assert 'BTC-USD' in test_config.trading_pairs
    assert test_config.paper_trading is True
    assert test_config.api_key == "test_api_key"
    assert test_config.api_secret == "test_api_secret"
    assert test_config.private_key == "test_private_key"
    # Explicitly verify risk management configuration
    assert test_config.risk_config.max_position_size == Decimal('1.0')
    assert abs(test_config.risk_config.stop_loss_pct - 0.02) < 1e-9
    assert test_config.risk_config.max_daily_loss == Decimal('100.0')
    assert test_config.risk_config.max_open_orders == 3
    # Verify strategy configuration
    assert test_config.strategy_config['ma_window'] == 20
    assert test_config.strategy_config['rsi_window'] == 14
    assert test_config.strategy_config['rsi_oversold'] == 30
    assert test_config.strategy_config['rsi_overbought'] == 70
    assert test_config.strategy_config['short_window'] == 5
    assert test_config.strategy_config['long_window'] == 20
    # Verify order settings
    assert test_config.order_settings['default_size'] == 0.1
    assert test_config.order_settings['min_trade_interval'] == 60
    assert test_config.order_settings['max_slippage_pct'] == 0.01
    # Verify logging configuration
    assert test_config.logging['level'] == 'INFO'
    assert test_config.logging['file_path'] == 'logs/trading.log'
    assert test_config.logging['rotation'] == 'daily'
    assert test_config.logging['retention'] == '30 days'
    # Verify retry settings
    assert test_config.retry_settings['max_attempts'] == 3
    assert test_config.retry_settings['initial_delay'] == 1.0
    assert test_config.retry_settings['max_delay'] == 60.0
    assert test_config.retry_settings['backoff_factor'] == 2.0
    # Verify config version
    assert test_config.config_version == 1

def test_validate_trading_pair(config_file_path, valid_config_data):
    """Test trading pair validation."""
    with open(config_file_path, 'w') as f:
        json.dump(valid_config_data, f)

    config_manager = ConfigManager(config_file_path)
    config_manager.load_config()
    
    assert config_manager.validate_trading_pair('BTC-USD') is True
    assert config_manager.validate_trading_pair('INVALID-PAIR') is False

def test_get_risk_params(config_file_path, valid_config_data):
    """Test retrieving risk parameters."""
    with open(config_file_path, 'w') as f:
        json.dump(valid_config_data, f)

    config_manager = ConfigManager(config_file_path)
    config_manager.load_config()
    risk_params = config_manager.get_risk_params()
    
    assert isinstance(risk_params, RiskConfig)
    assert risk_params.max_position_size == Decimal('5.0')
    assert abs(risk_params.stop_loss_pct - 0.05) < 1e-9

def test_update_config(config_file_path, valid_config_data):
    """Test configuration update functionality."""
    with open(config_file_path, 'w') as f:
        json.dump(valid_config_data, f, indent=4)

    config_manager = ConfigManager(config_file_path)
    config_manager.load_config()
    
    updates = {
        'paper_trading': False,
        'trading_pairs': ['ETH-USD'],
        'strategy_config': {'short_window': 10, 'long_window': 30}
    }
    
    config_manager.update_config(updates)
    
    assert config_manager.config.paper_trading is False
    assert config_manager.config.trading_pairs == ['ETH-USD']
    assert config_manager.config.strategy_config['short_window'] == 10
    assert config_manager.config.strategy_config['long_window'] == 30
    
    # Verify file was updated
    with open(config_file_path, 'r') as f:
        saved_config = json.load(f)
        assert saved_config['paper_trading'] is False
        assert saved_config['trading_pairs'] == ['ETH-USD']
        assert saved_config['strategy_config']['short_window'] == 10
        assert saved_config['strategy_config']['long_window'] == 30
