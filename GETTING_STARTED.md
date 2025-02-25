# Getting Started with crypto_trader_clean

This guide walks you through setting up the crypto_trader_clean project and initializing the thread management system.

## Initial Setup

1. Open PowerShell and navigate to the project:
   ```powershell
   cd C:\Projects\crypto_trader_clean
   ```

2. Create and activate virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

4. Set up project structure:
   ```powershell
   python scripts\setup_project_structure.py
   ```

## Verify Setup

1. Check directory structure:
   ```powershell
   python scripts\verify_thread.py --check-dirs
   ```

2. Verify environment:
   ```powershell
   python scripts\verify_thread.py --check-env
   ```

## Initialize Thread

**Note:** For detailed and current instructions on thread management, always refer to `THREAD_START_GUIDE.md` which is the single source of truth for thread initialization and management.

1. Review the `THREAD_START_GUIDE.md` file for the current thread initialization process.

2. Initialize the current thread (e.g., THREAD_005) following the instructions in the guide:
   ```powershell
   python scripts\thread_manager.py --init THREAD_005
   ```

3. Verify thread setup:
   ```powershell
   python scripts\verify_thread.py --check-all
   ```

## Important Verification Steps

Always run these verification commands after making changes:
```powershell
python scripts\verify_thread.py --check-all
python scripts\verify_thread.py --check-coverage
python scripts\verify_thread.py --cleanup
```

## Project Structure

After setup, your project should have this structure:
```
crypto_trader_clean/
├── config/                 # Configuration files
├── examples/              # Example code and usage
├── scripts/               # Project scripts
│   ├── setup_project_structure.py
│   ├── thread_manager.py
│   └── verify_thread.py
├── src/                   # Source code
│   ├── core/             # Core components
│   └── utils/            # Utility modules
├── tests/                 # Test suites
│   ├── test_core/        # Core tests
│   ├── test_utils/       # Utility tests
│   └── test_scripts/     # Script tests
└── thread_management/     # Thread management system
    ├── active_thread/    # Current thread state
    ├── completed_threads/# Archived threads
    ├── docs/            # Documentation
    ├── logs/            # System logs
    └── templates/       # Thread templates
```

## Working with Threads

Each development task is managed through a thread system that ensures:
- Clean directory structure
- Proper environment setup
- Test coverage
- Documentation

See `THREAD_START_GUIDE.md` for comprehensive instructions and `thread_management/README.md` for additional background information.

## Reference Project

The original CryptoJ_Trader_Streamlined project is kept as reference:
- Use for code examples and patterns
- DO NOT copy files directly
- Maintain clean separation

## Best Practices

1. Always verify environment before starting work:
   ```powershell
   python scripts\verify_thread.py --check-all
   ```

2. Keep threads focused and isolated:
   - One main objective per thread
   - Complete verification before marking done
   - Document any external dependencies

3. Maintain test coverage:
   - Write tests before implementation
   - Run full test suite before completion
   - Document any coverage exceptions

4. Use proper directory structure:
   - Core logic in src/core/
   - Utilities in src/utils/
   - Tests mirror source structure

## Getting Help

1. View command help:
   ```powershell
   python scripts\verify_thread.py --help
   python scripts\thread_manager.py --help
   ```

2. Check documentation:
   - THREAD_START_GUIDE.md
   - thread_management/README.md
   - thread_management/docs/verification_guide.md

3. View thread status:
   ```powershell
   python scripts\thread_manager.py --status <CURRENT_THREAD_ID>
   ```

## Next Steps

1. Complete thread setup verification
2. Review thread management documentation in THREAD_START_GUIDE.md
3. Start implementing core trading functionality

Remember: Keep the workspace clean and verify everything!
