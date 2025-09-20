# Scripts Directory

Utilities are grouped by runtime to make discovery and maintenance easier. Run them from the project root.

## python/
- cleanup_logs.py - rotate and prune log files.
- debug_errors.py - inspect recent error messages for common issues.
- test_day_modal_fix.py - regression check for the day modal callback chain.
- verify_requirements.py - compare the local environment against requirements.txt.

## shell/
- setup.sh - bootstrap Python and Node dependencies on Unix-like systems.
- test.sh - orchestrate linting and the pytest suite.

## node/
- append-casino-event.mjs - Scriptable helper to append new events to the CSV.
- trim-old-casino-events.mjs - Scriptable helper to purge stale events.

## windows/
- cleanup_logs.bat - purge log files on Windows.
- create_scheduled_cleanup.bat - set up a scheduled cleanup task.
- run_direct.bat - launch the Dash development server with environment setup.
- setup.bat - Windows-friendly bootstrapper.

Examples::

    python scripts/python/debug_errors.py --limit 20
    bash scripts/shell/test.sh
    node scripts/node/append-casino-event.mjs
