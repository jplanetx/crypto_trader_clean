"""Tests for OrderExecutor."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal

from src.core.order_executor import OrderExecutor, Order, OrderType, OrderSide, OrderStatus, CoinbaseExchange
from src.core.config_manager import ConfigManager, RiskConfig, TradingConfig
from src.utils.exceptions import ValidationError, OrderExecutionError, PositionError, ExchangeError


@pytest.fixture
def config_manager():
    """Create a ConfigManager with test configuration."""
    manager = ConfigManager()
    
    # Create risk config
    risk_config = RiskConfig(
        max_position_size=Decimal("1.0"),
        stop_loss_pct=0.05,
        max_daily_loss=Decimal("100.0"),
        max_open_orders=3
    )
    
    # Create trading config
    trading_config = TradingConfig(
        trading_pairs=["BTC-USD", "ETH-USD"],
        risk_config=risk_config,
        paper_trading=True,
        api_key="test_key",
        api_secret="test_secret"
    )
    
    # Set test config
    manager._test_config = trading_config
    manager.config = trading_config
    
    return manager


@pytest.fixture
def mock_client():
    """Create a mock client."""
    client = MagicMock()
    client.get_current_price.return_value = 50000.0
    return client


@pytest.fixture
def order_executor(config_manager, mock_client):
    """Create an OrderExecutor instance."""
    return OrderExecutor(mock_client, config_manager)


def test_initialization(order_executor, mock_client, config_manager):
    """Test OrderExecutor initialization."""
    assert order_executor.client == mock_client
    assert order_executor.config_manager == config_manager
    assert order_executor.is_paper_trading == True
    assert isinstance(order_executor.open_orders, dict)
    assert isinstance(order_executor.order_history, dict)


def test_validate_order_valid(order_executor):
    """Test validating a valid order."""
    # Create a valid order
    order = Order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.1")
    )
    
    # Validate it
    is_valid, error_message = order_executor.validate_order(order)
    
    # Should be valid
    assert is_valid == True
    assert error_message is None


def test_validate_order_invalid_symbol(order_executor):
    """Test validating an order with an invalid symbol."""
    # Create an order with invalid symbol
    order = Order(
        symbol="INVALID-USD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.1")
    )
    
    # Validate it
    is_valid, error_message = order_executor.validate_order(order)
    
    # Should be invalid
    assert is_valid == False
    assert "not allowed" in error_message.lower()


def test_validate_order_size_too_large(order_executor):
    """Test validating an order that exceeds max position size."""
    # Create an order with too large size
    order = Order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("2.0")  # Exceeds max_position_size of 1.0
    )
    
    # Validate it
    is_valid, error_message = order_executor.validate_order(order)
    
    # Should be invalid
    assert is_valid == False
    assert "exceeds maximum" in error_message.lower()


def test_validate_order_too_many_open_orders(order_executor):
    """Test validating when there are too many open orders."""
    # Add max number of open orders
    for i in range(3):  # max_open_orders is 3
        order_id = f"test-order-{i}"
        order = Order(
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("50000"),
            client_order_id=order_id
        )
        order_executor.open_orders[order_id] = order
    
    # Create a new order
    order = Order(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.1")
    )
    
    # Validate it
    is_valid, error_message = order_executor.validate_order(order)
    
    # Should be invalid
    assert is_valid == False
    assert "too many open orders" in error_message.lower()


def test_execute_order_paper_market(order_executor, mock_client):
    """Test executing a paper market order."""
    # Execute a paper market order
    order = order_executor.execute_order(
        symbol="BTC-USD",
        side="buy",
        order_type="market",
        quantity="0.1"
    )
    
    # Verify order properties
    assert order.symbol == "BTC-USD"
    assert order.side == OrderSide.BUY
    assert order.order_type == OrderType.MARKET
    assert order.quantity == Decimal("0.1")
    assert order.status == OrderStatus.FILLED
    assert order.filled_quantity == Decimal("0.1")
    assert order.avg_fill_price == Decimal("50000")
    assert order.exchange_order_id is not None
    assert order.client_order_id in order_executor.order_history
    
    # Verify mock was called
    mock_client.get_current_price.assert_called_once_with("BTC-USD")


def test_execute_order_paper_limit(order_executor):
    """Test executing a paper limit order."""
    # Execute a paper limit order
    order = order_executor.execute_order(
        symbol="BTC-USD",
        side="sell",
        order_type="limit",
        quantity="0.1",
        price="60000"
    )
    
    # Verify order properties
    assert order.symbol == "BTC-USD"
    assert order.side == OrderSide.SELL
    assert order.order_type == OrderType.LIMIT
    assert order.quantity == Decimal("0.1")
    assert order.price == Decimal("60000")
    assert order.status == OrderStatus.OPEN
    assert order.exchange_order_id is not None


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
