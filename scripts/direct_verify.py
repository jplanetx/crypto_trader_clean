"""
Direct verification of the CoinbaseStreaming component.
This script bypasses the regular verification framework to isolate the issue.
"""
import sys
import os
import importlib
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def verify_coinbase_streaming():
    """Directly verify the CoinbaseStreaming component."""
    logger.info("Starting direct verification of CoinbaseStreaming")
    
    # Check if file exists
    file_path = Path("src/core/coinbase_streaming.py")
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    logger.info(f"File exists: {file_path}")
    
    # Print current sys.path
    logger.info("Current sys.path:")
    for path in sys.path:
        logger.info(f"  - {path}")
    
    # Try different import methods
    try:
        logger.info("Attempting import method 1: direct import")
        from src.core.coinbase_streaming import CoinbaseStreaming
        logger.info("✅ Import method 1 succeeded")
        logger.info(f"CoinbaseStreaming class location: {CoinbaseStreaming.__module__}")
    except ImportError as e:
        logger.error(f"❌ Import method 1 failed: {e}")
    
    try:
        logger.info("Attempting import method 2: importlib")
        module = importlib.import_module("src.core.coinbase_streaming")
        cls = getattr(module, "CoinbaseStreaming", None)
        if cls:
            logger.info("✅ Import method 2 succeeded")
            logger.info(f"CoinbaseStreaming class location: {cls.__module__}")
        else:
            logger.error("❌ Import method 2 failed: Class not found in module")
            # List all attributes in the module
            logger.info("Module attributes:")
            for attr in dir(module):
                logger.info(f"  - {attr}")
    except ImportError as e:
        logger.error(f"❌ Import method 2 failed: {e}")
    
    # Check the file content
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        logger.info(f"File size: {len(content)} bytes")
        # Check if the class is defined in the file
        if "class CoinbaseStreaming" in content:
            logger.info("✅ CoinbaseStreaming class definition found in file")
        else:
            logger.error("❌ CoinbaseStreaming class definition NOT found in file")
            # Print the first few lines
            logger.info("First 10 lines of file:")
            for i, line in enumerate(content.split('\n')[:10]):
                logger.info(f"{i+1}: {line}")
    except Exception as e:
        logger.error(f"Error reading file: {e}")
    
    return True

if __name__ == "__main__":
    verify_coinbase_streaming()
