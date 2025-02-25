"""Verify workspace location and structure."""
import os
import sys
from pathlib import Path

def verify_workspace():
    """Verify we're in the correct workspace."""
    current = Path.cwd()
    expected = Path('C:/Projects/crypto_trader_clean')
    
    print("\nWorkspace Verification:")
    print("----------------------")
    print(f"Current directory: {current}")
    print(f"Expected directory: {expected}")
    
    if current != expected:
        print("\n❌ ERROR: Wrong working directory!")
        print("Please:")
        print("1. Close VS Code")
        print("2. Open C:/Projects/crypto_trader_clean as workspace")
        print("3. Run this script again")
        sys.exit(1)
    
    # Check for duplicate directory
    streamlined_path = Path('C:/Projects/CryptoJ_Trader_Streamlined/crypto_trader_clean')
    if streamlined_path.exists():
        print("\n⚠️ WARNING: Duplicate directory found!")
        print(f"Found duplicate at: {streamlined_path}")
        print("\nAction needed:")
        print("1. Move any needed files to C:/Projects/crypto_trader_clean")
        print("2. Delete the duplicate directory")
        sys.exit(1)
    
    print("\n✅ Workspace verified correctly!")
    print("Safe to proceed with implementation.")

if __name__ == '__main__':
    verify_workspace()
