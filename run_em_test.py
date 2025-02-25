"""
Simple script to run the emergency manager tests.
"""
import subprocess
import os

def run_tests():
    print("Running emergency manager tests...")
    os.environ["PYTHONPATH"] = os.getcwd()
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/test_core/test_emergency_manager.py", "-v"],
        capture_output=True,
        text=True
    )
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\nTests passed successfully!")
    else:
        print("\nTests failed!")
