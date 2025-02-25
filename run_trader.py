"""
Main script to run the trading system.
Simple startup script for personal use.
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
import coinbasepro

from src.core import TradingCore
from src.core.config_manager import ConfigManager

# Load environment variables
load_dotenv()

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"


logger = logging.getLogger(__name__)

async def coinbase_stream():
    """Connect to Coinbase and stream real-time data."""
    config_manager = ConfigManager()
    api_key = config_manager.coinbase_api_key
    api_secret = config_manager.coinbase_api_secret

    if not api_key or not api_secret:
        logger.error("Coinbase API key and secret must be set in .env file")
        return

    auth_client = coinbasepro.AuthenticatedClient(api_key, api_secret, os.getenv("COINBASE_API_PASSPHRASE"))

    async def handle_message(message):
        """Process incoming messages from the Coinbase stream."""
        logger.info(f"Received message: {message}")

    async def subscribe():
        """Subscribe to the Coinbase stream."""
        try:
            wsClient = coinbasepro.WebsocketClient(url="wss://ws-feed.exchange.coinbase.com", products=["BTC-USD"], auth=auth_client, channels=["ticker"])
            wsClient.message_callback = handle_message
            wsClient.start()
            await asyncio.sleep(3600)  # Run for 1 hour
            wsClient.close()
        except Exception as e:
            logger.error(f"Error connecting to Coinbase: {e}")

    await subscribe()

async def run_trading():
    """Run the trading system."""
    try:
        # Initialize trading system
        trading = TradingCore()
        await trading.initialize()
        logger.info("Trading system initialized successfully")

        # Start Coinbase stream
        asyncio.create_task(coinbase_stream())

        while trading.is_active():
            try:
                # Get current positions
                for pair in trading.get_trading_pairs():
                    position = await trading.get_position(pair)
                    logger.info(f"Current position for {pair}: {position}")

                # Get trading statistics
                stats = trading.get_daily_stats()
                logger.info(f"Daily trading statistics: {stats}")

                # Wait before next update
                await asyncio.sleep(60)  # Update every minute

            except KeyboardInterrupt:
                logger.info("Shutting down trading system...")
                await trading.shutdown()
                break
            except Exception as e:
                logger.error(f"Error during trading: {str(e)}")
                # Continue running despite errors
                await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise

def main():
    """Entry point for the trading system."""
    try:
        logger.info("Starting trading system...")
        asyncio.run(run_trading())
    except KeyboardInterrupt:
        logger.info("Trading system stopped by user")
    except Exception as e:
        logger.error(f"Trading system failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
