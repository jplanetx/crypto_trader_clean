#!/usr/bin/env python
"""
Task initialization script that sets up a proper working environment for a task.
"""
import sys
import os
import argparse
import logging
import shutil
from pathlib import Path
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_task(workitem_id: str, component: str):
    """Set up the environment for working on a specific task."""
    # Create task document if it doesn't exist
    task_doc_path = Path(f"docs/tasks/WORKITEM-{workitem_id}.md")
    task_doc_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not task_doc_path.exists():
        logger.info(f"Creating task document at {task_doc_path}")
        with open(task_doc_path, 'w') as f:
            f.write(f"# WORKITEM-{workitem_id}\n\n")
            f.write("## Task Details\n\n")
            f.write(f"Component: {component}\n\n")
            f.write("## Implementation Notes\n\n")
            f.write("## Testing Steps\n\n")
            f.write("## Verification Results\n\n")
    
    # Create a new git branch if it doesn't exist
    branch_name = f"workitem-{workitem_id}"
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], 
                      capture_output=True, text=True, check=False)
        logger.info(f"Created and switched to branch: {branch_name}")
    except subprocess.CalledProcessError:
        # Branch might already exist
        subprocess.run(["git", "checkout", branch_name], 
                      capture_output=True, text=True, check=False)
        logger.info(f"Switched to existing branch: {branch_name}")
    
    # Run verification to see the current state
    logger.info(f"Verifying component: {component}")
    subprocess.run(["python", "scripts/verify_implementation.py", 
                   f"--component={component}"], check=False)
    
    # Open relevant files in the default editor (if VSCode is installed)
    try:
        subprocess.run(["code", f"docs/tasks/WORKITEM-{workitem_id}.md", 
                       f"docs/work_tracking.md"], check=False)
        logger.info("Opened relevant documents in VSCode")
    except FileNotFoundError:
        logger.info("VSCode not found. Please open the task document manually.")
    
    logger.info(f"Task environment for WORKITEM-{workitem_id} is ready!")
    logger.info(f"Remember to update work_tracking.md to mark this task as 'In Progress'")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Set up task environment')
    parser.add_argument('workitem_id', help='Work item ID (number only)')
    parser.add_argument('component', help='Component to work on')
    
    args = parser.parse_args()
    
    setup_task(args.workitem_id, args.component)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
