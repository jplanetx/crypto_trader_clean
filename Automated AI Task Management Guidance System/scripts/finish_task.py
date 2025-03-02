#!/usr/bin/env python
"""
Task completion script that verifies work and updates tracking.
"""
import sys
import os
import argparse
import logging
import subprocess
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def complete_task(workitem_id: str, component: str):
    """Complete a task by running verification and updating tracking."""
    # Verify implementation
    logger.info(f"Verifying implementation of {component}...")
    result = subprocess.run(["python", "scripts/verify_implementation.py", 
                           f"--component={component}"], 
                          capture_output=True, text=True)
    
    verification_output = result.stdout + result.stderr
    
    # Update task document with verification results
    task_doc_path = Path(f"docs/tasks/WORKITEM-{workitem_id}.md")
    if task_doc_path.exists():
        with open(task_doc_path, 'r') as f:
            content = f.read()
        
        # Add verification results
        if "## Verification Results" in content:
            content = re.sub(r"## Verification Results.*?(?=^#|\Z)", 
                            f"## Verification Results\n\n```\n{verification_output}\n```\n\n", 
                            content, flags=re.DOTALL | re.MULTILINE)
        else:
            content += f"\n## Verification Results\n\n```\n{verification_output}\n```\n"
        
        with open(task_doc_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Updated task document with verification results")
    
    # Update work tracking status
    work_tracking_path = Path("docs/work_tracking.md")
    if work_tracking_path.exists():
        with open(work_tracking_path, 'r') as f:
            content = f.read()
        
        # Update status from "In Progress" to "Complete"
        pattern = rf"### WORKITEM-{workitem_id}: .*?\nStatus: In Progress"
        replacement = f"### WORKITEM-{workitem_id}: Implement Authentication Improvements\nStatus: Complete"
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement)
            
            with open(work_tracking_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Updated work tracking status to Complete")
        else:
            logger.warning(f"Couldn't find WORKITEM-{workitem_id} with 'In Progress' status")
    
    logger.info(f"Task WORKITEM-{workitem_id} completed!")
    logger.info(f"You can now commit your changes with:")
    logger.info(f"git add . && git commit -m \"WORKITEM-{workitem_id}: Complete {component} implementation\"")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Complete task and update tracking')
    parser.add_argument('workitem_id', help='Work item ID (number only)')
    parser.add_argument('component', help='Component that was worked on')
    
    args = parser.parse_args()
    
    complete_task(args.workitem_id, args.component)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
