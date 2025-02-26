# THREAD START GUIDE

This guide provides instructions for managing development threads.

## Archiving a Completed Thread
To mark a thread as complete, run:
```
python scripts/thread_manager.py --complete <THREAD_ID>
```

## Starting a New Thread
To initialize a new thread, run:
```
python scripts/thread_manager.py --init <THREAD_ID>
```

### Starting Continuation Thread: THREAD_005_A
Since THREAD_005 requires further work, it continues under the identifier THREAD_005_A.
1. Complete the original thread:
   ```
   python scripts/thread_manager.py --complete THREAD_005
   ```
2. Initialize the continuation thread:
   ```
   python scripts/thread_manager.py --init THREAD_005_A
   ```

Refer to this guide for additional verification steps and troubleshooting.
