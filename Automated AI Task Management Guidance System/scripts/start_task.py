#!/usr/bin/env python
"""
Script to start a new task by creating a task document and updating tracking.
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_task(workitem_id: str, component: str):
    """Start a new task by creating a task document and updating tracking."""
    # Create task document
    task_doc_path = Path(f"docs/tasks/WORKITEM-{workitem_id}.md")
    if not task_doc_path.exists():
        with open(task_doc_path, 'w') as f:
            f.write(f"# WORKITEM-{workitem_id}: Implement {component} Improvements\n\n")
            f.write("## Task Details\n\n")
            f.write(f"Component: {component}\n\n")
            f.write("## Implementation Notes\n\n")
            f.write("## Testing Steps\n\n")
            f.write("## Verification Results\n\n")
        logger.info(f"Created task document: {task_doc_path}")
    else:
        logger.warning(f"Task document already exists: {task_doc_path}")
    
    # Update work tracking status
    work_tracking_path = Path("docs/work_tracking.md")
    if work_tracking_path.exists():
        with open(work_tracking_path, 'r') as f:
            content = f.read()
        
        # Update status from "Pending" to "In Progress"
        pattern = f"### WORKITEM-{workitem_id}: .*?\nStatus: Pending"
        replacement = f"### WORKITEM-{workitem_id}: Implement {component} Improvements\nStatus: In Progress"
        
        if pattern in content:
            content = content.replace(pattern, replacement)
            
            with open(work_tracking_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Updated work tracking status to In Progress")
        else:
            logger.warning(f"Couldn't find WORKITEM-{workitem_id} with 'Pending' status")
    
    logger.info(f"Task WORKITEM-{workitem_id} started!")
    logger.info(f"You can now switch to the new branch with:")
    logger.info(f"git checkout -b workitem-{workitem_id}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Start a new task and update tracking')
    parser.add_argument('workitem_id', help='Work item ID (number only)')
    parser.add_argument('component', help='Component that will be worked on')
    
    args = parser.parse_args()
    
    start_task(args.workitem_id, args.component)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
