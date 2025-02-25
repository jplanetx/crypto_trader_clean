# AI Task Guide

This guide helps AI assistants understand how to work with this project effectively.

## Essential Context Files

When starting any task, request these files to understand the project context:

1. Project Structure and Configuration:
- `pyproject.toml` - Project dependencies and configuration
- `requirements.txt` - Project dependencies
- `.env` - Environment variables (if relevant to task)
- `config/config.json` - Current configuration
- `config/config_schema.json` - Configuration schema

2. Thread Management:
- `thread_management/active_thread/THREAD_XXX.json` - Current thread details
- `thread_management/templates/thread_XXX_init.json` - Thread template (if exists)

3. Documentation:
- `docs/verification_guide.md` - Verification procedures
- `docs/ai_assistance_guide.md` - AI workflow guidelines

4. Tests Related to Task:
- Relevant test files from `tests/` directory

## Working with THREAD Files

1. Understanding Thread Structure:
- Each thread file contains specific objectives and deliverables
- Check `thread_management/active_thread/` for current thread status
- Reference `thread_management/templates/` for detailed specifications

2. Making Progress:
- Update thread status when completing deliverables
- Follow verification steps defined in thread file
- Ensure all success criteria are met

3. Creating Task Prompts:
Example format:
```
Implement [specific deliverable] from THREAD_XXX:

1. Objective: [copied from thread file]
2. Requirements:
   - [specific requirements]
   - [validation criteria]
3. Files to Modify:
   - [list of files]
4. Success Criteria:
   - [from thread file]
   - [specific test requirements]

Please implement with test coverage meeting [X]% and update relevant documentation.
```

## Best Practices

1. Environment Setup:
- Always verify virtual environment is active
- Check PYTHONPATH includes project root
- Run verification script: `python scripts/verify_thread.py --check-all`

2. Code Changes:
- Follow existing patterns in the codebase
- Maintain test coverage requirements
- Update documentation for new features
- Respect project structure and conventions

3. Testing:
- Run tests before and after changes
- Ensure no regression in existing functionality
- Add new tests for new features
- Maintain test coverage threshold

4. Documentation:
- Update relevant documentation
- Include docstrings for new functions
- Add comments for complex logic
- Update configuration examples if needed

## Common Workflows

1. Starting a New Task:
```python
# 1. Check environment
python scripts/verify_thread.py --check-all

# 2. View thread details
cat thread_management/active_thread/THREAD_XXX.json

# 3. Run relevant tests
pytest tests/test_core/test_specific_module.py
```

2. Completing a Deliverable:
- Update thread status
- Run full test suite
- Document changes
- Update configuration if needed

Remember: Each change should maintain or improve the project's quality and reliability.
