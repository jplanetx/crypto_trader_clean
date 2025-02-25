# AI Assistance Guide for Crypto Trader Clean Project

This document summarizes the key learnings, process steps, and explanations from our interactions to guide you in successfully completing the project with AI assistance.

## 1. Project Setup and Environment

### 1.1. Workspace Setup
- Ensure you are working in the correct directory: `C:\Projects\crypto_trader_clean`
- Open VS Code with this directory as the workspace.
- Use the `verify_workspace.py` script to confirm the correct workspace:
  ```powershell
  python scripts/verify_workspace.py
  ```

### 1.2. Environment Setup
- Set up the development environment using:
  ```powershell
  scripts\setup_dev.bat
  ```
- Activate the virtual environment:
  ```powershell
  venv\Scripts\activate.bat
  ```
- Set the `PYTHONPATH`:
  ```powershell
  $env:PYTHONPATH = "C:\Projects\crypto_trader_clean;$env:PYTHONPATH"
  ```
- Verify the environment using:
  ```powershell
  python scripts/verify_thread.py --check-env
  ```

## 2. Thread Management System

### 2.1. Thread Overview
- The project uses a thread management system to organize development tasks.
- Each thread has a specific purpose, objectives, and completion criteria.
- Active threads are stored in `thread_management/active_thread/`.
- Completed threads are archived in `thread_management/completed_threads/`.

### 2.2. Thread Commands
- Initialize a new thread:
  ```powershell
  python scripts/thread_manager.py --init THREAD_XXX
  ```
- View thread status:
  ```powershell
  python scripts/thread_manager.py --status THREAD_XXX
  ```
- Mark a thread as complete:
  ```powershell
  python scripts/thread_manager.py --complete THREAD_XXX
  ```
- List all threads:
  ```powershell
  python scripts/thread_manager.py --list
  ```

### 2.3. Thread Verification
- Use `verify_thread.py` to check the directory structure and environment:
  ```powershell
  python scripts/verify_thread.py --check-dirs
  python scripts/verify_thread.py --check-env
  ```

### 2.4. Thread Completion
- Before completing a thread, ensure:
  - All objectives are met.
  - All tests are passing.
  - The completion checklist is complete.
- Update the thread's JSON file to reflect its completion status.

## 3. Development Workflow

### 3.1. General Steps
1. Start a new thread using `thread_manager.py`.
2. Implement the required changes.
3. Add tests to ensure the changes are working correctly.
4. Run verification scripts to check the environment and code quality.
5. Mark the thread as complete using `thread_manager.py`.

### 3.2. Code Location
- Place thread-specific code in `src/core/` or `src/utils/`.
- Add corresponding tests in `tests/test_core/` or `tests/test_utils/`.

### 3.3. Testing
- Run the test suite to ensure everything is working as expected:
  ```powershell
  python -m pytest tests/test_scripts/test_thread_system.py -v
  ```

## 4. Key Files and Documentation

### 4.1. Core Scripts
- `scripts/verify_thread.py`: Verifies the thread setup and environment.
- `scripts/thread_manager.py`: Manages the thread lifecycle.
- `scripts/setup_project_structure.py`: Sets up the project directory structure.

### 4.2. Documentation
- `thread_management/README.md`: Provides an overview of the thread management system.
- `thread_management/docs/verification_guide.md`: Details the verification procedures.
- `GETTING_STARTED.md`: Guides you through setting up the project.

## 5. Thread Sequence

1.  THREAD_001: Implement the thread management system (this thread).
2.  Future threads will focus on implementing trading functionality, such as integrating the Coinbase API, developing core services, and enhancing system components.

## 6. AI Assistance Guidelines

### 6.1. Task Clarity
- Clearly define the task or problem you want the AI to solve.
- Provide context, including relevant files and documentation.
- Specify the expected input and output.

### 6.2. Iterative Approach
- Break down the task into smaller, manageable steps.
- Use the AI to implement each step iteratively.
- Verify the results of each step before proceeding.

### 6.3. Verification
- Use the provided verification scripts to ensure the environment and code quality.
- Run the test suite to confirm that everything is working as expected.

### 6.4. Documentation
- Update the documentation to reflect the changes you have made.
- Follow the project's coding standards and best practices.

By following these guidelines, you can effectively leverage AI assistance to complete the Crypto Trader Clean project successfully.
