# Project Structure & Development Guidelines

## Directory Structure

```
/c:/Projects/crypto_trader_clean/
├── config/                  # Configuration files
├── docs/                    # Documentation
├── logs/                    # Application logs
├── scripts/                 # Utility scripts
├── src/                     # Source code
│   ├── core/                # Core functionality
│   ├── strategies/          # Trading strategies
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   ├── integration/         # Integration tests
│   └── unit/                # Unit tests
└── thread_management/       # Thread management files
```

## Core Components & Responsibilities

### 1. Configuration Management (`src/core/config_manager.py`)
- Loads and validates configuration files
- Provides access to configuration values
- Handles environment-specific settings

### 2. API Integration (`src/core/coinbase_streaming.py`)
- Manages WebSocket connections to Coinbase
- Processes real-time market data
- Caches price information

### 3. Trading Core (`src/core/trading_core.py`)
- Coordinates trading operations
- Manages position tracking
- Executes trading strategies

### 4. Order Execution (`src/core/order_executor.py`)
- Handles order placement and management
- Applies risk management rules
- Tracks order status

## Development Standards

### API Standards
- **Coinbase Advanced API**: All Coinbase integrations MUST use coinbase-advanced-trade library (not coinbasepro)
- All REST clients should be initialized as: `RESTClient(api_key=key, api_secret=secret)`
- WebSocket clients should follow the pattern in our documentation

### Error Handling Standards
- Use custom exception classes in `src/utils/exceptions.py`
- Log errors before raising exceptions
- Handle API errors gracefully with appropriate fallbacks

### Testing Standards
- All new functionality requires corresponding unit tests
- Test coverage target: 85% minimum
- Integration tests for critical paths required

## Implementation Dependencies & Order
1. Configuration Management
2. API Integration
3. Order Execution
4. Trading Core
5. Trading Strategies

Any change to a lower-level component must be propagated to dependent components.
