# Getting Started Guide

This guide will help you get up and running with the Crypto Trader Clean project.

## Prerequisites

- Python 3.8 or higher
- Git
- A Coinbase account with API access

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd crypto_trader_clean
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up your configuration:
   ```bash
   cp config/config_template.json config/config.json
   ```
   Edit `config/config.json` with your API credentials and settings.

## Initial Testing

1. Verify your environment:
   ```bash
   python scripts/verify_thread.py --check-env
   ```

2. Verify directory structure:
   ```bash
   python scripts/verify_thread.py --check-dirs
   ```

3. Run tests:
   ```bash
   python -m pytest
   ```

## Development Workflow

1. **Before starting work**:
   - Check the work tracking document for your assigned item
   - Ensure all dependencies are complete
   - Create a new branch: `git checkout -b feature/your-feature-name`

2. **Implementation**:
   - Follow the Quality Control Process (docs/quality_control_process.md)
   - Run the verification script frequently: `python scripts/verify_implementation.py --component=component_name`

3. **Testing**:
   - Write tests for your changes
   - Run specific tests: `python -m pytest tests/path/to/test.py`
   - Ensure test coverage: `python -m pytest --cov=your_module tests/path/to/test.py`

4. **Documentation**:
   - Update documentation if needed
   - Document any technical decisions

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "WORKITEM-XXX: Brief description of changes"
   ```

## Common Commands

- Run specific component tests:
  ```bash
  python -m pytest tests/test_core/test_config_manager.py -v
  ```

- Verify a specific component:
  ```bash
  python scripts/verify_implementation.py --component=config_manager
  ```

- Check test coverage:
  ```bash
  python -m pytest --cov=src.core.config_manager tests/test_core/test_config_manager.py
  ```

- Generate coverage report:
  ```bash
  python -m pytest --cov=src --cov-report=html
  ```
  This will create an HTML report in the `htmlcov` directory.

## Getting Help

If you encounter issues:
1. Check the common_issues.md document
2. Look through relevant test files for examples
3. Review component documentation in docs/components/
