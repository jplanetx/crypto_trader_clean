"""
Core trading functionality implementation.
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime
import os
import coinbasepro
import numpy as np
import pandas as pd

from .order_executor import OrderExecutor
from .config_manager import ConfigManager, TradingConfig
from ..utils.exceptions import (
    TradingException,
    ConfigurationError,
    OrderExecutionError
)
import json
from src.core.coinbase_streaming import CoinbaseStreaming

logger = logging.getLogger(__name__)

class CoinbaseExchange:
    """Handles real-time data streaming from Coinbase."""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws = None
        self.url = "wss://advanced-trade-ws.coinbase.com"  # Replace with actual WebSocket URL
        self.products = ["BTC-USD"]
        self.channels = ["ticker"]
        self.auth_client = coinbasepro.AuthenticatedClient(self.api_key, self.api_secret, os.getenv("COINBASE_API_PASSPHRASE"))

    async def connect(self):
        """Connect to the Coinbase WebSocket stream."""
        try:
            # Use the cbpro library to connect to the WebSocket stream
            # Replace with the correct implementation based on the documentation
            # For example:
            # self.ws = cbpro.WebsocketClient(url=self.url, products=self.products, auth=self.auth_client, channels=self.channels)
            # self.ws.message_callback = self.on_message
            # self.ws.start()
            logger.info("Coinbase WebSocket connected.")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def on_message(self, message):
        """Process incoming WebSocket messages."""
        try:
            logger.info(f"Received message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            # Replace with the correct implementation based on the documentation
            # self.ws.close()
            logger.info("Coinbase WebSocket disconnected.")

    async def run(self):
        """Run the WebSocket client."""
        await self.connect()

class TradingCore:
    """Coordinates trading operations and manages system state."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        exchange_interface: Optional[Any] = None,
        risk_manager: Optional[Any] = None
    ):
        self.config_manager = ConfigManager(config_path)
        self.config: TradingConfig = self.config_manager.config

        api_key = self.config.api_key
        api_secret = self.config.api_secret
        if not hasattr(self.config.risk_config, 'max_trade_size'):
            self.config.risk_config.max_trade_size = 1

        self.exchange_interface = CoinbaseExchange(api_key=api_key, api_secret=api_secret)
        
        self.order_executor = OrderExecutor(
            exchange_interface=self.exchange_interface,
            risk_manager=risk_manager
        )

        # Initialize Coinbase streaming
        self.coinbase_streaming = CoinbaseStreaming(
            api_key=api_key,
            api_secret=api_secret,
            product_ids=self.config.trading_pairs,
            channels=["ticker"]  # Subscribe to the ticker channel
        )
        
        # Trading state
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        self.price_data: Dict[str, List[float]] = {}  # Store price data for SMA calculation
        self.daily_stats: Dict[str, Any] = {
            'trades': 0,
            'volume': Decimal('0'),
            'pnl': Decimal('0'),
            'last_reset': datetime.utcnow().isoformat()
        }
        self.is_running: bool = False
        self.streaming_task: Optional[asyncio.Task[None]] = None


    async def initialize(self) -> None:
        """Initialize the trading system."""
        try:
            # Load configuration
            self.config = self.config_manager.load_config()
            logger.info("Trading system initialized with configuration.")

            await self.exchange_interface.connect()

            # Validate trading environment
            await self._validate_environment()

            self.is_running = True
            logger.info("Trading system initialization complete.")

            # Start the Coinbase streaming task
            self.streaming_task = asyncio.create_task(self._start_coinbase_streaming())

            # Start trading loop
            asyncio.create_task(self._trading_loop())

        except ConfigurationError as e:
            logger.error(f"Configuration error during initialization: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            raise TradingException(f"Initialization failed: {str(e)}")

    async def _start_coinbase_streaming(self) -> None:
        """Start the Coinbase streaming service."""
        try:
            await self.coinbase_streaming.connect()
            asyncio.create_task(self.coinbase_streaming.receive_data())
        except Exception as e:
            logger.error(f"Error starting Coinbase streaming: {e}")

    async def _validate_environment(self) -> None:
        """Validate trading environment and connectivity."""
        trading_pairs = self.config.trading_pairs
        if not trading_pairs:
            raise ConfigurationError("No trading pairs configured")

        # Basic environment checks
        if not self.config_manager.is_paper_trading():
            if not all([self.config.api_key, self.config.api_secret]):
                raise ConfigurationError("API credentials required for live trading")

    async def execute_trade(self, trading_pair: str, side: str, size: float, price: float) -> Dict[str, Any]:
        """Execute a trade with position and risk management."""
        try:
            # Get current price from streaming data
            current_price = await self.get_current_price(trading_pair)
            logger.info(f"Executing trade: {side} {size} {trading_pair} @ {price}, current price: {current_price}")

            # Validate trading pair
            if not self.config_manager.validate_trading_pair(trading_pair):
                raise ConfigurationError(f"Invalid trading pair: {trading_pair}")

            # Validate order side
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid order side: {side}. Must be 'buy' or 'sell'.")

            # Risk management parameters from config
            stop_loss_pct = self.config.risk_config.stop_loss_pct
            take_profit_pct = self.config.risk_config.take_profit_pct
            
            # Calculate stop loss and take profit prices
            if side == "buy":
                stop_loss_price = price * (1 - stop_loss_pct)
                take_profit_price = price * (1 + take_profit_pct)
            else:
                stop_loss_price = price * (1 + stop_loss_pct)
                take_profit_price = price * (1 - take_profit_pct)
            
            # Check daily loss limit
            if self.daily_stats['pnl'] < -abs(self.config.risk_config.daily_loss_limit):
                logger.warning("Daily loss limit reached. Trading stopped.")
                self.is_running = False
                return {}  # Return empty dict to indicate no trade

            # Execute order
            result = await self.order_executor.execute_order(
                side=side,
                size=size,
                price=price,
                trading_pair=trading_pair,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price
            )

            # Update trading state
            if result['status'] == 'filled':
                await self._update_trading_state(result)

            logger.info(f"Trade executed successfully. Order ID: {result.get('order_id', 'N/A')}")
            return result

        except (ConfigurationError, OrderExecutionError, ValueError) as e:
            logger.error(f"Trade execution error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during trade execution: {str(e)}")
            raise TradingException(f"Trade execution failed: {str(e)}")

    async def get_current_price(self, trading_pair: str) -> float:
        """Get the current price from the Coinbase streaming data."""
        return self.coinbase_streaming.get_current_price(trading_pair)

    async def _update_trading_state(self, trade_result: Dict[str, Any]) -> None:
        """Update internal trading state after successful trade."""
        trading_pair = trade_result['trading_pair']
        size = Decimal(trade_result['size'])
        price = Decimal(trade_result['price'])
        
        # Update daily statistics
        self.daily_stats['trades'] += 1
        self.daily_stats['volume'] += size * price
        
        # Track active trade
        self.active_trades[trade_result['order_id']] = {
            **trade_result,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def get_position(self, trading_pair: str) -> Dict[str, Any]:
        """Get current position for a trading pair."""
        return self.order_executor.get_position(trading_pair)

    async def adjust_position(
        self,
        trading_pair: str,
        target_size: float,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """Adjust position to target size."""
        return await self.order_executor.adjust_position(
            trading_pair=trading_pair,
            target_size=target_size,
            current_price=current_price
        )

    def get_trading_pairs(self) -> List[str]:
        """Get configured trading pairs."""
        return self.config.trading_pairs

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily trading statistics."""
        return {
            'trades': self.daily_stats['trades'],
            'volume': str(self.daily_stats['volume']),
            'pnl': str(self.daily_stats['pnl']),
            'last_reset': self.daily_stats['last_reset']
        }

    def reset_daily_stats(self) -> None:
        """Reset daily trading statistics."""
        self.daily_stats = {
            'trades': 0,
            'volume': Decimal('0'),
            'pnl': Decimal('0'),
            'last_reset': datetime.utcnow().isoformat()
        }

    def reset_daily_pnl(self) -> None:
        """Reset daily PnL for testing purposes."""
        self.daily_stats['pnl'] = Decimal('0')
        logger.info("Daily PnL reset to 0.")

    async def shutdown(self) -> None:
        """Gracefully shutdown the trading system."""
        logger.info("Initiating trading system shutdown...")
        self.is_running = False
        
        # Close all positions if configured
        if self.config.risk_config.max_position_size == Decimal('0'):
            for trading_pair in self.config.trading_pairs:
                position = await self.get_position(trading_pair)
                if position['size'] != Decimal('0'):
                    try:
                        await self.adjust_position(
                            trading_pair=trading_pair,
                            target_size=0,
                            current_price=0  # Market order
                        )
                    except Exception as e:
                        logger.error(f"Error closing position during shutdown: {str(e)}")

        logger.info("Trading system shutdown complete.")

    def is_active(self) -> bool:
        """Check if the trading system is active."""
        return self.is_running

    def store_price_data(self, trading_pair: str, price: float) -> None:
        """Stores the price data for the given trading pair."""
        if trading_pair not in self.price_data:
            self.price_data[trading_pair] = []
        self.price_data[trading_pair].append(price)
        logger.debug(f"Storing price data for {trading_pair}: {price}")

    def calculate_moving_average(self, trading_pair: str, window: int) -> float:
        """Calculate the moving average of the given data."""
        if trading_pair not in self.price_data or len(self.price_data[trading_pair]) < window:
            return 0  # Not enough data
        
        prices = self.price_data[trading_pair][-window:]
        return pd.Series(prices).mean()

    def calculate_rsi(self, trading_pair: str, window: int) -> float:
        """Calculate the Relative Strength Index (RSI) of the given data."""
        # This is a placeholder. The actual implementation will depend on how the
        # streaming data is stored and accessed.
        # For example, you might have a list of prices and calculate the RSI from that.
        return 50  # Replace with actual calculation

    async def run_moving_average_crossover_strategy(self, trading_pair: str):
        """Runs the moving average crossover strategy."""
        try:
            # Strategy parameters from config
            short_window = self.config.strategy_config.get('short_window', 5)
            long_window = self.config.strategy_config.get('long_window', 20)
            
            # Calculate moving averages
            short_ma = self.calculate_moving_average(trading_pair, short_window)
            long_ma = self.calculate_moving_average(trading_pair, long_window)
            
            # Get current price
            current_price = await self.get_current_price(trading_pair)
            self.store_price_data(trading_pair, current_price)
            
            # Generate trading signal
            signal = 0  # 0: Hold, 1: Buy, -1: Sell
            if short_ma > long_ma:
                signal = 1
            elif short_ma < long_ma:
                signal = -1
            
            # Execute trade
            size = self.config.risk_config.max_trade_size  # Example size
            if signal == 1:
                side = "buy"
                logger.info(f"SMA Crossover: BUY {trading_pair} at {current_price}, short_ma={short_ma}, long_ma={long_ma}")
                await self.execute_trade(trading_pair, side, size, current_price)
            elif signal == -1:
                side = "sell"
                logger.info(f"SMA Crossover: SELL {trading_pair} at {current_price}, short_ma={short_ma}, long_ma={long_ma}")
                await self.execute_trade(trading_pair, side, size, current_price)
            else:
                logger.debug(f"SMA Crossover: No signal for {trading_pair}, short_ma={short_ma}, long_ma={long_ma}")

        except Exception as e:
            logger.error(f"SMA Crossover Strategy execution error: {e}")

    async def run_rsi_strategy(self, trading_pair: str):
        """Runs the RSI strategy."""
        try:
            # Strategy parameters from config
            rsi_window = self.config.strategy_config['rsi_window']
            rsi_oversold = self.config.strategy_config['rsi_oversold']
            rsi_overbought = self.config.strategy_config['rsi_overbought']
            
            # Calculate RSI
            rsi = self.calculate_rsi(trading_pair, rsi_window)
            
            # Get current price
            current_price = await self.get_current_price(trading_pair)
            
            # Generate trading signal
            if rsi < rsi_oversold:
                side = "buy"
            elif rsi > rsi_overbought:
                side = "sell"
            else:
                return # No signal
            
            # Execute trade
            size = self.config.risk_config.max_trade_size  # Example size
            await self.execute_trade(trading_pair, side, size, current_price)

        except Exception as e:
            logger.error(f"Strategy execution error: {e}")

    async def _trading_loop(self) -> None:
        """Main trading loop."""
        logger.info("Starting trading loop...")
        while self.is_running:
            try:
                for trading_pair in self.config.trading_pairs:
                    logger.info(f"Running strategy for {trading_pair}")
                    await self.run_moving_average_crossover_strategy(trading_pair)
                    await self.run_rsi_strategy(trading_pair)
                await asyncio.sleep(1)  # Check every 1 second
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(10)  # Wait before retrying
