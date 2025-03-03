"""Package initialization."""
from .core import (
    OrderExecutor,
    TradingCore,
    ConfigManager,
    TradingConfig,
    RiskConfig
)

from .utils.exceptions import (
    TradingException,
    OrderExecutionError,
    ValidationError,
    PositionError,
    ConfigurationError,
    ExchangeError
)

__version__ = '0.1.0'

__all__ = [
    'OrderExecutor',
    'TradingCore',
    'ConfigManager',
    'TradingConfig',
    'RiskConfig',
    'TradingException',
    'OrderExecutionError',
    'ValidationError',
    'PositionError',
    'ConfigurationError',
    'ExchangeError'
]
