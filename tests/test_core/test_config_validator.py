import pytest
import json
from src.core.config_validator import ConfigValidator
from src.utils.exceptions import ConfigurationError

def test_load_valid_schema():
    """Test loading a valid JSON schema."""
    validator = ConfigValidator('config/config_schema.json')
    assert isinstance(validator.schema, dict)

def test_load_invalid_schema():
    """Test loading an invalid JSON schema."""
    with pytest.raises(ConfigurationError):
        ConfigValidator('config/invalid_schema.json')

def test_validate_valid_config():
    """Test validating a valid configuration."""
    validator = ConfigValidator('config/config_schema.json')
    config = {
        "trading_pairs": ["BTC-USD"],
        "risk_management": {
            "max_position_size": 5.0,
            "stop_loss_pct": 0.05,
            "max_daily_loss": 500.0,
            "max_open_orders": 5
        },
        "paper_trading": True,
        "api_key": "test_key",
            "api_secret": "test_secret",
            "private_key": "test_private_key",
            "order_settings": {
                "default_size": 0.01,
                "min_trade_interval": 60,
                "max_slippage_pct": 0.01
            },
        "logging": {
            "level": "INFO",
            "file_path": "logs/trading.log",
            "rotation": "1 day",
            "retention": "30 days"
        },
        "retry_settings": {
            "max_attempts": 3,
            "initial_delay": 1.0,
            "max_delay": 5.0,
            "backoff_factor": 2.0
        },
        "strategy_config": {
            "ma_window": 20,
            "rsi_window": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "short_window": 5,
            "long_window": 20
        },
        "config_version": 1
    }
    validator.validate_config(config)  # Should not raise an exception

def test_validate_invalid_config():
    """Test validating an invalid configuration."""
    validator = ConfigValidator('config/config_schema.json')
    config = {
        "trading_pairs": ["BTC-USD"],
        "risk_management": {
            "max_position_size": "invalid",  # Invalid data type
            "stop_loss_pct": 0.05,
            "max_daily_loss": 500.0,
            "max_open_orders": 5
        },
        "paper_trading": True,
        "api_key": "test_key",
        "api_secret": "test_secret",
         "order_settings": {
            "default_size": 0.01,
            "min_trade_interval": 60,
            "max_slippage_pct": 0.01
        },
        "logging": {
            "level": "INFO",
            "file_path": "logs/trading.log",
            "rotation": "1 day",
            "retention": "30 days"
        },
        "retry_settings": {
            "max_attempts": 3,
            "initial_delay": 1.0,
            "max_delay": 5.0,
            "backoff_factor": 2.0
        },
        "strategy_config": {
            "ma_window": 20,
            "rsi_window": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "short_window": 5,
            "long_window": 20
        },
        "config_version": 1
    }
    with pytest.raises(ConfigurationError):
        validator.validate_config(config)

def test_validate_missing_version():
    """Test validating a config with missing version."""
    validator = ConfigValidator('config/config_schema.json')
    config = {
        "trading_pairs": ["BTC-USD"],
        "risk_management": {
            "max_position_size":  5.0,
            "stop_loss_pct": 0.05,
            "max_daily_loss": 500.0,
            "max_open_orders": 5
        },
        "paper_trading": True,
        "api_key": "test_key",
        "api_secret": "test_secret",
         "order_settings": {
            "default_size": 0.01,
            "min_trade_interval": 60,
            "max_slippage_pct": 0.01
        },
        "logging": {
            "level": "INFO",
            "file_path": "logs/trading.log",
            "rotation": "1 day",
            "retention": "30 days"
        },
        "retry_settings": {
            "max_attempts": 3,
            "initial_delay": 1.0,
            "max_delay": 5.0,
            "backoff_factor": 2.0
        },
        "strategy_config": {
            "ma_window": 20,
            "rsi_window": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "short_window": 5,
            "long_window": 20
        }
    }
    with pytest.raises(ConfigurationError):
        validator.validate_config(config)

def test_validate_invalid_version():
    """Test validating an invalid version."""
    validator = ConfigValidator('config/config_schema.json')
    config = {
        "trading_pairs": ["BTC-USD"],
        "risk_management": {
            "max_position_size":  5.0,
            "stop_loss_pct": 0.05,
            "max_daily_loss": 500.0,
            "max_open_orders": 5
        },
        "paper_trading": True,
        "api_key": "test_key",
        "api_secret": "test_secret",
         "order_settings": {
            "default_size": 0.01,
            "min_trade_interval": 60,
            "max_slippage_pct": 0.01
        },
        "logging": {
            "level": "INFO",
            "file_path": "logs/trading.log",
            "rotation": "1 day",
            "retention": "30 days"
        },
        "retry_settings": {
            "max_attempts": 3,
            "initial_delay": 1.0,
            "max_delay": 5.0,
            "backoff_factor": 2.0
        },
        "strategy_config": {
            "ma_window": 20,
            "rsi_window": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "short_window": 5,
            "long_window": 20
        },
        "config_version": "invalid"
    }
    with pytest.raises(ConfigurationError):
        validator.validate_config(config)

@pytest.fixture
def invalid_schema_file(tmp_path):
    """Fixture for an invalid schema file."""
    invalid_schema = {"type": "invalid"}  # This is not a valid schema
    schema_file = tmp_path / "invalid_schema.json"
    with open(schema_file, "w") as f:
        json.dump(invalid_schema, f)
    return str(schema_file)

def test_load_invalid_schema_file(invalid_schema_file):
    """Test loading an invalid JSON schema file."""
    with pytest.raises(ConfigurationError) as excinfo:
        ConfigValidator(invalid_schema_file)
    assert "Invalid schema file" in str(excinfo.value)
