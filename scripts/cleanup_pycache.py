"""
Script to clean up Python's import cache directories to fix import issues.

This script removes __pycache__ directories and .pyc files that can cause
stale imports when module structure changes.
"""
import os
import shutil
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_pycache(directory='.'):
    """
    Clean up __pycache__ directories and .pyc files.
    
    Args:
        directory: Directory to start cleaning from
    
    Returns:
        int: Number of items cleaned up
    """
    count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_dir)
                logger.info(f"Removed directory: {pycache_dir}")
                count += 1
            except Exception as e:
                logger.error(f"Failed to remove {pycache_dir}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                try:
                    os.remove(pyc_file)
                    logger.info(f"Removed file: {pyc_file}")
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to remove {pyc_file}: {e}")
    
    return count

def main():
    """Main function."""
    start_dir = '.' if len(sys.argv) < 2 else sys.argv[1]
    
    logger.info(f"Cleaning Python cache files in {os.path.abspath(start_dir)}")
    cleaned = cleanup_pycache(start_dir)
    
    logger.info(f"Cleaned up {cleaned} cache items")
    return 0

if __name__ == "__main__":
    sys.exit(main())
