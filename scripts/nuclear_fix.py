"""
Reset everything related to the coinbase_streaming module.
This script performs a complete cleanup and recreation of the module.
"""
import os
import sys
import shutil
import importlib
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_directory(directory_path):
    """Remove a directory and all its contents."""
    try:
        if os.path.exists(directory_path):
            logger.info(f"Removing directory: {directory_path}")
            shutil.rmtree(directory_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error removing directory {directory_path}: {e}")
        return False

def nuclear_fix():
    """Perform a complete reset of the coinbase_streaming module."""
    # Get absolute paths
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Target paths
    module_dir = os.path.join(root_dir, 'src', 'core', 'coinbase_streaming')
    module_file = os.path.join(root_dir, 'src', 'core', 'coinbase_streaming.py')
    backup_file = os.path.join(root_dir, 'src', 'core', 'coinbase_streaming_backup.py')
    core_pycache = os.path.join(root_dir, 'src', 'core', '__pycache__')
    
    logger.info("Starting nuclear fix for coinbase_streaming module")
    
    # Save file content if it exists
    file_content = None
    if os.path.exists(module_file):
        try:
            with open(module_file, 'r') as f:
                file_content = f.read()
            logger.info(f"Saved content from {module_file} ({len(file_content)} bytes)")
        except Exception as e:
            logger.error(f"Error reading file {module_file}: {e}")
    
    # Create a backup of the file content if it exists
    if file_content:
        try:
            with open(backup_file, 'w') as f:
                f.write(file_content)
            logger.info(f"Created backup at {backup_file}")
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    # Clear Python's module cache
    modules_to_clear = []
    for key in list(sys.modules.keys()):
        if 'coinbase' in key or 'src' in key:
            modules_to_clear.append(key)
            del sys.modules[key]
    logger.info(f"Cleared {len(modules_to_clear)} modules from sys.modules cache")
    
    # Remove the directory if it exists
    if os.path.exists(module_dir) and os.path.isdir(module_dir):
        dir_removed = clean_directory(module_dir)
        if dir_removed:
            logger.info(f"Successfully removed directory: {module_dir}")
            # Small delay to ensure OS file operations complete
            time.sleep(0.5)
        else:
            logger.error(f"Failed to remove directory: {module_dir}")
    else:
        logger.info(f"Directory does not exist: {module_dir}")
    
    # Remove the file if it exists
    if os.path.exists(module_file):
        try:
            os.remove(module_file)
            logger.info(f"Removed file: {module_file}")
            # Small delay to ensure OS file operations complete
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error removing file {module_file}: {e}")
    
    # Remove __pycache__ directory in core
    if os.path.exists(core_pycache):
        cache_removed = clean_directory(core_pycache)
        if cache_removed:
            logger.info(f"Removed __pycache__ directory: {core_pycache}")
        else:
            logger.error(f"Failed to remove __pycache__ directory: {core_pycache}")
    
    # Create the file with the saved content
    if file_content:
        try:
            with open(module_file, 'w') as f:
                f.write(file_content)
            logger.info(f"Recreated file: {module_file} with {len(file_content)} bytes")
        except Exception as e:
            logger.error(f"Error creating file {module_file}: {e}")
    else:
        # Create a minimal file if no content was saved
        minimal_content = '''"""
Coinbase streaming module for real-time market data.
"""

class CoinbaseStreaming:
    """Coinbase Advanced Trade WebSocket API client."""
    
    def __init__(self, api_key, api_secret, product_ids):
        self.api_key = api_key
        self.api_secret = api_secret
        self.product_ids = product_ids
        self.prices = {}
    
    def connect(self):
        """Connect to the Coinbase WebSocket."""
        pass
    
    def receive_data(self):
        """Receive data from the WebSocket."""
        pass
    
    def get_current_price(self, symbol):
        """Get the current price for a symbol."""
        return self.prices.get(symbol, 0)
'''
        try:
            with open(module_file, 'w') as f:
                f.write(minimal_content)
            logger.info(f"Created minimal file: {module_file}")
        except Exception as e:
            logger.error(f"Error creating minimal file {module_file}: {e}")
    
    # Verify the file exists and directory doesn't
    file_exists = os.path.exists(module_file) and os.path.isfile(module_file)
    dir_exists = os.path.exists(module_dir) and os.path.isdir(module_dir)
    
    if file_exists and not dir_exists:
        logger.info("SUCCESS: File exists and directory doesn't exist")
    else:
        logger.error(f"PROBLEM: File exists: {file_exists}, Directory exists: {dir_exists}")
    
    # Try importing the module
    try:
        # Add root to path
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
            
        # Import the module
        importlib.invalidate_caches()
        from src.core.coinbase_streaming import CoinbaseStreaming
        logger.info("✅ Successfully imported CoinbaseStreaming!")
        return True
    except Exception as e:
        logger.error(f"❌ Import still failed: {e}")
        logger.error("You may need to restart your Python interpreter/terminal.")
        return False

if __name__ == "__main__":
    nuclear_fix()
