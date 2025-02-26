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
