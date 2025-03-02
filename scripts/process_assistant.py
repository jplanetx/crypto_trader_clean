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
        
        # Find in-progress work items
        in_progress = re.findall(r'WORKITEM-(\d+).*?\nStatus: In Progress', content)
        print(f"Found {len(in_progress)} work items in progress: {', '.join(in_progress)}")
        
        # Find next work items
        not_started = re.findall(r'WORKITEM-(\d+).*?\nStatus: Not Started', content)
        print(f"Found {len(not_started)} work items not started: {', '.join(not_started)}")
        
        # Recommend next steps
        if in_progress:
            workitem = in_progress[0]
            print(f"\nRecommended next steps for WORKITEM-{workitem}:")
            print("1. Run verification: python scripts/verify_implementation.py --component=NAME")
            print("2. Fix any failing tests")
            print("3. Update work_tracking.md when complete")
        elif not_started:
            workitem = not_started[0]
            print(f"\nRecommended next steps:")
            print(f"1. Start WORKITEM-{workitem}: python scripts/start_task.py {workitem} COMPONENT_NAME")
            print("2. Implement the required functionality")
            print("3. Run verification to check your work")
    else:
        print("Work tracking document not found. Please set up your project structure.")

if __name__ == "__main__":
    analyze_repository()
