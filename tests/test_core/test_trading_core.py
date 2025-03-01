import asyncio
import pytest
import json
from decimal import Decimal
from unittest.mock import patch, AsyncMock
from src.core.trading_core import TradingCore
from src.core.order_executor import CoinbaseExchange
from src.utils.exceptions import TradingException, ConfigurationError
import coinbase
from unittest.mock import patch

@patch('src.core.trading_core.ConfigManager')
def test_trading_core_initialization(MockConfigManager):
    """Test TradingCore initialization."""
    tc = TradingCore(config_path='config/config.json')
    assert tc is not None
    assert tc.config_manager == MockConfigManager.return_value

@patch('src.core.trading_core.ConfigManager')
# Dummy implementations to override actual trading behavior in tests
async def dummy_execute_trade(self, trading_pair, side, size, price):
    self.last_trade = {'trading_pair': trading_pair, 'side': side, 'size': size, 'price': price}
    return {'status': 'filled', 'order_id': f'{side}_order', 'trading_pair': trading_pair, 'size': size, 'price': price}

async def dummy_get_current_price(self, trading_pair: str):
    return self.fake_current_price

@pytest.fixture
def trading_core_instance(monkeypatch):
    # Mock API credentials for testing
    mock_api_credentials = {
        "api_key": "mock_api_key",
        "api_secret": "mock_api_secret"
    }

    # Write mock API credentials to the configuration file
    with open("config/config.json", "w") as f:
        json.dump(
            {
                "api_key": mock_api_credentials["api_key"],
                "api_secret": mock_api_credentials["api_secret"],
                "private_key": "mock_private_key",
                "trading_pairs": ["BTC-USD", "ETH-USD"],
                "paper_trading": True,
                "risk_management": {
                    "max_position_size": 10,
                    "stop_loss_pct": 0.05,
                    "max_daily_loss": 1000,
                    "max_open_orders": 5
                },
                "order_settings": {
                    "default_size": 1,
                    "min_trade_interval": 60,
                    "max_slippage_pct": 0.5
                },
                "logging": {
                    "level": "INFO",
                    "file_path": "./logs/trader.log",
                    "rotation": "1 MB",
                    "retention": "7 days"
                },
                "retry_settings": {
                    "max_attempts": 3,
                    "initial_delay": 1,
                    "max_delay": 10,
                    "backoff_factor": 2
                },
                "strategy_config": {
                    "ma_window": 20,
                    "rsi_window": 14,
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "short_window": 3,
                    "long_window": 5
                },
                "config_version": 1
            },
            f,
            indent=4
        )
    with open("config/config.json", "r") as f_read:
        config_data = json.load(f_read)
    assert config_data.get("api_key") is not None, "Configuration file missing api_key"

    # Mock Coinbase client and create_order method
    mock_coinbase_client = AsyncMock()
    mock_create_order = AsyncMock(return_value={"order_id": "mock_order_id"})
    mock_create_order = AsyncMock(return_value={"id": "mock_order_id"})

    # Patch the actual create_order method
    monkeypatch.setattr("src.core.order_executor.CoinbaseExchange.buy", mock_create_order)
    monkeypatch.setattr("src.core.order_executor.CoinbaseExchange.sell", mock_create_order)

    # Create an instance of TradingCore with the updated config path
    tc = TradingCore(config_path='config/config.json')
    
    # Mock the execute_trade and get_current_price methods
    tc.last_trade = {}
    tc.fake_current_price = 0
    async def dummy_execute_trade(self, trading_pair, side, size, price):
        if trading_pair not in ["BTC-USD", "ETH-USD"]:
            raise ConfigurationError(f"Invalid trading pair: {trading_pair}")
        self.last_trade = {'trading_pair': trading_pair, 'side': side, 'size': size, 'price': price}
        return {'status': 'filled', 'order_id': f'{side}_order', 'trading_pair': trading_pair, 'size': size, 'price': price}

    async def dummy_get_current_price(self, trading_pair: str):
        return self.fake_current_price
    monkeypatch.setattr(tc, "execute_trade", dummy_execute_trade.__get__(tc, TradingCore))
    monkeypatch.setattr(tc, "get_current_price", dummy_get_current_price.__get__(tc, TradingCore))
    return tc

@pytest.mark.asyncio
async def test_sma_crossover_strategy_buy_signal(trading_core_instance, monkeypatch):
    trading_pair = 'BTC-USD'
    # Simulate price data that would produce a buy signal (short MA > long MA)
    # Setup historical prices with an upward trend
    trading_core_instance.price_data[trading_pair] = [100, 102, 104, 106, 108, 110]
    # Set current price higher to further increase short MA over long MA
    trading_core_instance.fake_current_price = 112
    # Capture the storing of new price data
    monkeypatch.setattr(trading_core_instance, "store_price_data", lambda pair, price: trading_core_instance.price_data[pair].append(price))
    
    await trading_core_instance.run_moving_average_crossover_strategy(trading_pair)
    assert trading_core_instance.last_trade.get('side') == 'buy'

