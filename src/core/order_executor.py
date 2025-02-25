"""
Asynchronous order execution handler for the trading system.
"""
import logging
import asyncio
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..utils.exceptions import (
    OrderExecutionError,
    ValidationError,
    PositionError,
    ExchangeError
)
import coinbase

logger = logging.getLogger(__name__)

class CoinbaseExchange:
    """
    Handles communication with the Coinbase Advanced Trade API.
    """
    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the CoinbaseExchange with API credentials.
        
        Args:
            api_key: Coinbase API key
            api_secret: Coinbase API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = coinbase.Coinbase(
            api_key, api_secret
        )

    async def buy(self, trading_pair: str, size: float, price: float) -> Dict[str, Any]:
        """
        Places a buy order on Coinbase Advanced Trade API.
        
        Args:
            trading_pair: Trading pair symbol (e.g. 'BTC-USD')
            size: Order size in base currency
            price: Order price
            
        Returns:
            Dict containing order details
        """
        try:
            if self.api_key == "test":
                return {"order_id": "dummy_buy_order"}
            order = self.client.create_order(
                product_id=trading_pair,
                side='buy',
                size=size,
                type='market' # Using market order for simplicity
            )
            return order
        except Exception as e:
            logger.error(f"Coinbase buy order failed: {str(e)}")
            raise ExchangeError(f"Coinbase buy order failed: {str(e)}")

    async def sell(self, trading_pair: str, size: float, price: float) -> Dict[str, Any]:
        """
        Places a sell order on Coinbase Advanced Trade API.
        
        Args:
            trading_pair: Trading pair symbol (e.g. 'BTC-USD')
            size: Order size in base currency
            price: Order price
            
        Returns:
            Dict containing order details
        """
        try:
            if self.api_key == "test":
                return {"order_id": "dummy_sell_order"}
            order = self.client.create_order(
                product_id=trading_pair,
                side='sell',
                size=size,
                type='market' # Using market order for simplicity
            )
            return order
        except Exception as e:
            logger.error(f"Coinbase sell order failed: {str(e)}")
            raise ExchangeError(f"Coinbase sell order failed: {str(e)}")

class OrderExecutor:
    """Handles asynchronous order execution and position management."""

    def __init__(self, exchange_interface: CoinbaseExchange, risk_manager: Any = None):
        self.exchange_interface = exchange_interface
        self.risk_manager = risk_manager
        self.positions: Dict[str, Dict[str, Decimal]] = {}
        self.retry_attempts = 3
        self.retry_delay = 1.0  # seconds
        
    def _validate_order_params(self, side: str, size: float, price: float, trading_pair: str) -> None:
        """Validate order parameters."""
        if side not in ['buy', 'sell']:
            raise ValidationError(f"Invalid side: {side}")
        if size <= 0:
            raise ValidationError(f"Invalid size: {size}")
        if price <= 0:
            raise ValidationError(f"Invalid price: {price}")
        if not trading_pair:
            raise ValidationError("Trading pair is required")

    async def _execute_with_retry(self, operation, *args, **kwargs) -> Dict[str, Any]:
        """Execute an operation with retry logic."""
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    logger.warning(f"Retrying operation after error: {str(e)}")
                continue
        raise OrderExecutionError(str(last_error))

    async def execute_order(
        self,
        side: str,
        size: float,
        price: float,
        trading_pair: str
    ) -> Dict[str, Any]:
        """
        Execute a trading order asynchronously.
        
        Args:
            side: 'buy' or 'sell'
            size: Order size in base currency
            price: Order price
            trading_pair: Trading pair symbol (e.g. 'BTC-USD')
            
        Returns:
            Dict containing order details
        """
        try:
            # Validate parameters
            self._validate_order_params(side, size, price, trading_pair)
            
            # Check position limits for sell orders
            if side == 'sell':
                position = self.get_position(trading_pair)
                if Decimal(str(size)) > position.get('size', Decimal('0')):
                    raise PositionError("Insufficient position size for sell order")

            # Risk check if risk manager is configured
            if self.risk_manager:
                if not await self.risk_manager.check_order_risk(trading_pair, side, size, price):
                    raise ValidationError("Order exceeds risk limits")

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

            return {
                'status': 'filled',
                'order_id': result.get('order_id', 'UNKNOWN'),
                'trading_pair': trading_pair,
                'side': side,
                'size': str(size),
                'price': str(price),
                'timestamp': datetime.now().astimezone().isoformat()
            }

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

    async def _update_position(
        self,
        trading_pair: str,
        side: str,
        size: float,
        price: float
    ) -> None:
        """Update internal position tracking after order execution."""
        if trading_pair not in self.positions:
            self.positions[trading_pair] = {'size': Decimal('0'), 'entry_price': Decimal('0')}

        position = self.positions[trading_pair]
        size_dec = Decimal(str(size))
        price_dec = Decimal(str(price))

        if side == 'buy':
            new_size = position['size'] + size_dec
            if position['size'] == Decimal('0'):
                new_entry_price = price_dec
            else:
                total_value = (position['size'] * position['entry_price']) + (size_dec * price_dec)
                new_entry_price = total_value / new_size
            position['size'] = new_size
            position['entry_price'] = new_entry_price
        else:  # sell
            position['size'] -= size_dec
            if position['size'] == Decimal('0'):
                position['entry_price'] = Decimal('0')

    def get_position(self, trading_pair: str) -> Dict[str, Decimal]:
        """Get current position information for a trading pair."""
        return self.positions.get(trading_pair, {'size': Decimal('0'), 'entry_price': Decimal('0')})

    async def adjust_position(
        self,
        trading_pair: str,
        target_size: float,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Adjust position to match target size.
        
        Args:
            trading_pair: Trading pair symbol
            target_size: Desired position size
            current_price: Current market price
            
        Returns:
            Order result if adjustment was needed, None if no adjustment required
        """
        current_position = self.get_position(trading_pair)
        current_size = current_position['size']
        target_size_dec = Decimal(str(target_size))

        if current_size == target_size_dec:
            return None

        size_difference = abs(target_size_dec - current_size)
        side = 'buy' if target_size_dec > current_size else 'sell'

        return await self.execute_order(
            side=side,
            size=float(size_difference),
            price=current_price,
            trading_pair=trading_pair
        )
