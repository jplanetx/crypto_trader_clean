# Thread Management

## Overview
This directory contains all files and configurations related to the project's thread management system.

## Active Threads
Active thread configurations are stored in the **active_thread** folder. New threads are initialized using templates from the **templates** folder. For example, the continuation for THREAD_005 is stored as `THREAD_005_A.json`.

## Completed Threads
When a thread is marked as complete, its configuration file is moved to the **completed_threads** folder. Ensure that the archiving process is performed to maintain a clean active thread list.

## Thread Templates
Templates for initializing threads are available in the **templates** folder. Use these templates as a basis to create new thread configurations and follow the latest developer instructions.

## Managing Threads
- **Archiving a Thread:**  
  Use the following command to archive a completed thread:
  ```
  python scripts/thread_manager.py --complete <THREAD_ID>
  ```
- **Starting a New Thread:**  
  Use this command to initialize a new thread:
  ```
  python scripts/thread_manager.py --init <THREAD_ID>
  ```
For further details, refer to the [THREAD_START_GUIDE.md](../THREAD_START_GUIDE.md).
