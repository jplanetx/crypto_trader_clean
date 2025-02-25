"""
Basic example demonstrating how to use the trading system.
"""
import asyncio
import logging
from decimal import Decimal
from src.core import TradingCore

# Configure logging
logger = logging.getLogger(__name__)

class MockExchange:
    """Mock exchange interface for demonstration."""
    async def buy(self, trading_pair: str, size: float, price: float):
        logger.info(f"Mock buy: {size} {trading_pair} at {price}")
        return {
            'order_id': '12345',
            'status': 'filled'
        }

    async def sell(self, trading_pair: str, size: float, price: float):
        logger.info(f"Mock sell: {size} {trading_pair} at {price}")
        return {
            'order_id': '12346',
            'status': 'filled'
        }

class MockRiskManager:
    """Mock risk manager for demonstration."""
    async def check_order_risk(self, trading_pair: str, side: str, size: float, price: float) -> bool:
        logger.info(f"Checking risk for {side} {size} {trading_pair} at {price}")
        return True

async def run_trading_example():
    """Run a basic trading example."""
    try:
        # Initialize trading system with mocks
        trading = TradingCore(
            exchange_interface=MockExchange(),
            risk_manager=MockRiskManager()
        )
        
        # Initialize the system
        await trading.initialize()
        logger.info("Trading system initialized")
        
        # Example trade sequence
        trading_pair = 'BTC-USD'
        
        # Execute buy order
        buy_result = await trading.execute_trade(
            trading_pair=trading_pair,
            side='buy',
            size=1.0,
            price=50000.0
        )
        logger.info(f"Buy order executed: {buy_result}")
        
        # Check position
        position = await trading.get_position(trading_pair)
        logger.info(f"Current position: {position}")
        
        # Get trading statistics
        stats = trading.get_daily_stats()
        logger.info(f"Trading stats: {stats}")
        
        # Adjust position
        adjust_result = await trading.adjust_position(
            trading_pair=trading_pair,
            target_size=0.5,  # Reduce position by half
            current_price=55000.0
        )
        logger.info(f"Position adjusted: {adjust_result}")
        
        # Final position check
        final_position = await trading.get_position(trading_pair)
        logger.info(f"Final position: {final_position}")
        
        # Graceful shutdown
        await trading.shutdown()
        logger.info("Trading system shutdown complete")

    except Exception as e:
        logger.error(f"Error during trading: {str(e)}")
        raise

def main():
    """Main entry point."""
    try:
        asyncio.run(run_trading_example())
    except KeyboardInterrupt:
        logger.info("Trading example stopped by user")
    except Exception as e:
        logger.error(f"Trading example failed: {str(e)}")

if __name__ == "__main__":
    main()
