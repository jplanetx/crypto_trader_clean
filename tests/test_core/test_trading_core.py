import asyncio
import pytest
import json
from decimal import Decimal
from src.core.trading_core import TradingCore

# Dummy implementations to override actual trading behavior in tests
async def dummy_execute_trade(self, trading_pair, side, size, price):
    self.last_trade = {'trading_pair': trading_pair, 'side': side, 'size': size, 'price': price}
    return {'status': 'filled', 'order_id': f'{side}_order', 'trading_pair': trading_pair, 'size': size, 'price': price}

async def dummy_get_current_price(self, trading_pair: str):
    return self.fake_current_price

@pytest.fixture
def trading_core_instance(monkeypatch):
    # Load API credentials from cdp_api_key.json
    with open('config/cdp_api_key.json') as f:
        api_credentials = json.load(f)
    
    # Debug: Print loaded API credentials
    print(f"Loaded API Key: {api_credentials['api_key']}")
    print(f"Loaded API Secret: {api_credentials['api_secret']}")
    
    # Create an instance of TradingCore with a dummy config path (won't be loaded in test)
    tc = TradingCore(config_path='config/config.json')
    
    # Set the API credentials directly in the TradingCore instance
    tc.config_manager.config.api_key = api_credentials['api_key']
    tc.config_manager.config.api_secret = api_credentials['api_secret']
    
    # Debug: Print API credentials set in config
    print(f"Config API Key: {tc.config_manager.config.api_key}")
    print(f"Config API Secret: {tc.config_manager.config.api_secret}")
    
    # Ensure the configuration is loaded correctly
    tc.config_manager.load_config()
    
    # Set up a dummy config for testing SMA strategy
    tc.config.strategy_config['short_window'] = 3
    tc.config.strategy_config['long_window'] = 5
    
    # Set a risk config attribute for testing; add max_trade_size if not present
    if not hasattr(tc.config.risk_config, 'max_trade_size'):
        setattr(tc.config.risk_config, 'max_trade_size', 1)
    
    # Override methods to avoid real async calls
    monkeypatch.setattr(tc, "execute_trade", dummy_execute_trade.__get__(tc, TradingCore))
    monkeypatch.setattr(tc, "get_current_price", dummy_get_current_price.__get__(tc, TradingCore))
    
    # Initialize price_data dict for our trading pair
    tc.price_data = {'BTC-USD': []}
    tc.last_trade = {}
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
