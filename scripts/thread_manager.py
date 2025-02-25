"""Thread management script for crypto_trader_clean project."""
import os
import sys
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

def setup_logging() -> None:
    """Configure logging for the thread manager."""
    log_dir = Path('thread_management/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    

def load_template(thread_id: str) -> Dict[str, Any]:
    """Load the thread template configuration.
    
    First tries to load a specific template for the thread ID,
    falls back to the default template if not found.
    """
    # Try specific template first (e.g., thread_005_init.json)
    specific_template = Path(f'thread_management/templates/thread_{thread_id.lower()}_init.json')
    if specific_template.exists():
        with open(specific_template) as f:
            return json.load(f)
            
    # Fall back to default template
    template_path = Path('thread_management/templates/thread_init_template.json')
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
        
    with open(template_path) as f:
        return json.load(f)

def init_thread(thread_id: str) -> None:
    """Initialize a new thread configuration with a standardized thread ID.
    
    If the provided thread_id does not start with 'THREAD_', it will be prefixed.
    """
    # Standardize thread ID by adding prefix if needed.
    if not thread_id.startswith("THREAD_"):
        thread_id = "THREAD_" + thread_id

    template = load_template(thread_id.replace("THREAD_", ""))
    
    # Update template with thread-specific info
    template['thread_id'] = thread_id
    template['start_time'] = datetime.now().isoformat()
    
    # Create thread directory
    thread_dir = Path('thread_management/active_thread')
    thread_dir.mkdir(parents=True, exist_ok=True)
    
    # Save thread configuration as THREAD_XXX.json
    config_path = thread_dir / f"{thread_id}.json"
    with open(config_path, 'w') as f:
        json.dump(template, f, indent=4)
        
    logging.info(f"Initialized thread {thread_id}")
    
def get_thread_status(thread_id: str) -> Dict[str, Any]:
    """Get the current status of a thread."""
    config_path = Path(f'thread_management/active_thread/{thread_id}.json')
    if not config_path.exists():
        raise FileNotFoundError(f"Thread config not found: {thread_id}")
        
    with open(config_path) as f:
        return json.load(f)
        
def complete_thread(thread_id: str) -> None:
    """Mark a thread as complete and archive it."""
    status = get_thread_status(thread_id)
    status['status'] = 'completed'
    status['completion_time'] = datetime.now().isoformat()
    
    # Create archive directory
    archive_dir = Path('thread_management/completed_threads')
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Move thread config to archive
    src_path = Path(f'thread_management/active_thread/{thread_id}.json')
    dst_path = archive_dir / f"{thread_id}.json"
    
    with open(dst_path, 'w') as f:
        json.dump(status, f, indent=4)
        
    os.remove(src_path)
    logging.info(f"Completed and archived thread {thread_id}")

def list_threads() -> None:
    """List all threads and their status."""
    active_dir = Path('thread_management/active_thread')
    completed_dir = Path('thread_management/completed_threads')
    
    print("\nActive Threads:")
    print("-------------")
    if active_dir.exists():
        for file in active_dir.glob('*.json'):
            with open(file) as f:
                data = json.load(f)
                print(f"{data['thread_id']}: {data['name']} (Status: {data['status']})")
    
    print("\nCompleted Threads:")
    print("----------------")
    if completed_dir.exists():
        for file in completed_dir.glob('*.json'):
            with open(file) as f:
                data = json.load(f)
                print(f"{data['thread_id']}: {data['name']} (Completed)")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage thread lifecycle'
    )
    parser.add_argument(
        '--init',
        metavar='THREAD_ID',
        help='Initialize a new thread'
    )
    parser.add_argument(
        '--status',
        metavar='THREAD_ID',
        help='Get thread status'
    )
    parser.add_argument(
        '--complete',
        metavar='THREAD_ID',
        help='Mark thread as complete'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all threads'
    )
    
    args = parser.parse_args()
    setup_logging()
    
    try:
        if args.init:
            init_thread(args.init)
        elif args.status:
            status = get_thread_status(args.status)
            print(json.dumps(status, indent=2))
        elif args.complete:
            complete_thread(args.complete)
        elif args.list:
            list_threads()
        else:
            parser.print_help()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
