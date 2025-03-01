"""Configuration management for the crypto trader application."""
import os
import json
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional

from src.utils.exceptions import ConfigurationError


class RiskConfig:
    """Risk management configuration parameters."""

    def __init__(
        self,
        max_position_size: Decimal = Decimal("5.0"),
        stop_loss_pct: float = 0.05,
        max_daily_loss: Decimal = Decimal("500.0"),
        max_open_orders: int = 5,
    ):
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.max_daily_loss = max_daily_loss
        self.max_open_orders = max_open_orders

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskConfig":
        """Create a RiskConfig instance from a dictionary.

        Args:
            data: Dictionary containing risk configuration parameters.

        Returns:
            RiskConfig instance.

        Raises:
            ConfigurationError: If validation fails.
        """
        errors = []
        max_position_size = Decimal("5.0")  # Default value
        stop_loss_pct = 0.05  # Default value
        max_daily_loss = Decimal("500.0")  # Default value
        max_open_orders = 5  # Default value
        
        # Validate max_position_size
        if "max_position_size" in data:
            try:
                max_position_size = Decimal(str(data["max_position_size"]))
                if max_position_size <= Decimal("0"):
                    errors.append("max_position_size must be positive")
            except (InvalidOperation, ValueError, TypeError):
                errors.append("max_position_size must be a valid number")
            
        # Validate stop_loss_pct
        if "stop_loss_pct" in data:
            try:
                stop_loss_pct = float(data["stop_loss_pct"])
                if stop_loss_pct <= 0 or stop_loss_pct >= 1:
                    errors.append("stop_loss_pct must be between 0 and 1")
            except (ValueError, TypeError):
                errors.append("stop_loss_pct must be a valid number")
            
        # Validate max_daily_loss
        if "max_daily_loss" in data:
            try:
                max_daily_loss = Decimal(str(data["max_daily_loss"]))
                if max_daily_loss <= Decimal("0"):
                    errors.append("max_daily_loss must be positive")
            except (InvalidOperation, ValueError, TypeError):
                errors.append("max_daily_loss must be a valid number")
            
        # Validate max_open_orders
        if "max_open_orders" in data:
            try:
                max_open_orders = int(data["max_open_orders"])
                if max_open_orders <= 0:
                    errors.append("max_open_orders must be positive")
            except (ValueError, TypeError):
                errors.append("max_open_orders must be a valid integer")

        # If any validation errors occurred, raise ConfigurationError
        if errors:
            raise ConfigurationError(f"Invalid risk configuration: {'; '.join(errors)}")
            
        return cls(
            max_position_size=max_position_size,
            stop_loss_pct=stop_loss_pct,
            max_daily_loss=max_daily_loss,
            max_open_orders=max_open_orders,
        )


