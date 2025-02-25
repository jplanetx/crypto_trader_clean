# Starting New Thread

To start a new thread, follow these steps:

1. **Review the Template:**  
   Open the base thread template file at `thread_management/templates/thread_init_template.json` for reference.

2. **Copy and Update Template for New Thread:**  
   - Copy the provided template file `thread_management/templates/thread_005_init.json` as your starting point.
   - Update the `"thread_id"` field to your new thread ID (for example, `"006"` or `"005_A"` if continuing specific work from THREAD_005).
   - Edit other fields such as `"objectives"`, `"required_components"`, and `"completion_checklist"` to reflect the new tasks.

3. **Initialize the New Thread:**  
   From the project root, run:
   ```
   python scripts/thread_manager.py --init <NEW_THREAD_ID>
   ```
   This command creates a new active thread file in `thread_management/active_thread/`.

4. **Future Thread Continuity:**  
   **Important:** Once THREAD_005 is complete, update this document so that all new threads follow the same process. You may also use or develop a command-line tool or script (e.g., `python scripts/update_next_thread_template.py --next`) that updates these instruction files automatically for the next thread.

5. **Completion:**  
   After finishing work on a thread, mark it complete with:
   ```
   python scripts/thread_manager.py --complete <THREAD_ID>
   ```

This document ensures continuity: as soon as THREAD_005 is done, simply update the thread ID in these instructions for future tasks.
