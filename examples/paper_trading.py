"""
Example of paper trading using the CoinbaseClient.
"""
import time
import logging
from decimal import Decimal
import asyncio
from src.core.coinbase_client import CoinbaseClient
from src.core.config_manager import ConfigManager, TradingConfig, RiskConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_paper_trading():
    """Run paper trading example."""
    # Create a configuration
    risk_config = RiskConfig(
        max_position_size=Decimal("0.01"),  # Small position size for testing
        stop_loss_pct=0.02,                 # 2% stop loss
        max_daily_loss=Decimal("50.0"),     # $50 max daily loss
        max_open_orders=3                   # Max 3 open orders at once
    )
    
    # Create config
    config = TradingConfig(
        trading_pairs=["BTC-USD", "ETH-USD"],
        risk_config=risk_config,
        paper_trading=True,
        api_key="your_test_api_key",
        api_secret="your_test_api_secret"
    )
    
    # Initialize the client
    client = CoinbaseClient(
        api_key=config.api_key,
        private_key=config.api_secret,
        product_ids=config.trading_pairs
    )
    
    # In paper trading mode, simulate prices
    client.simulate_price_update("BTC-USD", 50000.0)
    client.simulate_price_update("ETH-USD", 3000.0)
    
    # Print current prices
    btc_price = client.get_current_price("BTC-USD")
    eth_price = client.get_current_price("ETH-USD")
    
    logger.info(f"Current BTC price: ${btc_price}")
    logger.info(f"Current ETH price: ${eth_price}")
    
    # Paper trading simulation
    logger.info("Starting paper trading simulation...")
    
    # Simulate some price changes
    for i in range(10):
        # Simulate market movements
        btc_change = (i % 3 - 1) * 100  # -100, 0, or +100
        eth_change = (i % 5 - 2) * 10   # -20, -10, 0, +10, or +20
        
        new_btc_price = btc_price + btc_change
        new_eth_price = eth_price + eth_change
        
        # Update simulated prices
        client.simulate_price_update("BTC-USD", new_btc_price)
        client.simulate_price_update("ETH-USD", new_eth_price)
        
        logger.info(f"[{i+1}/10] BTC: ${new_btc_price} ({btc_change:+.2f}), ETH: ${new_eth_price} ({eth_change:+.2f})")
        
        # Simple trading logic for demonstration
        if btc_change > 0 and eth_change < 0:
            logger.info("SIGNAL: Buy BTC, Sell ETH")
        elif btc_change < 0 and eth_change > 0:
            logger.info("SIGNAL: Sell BTC, Buy ETH")
        else:
            logger.info("SIGNAL: Hold positions")
        
        # Wait a bit before the next iteration
        await asyncio.sleep(1)
    
    logger.info("Paper trading simulation complete!")

if __name__ == "__main__":
    asyncio.run(run_paper_trading())
