"""
Script to fix module structure issues where Python might be confused between
directory modules and file modules.

This script:
1. Detects conflicts where both a .py file and directory with the same name exist
2. Removes the directory structure completely
3. Cleans Python's import cache
"""
import os
import sys
import shutil
import logging
import stat

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_readonly(func, path, excinfo):
    """Remove read-only attribute and retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def fix_coinbase_streaming():
    """
    Specifically fix the coinbase_streaming module structure.
    
    This function:
    1. Checks if both file and directory exist
    2. Backs up directory content if needed
    3. Removes the directory structure
    4. Cleans Python cache files
    """
    logger.info("Fixing coinbase_streaming module structure...")
    
    # Define paths
    module_dir = os.path.join('src', 'core', 'coinbase_streaming')
    module_file = os.path.join('src', 'core', 'coinbase_streaming.py')
    
    # Check if directory exists
    if os.path.isdir(module_dir):
        logger.info(f"Found directory: {module_dir}")
        
        # Check if there's an __init__.py file to back up
        init_file = os.path.join(module_dir, '__init__.py')
        if os.path.exists(init_file):
            logger.info(f"Found __init__.py in directory")
            
            # Create backup
            backup_file = os.path.join('src', 'core', 'coinbase_streaming_init_backup.py')
            try:
                shutil.copy(init_file, backup_file)
                logger.info(f"Backed up __init__.py to {backup_file}")
            except Exception as e:
                logger.error(f"Failed to back up __init__.py: {e}")
        
        # Remove directory structure
        try:
            shutil.rmtree(module_dir, onerror=remove_readonly)
            logger.info(f"Successfully removed directory: {module_dir}")
        except Exception as e:
            logger.error(f"Failed to remove directory {module_dir}: {e}")
            logger.error("Please close any programs that might be using files in this directory and try again.")
            return False
    else:
        logger.info(f"Directory {module_dir} does not exist")
    
    # Check if the file exists
    if os.path.exists(module_file):
        logger.info(f"File {module_file} exists")
    else:
        logger.error(f"File {module_file} does not exist!")
        logger.error("Please create this file with the proper CoinbaseStreaming implementation")
        return False
    
    # Clean Python cache files
    clean_python_cache()
    
    logger.info("Module structure fix complete")
    return True

def clean_python_cache():
    """Remove Python cache files to force reloading modules."""
    logger.info("Cleaning Python cache files...")
    
    # Track count of removed items
    count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk('.'):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_dir)
                logger.info(f"Removed cache directory: {pycache_dir}")
                count += 1
            except Exception as e:
                logger.error(f"Failed to remove {pycache_dir}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                try:
                    os.remove(pyc_file)
                    logger.info(f"Removed cache file: {pyc_file}")
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to remove {pyc_file}: {e}")
    
    logger.info(f"Cleaned {count} cache items")

def main():
    """Main function."""
    success = fix_coinbase_streaming()
    
    if success:
        logger.info("Module structure has been fixed. Please run your verification script again.")
        return 0
    else:
        logger.error("Failed to fix module structure. Manual intervention required.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
