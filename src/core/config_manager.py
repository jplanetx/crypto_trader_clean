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
        
        # Validate max_position_size
        try:
            max_position_size = Decimal(str(data.get("max_position_size", 5.0)))
        except (InvalidOperation, ValueError, TypeError):
            errors.append("max_position_size must be a valid number")
            max_position_size = Decimal("5.0")  # Use default
            
        # Validate stop_loss_pct
        try:
            stop_loss_pct = float(data.get("stop_loss_pct", 0.05))
        except (ValueError, TypeError):
            errors.append("stop_loss_pct must be a valid number")
            stop_loss_pct = 0.05  # Use default
            
        # Validate max_daily_loss
        try:
            max_daily_loss = Decimal(str(data.get("max_daily_loss", 500.0)))
        except (InvalidOperation, ValueError, TypeError):
            errors.append("max_daily_loss must be a valid number")
            max_daily_loss = Decimal("500.0")  # Use default
            
        # Validate max_open_orders
        try:
            max_open_orders = int(data.get("max_open_orders", 5))
        except (ValueError, TypeError):
            errors.append("max_open_orders must be a valid integer")
            max_open_orders = 5  # Use default

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
        
        # Validate trading_pairs
        trading_pairs_raw = data.get("trading_pairs", ["BTC-USD"])
        if not isinstance(trading_pairs_raw, list):
            errors.append("trading_pairs must be a list")
            trading_pairs = ["BTC-USD"]  # Use default
        else:
            trading_pairs = trading_pairs_raw
            
        # Validate paper_trading
        paper_trading_raw = data.get("paper_trading", True)
        if not isinstance(paper_trading_raw, bool):
            errors.append("paper_trading must be a boolean")
            paper_trading = True  # Use default
        else:
            paper_trading = paper_trading_raw
            
        # Process risk_config
        try:
            risk_config = RiskConfig.from_dict(data.get("risk_management", {}))
        except ConfigurationError as e:
            errors.append(str(e))
            risk_config = RiskConfig()  # Use default
            
        # Validate other fields
        try:
            api_key = str(data.get("api_key", ""))
            api_secret = str(data.get("api_secret", ""))
            private_key = str(data.get("private_key", ""))
            strategy_config = data.get("strategy_config", {})
            order_settings = data.get("order_settings", {})
            logging = data.get("logging", {})
            retry_settings = data.get("retry_settings", {})
            
            try:
                config_version = int(data.get("config_version", 1))
            except (ValueError, TypeError):
                errors.append("config_version must be an integer")
                config_version = 1  # Use default
                
        except Exception as e:
            errors.append(f"Error processing configuration: {e}")
        
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
