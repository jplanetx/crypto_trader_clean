"""
Script to debug the logging issue with EmergencyManager tests.
"""
import logging
import sys
import pytest
from unittest.mock import patch

def main():
    # Configure root logger for console output
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    # Log some diagnostic information
    logging.info("Starting debug script")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Pytest version: {pytest.__version__}")
    
    # Try to diagnose the mock issue
    logging.info("Testing mock behavior that might be causing the error")
    try:
        from unittest.mock import MagicMock
        mock = MagicMock()
        # This is similar to what's happening in the test
        logging_level = mock
        # Try the same operation that's failing
        if isinstance(logging_level, int):
            pass
        elif str(logging_level) == logging_level:
            pass
        else:
            raise TypeError(f"Level not an integer or a valid string: {logging_level}")
    except Exception as e:
        logging.error(f"Mock test produced error: {e}")
        logging.exception("Traceback:")
    
    # Run only the problematic test with detailed output
    logging.info("Running the failing test with verbose output")
    
    # Define the test we want to run
    test_path = "tests/test_core/test_emergency_manager.py::test_perform_emergency_shutdown"
    
    try:
        # Try with patching the problematic part
        logging.info("Attempting to run test with patched logging")
        
        # Run pytest programmatically with specific args
        args = [
            "-v",  # Verbose
            "--no-header",  # No header
            "--tb=native",  # Native traceback format
            "-s",  # Don't capture stdout/stderr
            test_path
        ]
        
        # Run pytest and capture the exit code
        exit_code = pytest.main(args)
        logging.info(f"Test run completed with exit code: {exit_code}")
        
    except Exception as e:
        logging.error(f"Error running test: {e}")
        logging.exception("Traceback:")

if __name__ == "__main__":
    main()
