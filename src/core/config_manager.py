"""
Configuration management for the trading system.
"""
import json
import os
from typing import Dict, Any, List, Optional
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from dotenv import load_dotenv

from .config_validator import ConfigValidator
from ..utils.exceptions import ConfigurationError

load_dotenv()

@dataclass
class RiskConfig:
    """Risk management configuration parameters."""
    max_position_size: Decimal
    stop_loss_pct: float
    max_daily_loss: Decimal
    max_open_orders: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskConfig':
        """Create RiskConfig from dictionary."""
        try:
            return cls(
                max_position_size=Decimal(str(data.get('max_position_size', '5.0'))),
                stop_loss_pct=float(data.get('stop_loss_pct', '0.05')),
                max_daily_loss=Decimal(str(data.get('max_daily_loss', '500.0'))),
                max_open_orders=int(data.get('max_open_orders', '5'))
            )
        except (ValueError, TypeError, InvalidOperation) as e:
            raise ConfigurationError(f"Invalid risk configuration: {str(e)}")

@dataclass
class TradingConfig:
    """Trading configuration parameters."""
    trading_pairs: List[str]
    risk_config: RiskConfig
    paper_trading: bool
    api_key: Optional[str]
    api_secret: Optional[str]
    strategy_config: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingConfig':
        """Create TradingConfig from dictionary."""
        try:
            trading_pairs = data.get('trading_pairs', ['BTC-USD'])
            if not isinstance(trading_pairs, list) or not all(isinstance(p, str) for p in trading_pairs):
                raise ValueError("Trading pairs must be a list of strings")

            api_key = data.get('api_key')
            api_secret = data.get('api_secret')
            strategy_config_data = data.get('strategy', {}) or data.get('strategy_config', {})
            default_strategy_config = {
                'ma_window': 20,
                'rsi_window': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            strategy_config = {**default_strategy_config, **strategy_config_data}

            return cls(
                trading_pairs=trading_pairs,
                risk_config=RiskConfig.from_dict(data.get('risk_management', {})),
                paper_trading=bool(data.get('paper_trading', True)),
                api_key=str(api_key) if api_key else None,
                api_secret=str(api_secret) if api_secret else None,
                strategy_config=strategy_config
            )
        except (ValueError, TypeError) as e:
            raise ConfigurationError(f"Invalid trading configuration: {str(e)}")

class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: Optional[str] = None, schema_path: str = 'config/config_schema.json'):
        self.config_path = config_path or os.getenv('TRADING_CONFIG_PATH', 'config/config.json')
        self.schema_path = schema_path
        self.coinbase_api_key = os.getenv("COINBASE_API_KEY")
        self.coinbase_api_secret = os.getenv("COINBASE_API_SECRET")
        self._config: Optional[TradingConfig] = None
        self.validator = ConfigValidator(self.schema_path)

    def load_config(self) -> TradingConfig:
        """Load and validate configuration from file."""
        try:
            if not os.path.exists(self.config_path):
                raise ConfigurationError(f"Configuration file not found: {self.config_path}")

            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Validate config
            self.validator.validate_config(config_data)

            # Load strategy config
            strategy_config_data = config_data.get('strategy_config', {})
            
            self._config = TradingConfig.from_dict({
                **config_data,
                'strategy': strategy_config_data
            })
            return self._config

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {str(e)}")

    @property
    def config(self) -> TradingConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

    def get_test_config(self) -> TradingConfig:
        """Get a test configuration for development/testing."""
        test_config = {
            'trading_pairs': ['BTC-USD'],
            'risk_management': {
                'max_position_size': 1.0,
                'stop_loss_pct': 0.02,
                'max_daily_loss': 100.0,
                'max_open_orders': 3
            },
            'paper_trading': True,
            'api_key': self.coinbase_api_key,
            'api_secret': self.coinbase_api_secret,
            'strategy': {
                'ma_window': 20
            }
        }
        return TradingConfig.from_dict(test_config)

    def validate_trading_pair(self, trading_pair: str) -> bool:
        """Validate if a trading pair is configured."""
        return trading_pair in self.config.trading_pairs

    def get_risk_params(self) -> RiskConfig:
        """Get risk management parameters."""
        return self.config.risk_config

    def is_paper_trading(self) -> bool:
        """Check if paper trading is enabled."""
        return self.config.paper_trading

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        if self._config is None:
            self.load_config()

        current_config = self._config.__dict__.copy()
        current_config.update(updates)
        if 'risk_config' in current_config and isinstance(current_config['risk_config'], RiskConfig):
            risk_obj = current_config.pop('risk_config')
            current_config['risk_management'] = risk_obj.__dict__
        self._config = TradingConfig.from_dict(current_config)

        # Save updated config to file
        with open(self.config_path, 'w') as f:
            json.dump(current_config, f, indent=4, default=str)
