"""
Update imports in all project files from coinbase_streaming to coinbase_client.
This script updates all references to maintain compatibility.
"""
import os
import re
from pathlib import Path

def update_imports(directory):
    """Update imports in all Python files in the directory and subdirectories."""
    print(f"Scanning directory: {directory}")
    
    # Get all Python files
    python_files = list(Path(directory).rglob("*.py"))
    print(f"Found {len(python_files)} Python files")
    
    # Count of files updated
    updated_files = 0
    
    for file_path in python_files:
        # Skip the new coinbase_client.py file itself
        if file_path.name == "coinbase_client.py":
            continue
            
        # Skip our script
        if file_path.name == "update_imports.py":
            continue
            
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for imports to update
        original_content = content
        
        # Update imports
        content = re.sub(
            r'from\s+src\.core\.coinbase_streaming\s+import\s+CoinbaseStreaming',
            'from src.core.coinbase_client import CoinbaseClient',
            content
        )
        
        # Update class names
        content = re.sub(r'CoinbaseStreaming\(', 'CoinbaseClient(', content)
        content = re.sub(r'CoinbaseStreaming\.', 'CoinbaseClient.', content)
        content = re.sub(r'isinstance\([^,]+,\s*CoinbaseStreaming\)', 
                        'isinstance(\\1, CoinbaseClient)', content)
        
        # If content was changed, write it back
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            updated_files += 1
            print(f"Updated imports in {file_path}")
    
    print(f"Updated {updated_files} files")
    return updated_files

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    update_imports(project_root)
