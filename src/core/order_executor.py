"""
Asynchronous order execution handler for the trading system.

This module provides a robust interface for executing trades on the Coinbase Advanced
Trade API with proper error handling, position tracking, and retry logic. It includes
comprehensive logging of all trading operations and validation steps.

Key features:
- Asynchronous order execution with retry capabilities
- Position tracking and management
- Risk limit validation
- Comprehensive error handling and logging
"""
import logging
import asyncio
import time
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.utils.exceptions import (
    OrderExecutionError,
    ValidationError,
    PositionError,
    ExchangeError
)
import coinbasepro

# Configure module logger
logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to parent loggers

class CoinbaseExchange:
    """
    Handles communication with the Coinbase Advanced Trade API.
    
    This class provides a clean interface for executing buy and sell orders
    through Coinbase's API with proper error handling and logging.
    """
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize the CoinbaseExchange with API credentials.
        
        Args:
            api_key (str): Coinbase API key for authentication
            api_secret (str): Coinbase API secret for authentication
            
        Raises:
            ExchangeError: If credentials are invalid or client initialization fails
        """
        if not api_key or not api_secret:
            logger.error("Missing API credentials")
            raise ExchangeError("API key and secret are required")
            
        self.api_key = api_key
        self.api_secret = api_secret
        
        try:
            self.client = coinbasepro.AuthenticatedClient(api_key, api_secret, "")
            logger.info("Successfully initialized CoinbasePro client")
        except Exception as e:
            logger.error(f"Failed to initialize CoinbasePro client: {e}")
            raise ExchangeError(f"Failed to initialize CoinbasePro client: {e}")

    async def connect(self) -> None:
        """
        Connect to the Coinbase API.
        """
        logger.info("Connecting to Coinbase API...")
        # No explicit connection needed for coinbasepro library
        logger.info("Coinbase API connection established")

    async def buy(self, trading_pair: str, size: float, price: float) -> Dict[str, Any]:
        """
        Place a buy order on Coinbase Advanced Trade API.
        
        Args:
            trading_pair (str): Trading pair symbol (e.g. 'BTC-USD')
            size (float): Order size in base currency
            price (float): Order price (note: using market orders, price is indicative)
            
        Returns:
            Dict[str, Any]: Order details from the exchange
            
        Raises:
            ExchangeError: If order placement fails
        """
        try:
            logger.info(f"Placing buy order - Pair: {trading_pair}, Size: {size}")
            if self.api_key == "test":
                logger.debug("Using test mode - returning dummy order")
                return {"order_id": "dummy_buy_order"}
                
            order = self.client.place_market_order(
                product_id=trading_pair,
                side='buy',
                size=size,
            )
            logger.info(f"Buy order placed successfully - Order ID: {order.get('id')}")
            return order
            
        except Exception as e:
            error_msg = f"Coinbase buy order failed: {str(e)}"
            logger.error(error_msg)
            raise ExchangeError(error_msg)

    async def sell(self, trading_pair: str, size: float, price: float) -> Dict[str, Any]:
        """
        Place a sell order on Coinbase Advanced Trade API.
        
        Args:
            trading_pair (str): Trading pair symbol (e.g. 'BTC-USD')
            size (float): Order size in base currency
            price (float): Order price (note: using market orders, price is indicative)
            
        Returns:
            Dict[str, Any]: Order details from the exchange
            
        Raises:
            ExchangeError: If order placement fails
        """
        try:
            logger.info(f"Placing sell order - Pair: {trading_pair}, Size: {size}")
            if self.api_key == "test":
                logger.debug("Using test mode - returning dummy order")
                return {"order_id": "dummy_sell_order"}
                
            order = self.client.place_market_order(
                product_id=trading_pair,
                side='sell',
                size=size,
            )
            logger.info(f"Sell order placed successfully - Order ID: {order.get('id')}")
            return order
            
        except Exception as e:
            error_msg = f"Coinbase sell order failed: {str(e)}"
            logger.error(error_msg)
            raise ExchangeError(error_msg)


class OrderExecutor:
    """
    Handles asynchronous order execution and position management.
    
    This class provides the core trading functionality with:
    - Asynchronous order execution with retry logic
    - Position tracking and management
    - Parameter validation
    - Risk management integration
    - Comprehensive error handling
    """

    def __init__(self, exchange_interface: CoinbaseExchange, risk_manager: Any = None):
        """
        Initialize the OrderExecutor.
        
        Args:
            exchange_interface (CoinbaseExchange): Interface for executing orders
            risk_manager (Any, optional): Risk management component. Defaults to None.
        """
        self.exchange_interface = exchange_interface
        self.risk_manager = risk_manager
        self.positions: Dict[str, Dict[str, Decimal]] = {}
        self.retry_attempts = 3
        self.retry_delay = 1.0  # seconds
        logger.info("OrderExecutor initialized")
        
    def _validate_order_params(self, side: str, size: float, price: float, trading_pair: str) -> None:
        """
        Validate order parameters before execution.
        
        Args:
            side (str): Order side ('buy' or 'sell')
            size (float): Order size in base currency
            price (float): Order price
            trading_pair (str): Trading pair symbol (e.g. 'BTC-USD')
            
        Raises:
            ValidationError: If any parameters are invalid
        """
        logger.debug(f"Validating order parameters - Side: {side}, Size: {size}, "
                    f"Price: {price}, Trading Pair: {trading_pair}")
                    
        if side not in ['buy', 'sell']:
            msg = f"Invalid order side: {side} (must be 'buy' or 'sell')"
            logger.error(msg)
            raise ValidationError(msg)
            
        if size <= 0:
            msg = f"Invalid order size: {size} (must be positive)"
            logger.error(msg)
            raise ValidationError(msg)
            
        if price <= 0:
            msg = f"Invalid order price: {price} (must be positive)"
            logger.error(msg)
            raise ValidationError(msg)
            
        if not trading_pair:
            msg = "Trading pair is required"
            logger.error(msg)
            raise ValidationError(msg)
            
        logger.debug("Order parameter validation successful")

    async def _execute_with_retry(self, operation, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Dict[str, Any]: Operation result
            
        Raises:
            OrderExecutionError: If all retry attempts fail
        """
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Execution attempt {attempt + 1}/{self.retry_attempts}")
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (attempt + 1)
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. "
                                f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                continue
                
        logger.error(f"All {self.retry_attempts} retry attempts failed")
        raise OrderExecutionError(f"Operation failed after {self.retry_attempts} attempts: {str(last_error)}")

    async def _update_position(
        self,
        trading_pair: str,
        side: str,
        size: float,
        price: float
    ) -> None:
        """
        Update internal position tracking after order execution.
        
        Args:
            trading_pair (str): Trading pair symbol
            side (str): Order side ('buy' or 'sell')
            size (float): Order size in base currency
            price (float): Order price
            
        This method maintains an accurate record of current positions and their
        entry prices, using weighted average for entry price calculations.
        
        Raises:
            PositionError: If position update fails
        """
        logger.debug(f"Updating position for {trading_pair} - Side: {side}, "
                    f"Size: {size}, Price: {price}")
                    
        try:
            if trading_pair not in self.positions:
                logger.debug(f"Initializing new position tracking for {trading_pair}")
                self.positions[trading_pair] = {'size': Decimal('0'), 'entry_price': Decimal('0')}

            position = self.positions[trading_pair]
            size_dec = Decimal(str(size))
            price_dec = Decimal(str(price))

            old_size = position['size']
            old_price = position['entry_price']

            if side == 'buy':
                new_size = position['size'] + size_dec
                if position['size'] == Decimal('0'):
                    new_entry_price = price_dec
                else:
                    total_value = (position['size'] * position['entry_price']) + (size_dec * price_dec)
                    new_entry_price = total_value / new_size
                position['size'] = new_size
                position['entry_price'] = new_entry_price
                
                logger.info(f"Updated {trading_pair} position after buy - "
                          f"New Size: {new_size}, New Entry Price: {new_entry_price}")
            else:  # sell
                new_size = position['size'] - size_dec
                position['size'] = new_size
                if new_size == Decimal('0'):
                    position['entry_price'] = Decimal('0')
                    logger.info(f"Closed {trading_pair} position")
                else:
                    logger.info(f"Updated {trading_pair} position after sell - "
                              f"New Size: {new_size}, Entry Price: {position['entry_price']}")
                              
            logger.debug(f"Position change summary for {trading_pair}:\n"
                        f"Size: {old_size} -> {position['size']}\n"
                        f"Entry Price: {old_price} -> {position['entry_price']}")
                        
        except Exception as e:
            logger.error(f"Error updating position for {trading_pair}: {e}")
            raise PositionError(f"Failed to update position: {e}")

    def get_position(self, trading_pair: str) -> Dict[str, Decimal]:
        """
        Get current position information for a trading pair.
        
        Args:
            trading_pair (str): Trading pair symbol
            
        Returns:
            Dict[str, Decimal]: Current position details including size and entry price
        """
        logger.debug(f"Retrieving position for {trading_pair}")
        return self.positions.get(trading_pair, {'size': Decimal('0'), 'entry_price': Decimal('0')})

    async def execute_order(
        self,
        side: str,
        size: float,
        price: float,
        trading_pair: str
    ) -> Dict[str, Any]:
        """
        Execute a trading order asynchronously.
        
        This method handles the complete order execution workflow including:
        - Parameter validation
        - Position limit checks
        - Risk management checks
        - Order execution with retry logic
        - Position tracking updates
        
        Args:
            side (str): Order side ('buy' or 'sell')
            size (float): Order size in base currency
            price (float): Order price
            trading_pair (str): Trading pair symbol (e.g. 'BTC-USD')
            
        Returns:
            Dict[str, Any]: Order execution details
            
        Raises:
            ValidationError: If parameters are invalid
            PositionError: If position limits are exceeded
            OrderExecutionError: If order execution fails
        """
        logger.info(f"Executing {side} order - Pair: {trading_pair}, Size: {size}, Price: {price}")
        
        try:
            # Validate parameters
            self._validate_order_params(side, size, price, trading_pair)
            
            # Check position limits for sell orders
            if side == 'sell':
                position = self.get_position(trading_pair)
                if Decimal(str(size)) > position.get('size', Decimal('0')):
                    msg = f"Insufficient position size for sell order: {size}"
                    logger.error(msg)
                    raise PositionError(msg)

            # Risk check if risk manager is configured
            if self.risk_manager:
                logger.debug("Performing risk check...")
                if not await self.risk_manager.check_order_risk(trading_pair, side, size, price):
                    msg = "Order exceeds risk limits"
                    logger.error(msg)
                    raise ValidationError(msg)

            # Execute order
            order_func = (
                self.exchange_interface.buy if side == 'buy'
                else self.exchange_interface.sell
            )
            
            result = await self._execute_with_retry(
                order_func,
                trading_pair=trading_pair,
                size=size,
                price=price
            )

            # Update position tracking
            await self._update_position(trading_pair, side, size, price)

            order_result = {
                'status': 'filled',
                'order_id': result.get('order_id', 'UNKNOWN'),
                'trading_pair': trading_pair,
                'side': side,
                'size': str(size),
                'price': str(price),
                'timestamp': datetime.now().astimezone().isoformat()
            }
            
            logger.info(f"Order executed successfully - ID: {order_result['order_id']}")
            logger.debug(f"Order details: {order_result}")
            return order_result

        except (ValidationError, PositionError) as e:
            logger.error(f"Order validation error: {str(e)}")
            raise
        except ExchangeError as e:
            logger.error(f"Exchange error during order execution: {str(e)}")
            if isinstance(e, OrderExecutionError):
                raise
            else:
                raise OrderExecutionError(str(e))
        except Exception as e:
            logger.exception("Unexpected error during order execution")
            raise OrderExecutionError(str(e))

    async def adjust_position(
        self,
        trading_pair: str,
        target_size: float,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Adjust position to match target size.
        
        This method calculates the required order to achieve the target position size
        and executes it if necessary.
        
        Args:
            trading_pair (str): Trading pair symbol
            target_size (float): Desired position size
            current_price (float): Current market price
            
        Returns:
            Optional[Dict[str, Any]]: Order result if adjustment was needed, None if no adjustment required
            
        Raises:
            OrderExecutionError: If position adjustment fails
        """
        logger.info(f"Adjusting position for {trading_pair} to target size: {target_size}")
        
        try:
            current_position = self.get_position(trading_pair)
            current_size = current_position['size']
            target_size_dec = Decimal(str(target_size))

            if current_size == target_size_dec:
                logger.info(f"No position adjustment needed for {trading_pair}")
                return None

            size_difference = abs(target_size_dec - current_size)
            side = 'buy' if target_size_dec > current_size else 'sell'
            
            logger.info(f"Executing {side} order to adjust position - "
                      f"Size: {float(size_difference)}")

            return await self.execute_order(
                side=side,
                size=float(size_difference),
                price=current_price,
                trading_pair=trading_pair
            )
            
        except Exception as e:
            logger.error(f"Failed to adjust position: {e}")
            raise OrderExecutionError(f"Position adjustment failed: {e}")

"""Order execution system for the crypto trader application."""
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
import time
from enum import Enum

from src.core.config_manager import ConfigManager
from src.utils.exceptions import OrderExecutionError, ValidationError

# Set up module logger
logger = logging.getLogger(__name__)

class OrderType(Enum):
    """Order types supported by the system."""
    MARKET = "market"
    LIMIT = "limit"
    
class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """Order statuses."""
    OPEN = "open"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    PENDING = "pending"

class Order:
    """Represents an order in the system."""
    
    def __init__(
        self, 
        symbol: str, 
        side: OrderSide, 
        order_type: OrderType,
        quantity: Decimal = None,
        price: Decimal = None,
        client_order_id: str = None
    ):
        """Initialize an order."""
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.client_order_id = client_order_id or f"order_{int(time.time() * 1000)}"
        self.exchange_order_id = None
        self.status = OrderStatus.PENDING
        self.filled_quantity = Decimal("0")
        self.avg_fill_price = None
        self.created_at = time.time()
        self.updated_at = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the order to a dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": str(self.quantity) if self.quantity else None,
            "price": str(self.price) if self.price else None,
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "status": self.status.value,
            "filled_quantity": str(self.filled_quantity),
            "avg_fill_price": str(self.avg_fill_price) if self.avg_fill_price else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Create an order from a dictionary."""
        order = cls(
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            order_type=OrderType(data["order_type"]),
            quantity=Decimal(data["quantity"]) if data.get("quantity") else None,
            price=Decimal(data["price"]) if data.get("price") else None,
            client_order_id=data.get("client_order_id")
        )
        
        if "exchange_order_id" in data:
            order.exchange_order_id = data["exchange_order_id"]
            
        if "status" in data:
            order.status = OrderStatus(data["status"])
            
        if "filled_quantity" in data:
            order.filled_quantity = Decimal(data["filled_quantity"])
            
        if "avg_fill_price" in data and data["avg_fill_price"]:
            order.avg_fill_price = Decimal(data["avg_fill_price"])
            
        if "created_at" in data:
            order.created_at = data["created_at"]
            
        if "updated_at" in data:
            order.updated_at = data["updated_at"]
            
        return order
        
class OrderExecutor:
    """Executes and manages orders."""
    
    def __init__(self, client, config_manager: ConfigManager):
        """Initialize the OrderExecutor.
        
        Args:
            client: The API client to use for executing orders.
            config_manager: The configuration manager.
        """
        self.client = client
        self.config_manager = config_manager
        self.open_orders: Dict[str, Order] = {}
        self.order_history: Dict[str, Order] = {}
        self.is_paper_trading = config_manager.config.paper_trading if config_manager.config else True
        
        logger.info(f"OrderExecutor initialized (paper trading: {self.is_paper_trading})")
        
    def validate_order(self, order: Order) -> Tuple[bool, Optional[str]]:
        """Validate an order against risk parameters.
        
        Args:
            order: The order to validate.
            
        Returns:
            Tuple[bool, Optional[str]]: A tuple containing whether the order is valid and
                                       an optional error message.
        """
        if not self.config_manager.config:
            raise ValidationError("Configuration not loaded")
            
        risk_config = self.config_manager.get_risk_params()
        
        # Check if trading pair is allowed
        if not self.config_manager.validate_trading_pair(order.symbol):
            return False, f"Trading pair {order.symbol} not allowed"
            
        # Check if position size exceeds max allowed
        if order.quantity and order.quantity > risk_config.max_position_size:
            return False, f"Order size ({order.quantity}) exceeds maximum allowed position size ({risk_config.max_position_size})"
            
        # Check if we have too many open orders
        if len(self.open_orders) >= risk_config.max_open_orders:
            return False, f"Too many open orders ({len(self.open_orders)}/{risk_config.max_open_orders})"
            
        # Add additional validation as needed
        
        return True, None
    
    def execute_order(self, symbol: str, side: str, order_type: str, **kwargs) -> Order:
        """Execute an order.
        
        Args:
            symbol: The trading pair.
            side: The order side ('buy' or 'sell').
            order_type: The order type ('market' or 'limit').
            **kwargs: Additional order parameters.
                - quantity: The order quantity.
                - price: The order price (required for limit orders).
                
        Returns:
            Order: The executed order.
            
        Raises:
            ValidationError: If the order is invalid.
            OrderExecutionError: If the order execution fails.
        """
        try:
            # Parse parameters
            order_side = OrderSide(side.lower())
            order_type_enum = OrderType(order_type.lower())
            
            # Create the order object
            quantity = Decimal(str(kwargs.get("quantity", "0")))
            price = Decimal(str(kwargs.get("price", "0"))) if "price" in kwargs else None
            
            order = Order(
                symbol=symbol,
                side=order_side,
                order_type=order_type_enum,
                quantity=quantity,
                price=price
            )
            
            # Validate the order
            is_valid, error_message = self.validate_order(order)
            if not is_valid:
                order.status = OrderStatus.REJECTED
                raise ValidationError(f"Order validation failed: {error_message}")
                
            # Execute the order
            if self.is_paper_trading:
                return self._execute_paper_order(order)
            else:
                return self._execute_live_order(order)
                
        except (ValidationError, ValueError) as e:
            logger.error(f"Order validation failed: {e}")
            raise ValidationError(str(e))
            
        except Exception as e:
            logger.error(f"Order execution failed: {e}")
            raise OrderExecutionError(f"Order execution failed: {e}")
    
    def _execute_paper_order(self, order: Order) -> Order:
        """Execute a paper trading order.
        
        Args:
            order: The order to execute.
            
        Returns:
            Order: The executed order.
        """
        logger.info(f"Executing paper order: {order.to_dict()}")
        
        # Simulate order execution
        order.exchange_order_id = f"paper-{order.client_order_id}"
        
        # For market orders, simulate immediate fill
        if order.order_type == OrderType.MARKET:
            # Get current price from client
            try:
                price = self.client.get_current_price(order.symbol)
                
                # Fill the order
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.avg_fill_price = Decimal(str(price))
                order.updated_at = time.time()
                
                logger.info(f"Paper market order filled at price {price}")
                
                # Store in history
                self.order_history[order.client_order_id] = order
                
            except Exception as e:
                logger.error(f"Error simulating paper order: {e}")
                order.status = OrderStatus.REJECTED
                
        # For limit orders, add to open orders
        else:
            order.status = OrderStatus.OPEN
            self.open_orders[order.client_order_id] = order
            logger.info(f"Paper limit order added to open orders")
            
        return order
    
    def _execute_live_order(self, order: Order) -> Order:
        """Execute a live order.
        
        Args:
            order: The order to execute.
            
        Returns:
            Order: The executed order.
            
        Raises:
            OrderExecutionError: If the order execution fails.
        """
        logger.info(f"Executing live order: {order.to_dict()}")
        
        # Prepare order parameters
        params = {
            "product_id": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value
        }
        
        # Add quantity and price parameters
        if order.quantity:
            params["size"] = str(order.quantity)
            
        if order.price and order.order_type == OrderType.LIMIT:
            params["price"] = str(order.price)
            
        # Add client_order_id if supported by the exchange
        params["client_order_id"] = order.client_order_id
        
        try:
            # Call the exchange API
            response = self.client.place_order(**params)
            
            # Update order with exchange information
            order.exchange_order_id = response.get("id")
            order.status = OrderStatus(response.get("status", "open"))
            order.created_at = time.time()
            order.updated_at = time.time()
            
            # Add to open orders or history depending on status
            if order.status == OrderStatus.FILLED:
                order.filled_quantity = order.quantity
                order.avg_fill_price = Decimal(str(response.get("price", "0")))
                self.order_history[order.client_order_id] = order
            else:
                self.open_orders[order.client_order_id] = order
                
            logger.info(f"Order executed: {order.exchange_order_id}")
            return order
            
        except Exception as e:
            logger.error(f"Live order execution failed: {e}")
            order.status = OrderStatus.REJECTED
            raise OrderExecutionError(f"Order execution failed: {e}")

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID.
        
        Args:
            order_id: The client order ID.
            
        Returns:
            Optional[Order]: The order if found, None otherwise.
        """
        # Check open orders
        if order_id in self.open_orders:
            return self.open_orders[order_id]
            
        # Check order history
        if order_id in self.order_history:
            return self.order_history[order_id]
            
        # Try to fetch from exchange if not a paper order
        if not self.is_paper_trading and not order_id.startswith("paper-"):
            try:
                response = self.client.get_order(order_id)
                # Convert response to Order object
                # ... implementation depends on the client's response format
                return None  # Placeholder until implementation
            except Exception as e:
                logger.error(f"Failed to get order from exchange: {e}")
                
        return None

    def update_open_orders(self):
        """Update the status of all open orders."""
        if self.is_paper_trading:
            self._update_paper_orders()
        else:
            self._update_live_orders()

    def _update_paper_orders(self):
        """Update paper trading orders."""
        if not self.open_orders:
            return
            
        # Get current prices
        prices = {}
        for order_id, order in list(self.open_orders.items()):
            try:
                if order.symbol not in prices:
                    prices[order.symbol] = Decimal(str(self.client.get_current_price(order.symbol)))
                    
                current_price = prices[order.symbol]
                
                # Check if limit orders should be filled
                if order.order_type == OrderType.LIMIT:
                    should_fill = False
                    
                    # Buy orders fill when price drops at or below limit price
                    if order.side == OrderSide.BUY and current_price <= order.price:
                        should_fill = True
                    
                    # Sell orders fill when price rises at or above limit price
                    elif order.side == OrderSide.SELL and current_price >= order.price:
                        should_fill = True
                        
                    if should_fill:
                        order.status = OrderStatus.FILLED
                        order.filled_quantity = order.quantity
                        order.avg_fill_price = order.price
                        order.updated_at = time.time()
                        
                        # Move from open orders to history
                        del self.open_orders[order_id]
                        self.order_history[order_id] = order
                        
                        logger.info(f"Paper limit order {order_id} filled at {order.price}")
                
            except Exception as e:
                logger.error(f"Error updating paper order {order_id}: {e}")

    def _update_live_orders(self):
        """Update live orders from the exchange."""
        if not self.open_orders:
            return
            
        try:
            # Get all open orders from exchange
            exchange_orders = self.client.get_open_orders()
            
            # Create a map of exchange order IDs to orders
            exchange_order_map = {order.get("id"): order for order in exchange_orders}
            
            # Update our open orders
            for order_id, order in list(self.open_orders.items()):
                if not order.exchange_order_id:
                    continue
                    
                # Check if the order is still open on the exchange
                if order.exchange_order_id in exchange_order_map:
                    exchange_order = exchange_order_map[order.exchange_order_id]
                    
                    # Update order status
                    new_status = OrderStatus(exchange_order.get("status", "open"))
                    if new_status != order.status:
                        order.status = new_status
                        order.updated_at = time.time()
                        
                    # Update filled quantity and price if available
                    if "filled_size" in exchange_order:
                        order.filled_quantity = Decimal(str(exchange_order["filled_size"]))
                    
                    if "price" in exchange_order and order.filled_quantity > 0:
                        order.avg_fill_price = Decimal(str(exchange_order["price"]))
                        
                    # Move filled orders to history
                    if order.status == OrderStatus.FILLED:
                        del self.open_orders[order_id]
                        self.order_history[order_id] = order
                else:
                    # Order not found on exchange, check its status
                    try:
                        order_details = self.client.get_order(order.exchange_order_id)
                        
                        # Update status
                        new_status = OrderStatus(order_details.get("status", "open"))
                        if new_status != order.status:
                            order.status = new_status
                            order.updated_at = time.time()
                            
                        # Update filled quantity and price if available
                        if "filled_size" in order_details:
                            order.filled_quantity = Decimal(str(order_details["filled_size"]))
                        
                        if "price" in order_details and order.filled_quantity > 0:
                            order.avg_fill_price = Decimal(str(order_details["price"]))
                            
                        # Move filled or canceled orders to history
                        if order.status in (OrderStatus.FILLED, OrderStatus.CANCELED):
                            del self.open_orders[order_id]
                            self.order_history[order_id] = order
                            
                    except Exception as e:
                        logger.error(f"Failed to get order details for {order.exchange_order_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to update live orders: {e}")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: The client order ID.
            
        Returns:
            bool: True if the order was canceled, False otherwise.
        """
        # Check if we have the order
        if order_id not in self.open_orders:
            logger.warning(f"Cannot cancel order {order_id}: not found in open orders")
            return False
            
        order = self.open_orders[order_id]
        
        # Cancel the order
        if self.is_paper_trading:
            # Paper trading - just update status
            order.status = OrderStatus.CANCELED
            order.updated_at = time.time()
            
            # Move to history
            del self.open_orders[order_id]
            self.order_history[order_id] = order
            
            logger.info(f"Canceled paper order {order_id}")
            return True
        else:
            # Live trading - call exchange API
            try:
                if not order.exchange_order_id:
                    logger.error(f"Cannot cancel order {order_id}: no exchange order ID")
                    return False
                    
                result = self.client.cancel_order(order.exchange_order_id)
                
                # Update order status
                order.status = OrderStatus.CANCELED
                order.updated_at = time.time()
                
                # Move to history
                del self.open_orders[order_id]
                self.order_history[order_id] = order
                
                logger.info(f"Canceled order {order_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to cancel order {order_id}: {e}")
                return False
