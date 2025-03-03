#!/usr/bin/env python
"""
Process assistant script that provides guidance on next steps.
"""
import os
import sys
import argparse
import re
from pathlib import Path

def analyze_repository():
    """Analyze the repository structure and work state."""
    # Check work tracking document
    work_tracking_path = Path("docs/work_tracking.md")
    if work_tracking_path.exists():
        with open(work_tracking_path, 'r') as f:
            content = f.read()
        
        # Find in-progress work items - case insensitive matching
        in_progress = re.findall(r'WORKITEM-(\d+).*?\nStatus:\s*In\s*Progress', content, re.IGNORECASE)
        print(f"Found {len(in_progress)} work items in progress: {', '.join(in_progress)}")
        
        # Find not-started work items - case insensitive matching
        not_started = re.findall(r'WORKITEM-(\d+).*?\nStatus:\s*Not\s*Started', content, re.IGNORECASE)
        print(f"Found {len(not_started)} work items not started: {', '.join(not_started)}")
        
        # Find completed work items
        completed = re.findall(r'WORKITEM-(\d+).*?\nStatus:\s*Complete', content, re.IGNORECASE)
        print(f"Found {len(completed)} completed work items: {', '.join(completed)}")
        
        # Recommend next steps
        if in_progress:
            workitem = in_progress[0]
            # Get component name - improved regex to capture the correct component
            component_match = re.search(rf'WORKITEM-{workitem}.*?\nComponents:\s*([\w_]+)', content, re.IGNORECASE)
            if not component_match:
                # Try an alternative pattern that might better match the document format
                component_match = re.search(rf'WORKITEM-{workitem}.*?Components:\s*([\w_]+)', content, re.IGNORECASE | re.DOTALL)
            
            component = component_match.group(1) if component_match else "unknown_component"
            
            print(f"\nRecommended next steps for WORKITEM-{workitem}:")
            print(f"1. Run verification: python scripts/verify_implementation.py --component={component}")
            print("2. Fix any failing tests")
            print("3. Update work_tracking.md when complete")
        elif not_started:
            workitem = not_started[0]
            # Get component name with improved regex
            component_match = re.search(rf'WORKITEM-{workitem}.*?\nComponents:\s*([\w_]+)', content, re.IGNORECASE)
            if not component_match:
                component_match = re.search(rf'WORKITEM-{workitem}.*?Components:\s*([\w_]+)', content, re.IGNORECASE | re.DOTALL)
            
            component = component_match.group(1) if component_match else "unknown_component"
            
            print(f"\nRecommended next steps:")
            print(f"1. Start WORKITEM-{workitem}: python scripts/start_task.py {workitem} {component}")
            print("2. Implement the required functionality")
            print("3. Run verification to check your work")
        elif completed:
            print("\nAll defined work items are complete! Consider defining new work items.")
        else:
            print("\nNo work items found. Consider adding work items to docs/work_tracking.md.")
    else:
        print("Work tracking document not found at docs/work_tracking.md. Please set up your project structure.")
        
        # Check if docs directory exists
        if not Path("docs").exists():
            print("The 'docs' directory doesn't exist. Create it and add work_tracking.md.")
        else:
            print("Create work_tracking.md in the docs directory.")

if __name__ == "__main__":
    analyze_repository()
