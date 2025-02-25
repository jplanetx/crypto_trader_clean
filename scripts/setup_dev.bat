@echo off
setlocal enabledelayedexpansion

echo Setting up development environment for CryptoTrader Clean...

:: Check Python version
python -c "import sys; assert sys.version_info >= (3, 8), 'Python 3.8 or higher is required'" 2>nul
if errorlevel 1 (
    echo Error: Python 3.8 or higher is required
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Installing dependencies...
pip install -e .[dev,test]

:: Create logs directory
if not exist "logs" mkdir logs

:: Initialize git if not already initialized
if not exist ".git" (
    echo Initializing git repository...
    git init
)

:: Setup git hooks
if exist ".git" (
    echo Setting up git hooks...
    python scripts\setup_dev.py
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Update config/config.json with your settings
echo 2. Activate the virtual environment: venv\Scripts\activate
echo 3. Run tests: pytest tests/
echo 4. Try the example: python examples/basic_trading.py

endlocal
