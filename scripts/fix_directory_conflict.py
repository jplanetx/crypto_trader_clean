"""
Script to fix directory vs file conflicts in the project structure.

This script ensures that module paths are files rather than directories
with __init__.py files, which can cause import conflicts.
"""
import os
import shutil
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_directory_conflict(module_path):
    """
    Convert a module implemented as a directory with __init__.py to a single file.
    
    Args:
        module_path: Path to the module (without .py extension)
    
    Returns:
        bool: True if fixed, False otherwise
    """
    # Check if directory exists
    dir_path = module_path
    file_path = f"{module_path}.py"
    init_path = os.path.join(dir_path, "__init__.py")
    
    if not os.path.isdir(dir_path):
        logger.info(f"No directory conflict for {dir_path}")
        return False
    
    logger.info(f"Found directory module: {dir_path}")
    
    # Check if __init__.py exists
    if os.path.exists(init_path):
        # Read the content of __init__.py
        try:
            with open(init_path, 'r') as f:
                init_content = f.read()
            logger.info(f"Read content from {init_path}")
        except Exception as e:
            logger.error(f"Failed to read {init_path}: {e}")
            init_content = ""
    else:
        logger.warning(f"No __init__.py found in {dir_path}")
        init_content = ""
    
    # Create or update the .py file
    try:
        # If the file doesn't exist yet, create it with __init__.py content
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(init_content)
            logger.info(f"Created {file_path}")
        else:
            # If both exist, we'll need to decide which content to keep
            logger.warning(f"File {file_path} already exists. Please merge content manually.")
    except Exception as e:
        logger.error(f"Failed to create/update {file_path}: {e}")
        return False
    
    # Remove the directory
    try:
        # On Windows, sometimes we need to be more forceful with removal
        try:
            shutil.rmtree(dir_path)
        except Exception:
            import stat
            # Make all files writeable to allow deletion
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    os.chmod(file_path, stat.S_IWRITE)
            # Try again
            shutil.rmtree(dir_path)
        
        logger.info(f"Removed directory {dir_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to remove directory {dir_path}: {e}")
        logger.error("Please remove it manually and try again.")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        logger.error("Usage: python fix_directory_conflict.py <module_path>")
        logger.info("Example: python fix_directory_conflict.py src/core/coinbase_streaming")
        return 1
    
    module_path = sys.argv[1]
    
    # Convert forward slashes to OS-specific path separator
    module_path = os.path.normpath(module_path)
    
    if fix_directory_conflict(module_path):
        logger.info("Directory conflict resolved successfully.")
        return 0
    else:
        logger.error("Failed to resolve directory conflict.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
