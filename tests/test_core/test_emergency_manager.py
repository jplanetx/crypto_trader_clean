import os
import shutil
import pytest
import logging
import time
from src.core.emergency_manager import EmergencyManager

# Use the new safe_tmp_path fixture from conftest.py
@pytest.fixture
def emergency_manager(safe_tmp_path):
    """Fixture for creating an EmergencyManager instance with a safe temporary directory."""
    # Use the safe temporary directory
    backup_dir = os.path.join(safe_tmp_path, "emergency_backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    config = {"test_setting": "test_value"}
    manager = EmergencyManager(backup_dir=backup_dir, config=config)
    
    yield manager

@pytest.fixture
def test_file(safe_tmp_path):
    """Fixture for creating a test file in a safe temporary directory."""
    test_file_path = os.path.join(safe_tmp_path, "test_file.txt")
    with open(test_file_path, "w") as f:
        f.write("This is a test file.")
    return test_file_path

def test_create_backup(emergency_manager, test_file):
    backup_file = emergency_manager.create_backup(test_file)
    assert backup_file is not None
    assert os.path.exists(backup_file)
    assert backup_file.startswith(emergency_manager.backup_dir)
    # Additional check to ensure the backup file is not empty
    assert os.path.getsize(backup_file) > 0

def test_recover_from_backup(emergency_manager, test_file):
    backup_file = emergency_manager.create_backup(test_file)
    assert backup_file is not None

    # Modify the original file
    with open(test_file, "w") as f:
        f.write("This is the modified content.")

    # Recover from backup
    emergency_manager.recover_from_backup(backup_file, test_file)

    # Verify the content is restored
    with open(test_file, "r") as f:
        content = f.read()
    assert content == "This is a test file."

def test_verify_backup(emergency_manager, test_file):
    backup_file = emergency_manager.create_backup(test_file)
    assert backup_file is not None

    # Verify the backup
    result = emergency_manager.verify_backup(backup_file, test_file)
    assert result is True

    # Modify the original file
    with open(test_file, "w") as f:
        f.write("This is the modified content.")

    # Verify the backup again (should fail)
    result = emergency_manager.verify_backup(backup_file, test_file)
    assert result is False

def test_recover_from_backup_file_not_found(emergency_manager, test_file):
    backup_file = "non_existent_backup.bak"
    target_file = test_file
    result = emergency_manager.recover_from_backup(backup_file, target_file)
    assert result is False

def test_recover_from_backup_success(emergency_manager, test_file):
    # Create a backup file
    backup_file = emergency_manager.create_backup(test_file)
    assert backup_file is not None

    # Modify the original file
    with open(test_file, "w") as f:
        f.write("This is the modified content.")

    # Recover from backup
    result = emergency_manager.recover_from_backup(backup_file, test_file)
    assert result is True

    # Verify the content is restored
    with open(test_file, "r") as f:
        content = f.read()
    assert content == "This is a test file."

# Use the patch_logging fixture along with caplog
@pytest.mark.usefixtures("patch_logging")
def test_perform_emergency_shutdown(emergency_manager, caplog):
    """Test that perform_emergency_shutdown logs a critical message."""
    # Clear any existing logs first
    caplog.clear()
    
    # Set the log level to CRITICAL to capture the log
    with caplog.at_level(logging.CRITICAL):
        # Perform the emergency shutdown
        emergency_manager.perform_emergency_shutdown()
    
    # Find the specific log message we're looking for
    critical_messages = [record.message for record in caplog.records 
                         if record.levelname == "CRITICAL"]
    
    # Check if our message is in the critical messages
    assert "Emergency shutdown initiated!" in critical_messages
