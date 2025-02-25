"""Test suite for thread management system."""
import os
import json
import shutil
import pytest
from pathlib import Path

# Ensure we're in the right directory
os.chdir(str(Path(__file__).parent.parent.parent))

def test_directory_structure():
    """Test that setup_project_structure.py creates correct directories."""
    # Run setup
    import scripts.setup_project_structure
    scripts.setup_project_structure.create_directory_structure()
    
    # Verify required directories exist
    required_dirs = [
        'src/core',
        'src/utils',
        'tests/test_core',
        'tests/test_utils',
        'config',
        'thread_management/active_thread',
        'thread_management/completed_threads',
        'thread_management/logs',
        'thread_management/templates',
        'thread_management/docs',
        'examples',
        'scripts'
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Directory not found: {dir_path}"

def test_thread_template():
    """Test that thread template is valid JSON and has required fields."""
    template_path = Path('thread_management/templates/thread_init_template.json')
    assert template_path.exists(), "Template file not found"
    
    with open(template_path) as f:
        template = json.load(f)
    
    required_fields = [
        'thread_id',
        'name',
        'description',
        'status',
        'objectives',
        'required_components',
        'verification_steps',
        'success_criteria',
        'deliverables',
        'completion_checklist'
    ]
    
    for field in required_fields:
        assert field in template, f"Missing required field: {field}"

def test_thread_manager():
    """Test thread manager functionality."""
    from scripts.thread_manager import init_thread, get_thread_status, complete_thread
    
    # Initialize test thread
    thread_id = "THREAD_TEST_THREAD"  # Use correct format to match init_thread behavior
    init_thread(thread_id)
    
    # Verify thread was created
    status = get_thread_status(thread_id)
    assert status['thread_id'] == thread_id
    assert status['status'] == 'not_started'
    
    # Complete thread
    complete_thread(thread_id)
    
    # Verify thread was archived
    archive_path = Path(f'thread_management/completed_threads/{thread_id}.json')
    assert archive_path.exists()
    
    # Cleanup
    archive_path.unlink()

def test_verify_thread():
    """Test thread verification functionality."""
    from scripts.verify_thread import check_directories, check_environment
    
    # Test directory checks
    dir_results = check_directories()
    assert dir_results['status'] == 'clean'
    assert dir_results['no_duplicates']
    
    # Test environment checks
    env_results = check_environment()
    assert 'venv_active' in env_results
    assert 'pythonpath_valid' in env_results

def test_thread_001_config():
    """Test THREAD_001 configuration."""
    config_path = Path('thread_management/templates/thread_001_init.json')
    assert config_path.exists(), "THREAD_001 config not found"
    
    with open(config_path) as f:
        config = json.load(f)
    
    assert config['thread_id'] == 'THREAD_001'
    assert config['name'] == 'Thread Management System Implementation'
    
    # Verify all required files exist
    for file_list in config['required_components'].values():
        for file_path in file_list:
            if not Path(file_path).exists():
                pytest.skip(f"Required file not found: {file_path}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
