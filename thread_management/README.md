# Thread Management System

## Overview
This system manages the development process through discrete threads, ensuring clean transitions and maintaining project quality through automated verification.

**Important Note:** For current instructions on starting and managing threads, please refer to `THREAD_START_GUIDE.md` in the project root. This README provides background information on the thread management system.

## Directory Structure
```
thread_management/
├── active_thread/     # Current thread configuration
├── completed_threads/ # Archived thread configurations
├── docs/             # Documentation
├── logs/             # Verification and thread logs
└── templates/        # Thread templates
```

## Key Components

### 1. Thread Verification (verify_thread.py)
- Checks directory structure
- Verifies environment setup
- Validates project isolation
- Monitors test coverage

### 2. Thread Manager (thread_manager.py)
- Initializes new threads
- Tracks thread status
- Archives completed threads
- Manages thread lifecycle

## Usage

### Starting a New Thread

**Note:** The following instructions are provided for reference. For current thread initialization, always follow the guidelines in `THREAD_START_GUIDE.md`.

1. Initialize thread:
```powershell
python scripts/thread_manager.py --init <THREAD_ID>
```

2. Verify setup:
```powershell
python scripts/verify_thread.py --check-dirs
python scripts/verify_thread.py --check-env
```

### During Development

1. Regular verification:
```powershell
python scripts/verify_thread.py --check-all
```

2. Check status:
```powershell
python scripts/thread_manager.py --status <THREAD_ID>
```

### Completing a Thread

1. Final verification (always run these commands):
```powershell
python scripts/verify_thread.py --check-all
python scripts/verify_thread.py --check-coverage
python scripts/verify_thread.py --cleanup
```

2. Mark as complete:
```powershell
python scripts/thread_manager.py --complete <THREAD_ID>
```

## Thread States

- `not_started`: Initialized but not begun
- `in_progress`: Currently being implemented
- `completed`: Finished and verified
- `failed`: Critical error encountered

## Best Practices

1. Always run verification before starting work:
   ```powershell
   python scripts/verify_thread.py --check-all
   ```

2. Keep CryptoJ_Trader_Streamlined workspace open for reference only
   - All new development happens in crypto_trader_clean
   - Use as reference for porting functionality

3. Maintain Directory Isolation
   - No duplicate crypto_trader_clean directories
   - All paths relative to project root
   - No hardcoded references to old project

4. Test Coverage
   - Maintain minimum 85% coverage
   - Run tests before marking thread complete
   - Document any coverage exceptions

## Error Recovery

If verification fails:

1. Check error logs in thread_management/logs/
2. Run cleanup if needed:
   ```powershell
   python scripts/verify_thread.py --cleanup
   ```
3. Fix issues and re-verify

## Configuration

Thread configurations are stored in JSON format:
- Templates: thread_management/templates/
- Active: thread_management/active_thread/
- Completed: thread_management/completed_threads/

## Logging

All operations are logged to:
- thread_management/logs/verify_thread.log
- thread_management/logs/thread_manager.log

## Getting Help

Show command help:
```powershell
python scripts/verify_thread.py --help
python scripts/thread_manager.py --help
```

For comprehensive instructions on managing threads using the current conventions, please refer to `THREAD_START_GUIDE.md` in the project root.