class TradingConfig:
    """Trading configuration parameters."""

    def __init__(
        self,
        trading_pairs: List[str],
        risk_config: RiskConfig,
        paper_trading: bool = True,
        api_key: str = "",
        api_secret: str = "",
        private_key: str = "",
        strategy_config: Dict[str, Any] = None,
        order_settings: Dict[str, Any] = None,
        logging: Dict[str, Any] = None,
        retry_settings: Dict[str, Any] = None,
        config_version: int = 1,
    ):
        self.trading_pairs = trading_pairs
        self.risk_config = risk_config
        self.paper_trading = paper_trading
        self.api_key = api_key
        self.api_secret = api_secret
        self.private_key = private_key
        self.strategy_config = strategy_config or {}
        self.order_settings = order_settings or {}
        self.logging = logging or {}
        self.retry_settings = retry_settings or {}
        self.config_version = config_version

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingConfig":
        """Create a TradingConfig instance from a dictionary.

        Args:
            data: Dictionary containing trading configuration parameters.

        Returns:
            TradingConfig instance.

        Raises:
            ConfigurationError: If validation fails.
        """
        errors = []
        
        # Set default values
        trading_pairs = ["BTC-USD"]
        paper_trading = True
        risk_config = None
        api_key = ""
        api_secret = ""
        private_key = ""
        strategy_config = {}
        order_settings = {}
        logging = {}
        retry_settings = {}
        config_version = 1
        
        # Validate trading_pairs
        if "trading_pairs" in data:
            if not isinstance(data["trading_pairs"], list):
                errors.append("trading_pairs must be a list")
            else:
                trading_pairs = data["trading_pairs"]
            
        # Validate paper_trading
        if "paper_trading" in data:
            if not isinstance(data["paper_trading"], bool):
                errors.append("paper_trading must be a boolean")
            else:
                paper_trading = data["paper_trading"]
            
        # Process risk_config
        try:
            risk_config = RiskConfig.from_dict(data.get("risk_management", {}))
        except ConfigurationError as e:
            errors.append(str(e))
        
        # If risk_config is None (due to exception), create a default one
        if risk_config is None:
            risk_config = RiskConfig()
            
        # Validate other fields
        if "api_key" in data:
            api_key = str(data["api_key"])
            
        if "api_secret" in data:
            api_secret = str(data["api_secret"])
            
        if "private_key" in data:
            private_key = str(data["private_key"])
            
        if "strategy_config" in data:
            if not isinstance(data["strategy_config"], dict):
                errors.append("strategy_config must be a dictionary")
            else:
                strategy_config = data["strategy_config"]
                
        if "order_settings" in data:
            if not isinstance(data["order_settings"], dict):
                errors.append("order_settings must be a dictionary")
            else:
                order_settings = data["order_settings"]
                
        if "logging" in data:
            if not isinstance(data["logging"], dict):
                errors.append("logging must be a dictionary")
            else:
                logging = data["logging"]
                
        if "retry_settings" in data:
            if not isinstance(data["retry_settings"], dict):
                errors.append("retry_settings must be a dictionary")
            else:
                retry_settings = data["retry_settings"]
                
        if "config_version" in data:
            try:
                config_version = int(data["config_version"])
                if config_version < 1:
                    errors.append("config_version must be a positive integer")
            except (ValueError, TypeError):
                errors.append("config_version must be an integer")
        
        # If any validation errors occurred, raise ConfigurationError
        if errors:
            raise ConfigurationError(f"Invalid trading configuration: {'; '.join(errors)}")
            
        return cls(
            trading_pairs=trading_pairs,
            risk_config=risk_config,
            paper_trading=paper_trading,
            api_key=api_key,
            api_secret=api_secret,
            private_key=private_key,
            strategy_config=strategy_config,
            order_settings=order_settings,
            logging=logging,
            retry_settings=retry_settings,
            config_version=config_version,
        )


class ConfigManager:
    """Manages configuration loading, validation, and updates."""

    def __init__(self, config_file_path: str = None):
        """Initialize ConfigManager.

        Args:
            config_file_path: Path to the configuration file.
        """
        self.config_file_path = config_file_path
        self.config = None
        self._test_config = None
        self._test_config_data = None

    def load_config(self) -> TradingConfig:
        """Load configuration from file.

        Returns:
            TradingConfig instance.

        Raises:
            ConfigurationError: If configuration loading fails.
        """
        if not self.config_file_path or not os.path.exists(self.config_file_path):
            raise ConfigurationError("Configuration file not found")

        try:
            with open(self.config_file_path, "r") as f:
                config_data = json.load(f)
        except json.JSONDecodeError:
            raise ConfigurationError("Invalid JSON in configuration file")
        except Exception as e:
            raise ConfigurationError(f"Failed to read configuration file: {e}")

        self.config = TradingConfig.from_dict(config_data)
        return self.config

    def set_test_config(self, config_data: Dict[str, Any]) -> None:
        """Set test configuration.

        Args:
            config_data: Dictionary containing test configuration data.
        """
        # Store both raw data and processed config
        self._test_config_data = config_data.copy()
        self._test_config = TradingConfig.from_dict(config_data)

    def get_test_config(self) -> TradingConfig:
        """Get test configuration.

        Returns:
            TradingConfig instance.

        Raises:
            ConfigurationError: If test configuration is not set.
        """
        if self._test_config is None:
            raise ConfigurationError("Test configuration not set")
        return self._test_config

    def validate_trading_pair(self, trading_pair: str) -> bool:
        """Validate if a trading pair is configured.

        Args:
            trading_pair: Trading pair to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not self.config:
            return False
        return trading_pair in self.config.trading_pairs

    def get_risk_params(self) -> RiskConfig:
        """Get risk parameters.

        Returns:
            RiskConfig instance.

        Raises:
            ConfigurationError: If configuration is not loaded.
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded")
        return self.config.risk_config

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration.

        Args:
            updates: Dictionary containing configuration updates.

        Raises:
            ConfigurationError: If configuration update fails.
        """
        if not self.config:
            raise ConfigurationError("Configuration not loaded")

        # Load current config as dictionary
        with open(self.config_file_path, "r") as f:
            config_data = json.load(f)

        # Apply updates
        for key, value in updates.items():
            if isinstance(value, dict) and key in config_data and isinstance(config_data[key], dict):
                config_data[key].update(value)
            else:
                config_data[key] = value

        # Save updated config
        try:
            with open(self.config_file_path, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

        # Reload config
        self.config = TradingConfig.from_dict(config_data)
