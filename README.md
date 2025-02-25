# CryptoTrader Clean

A streamlined cryptocurrency trading system for personal use. Built with a focus on reliability and ease of use.

## Quick Start

1. Make sure Python 3.8 or higher is installed
2. Double-click `start_trading.bat` to run the trading system
3. Check the `logs` directory for trading activity

## Configuration

Edit `config/config.json` to set your preferences:

```json
{
    "trading_pairs": ["BTC-USD", "ETH-USD"],
    "risk_management": {
        "max_position_size": 5.0,
        "stop_loss_pct": 0.05,
        "max_daily_loss": 500.0,
        "max_open_orders": 5
    },
    "paper_trading": true,
    "api_key": "",
    "api_secret": ""
}
```

## Features

- Asynchronous order execution
- Automatic position tracking
- Risk management controls
- Detailed logging
- Paper trading mode for testing

## Project Structure

```
crypto_trader_clean/
├── src/
│   ├── core/                 # Core trading components
│   │   ├── order_executor.py # Order execution
│   │   ├── trading_core.py   # Main trading logic
│   │   └── config_manager.py # Configuration
│   └── utils/
│       └── exceptions.py     # Custom exceptions
├── config/
│   └── config.json          # Trading configuration
├── logs/                    # Trading logs
└── start_trading.bat       # Easy startup script
```

## Monitoring

- Check `logs/trading_YYYYMMDD.log` for detailed activity
- Current positions and stats are displayed in the console
- Press Ctrl+C to safely stop trading

## Testing

Run tests to verify everything is working:

```bash
# Activate virtual environment
venv\Scripts\activate

# Run tests
pytest tests/
```

## Development

The main files to modify for customization:
- `config/config.json` - Trading parameters
- `src/core/trading_core.py` - Core trading logic
- `run_trader.py` - Main execution loop

### Thread Management

This project uses a thread management system to organize development tasks and maintain project quality. For developers contributing to this project:

- Refer to `THREAD_START_GUIDE.md` for comprehensive instructions on thread initialization and management
- Follow the verification processes to ensure code quality
- Run verification commands (`--check-all`, `--check-coverage`, `--cleanup`) after making changes

See `GETTING_STARTED.md` for initial setup instructions.
