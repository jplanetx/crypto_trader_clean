# Thread Start Guide

This document consolidates instructions for starting a new thread in the crypto_trader_clean project. It merges key information from OLD_START_NEW_THREAD.md, OLD_next_thread_instructions.md, and OLD_next_thread_prompt.md so that you have a single reference point for initiating new threads.

**Note: All new thread work should now refer solely to this THREAD_START_GUIDE.md file as the single source of instructions.**

---

## 1. Overview

Each new thread represents a set of tasks or improvements to be implemented. When a thread is complete, update this guide (or use a future update command) to prepare for the next one. For example, if you finish THREAD_005, the next thread might be THREAD_006 or a continuation thread like THREAD_005_A, and this guide should be updated accordingly.

---

## 2. Starting a New Thread

### Step 1: Review the Base Template
- Open the base template located at:
  ```
  thread_management/templates/thread_init_template.json
  ```
  This file provides the default structure for all threads.

### Step 2: Prepare the New Thread Configuration
- Copy an existing thread configuration (e.g., the most recent one, such as `thread_management/templates/thread_005_init.json`) to use as a starting point.
- Update the `"thread_id"` field to the new value (for example, "006" or "005_A" if continuing specific work from THREAD_005).
- Modify fields like `"objectives"`, `"required_components"`, and `"completion_checklist"` to reflect the tasks planned for the new thread.

### Step 3: Initialize the New Thread
- From the project root, run the following command to initialize the thread:
  ```
  python scripts/thread_manager.py --init <NEW_THREAD_ID>
  ```
  This creates an active thread file under `thread_management/active_thread/`.

---

## 3. Work and Verification

### Task Execution
- Use the new thread configuration as your container for all tasks. For example, if you're starting THREAD_005, work on tasks such as system enhancements, refactoring, or new features as defined in that thread's objectives.
- As you complete tasks, manually update the corresponding checklist items within the thread's JSON file to reflect progress.

### Verification Steps
- Before starting a development session, always verify your project setup:
  ```
  python scripts/verify_thread.py --check-all
  ```
- After completing tasks and before marking the thread complete, run:
  ```
  python scripts/verify_thread.py --cleanup
  ```
  This ensures the workspace is free of stale temporary files.

### Running Test Coverage
- To check test coverage after tasks, run:
  ```
  python scripts/verify_thread.py --check-coverage
  ```
  (Currently, this command uses a placeholder implementation that prints coverage results. Update it later with real coverage tools when necessary.) ## Need to verify this

---

## 4. Completing the Thread and Preparing for the Next

### Mark Completion
- Once all tasks and checklist items for the thread are complete, mark the thread as complete with:
  ```
  python scripts/thread_manager.py --complete <THREAD_ID>
  ```
  This archives the thread in `thread_management/completed_threads/`.

### Transitioning to the Next Thread
- Before starting a new thread, update this guide to reflect the new context (e.g., change the thread ID, objectives, and any specifics that carry over from the previous work).
- Optionally, a custom command (e.g., `python scripts/update_next_thread_template.py --next`) can be developed in the future to automate updating this guide for the next thread.

---

## 5. AI Verification Reminder

**Before marking any thread as complete, ALWAYS run:**
```
python scripts/verify_thread.py --check-all
python scripts/verify_thread.py --check-coverage
python scripts/verify_thread.py --cleanup
```

Ensure that every checklist item in the thread's JSON file is verified prior to closing the thread.

---

## 6. Summary

- **Review the template:** Use `thread_init_template.json` as reference.
- **Copy and update:** Use the most recent thread configuration as the base and update the thread ID and task details.
- **Initialize:** Run the init command to create the active thread file.
- **Work and verify:** Use verification commands (`--check-all`, `--cleanup`, `--check-coverage`) to ensure every change is validated.
- **Complete and transition:** Mark the thread complete and update this guide for the next set of tasks.

This unified guide is your single source of reference for starting, managing, and transitioning between threads, ensuring continuity and clarity throughout your project.
