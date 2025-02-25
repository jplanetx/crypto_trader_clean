@echo off
echo Starting CryptoTrader...

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -e .
) else (
    call venv\Scripts\activate
)

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

:: Start the trading system
python run_trader.py

:: Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Trading system exited with an error.
    echo Check the logs for details.
    pause
)
