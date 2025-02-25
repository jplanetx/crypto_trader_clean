"""Setup script for crypto_trader_clean project structure."""
import os
from pathlib import Path

def create_directory_structure():
    """Create the required directory structure."""
    directories = [
        # Source code
        'src/core',
        'src/utils',
        
        # Tests
        'tests/test_core',
        'tests/test_utils',
        
        # Configuration
        'config',
        
        # Thread management
        'thread_management/active_thread',
        'thread_management/completed_threads',
        'thread_management/logs',
        'thread_management/templates',
        'thread_management/docs',
        
        # Examples
        'examples',
        
        # Scripts
        'scripts'
    ]
    
    # Create directories
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        
    # Create .gitkeep files for empty directories
    empty_dirs = [
        'thread_management/active_thread',
        'thread_management/completed_threads',
        'thread_management/logs'
    ]
    
    for dir_path in empty_dirs:
        gitkeep = Path(dir_path) / '.gitkeep'
        gitkeep.touch()
        print(f"Created .gitkeep in: {dir_path}")

def main():
    """Main entry point."""
    print("Setting up project directory structure...")
    create_directory_structure()
    print("\nDirectory structure setup complete!")
    print("\nNext steps:")
    print("1. Run environment setup:")
    print("   python scripts/verify_thread.py --check-env")
    print("\n2. Verify directory structure:")
    print("   python scripts/verify_thread.py --check-dirs")
    print("\n3. Initialize first thread:")
    print("   python scripts/thread_manager.py --init THREAD_001")

if __name__ == '__main__':
    main()
