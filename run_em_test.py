"""
Script to run the emergency manager test with detailed output.
"""
import subprocess
import os
import sys

def main():
    """Run the test and print detailed output."""
    print("Running emergency manager tests...")
    
    # Command to run the specific test
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_core/test_emergency_manager.py::test_perform_emergency_shutdown",
        "-v",  # Verbose output
        "--no-header",  # No header info
        "-s",  # Don't capture stdout/stderr
    ]
    
    try:
        # Run the command and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        stdout, stderr = process.communicate()
        
        # Print the output
        print("\n--- STDOUT ---")
        print(stdout)
        
        if stderr:
            print("\n--- STDERR ---")
            print(stderr)
        
        # Check exit code
        if process.returncode == 0:
            print("\n✅ Test passed successfully!")
        else:
            print(f"\n❌ Test failed with exit code {process.returncode}")
            
        # Run all tests as well
        print("\n\nRunning all emergency manager tests...")
        cmd[2] = "tests/test_core/test_emergency_manager.py"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )
        stdout, stderr = process.communicate()
        
        # Print the output
        print("\n--- STDOUT ---")
        print(stdout)
        
        if stderr:
            print("\n--- STDERR ---")
            print(stderr)
        
        # Check exit code
        if process.returncode == 0:
            print("\n✅ All tests passed successfully!")
        else:
            print(f"\n❌ Some tests failed with exit code {process.returncode}")
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
