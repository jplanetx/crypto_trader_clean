"""
Simple script to test importing critical modules.
This will help identify import issues quickly.
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_coinbase_streaming_import():
    """Test importing the CoinbaseStreaming class."""
    logger.info("Testing import of CoinbaseStreaming...")
    try:
        # Add the project root to the path to ensure imports work
        sys.path.insert(0, '.')
        
        # Try importing directly from module file
        from src.core.coinbase_streaming import CoinbaseStreaming
        
        logger.info("✓ Successfully imported CoinbaseStreaming!")
        logger.info(f"CoinbaseStreaming class location: {CoinbaseStreaming.__module__}")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import CoinbaseStreaming: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_coinbase_streaming_import()
    sys.exit(0 if success else 1)