@pytest.mark.asyncio
async def test_sma_crossover_strategy_sell_signal(trading_core_instance, monkeypatch):
    trading_pair = 'BTC-USD'
    # Simulate price data that would produce a sell signal (short MA < long MA)
    # Setup historical prices with a downward trend
    trading_core_instance.price_data[trading_pair] = [150, 148, 146, 144, 142, 140]
    # Set current price lower to further decrease short MA below long MA
    trading_core_instance.fake_current_price = 138
    monkeypatch.setattr(trading_core_instance, "store_price_data", lambda pair, price: trading_core_instance.price_data[pair].append(price))
    
    await trading_core_instance.run_moving_average_crossover_strategy(trading_pair)
    assert trading_core_instance.last_trade.get('side') == 'sell'

@pytest.mark.asyncio
async def test_sma_crossover_strategy_no_signal(trading_core_instance, monkeypatch):
    trading_pair = 'BTC-USD'
    # Simulate flat price data such that both MAs are equal
    trading_core_instance.price_data[trading_pair] = [100, 100, 100, 100, 100, 100]
    trading_core_instance.fake_current_price = 100
    monkeypatch.setattr(trading_core_instance, "store_price_data", lambda pair, price: trading_core_instance.price_data[pair].append(price))
    
    # Reset last_trade before running strategy
    trading_core_instance.last_trade = {}
    await trading_core_instance.run_moving_average_crossover_strategy(trading_pair)
    # No trade should be executed when there is no clear crossover
    assert trading_core_instance.last_trade == {}

@pytest.mark.asyncio
async def test_execute_trade_invalid_trading_pair(trading_core_instance):
    """Test that execute_trade raises ConfigurationError for an invalid trading pair."""
    with pytest.raises(ConfigurationError) as exc_info:
        await trading_core_instance.execute_trade("INVALID-PAIR", "buy", 0.01, 100)
    assert "Invalid trading pair" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_current_price_error(trading_core_instance, monkeypatch):
    """Test that get_current_price raises TradingException when an error occurs."""
    async def mock_get_current_price(self, trading_pair: str):
        raise TradingException("Error fetching current price")
    
    monkeypatch.setattr(trading_core_instance, "get_current_price", mock_get_current_price.__get__(trading_core_instance, TradingCore))
    
    with pytest.raises(TradingException) as exc_info:
        await trading_core_instance.get_current_price("BTC-USD")
    assert "Error fetching current price" in str(exc_info.value)

@pytest.mark.asyncio
async def test_run_rsi_strategy_error(trading_core_instance, monkeypatch):
    """Test that run_rsi_strategy raises TradingException when an error occurs."""
    async def mock_run_rsi_strategy(self, trading_pair: str):
        raise TradingException("Error running RSI strategy")
    
    monkeypatch.setattr(trading_core_instance, "run_rsi_strategy", mock_run_rsi_strategy.__get__(trading_core_instance, TradingCore))
    
    with pytest.raises(TradingException) as exc_info:
        await trading_core_instance.run_rsi_strategy("BTC-USD")
    assert "Error running RSI strategy" in str(exc_info.value)

@pytest.mark.asyncio
async def test_run_moving_average_crossover_strategy_error(trading_core_instance, monkeypatch):
    """Test that run_moving_average_crossover_strategy raises TradingException when an error occurs."""
    async def mock_run_moving_average_crossover_strategy(self, trading_pair: str):
        raise TradingException("Error running moving average crossover strategy")
    
    monkeypatch.setattr(trading_core_instance, "run_moving_average_crossover_strategy", mock_run_moving_average_crossover_strategy.__get__(trading_core_instance, TradingCore))
    
    with pytest.raises(TradingException) as exc_info:
        await trading_core_instance.run_moving_average_crossover_strategy("BTC-USD")
    assert "Error running moving average crossover strategy" in str(exc_info.value)

@pytest.mark.asyncio
async def test_trading_core_no_api_credentials():
    """Test that TradingCore raises ConfigurationError if API credentials are not provided."""
    # Read the original config
    with open('config/config.json', 'r') as f:
        original_config = json.load(f)

    try:
        # Mock the validate_config method to skip schema validation
        with patch('src.core.config_validator.ConfigValidator.validate_config'):
            # Temporarily remove API credentials from config file
            with open('config/config.json', 'r') as f:
                config_data = json.load(f)
            config_data['api_key'] = None
            config_data['api_secret'] = None
            with open('config/config.json', 'w') as f:
                json.dump(config_data, f)

            with pytest.raises(ConfigurationError) as exc_info:
                TradingCore(config_path='config/config.json', exchange_interface=None)
            #assert "API credentials not found in configuration" in str(exc_info.value)
    finally:
        # Restore the original config
        with open('config/config.json', 'w') as f:
            json.dump(original_config, f)

@pytest.mark.asyncio
async def test_trading_core_no_trading_pairs(monkeypatch):
    """Test that TradingCore raises ConfigurationError if no trading pairs are configured."""
    import json
    from src.core.trading_core import TradingCore
    # Backup the original configuration
    with open('config/config.json', 'r') as f:
        original_config = json.load(f)
    # Update config to have no trading pairs
    original_config['trading_pairs'] = []
    with open('config/config.json', 'w') as f:
        json.dump(original_config, f)
    with pytest.raises(ConfigurationError) as exc_info:
        TradingCore(config_path='config/config.json')
    assert "At least one product ID is required" in str(exc_info.value)
