"""
Configuration management for the trading system.

This module handles loading, validation, and management of trading system configuration,
including risk parameters, trading pairs, and API credentials. It provides a robust
interface for accessing and updating configuration with proper validation and error handling.

Key features:
- Configuration loading and validation
- Risk parameter management
- Trading pair validation
- Environment variable integration
- Configuration updates with validation
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from dotenv import load_dotenv

from .config_validator import ConfigValidator
from ..utils.exceptions import ConfigurationError

# Configure module logger
logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to parent loggers

load_dotenv()

@dataclass
class RiskConfig:
    """
    Risk management configuration parameters.
    
    Attributes:
        max_position_size (Decimal): Maximum allowed position size
        stop_loss_pct (float): Stop loss percentage
        max_daily_loss (Decimal): Maximum allowed daily loss
        max_open_orders (int): Maximum number of open orders
    """
    max_position_size: Decimal
    stop_loss_pct: float
    max_daily_loss: Decimal
    max_open_orders: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskConfig':
        """
        Create RiskConfig from dictionary.
        
        Args:
            data: Dictionary containing risk configuration parameters
            
        Returns:
            RiskConfig: Instance with parsed configuration
            
        Raises:
            ConfigurationError: If risk parameters are invalid
        """
        logger.debug("Parsing risk configuration")
        try:
            config = cls(
                max_position_size=Decimal(str(data.get('max_position_size', '5.0'))),
                stop_loss_pct=float(data.get('stop_loss_pct', '0.05')),
                max_daily_loss=Decimal(str(data.get('max_daily_loss', '500.0'))),
                max_open_orders=int(data.get('max_open_orders', '5'))
            )
            logger.debug(f"Risk config created: {config}")
            return config
        except (ValueError, TypeError, InvalidOperation) as e:
            error_msg = f"Invalid risk configuration: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

@dataclass
class TradingConfig:
    """
    Trading configuration parameters.
    
    Attributes:
        trading_pairs (List[str]): List of trading pairs to monitor
        risk_config (RiskConfig): Risk management configuration
        paper_trading (bool): Whether paper trading is enabled
        api_key (Optional[str]): Coinbase API key
        private_key (Optional[str]): Coinbase API private key
        strategy_config (Dict[str, Any]): Strategy-specific configuration
    """
    trading_pairs: List[str]
    risk_config: RiskConfig
    paper_trading: bool
    api_key: Optional[str]
    private_key: Optional[str]
    strategy_config: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingConfig':
        """
        Create TradingConfig from dictionary.
        
        Args:
            data: Dictionary containing trading configuration
            
        Returns:
            TradingConfig: Instance with parsed configuration
            
        Raises:
            ConfigurationError: If trading parameters are invalid
        """
        logger.debug("Parsing trading configuration")
        try:
            trading_pairs = data.get('trading_pairs', ['BTC-USD'])
            if not isinstance(trading_pairs, list) or not all(isinstance(p, str) for p in trading_pairs):
                error_msg = "Trading pairs must be a list of strings"
                logger.error(error_msg)
                raise ValueError(error_msg)

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
            
            config = cls(
                trading_pairs=trading_pairs,
                risk_config=RiskConfig.from_dict(data.get('risk_management', {})),
                paper_trading=bool(data.get('paper_trading', True)),
                api_key=str(api_key) if api_key else None,
                private_key=str(data.get('private_key')) if data.get('private_key') else None,
                strategy_config=strategy_config
            )
            
            logger.info(f"Trading configuration created with {len(trading_pairs)} pairs")
            logger.debug(f"Trading pairs: {trading_pairs}")
            logger.debug(f"Paper trading: {config.paper_trading}")
            return config
            
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid trading configuration: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

class ConfigManager:
    """
    Manages configuration loading and validation.
    
    This class provides centralized configuration management with:
    - File-based configuration loading
    - Schema validation
    - Environment variable integration
    - Configuration updates with validation
    """

    def __init__(self, config_path: Optional[str] = None, schema_path: str = 'config/config_schema.json'):
        """
        Initialize the ConfigManager.
        
        Args:
            config_path: Path to configuration file (optional)
            schema_path: Path to JSON schema file
        """
        self.config_path = config_path or os.getenv('TRADING_CONFIG_PATH', 'config/config.json')
        self.schema_path = schema_path
        self.coinbase_api_key = os.getenv("COINBASE_API_KEY")
        self.coinbase_private_key = os.getenv("COINBASE_PRIVATE_KEY")
        self._config: Optional[TradingConfig] = None
        
        logger.info(f"Initializing ConfigManager with config path: {self.config_path}")
        self.validator = ConfigValidator(self.schema_path)

    def load_config(self) -> TradingConfig:
        """
        Load and validate configuration from file.
        
        Returns:
            TradingConfig: Validated trading configuration
            
        Raises:
            ConfigurationError: If configuration is invalid or cannot be loaded
        """
        logger.info(f"Loading configuration from {self.config_path}")
        try:
            if not os.path.exists(self.config_path):
                error_msg = f"Configuration file not found: {self.config_path}"
                logger.error(error_msg)
                raise ConfigurationError(error_msg)

            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            logger.debug("Validating configuration against schema")
            self.validator.validate_config(config_data)

            strategy_config_data = config_data.get('strategy_config', {})
            logger.debug(f"Loading strategy configuration: {strategy_config_data}")
            
            self._config = TradingConfig.from_dict({
                **config_data,
                'strategy': strategy_config_data
            })
            
            logger.info("Configuration loaded and validated successfully")
            return self._config

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"Error loading configuration: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

    @property
    def config(self) -> TradingConfig:
        """
        Get the current configuration.
        
        Returns:
            TradingConfig: Current trading configuration
        """
        if self._config is None:
            logger.debug("Configuration not loaded, loading now")
            return self.load_config()
        return self._config

    def get_test_config(self) -> TradingConfig:
        """
        Get a test configuration for development/testing.
        
        Returns:
            TradingConfig: Test configuration instance
        """
        logger.info("Creating test configuration")
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
            'api_secret': self.coinbase_private_key,
            'strategy': {
                'ma_window': 20
            }
        }
        
        logger.debug("Creating TradingConfig from test configuration")
        return TradingConfig.from_dict(test_config)

    def validate_trading_pair(self, trading_pair: str) -> bool:
        """
        Validate if a trading pair is configured.
        
        Args:
            trading_pair: Trading pair to validate
            
        Returns:
            bool: True if trading pair is valid
        """
        is_valid = trading_pair in self.config.trading_pairs
        logger.debug(f"Trading pair validation - {trading_pair}: {'valid' if is_valid else 'invalid'}")
        return is_valid

    def get_risk_params(self) -> RiskConfig:
        """
        Get risk management parameters.
        
        Returns:
            RiskConfig: Current risk configuration
        """
        logger.debug("Retrieving risk parameters")
        return self.config.risk_config

    def is_paper_trading(self) -> bool:
        """
        Check if paper trading is enabled.
        
        Returns:
            bool: True if paper trading is enabled
        """
        logger.debug(f"Checking paper trading mode: {self.config.paper_trading}")
        return self.config.paper_trading

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        This method updates the configuration and saves it to the config file.
        
        Args:
            updates: Dictionary containing configuration updates
            
        Raises:
            ConfigurationError: If updates are invalid
        """
        logger.info("Updating configuration")
        try:
            if self._config is None:
                logger.debug("Configuration not loaded, loading before update")
                self.load_config()

            current_config = self._config.__dict__.copy()
            logger.debug(f"Applying updates: {updates}")
            current_config.update(updates)
            
            if 'risk_config' in current_config and isinstance(current_config['risk_config'], RiskConfig):
                risk_obj = current_config.pop('risk_config')
                current_config['risk_management'] = risk_obj.__dict__
                
            self._config = TradingConfig.from_dict(current_config)

            logger.debug(f"Saving updated configuration to {self.config_path}")
            with open(self.config_path, 'w') as f:
                json.dump(current_config, f, indent=4, default=str)
                
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            error_msg = f"Failed to update configuration: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
