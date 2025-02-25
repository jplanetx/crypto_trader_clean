"""
Pytest configuration for the project.
"""
import os
import shutil
import pytest
import logging
import tempfile
import time
from unittest.mock import patch

# Configure logging for tests
@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for all tests."""
    # Reset logging config
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        
    # Configure basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Make sure all loggers propagate
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.propagate = True
        
    # Return the root logger
    return root

# Create a fixture to patch the manager.disable attribute that causes the TypeError
@pytest.fixture
def patch_logging():
    """Patch logging.disable to avoid TypeError with MagicMock."""
    real_check_level = logging._checkLevel
    
    def patched_check_level(level):
        # Handle MagicMock objects by returning a default level
        if hasattr(level, '_mock_name') and 'disable' in getattr(level, '_mock_name', ''):
            return logging.NOTSET
        return real_check_level(level)
    
    with patch('logging._checkLevel', side_effect=patched_check_level):
        yield

# Create a safe temporary directory fixture that cleans up properly
@pytest.fixture
def safe_tmp_path():
    """Create a temporary directory that cleans up properly on Windows."""
    # Create temporary directory with a unique name based on timestamp
    tmp_dir = tempfile.mkdtemp(prefix=f"pytest_safe_{int(time.time())}_")
    yield tmp_dir
    
    # Clean up: First sleep a bit to let any file operations complete
    time.sleep(0.5)
    
    # Force cleanup of any lingering handles
    import gc
    gc.collect()
    
    # Try to remove the directory with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Remove all files first
            for root, dirs, files in os.walk(tmp_dir, topdown=False):
                for name in files:
                    try:
                        path = os.path.join(root, name)
                        os.chmod(path, 0o777)  # Ensure we have permissions
                        os.unlink(path)
                    except:
                        pass
                        
                # Then remove directories
                for name in dirs:
                    try:
                        path = os.path.join(root, name)
                        os.chmod(path, 0o777)  # Ensure we have permissions
                        os.rmdir(path)
                    except:
                        pass
            
            # Finally remove the top directory
            if os.path.exists(tmp_dir):
                os.rmdir(tmp_dir)
                
            # If we get here, cleanup was successful
            break
        except:
            # If cleanup failed, wait and try again
            time.sleep(1)
    
    # Even if cleanup failed, don't fail the test
