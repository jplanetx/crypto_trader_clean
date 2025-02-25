"""Example of testing log messages using pytest's caplog fixture."""
import pytest
import logging
from src.core.emergency_manager import EmergencyManager

def test_critical_log_capture(caplog):
    """Demonstrate capturing CRITICAL level log messages."""
    # Set the log level to capture
    caplog.set_level(logging.CRITICAL)
    
    # Create instance of class being tested
    manager = EmergencyManager()
    
    # Perform action that should generate CRITICAL log
    manager.handle_critical_failure("Database connection lost")
    
    # Verify log message content and level
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "CRITICAL"
    assert "Database connection lost" in record.message
    
    # You can also check multiple attributes of the log record
    assert record.levelno == logging.CRITICAL
    assert record.module == "emergency_manager"

def test_multiple_log_messages(caplog):
    """Demonstrate capturing multiple log messages."""
    caplog.set_level(logging.CRITICAL)
    manager = EmergencyManager()
    
    # Generate multiple critical logs
    manager.handle_critical_failure("Error 1")
    manager.handle_critical_failure("Error 2")
    
    # Filter for specific messages
    critical_logs = [
        record for record in caplog.records
        if record.levelno == logging.CRITICAL
    ]
    
    assert len(critical_logs) == 2
    assert "Error 1" in critical_logs[0].message
    assert "Error 2" in critical_logs[1].message

def test_log_context(caplog):
    """Demonstrate using caplog as a context manager."""
    manager = EmergencyManager()
    
    # Use caplog as context manager to capture specific section
    with caplog.at_level(logging.CRITICAL):
        manager.handle_critical_failure("Test error")
    
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Emergency: Test error"

def test_clear_logs(caplog):
    """Demonstrate clearing logs between test sections."""
    manager = EmergencyManager()
    
    # First section
    with caplog.at_level(logging.CRITICAL):
        manager.handle_critical_failure("First error")
    assert len(caplog.records) == 1
    
    # Clear logs
    caplog.clear()
    
    # Second section
    with caplog.at_level(logging.CRITICAL):
        manager.handle_critical_failure("Second error")
    assert len(caplog.records) == 1
    assert "Second error" in caplog.records[0].message

def test_log_formatting(caplog):
    """Demonstrate checking log formatting."""
    caplog.set_level(logging.CRITICAL)
    manager = EmergencyManager()
    
    manager.handle_critical_failure("Test")
    
    record = caplog.records[0]
    # Check log follows expected format
    assert record.name == "emergency_manager"  # Logger name
    assert record.levelname == "CRITICAL"      # Level name
    assert record.pathname.endswith("emergency_manager.py")  # Source file
    assert isinstance(record.created, float)   # Timestamp
    assert isinstance(record.lineno, int)      # Line number
