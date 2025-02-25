import os
import shutil
import pytest
import logging
import time
from src.core.emergency_manager import EmergencyManager

# Setup and Teardown
@pytest.fixture
def emergency_manager(tmp_path):
    # Create a more reliable test directory path
    base_dir = tmp_path.parent
    backup_dir = base_dir / f"backup_test_{int(time.time())}"
    backup_dir.mkdir(exist_ok=True)
    
    config = {"test_setting": "test_value"}
    manager = EmergencyManager(backup_dir=str(backup_dir), config=config)
    
    yield manager
    
    # Teardown: ensure proper cleanup of file handles
    # We first make sure all file handles are closed
    manager = None  # Clear reference to allow GC
    import gc
    gc.collect()    # Force garbage collection
    
    # Wait a brief moment to ensure file operations complete
    time.sleep(0.2)
    
    # Try to remove the directory with proper error handling
    if backup_dir.exists():
        try:
            # On Windows, use os.rmdir for better permission handling
            for root, dirs, files in os.walk(str(backup_dir), topdown=False):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass
                for dir in dirs:
                    try:
                        os.rmdir(os.path.join(root, dir))
                    except:
                        pass
            # Try to remove the top directory
            try:
                os.rmdir(str(backup_dir))
            except:
                pass
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
    # Configure caplog properly
    caplog.clear()  # Clear any existing logs
    
    # Ensure the log level is set correctly for the test
    with caplog.at_level(logging.CRITICAL, logger="src.core.emergency_manager"):
        # Perform the emergency shutdown
        emergency_manager.perform_emergency_shutdown()
    
    # Assert that the log message is in the output
    assert "Emergency shutdown initiated!" in caplog.text
    
    # Additional verification
    found_critical_log = False
    for record in caplog.records:
        if (record.levelname == "CRITICAL" and 
            record.message == "Emergency shutdown initiated!" and
            record.name == "src.core.emergency_manager"):
            found_critical_log = True
            break
    
    assert found_critical_log, "Critical log message not found in expected format"
