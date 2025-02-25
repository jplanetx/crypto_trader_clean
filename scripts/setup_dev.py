"""
Development environment setup script.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required")
        sys.exit(1)

def install_dependencies(dev_mode=True):
    """Install project dependencies."""
    try:
        # Install base dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        
        if dev_mode:
            # Install development dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-e", ".[dev,test]"
            ], check=True)
            
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def create_config():
    """Create initial configuration if not exists."""
    config_dir = Path("config")
    config_file = config_dir / "config.json"
    
    if not config_file.exists():
        print("Creating example configuration file...")
        example_config = config_dir / "config.json"
        if example_config.exists():
            print("Example configuration already exists")
        else:
            print("Error: Configuration template not found")
            sys.exit(1)

def setup_git_hooks():
    """Set up Git hooks for development."""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("Git hooks directory not found. Initializing git repository...")
        subprocess.run(["git", "init"], check=True)

    # Create pre-commit hook
    pre_commit = hooks_dir / "pre-commit"
    with open(pre_commit, 'w') as f:
        f.write("""#!/bin/sh
echo "Running pre-commit checks..."

# Run tests
python -m pytest tests/ || exit 1

# Run black
python -m black . --check || exit 1

# Run isort
python -m isort . --check-only || exit 1

# Run flake8
python -m flake8 . || exit 1
""")
    
    # Make hook executable
    os.chmod(pre_commit, 0o755)
    print("Git hooks installed")

def setup_dev_environment():
    """Main setup function."""
    print("Setting up development environment...")
    
    check_python_version()
    install_dependencies(dev_mode=True)
    create_config()
    setup_git_hooks()
    
    print("\nDevelopment environment setup complete!")
    print("\nNext steps:")
    print("1. Update config/config.json with your settings")
    print("2. Run tests: pytest tests/")
    print("3. Try the example: python examples/basic_trading.py")

def main():
    """Script entry point."""
    try:
        setup_dev_environment()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
