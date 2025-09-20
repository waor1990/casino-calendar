# Python Utility Scripts

These helpers run from the project root with the virtual environment activated.

- cleanup_logs.py - purge old log files based on retention rules.
- debug_errors.py - inspect recent error logs and summarize stack traces.
- test_day_modal_fix.py - regression runner for day modal interactions.
- verify_requirements.py - compare the installed packages against requirements.txt.

Example::

    python scripts/python/cleanup_logs.py --days 7
