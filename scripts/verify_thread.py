"""Thread verification script for crypto_trader_clean project."""
import os
import sys
import json
import argparse
import logging
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def setup_logging() -> None:
    """Configure logging for the verification script."""

def verify_project_root() -> bool:
    """Verify we're in the correct project directory."""
    current_dir = Path.cwd()
    if current_dir.name != 'crypto_trader_clean':
        logging.error(f"Must run from crypto_trader_clean directory, not {current_dir}")
        return False
    return True

def check_directories() -> Dict[str, Any]:
    """Check for correct directory structure and no duplicates."""
    results = {
        "status": "clean",
        "no_duplicates": True,
        "issues": []
    }
    
    # Required directories
    required_dirs = [
        'src/core',
        'src/utils',
        'tests/test_core',
        'tests/test_utils',
        'scripts',
        'config',
        'thread_management'
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            results["status"] = "incomplete"
            results["issues"].append(f"Missing directory: {dir_path}")
            
    # Check for duplicate directories
    parent_dir = Path.cwd().parent
    duplicates = list(parent_dir.glob("**/crypto_trader_clean"))
    if len(duplicates) > 1:
        results["no_duplicates"] = False
        results["issues"].extend([
            f"Found duplicate directory: {d}" for d in duplicates
        ])
        
    return results

def check_environment() -> Dict[str, Any]:
    """Verify Python environment setup."""
    results = {
        "venv_active": False,
        "pythonpath_valid": False,
        "issues": []
    }
    
    # Check virtual environment
    if sys.prefix != sys.base_prefix:
        results["venv_active"] = True
    else:
        results["issues"].append("Virtual environment not activated")
        
    # Check PYTHONPATH
    python_path = os.environ.get('PYTHONPATH', '')
    project_root = str(Path.cwd())
    if project_root in python_path:
        results["pythonpath_valid"] = True
    else:
        results["issues"].append("Project root not in PYTHONPATH")
        
    return results

def parse_coverage_output(output: str) -> Optional[float]:
    """Parse coverage percentage from pytest-cov output.
    
    Args:
        output: The stdout from pytest-cov run
        
    Returns:
        Total coverage percentage as a float, or None if parsing failed
    """
    # Look for the TOTAL line at the end of the coverage report
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)%', output)
    if match:
        return float(match.group(1))
    return None

def check_coverage(threshold: float = 85.0) -> Tuple[bool, Optional[float]]:
    """Run test coverage check using pytest-cov.
    
    Args:
        threshold: Minimum required coverage percentage (default: 85.0)
        
    Returns:
        Tuple of (meets_threshold, coverage_percentage)
    """
    print("Running test coverage check...")
    try:
        # Run pytest with coverage using the specified command
        result = subprocess.run(
            ["pytest", "--maxfail=1", "--disable-warnings", "--cov=.", "--cov-report=term"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Print stdout for visualization
        print(result.stdout)
        
        if result.returncode != 0:
            print("Test coverage check failed to complete:")
            print(result.stderr)
            return False, None
        
        # Parse the coverage percentage
        coverage_percentage = parse_coverage_output(result.stdout)
        
        if coverage_percentage is None:
            print("Failed to parse coverage percentage from output.")
            return False, None
            
        # Compare against threshold
        if coverage_percentage < threshold:
            print(f"WARNING: Test coverage ({coverage_percentage}%) is below the required threshold ({threshold}%).")
            return False, coverage_percentage
        else:
            print(f"Test coverage meets requirements: {coverage_percentage}% (threshold: {threshold}%).")
            return True, coverage_percentage
            
    except Exception as e:
        print(f"Error running test coverage: {e}")
        return False, None

def cleanup():
    """Perform cleanup operations: remove temporary files/directories."""
    temp_dir = Path("thread_management/active_thread/tmp")
    if temp_dir.exists():
        try:
            import shutil
            shutil.rmtree(temp_dir)
            print(f"Temporary directory {temp_dir} removed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    else:
        print("No temporary files or directories to clean up.")

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Verify thread management system state'
    )
    parser.add_argument(
        '--check-dirs',
        action='store_true',
        help='Check directory structure'
    )
    parser.add_argument(
        '--check-env',
        action='store_true',
        help='Check environment setup'
    )
    parser.add_argument(
        '--check-coverage',
        action='store_true',
        help='Check test coverage'
    )
    parser.add_argument(
        '--coverage-threshold',
        type=float,
        default=85.0,
        help='Minimum coverage percentage required (default: 85.0)'
    )
    parser.add_argument(
        '--check-all',
        action='store_true',
        help='Run all verification checks (dirs, env, coverage)'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up temporary files and directories'
    )
    return parser.parse_args()

def run_all_checks(args: argparse.Namespace) -> None:
    """Run all verification checks."""
    print("Running all verification checks...")
    results_dirs = check_directories()
    if results_dirs["status"] != "clean" or not results_dirs["no_duplicates"]:
        logging.error("Directory check failed:")
        for issue in results_dirs["issues"]:
            logging.error(f"  - {issue}")
        sys.exit(1)
    else:
        logging.info("Directory structure verified successfully")
    results_env = check_environment()
    if not all([results_env["venv_active"], results_env["pythonpath_valid"]]):
        logging.error("Environment check failed:")
        for issue in results_env["issues"]:
            logging.error(f"  - {issue}")
        sys.exit(1)
    else:
        logging.info("Environment verified successfully")
    meets_threshold, _ = check_coverage(args.coverage_threshold)
    if not meets_threshold:
        sys.exit(1)
    sys.exit(0)

def check_directories_and_exit() -> None:
    """Check directories and exit if there are issues."""
    results = check_directories()
    if results["status"] != "clean" or not results["no_duplicates"]:
        logging.error("Directory check failed:")
        for issue in results["issues"]:
            logging.error(f"  - {issue}")
        sys.exit(1)
    logging.info("Directory structure verified successfully")

def check_environment_and_exit() -> None:
    """Check environment and exit if there are issues."""
    results = check_environment()
    if not all([results["venv_active"], results["pythonpath_valid"]]):
        logging.error("Environment check failed:")
        for issue in results["issues"]:
            logging.error(f"  - {issue}")
        sys.exit(1)
    logging.info("Environment verified successfully")

def check_coverage_and_exit(threshold: float) -> None:
    """Check test coverage and exit if it does not meet the threshold."""
    meets_threshold, _ = check_coverage(threshold)
    if not meets_threshold:
        sys.exit(1)

def main():
    """Main entry point."""
    args = parse_arguments()
    
    setup_logging()
    
    if not verify_project_root():
        sys.exit(1)
    
    if args.check_all:
        run_all_checks(args)
    
    if args.check_dirs:
        check_directories_and_exit()
        
    if args.check_env:
        check_environment_and_exit()
    
    if args.check_coverage:
        check_coverage_and_exit(args.coverage_threshold)
    
    if args.cleanup:
        cleanup()
    
if __name__ == '__main__':
    main()
