"""Tests for order_executor.py."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from src.core.order_executor import OrderExecutor, CoinbaseExchange
from src.core.config_manager import RiskConfig
from src.utils.exceptions import (
    OrderExecutionError,
    ValidationError,
    PositionError,
    ExchangeError
)

@pytest.fixture
def mock_exchange():
    """Mock CoinbaseExchange for testing."""
    exchange = AsyncMock(spec=CoinbaseExchange)
    exchange.buy.return_value = {'order_id': 'buy_order_id'}
    exchange.sell.return_value = {'order_id': 'sell_order_id'}
    return exchange

@pytest.fixture
def risk_config():
    """RiskConfig fixture."""
    return RiskConfig(
        max_position_size=5.0,
        stop_loss_pct=0.05,
        max_daily_loss=500.0,
        max_open_orders=5
    )

@pytest.fixture
def mock_risk_manager():
    """Mock RiskManager for testing."""
    risk_manager = AsyncMock()
    risk_manager.check_order_risk.return_value = True  # Assume all orders pass risk check
    return risk_manager

@pytest.fixture
def order_executor(mock_exchange, mock_risk_manager):
    """OrderExecutor fixture with mocked dependencies."""
    return OrderExecutor(exchange_interface=mock_exchange, risk_manager=mock_risk_manager)

@pytest.mark.asyncio
async def test_execute_buy_order(order_executor, mock_exchange):
    """Test successful execution of a buy order."""
    result = await order_executor.execute_order(
        side='buy',
        size=1.0,
        price=50000.0,
        trading_pair='BTC-USD'
    )
    
    assert result['status'] == 'filled'
    assert result['order_id'] == 'buy_order_id'
    assert mock_exchange.buy.called
    
@pytest.mark.asyncio
async def test_execute_sell_order(order_executor, mock_exchange):
    """Test successful execution of a sell order."""
    # First, create a position
    await order_executor.execute_order(
        side='buy',
        size=2.0,
        price=50000.0,
        trading_pair='BTC-USD'
    )
    
    result = await order_executor.execute_order(
        side='sell',
        size=1.0,
        price=50000.0,
        trading_pair='BTC-USD'
    )
    
    assert result['status'] == 'filled'
    assert result['order_id'] == 'sell_order_id'
    assert mock_exchange.sell.called

@pytest.mark.asyncio
async def test_execute_order_validation_error(order_executor):
    """Test order validation failure."""
    with pytest.raises(ValidationError):
        await order_executor.execute_order(
            side='invalid',
            size=0,
            price=-100,
            trading_pair=''
        )

@pytest.mark.asyncio
async def test_execute_order_exchange_error(order_executor, mock_exchange):
    """Test exchange error during order execution."""
    mock_exchange.buy.side_effect = ExchangeError("Coinbase API failed")
    
    with pytest.raises(OrderExecutionError, match="Coinbase API failed"):
        await order_executor.execute_order(
            side='buy',
            size=1.0,
            price=50000.0,
            trading_pair='BTC-USD'
        )

@pytest.mark.asyncio
async def test_execute_sell_order_with_position(order_executor, mock_exchange):
    """Test successful execution of a sell order with existing position."""
    # First, create a position
    await order_executor.execute_order('buy', 2.0, 50000.0, 'BTC-USD')
    
    # Now, sell part of the position
    result = await order_executor.execute_order('sell', 1.0, 55000.0, 'BTC-USD')
    
    assert result['status'] == 'filled'
    assert mock_exchange.sell.called

@pytest.mark.asyncio
async def test_execute_sell_exceeding_position(order_executor, mock_exchange):
    """Test attempting to sell more than the existing position."""
    # First, create a position
    await order_executor.execute_order('buy', 1.0, 50000.0, 'BTC-USD')
    
    # Now, try to sell more than we have
    with pytest.raises(PositionError, match="Insufficient position size for sell order"):
        await order_executor.execute_order('sell', 2.0, 55000.0, 'BTC-USD')

@pytest.mark.asyncio
async def test_risk_check_failure(order_executor, mock_risk_manager):
    """Test order exceeding risk limits."""
    mock_risk_manager.check_order_risk.return_value = False
    
    with pytest.raises(ValidationError, match="Order exceeds risk limits"):
        await order_executor.execute_order('buy', 1.0, 50000.0, 'BTC-USD')

@pytest.mark.asyncio
async def test_adjust_position(order_executor, mock_exchange):
    """Test adjusting position to a target size."""
    # Initial position
    await order_executor.execute_order('buy', 1.0, 50000.0, 'BTC-USD')
    
    # Adjust to a smaller position
    result = await order_executor.adjust_position('BTC-USD', 0.5, 60000.0)
    assert result is not None
    assert mock_exchange.sell.called
    
    # Adjust to a larger position
    result = await order_executor.adjust_position('BTC-USD', 1.0, 50000.0)
    assert result is not None
    assert mock_exchange.buy.called
    
    # No adjustment needed
    result = await order_executor.adjust_position('BTC-USD', 1.0, 50000.0)
    assert result is None

@pytest.mark.asyncio
async def test_position_tracking(order_executor, mock_exchange):
    """Test accurate position tracking through multiple orders."""
    # Initial buy
    await order_executor.execute_order('buy', 2.0, 50000.0, 'BTC-USD')
    position = order_executor.get_position('BTC-USD')
    assert position['size'] == Decimal('2.0')
    assert position['entry_price'] == Decimal('50000.0')

    # Add to position at different price
    await order_executor.execute_order('buy', 1.0, 55000.0, 'BTC-USD')
    position = order_executor.get_position('BTC-USD')
    assert position['size'] == Decimal('3.0')
    assert position['entry_price'] == pytest.approx(Decimal('51666.666666666666666666666667'))

    # Sell part of position
    await order_executor.execute_order('sell', 1.5, 60000.0, 'BTC-USD')
    position = order_executor.get_position('BTC-USD')
    assert position['size'] == Decimal('1.5')
    assert position['entry_price'] == pytest.approx(Decimal('51666.666666666666666666666667'))

    # Sell remaining position
    await order_executor.execute_order('sell', 1.5, 65000.0, 'BTC-USD')
    position = order_executor.get_position('BTC-USD')
    assert position['size'] == Decimal('0')
    assert position['entry_price'] == Decimal('0')
