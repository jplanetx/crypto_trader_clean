# Verification Guide

This guide details the procedures to verify the setup and quality of your Crypto Trader Clean project. It covers directory structure, environment configuration, test coverage, and cleanup operations.

---

## 1. Check Directories (`--check-dirs`)

### Command:
```bash
python scripts/verify_thread.py --check-dirs
```

### Purpose:
- Ensures all required directories (e.g., `src/core`, `tests/test_core`, `scripts`, `config`, `thread_management`) are present.
- Checks that there are no duplicate directories in the project structure.

### Expected Output:
```
Checking directories...
Directory structure clean.
```
If issues are found, they will be listed as errors.

---

## 2. Check Environment (`--check-env`)

### Command:
```bash
python scripts/verify_thread.py --check-env
```

### Purpose:
- Verifies that the virtual environment is active.
- Ensures that the project root is correctly included in the `PYTHONPATH`.

### Expected Output:
```
Checking environment...
Environment is valid.
```
Any issues (e.g., virtual environment not activated, project root missing in PYTHONPATH) will be reported.

---

## 3. Check Test Coverage (`--check-coverage`)

### Command:
```bash
python scripts/verify_thread.py --check-coverage
```

### Purpose:
- Evaluates that the test coverage meets the required thresholds.
- This is a placeholder for verifying that automated tests sufficiently cover the codebase.

### Expected Output:
```
Checking test coverage...
Test coverage meets requirements.
```
*Note: This command uses a dummy implementation in the current script; integrate real test coverage checks as needed.*

---

## 4. Run All Verification Checks (`--check-all`)

### Command:
```bash
python scripts/verify_thread.py --check-all
```

### Purpose:
- Runs all three checks (directories, environment, and test coverage) consecutively.
- Provides a comprehensive verification of your project setup.

### Expected Output:
- Combined outputs from the individual checks. All must pass without errors.

---

## 5. Cleanup (`--cleanup`)

### Command:
```bash
python scripts/verify_thread.py --cleanup
```

### Purpose:
- Removes stale temporary files/directories that might interfere with the project setup.
- Currently, it targets a temporary directory (`thread_management/active_thread/tmp`). Modify this behavior if additional cleanup is required.

### Expected Output:
```
Temporary directory thread_management/active_thread/tmp removed.
```
Or a message indicating no temporary files/directories to clean up.

---

## How to Use This Guide

1. **Before starting development**, run:
    ```bash
    python scripts/verify_thread.py --check-all
    ```
   Ensure that all required aspects of your setup are validated.

2. **After changes or development sessions**, run the cleanup command:
    ```bash
    python scripts/verify_thread.py --cleanup
    ```
   This step ensures that your project directory remains clean and free from obsolete temporary files.

3. **Refer to this guide** whenever you need to verify your project’s structure or when facing environment configuration issues.

---

This guide complements the AI Assistance Guide and ensures you have clear steps to validate your project’s health.
