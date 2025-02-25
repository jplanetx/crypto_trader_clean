import os
import shutil
import pytest
import logging
from src.core.emergency_manager import EmergencyManager

# Setup and Teardown
@pytest.fixture
def emergency_manager(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    config = {"test_setting": "test_value"}
    manager = EmergencyManager(backup_dir=str(backup_dir), config=config)
    yield manager
    # Teardown: remove the backup directory after the test
    try:
        # Close any potential file handles
        import gc
        gc.collect()  # Force garbage collection to close any lingering file handles
        
        # Try to remove the directory
        if backup_dir.exists():
            for retry in range(3):  # Retry a few times
                try:
                    shutil.rmtree(str(backup_dir), ignore_errors=True)
                    break
                except (PermissionError, OSError):
                    import time
                    time.sleep(0.1)  # Small delay before retry
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to cleanup test directory: {e}")
        # Don't fail the test if cleanup fails
        pass

@pytest.fixture
def test_file(tmp_path):
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("This is a test file.")
    return str(test_file)

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

def test_perform_emergency_shutdown(emergency_manager, caplog):
    # Configure caplog
    caplog.set_level(logging.CRITICAL)
    
    # Perform the emergency shutdown
    emergency_manager.perform_emergency_shutdown()
    
    # Assert that the log message is in the output
    assert "Emergency shutdown initiated!" in caplog.text
    
    # Verify the log level and other attributes
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "CRITICAL"
    assert record.message == "Emergency shutdown initiated!"
    assert record.name == "src.core.emergency_manager"