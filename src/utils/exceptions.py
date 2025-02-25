"""Custom exceptions for the trading system."""

class TradingException(Exception):
    """Base exception class for all trading related errors."""
    def __init__(self, message: str, error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class OrderExecutionError(TradingException):
    """Raised when there is an error executing an order."""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(f"Order execution error: {message}", error_code)

class ValidationError(TradingException):
    """Raised when there is an error validating order parameters."""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(f"Validation error: {message}", error_code)

class PositionError(TradingException):
    """Raised when there is an error related to position management."""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(f"Position error: {message}", error_code)

class ConfigurationError(TradingException):
    """Raised when there is an error in configuration."""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(f"Configuration error: {message}", error_code)

class ExchangeError(TradingException):
    """Raised when there is an error communicating with the exchange."""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(f"Exchange error: {message}", error_code)
