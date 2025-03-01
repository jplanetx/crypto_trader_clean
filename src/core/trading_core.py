"""
Core trading functionality implementation.

This module coordinates all trading operations including:
- Strategy execution
- Position management
- Market data processing
- Risk management
- Technical analysis
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal
from datetime import datetime, timezone
import os
import numpy as np
import pandas as pd

from .order_executor import OrderExecutor, CoinbaseExchange
from .config_manager import ConfigManager, TradingConfig
from ..utils.exceptions import (
    TradingException,
    ConfigurationError,
    OrderExecutionError
)
from .coinbase_streaming import CoinbaseStreaming

# Configure module logger
logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to parent loggers

class TradingCore:
    """
    Coordinates trading operations and manages system state.
    
    This class serves as the central coordinator for the trading system,
    managing trading strategies, position tracking, and system state.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        exchange_interface: Optional[CoinbaseExchange] = None,
        risk_manager: Optional[Any] = None
    ):
        """
        Initialize the TradingCore.
        
        Args:
            config_path: Optional path to configuration file
            exchange_interface: Optional pre-configured exchange interface
            risk_manager: Optional risk management component
            
        Raises:
            ConfigurationError: If trading configuration is invalid
        """
        logger.info("Initializing TradingCore")
        try:
            # Load configuration
            self.config_manager = ConfigManager(config_path)
            self.config: TradingConfig = self.config_manager.config

            # Initialize exchange interface
            if exchange_interface:
                self.exchange_interface = exchange_interface
            else:
                if not all([self.config.api_key, self.config.private_key]):
                    error_msg = "API credentials not found in configuration"
                    logger.error(error_msg)
                    raise ConfigurationError(error_msg)
                    
                self.exchange_interface = CoinbaseExchange(
                    api_key=self.config.api_key,
                    api_secret=self.config.private_key
                )

            # Initialize order executor
            self.order_executor = OrderExecutor(
                exchange_interface=self.exchange_interface,
                risk_manager=risk_manager
            )

            # Initialize Coinbase streaming
            self.coinbase_streaming = CoinbaseStreaming(
                api_key=self.config.api_key,
                private_key=self.config.private_key,
                product_ids=self.config.trading_pairs,
                channels=["ticker"]
            )
            
            # Trading state initialization
            self._initialize_trading_state()
            
            logger.info("TradingCore initialization complete")
            
        except Exception as e:
            error_msg = f"Failed to initialize TradingCore: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

    def _initialize_trading_state(self) -> None:
        """Initialize internal trading state variables."""
        logger.debug("Initializing trading state")
        
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        self.price_data: Dict[str, List[float]] = {}
        self.daily_stats: Dict[str, Any] = {
            'trades': 0,
            'volume': Decimal('0'),
            'pnl': Decimal('0'),
            'last_reset': datetime.now(timezone.utc).isoformat()
        }
        self.is_running: bool = False
        self.streaming_task: Optional[asyncio.Task[None]] = None

    def get_trading_pairs(self) -> List[str]:
        """Get the configured trading pairs."""
        return self.config.trading_pairs

    async def initialize(self) -> None:
        """
        Initialize the trading system.
        
        This method performs startup tasks including:
        - Configuration validation
        - Exchange connection
        - Data streaming initialization
        
        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            logger.info("Starting trading system initialization")
            
            # Load and validate configuration
            self.config = self.config_manager.load_config()
            logger.info("Configuration loaded successfully")

            # Initialize exchange connection
            await self.exchange_interface.connect()
            logger.info("Exchange connection established")

            # Validate trading environment
            await self._validate_environment()
            logger.info("Trading environment validated")

            # Start components
            self.is_running = True
            self.streaming_task = asyncio.create_task(self._start_coinbase_streaming())
            asyncio.create_task(self._trading_loop())
            
            logger.info("Trading system initialization complete")

        except ConfigurationError as e:
            logger.error(f"Configuration error during initialization: {e}")
            raise
        except Exception as e:
            error_msg = f"Initialization failed: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def _validate_environment(self) -> None:
        """
        Validate trading environment and connectivity.
        
        Raises:
            ConfigurationError: If validation fails
        """
        logger.debug("Validating trading environment")
        
        trading_pairs = self.config.trading_pairs
        if not trading_pairs:
            error_msg = "No trading pairs configured"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

        if not self.config_manager.is_paper_trading():
            if not all([self.config.api_key, self.config.private_key]):
                error_msg = "API credentials required for live trading"
                logger.error(error_msg)
                raise ConfigurationError(error_msg)
        logger.debug("Trading environment validation successful")

    async def _start_coinbase_streaming(self) -> None:
        """
        Start the Coinbase data streaming service.
        
        Raises:
            TradingException: If streaming initialization fails
        """
        try:
            logger.info("Starting Coinbase data streaming")
            await self.coinbase_streaming.connect()
            asyncio.create_task(self.coinbase_streaming.receive_data())
            logger.info("Coinbase streaming started successfully")
        except Exception as e:
            error_msg = f"Failed to start Coinbase streaming: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def execute_trade(
        self, 
        trading_pair: str, 
        side: str, 
        size: float, 
        price: float
    ) -> Dict[str, Any]:
        """
        Execute a trade with position and risk management.
        
        Args:
            trading_pair: Trading pair symbol
            side: Order side ('buy' or 'sell')
            size: Order size in base currency
            price: Order price
            
        Returns:
            Dict[str, Any]: Order execution details
            
        Raises:
            ValidationError: If parameters are invalid
            OrderExecutionError: If order execution fails
        """
        try:
            # Get current market price
            current_price = await self.get_current_price(trading_pair)
            logger.info(f"Executing trade: {side} {size} {trading_pair} @ {price}")
            logger.debug(f"Current market price: {current_price}")

            # Trading pair validation
            if not self.config_manager.validate_trading_pair(trading_pair):
                error_msg = f"Invalid trading pair: {trading_pair}"
                logger.error(error_msg)
                raise ConfigurationError(error_msg)

            # Order side validation
            if side not in ['buy', 'sell']:
                error_msg = f"Invalid order side: {side}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Get risk parameters
            stop_loss_pct = self.config.risk_config.stop_loss_pct
            take_profit_pct = getattr(self.config.risk_config, 'take_profit_pct', 0.05)
            
            # Calculate order prices
            stop_loss_price = price * (1 - stop_loss_pct if side == "buy" else 1 + stop_loss_pct)
            take_profit_price = price * (1 + take_profit_pct if side == "buy" else 1 - take_profit_pct)
            
            logger.debug(f"Order prices - Stop Loss: {stop_loss_price}, Take Profit: {take_profit_price}")
            
            # Check daily loss limit
            if self.daily_stats['pnl'] < -abs(getattr(self.config.risk_config, 'daily_loss_limit', float('inf'))):
                logger.warning("Daily loss limit reached. Trading halted.")
                self.is_running = False
                return {}

            # Execute order
            result = await self.order_executor.execute_order(
                side=side,
                size=size,
                price=price,
                trading_pair=trading_pair
            )

            # Update state if order filled
            if result['status'] == 'filled':
                await self._update_trading_state(result)
                logger.info(f"Trade executed successfully - Order ID: {result.get('order_id', 'N/A')}")

            return result

        except (ConfigurationError, OrderExecutionError, ValueError) as e:
            logger.error(f"Trade execution error: {e}")
            raise
        except Exception as e:
            error_msg = f"Unexpected error during trade execution: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def get_current_price(self, trading_pair: str) -> float:
        """
        Get the current market price from streaming data.
        
        Args:
            trading_pair: Trading pair symbol
            
        Returns:
            float: Current market price
            
        Raises:
            TradingException: If price data is unavailable
        """
        try:
            return self.coinbase_streaming.get_current_price(trading_pair)
        except Exception as e:
            error_msg = f"Failed to get current price for {trading_pair}: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def _update_trading_state(self, trade_result: Dict[str, Any]) -> None:
        """
        Update internal trading state after trade execution.
        
        Args:
            trade_result: Trade execution details
            
        Raises:
            TradingException: If state update fails
        """
        try:
            size = Decimal(trade_result['size'])
            price = Decimal(trade_result['price'])
            
            # Update statistics
            logger.debug("Updating trading statistics")
            self.daily_stats['trades'] += 1
            self.daily_stats['volume'] += size * price
            
            # Track active trade
            self.active_trades[trade_result['order_id']] = {
                **trade_result,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.debug(f"Trading state updated - Trades: {self.daily_stats['trades']}, "
                      f"Volume: {self.daily_stats['volume']}")
                      
        except Exception as e:
            error_msg = f"Failed to update trading state: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    def store_price_data(self, trading_pair: str, price: float) -> None:
        """
        Store price data for technical analysis.
        
        Args:
            trading_pair: Trading pair symbol
            price: Market price
        """
        try:
            if trading_pair not in self.price_data:
                self.price_data[trading_pair] = []
            self.price_data[trading_pair].append(price)
            logger.debug(f"Stored price data for {trading_pair}: {price}")
        except Exception as e:
            logger.error(f"Failed to store price data: {e}")

    def calculate_moving_average(self, trading_pair: str, window: int) -> float:
        """
        Calculate simple moving average.
        
        Args:
            trading_pair: Trading pair symbol
            window: MA window size
            
        Returns:
            float: Moving average value
            
        Raises:
            TradingException: If calculation fails
        """
        try:
            if trading_pair not in self.price_data:
                return 0
                
            prices = self.price_data[trading_pair]
            if len(prices) < window:
                logger.debug(f"Insufficient data for {window}-period MA calculation")
                return 0
                
            ma_value = pd.Series(prices[-window:]).mean()
            logger.debug(f"{window}-period MA for {trading_pair}: {ma_value}")
            return ma_value
            
        except Exception as e:
            error_msg = f"Failed to calculate moving average: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    def calculate_rsi(self, trading_pair: str, window: int) -> float:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            trading_pair: Trading pair symbol
            window: RSI period
            
        Returns:
            float: RSI value
            
        Raises:
            TradingException: If calculation fails
        """
        try:
            if trading_pair not in self.price_data:
                return 50
                
            prices = self.price_data[trading_pair]
            if len(prices) < window + 1:
                logger.debug(f"Insufficient data for {window}-period RSI calculation")
                return 50
                
            # Calculate price changes
            delta = pd.Series(prices).diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)
            
            # Calculate RSI
            avg_gain = gains.rolling(window=window).mean()
            avg_loss = losses.rolling(window=window).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs.iloc[-1]))
            
            logger.debug(f"{window}-period RSI for {trading_pair}: {rsi}")
            return float(rsi)
            
        except Exception as e:
            error_msg = f"Failed to calculate RSI: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def run_moving_average_crossover_strategy(self, trading_pair: str) -> None:
        """
        Execute moving average crossover trading strategy.
        
        Args:
            trading_pair: Trading pair to trade
            
        Raises:
            TradingException: If strategy execution fails
        """
        try:
            # Get strategy parameters
            short_window = self.config.strategy_config.get('short_window', 5)
            long_window = self.config.strategy_config.get('long_window', 20)
            
            logger.debug(f"Running MA crossover strategy for {trading_pair}")
            
            # Calculate indicators
            short_ma = self.calculate_moving_average(trading_pair, short_window)
            long_ma = self.calculate_moving_average(trading_pair, long_window)
            
            # Get current market data
            current_price = await self.get_current_price(trading_pair)
            self.store_price_data(trading_pair, current_price)
            
            # Generate trading signal
            signal = 0
            if short_ma > long_ma:
                signal = 1  # Buy signal
            elif short_ma < long_ma:
                signal = -1  # Sell signal
                
            # Execute trade if signal present
            if signal != 0:
                size = float(self.config.risk_config.max_position_size)
                side = "buy" if signal == 1 else "sell"
                
                logger.info(f"MA Crossover signal for {trading_pair}: {side.upper()}")
                logger.debug(f"Signal details - Price: {current_price}, "
                          f"Short MA: {short_ma}, Long MA: {long_ma}")
                          
                await self.execute_trade(trading_pair, side, size, current_price)
            else:
                logger.debug(f"No MA Crossover signal for {trading_pair}")

        except Exception as e:
            error_msg = f"MA Crossover strategy execution failed: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def run_rsi_strategy(self, trading_pair: str) -> None:
        """
        Execute RSI-based trading strategy.
        
        Args:
            trading_pair: Trading pair to trade
            
        Raises:
            TradingException: If strategy execution fails
        """
        try:
            # Get strategy parameters
            rsi_window = self.config.strategy_config.get('rsi_window', 14)
            rsi_oversold = self.config.strategy_config.get('rsi_oversold', 30)
            rsi_overbought = self.config.strategy_config.get('rsi_overbought', 70)
            
            logger.debug(f"Running RSI strategy for {trading_pair}")
            
            # Calculate RSI
            rsi = self.calculate_rsi(trading_pair, rsi_window)
            current_price = await self.get_current_price(trading_pair)
            
            # Generate trading signal
            if rsi < rsi_oversold:
                side = "buy"
                logger.info(f"RSI Oversold signal for {trading_pair}")
            elif rsi > rsi_overbought:
                side = "sell"
                logger.info(f"RSI Overbought signal for {trading_pair}")
            else:
                logger.debug(f"No RSI signal for {trading_pair} (RSI: {rsi})")
                return
                
            # Execute trade
            size = float(self.config.risk_config.max_position_size)
            logger.debug(f"Executing {side} order - Size: {size}, Price: {current_price}")
            await self.execute_trade(trading_pair, side, size, current_price)

        except Exception as e:
            error_msg = f"RSI strategy execution failed: {e}"
            logger.error(error_msg)
            raise TradingException(error_msg)

    async def _trading_loop(self) -> None:
        """
        Main trading loop executing configured strategies.
        
        This method runs continuously while the system is active,
        executing trading strategies for each configured trading pair.
        """
        logger.info("Starting main trading loop")
        
        while self.is_running:
            try:
                for trading_pair in self.config.trading_pairs:
                    logger.debug(f"Running strategies for {trading_pair}")
                    await self.run_moving_average_crossover_strategy(trading_pair)
                    await self.run_rsi_strategy(trading_pair)
                    
                await asyncio.sleep(1)  # Trading interval
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(10)  # Error backoff

    async def shutdown(self) -> None:
        """
        Perform graceful system shutdown.
        
        This method ensures all positions are properly closed and
        resources are released before shutting down.
        """
        logger.info("Initiating trading system shutdown")
        
        self.is_running = False
        
        try:
            # Close all positions if configured
            if self.config.risk_config.max_position_size == Decimal('0'):
                logger.info("Closing all positions")
                for trading_pair in self.config.trading_pairs:
                    position = await self.get_position(trading_pair)
                    if position['size'] != Decimal('0'):
                        try:
                            await self.adjust_position(
                                trading_pair=trading_pair,
                                target_size=0,
                                current_price=0  # Market order
                            )
                            logger.info(f"Closed position for {trading_pair}")
                        except Exception as e:
                            logger.error(f"Failed to close position for {trading_pair}: {e}")

            # Close streaming connection
            if self.streaming_task:
                self.streaming_task.cancel()
                
            logger.info("Trading system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Get the current position for a specific trading pair.
        
        Args:
            symbol (str): The trading pair symbol (e.g., 'BTC-USD')
            
        Returns:
            dict: Position information including size, entry price, etc.
        """
        try:
            # Example implementation
            accounts = await self.exchange_interface.get_accounts()
            position = {
                'size': 0,
                'entry_price': 0,
                'current_value': 0
            }
            
            # Parse the symbol to get the base currency
            base_currency = symbol.split('-')[0]
            
            # Find the account for this currency
            for account in accounts:
                if account['currency'] == base_currency:
                    position['size'] = float(account['balance'])
                    #if position['size'] > 0 and 'avg_entry_price' in account: #avg_entry_price is not available in the response
                    #    position['entry_price'] = float(account['avg_entry_price'])
                    position['current_value'] = position['size'] * await self.get_current_price(symbol)
            
            return position
        except Exception as e:
            logger.error(f"Failed to get position for {symbol}: {e}")
            return {
                'size': 0,
                'entry_price': 0,
                'current_value': 0,
                'error': str(e)
            }
