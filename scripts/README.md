# Scripts Directory

Utilities are grouped by runtime to make discovery and maintenance easier. Run them from the project root.

## python/

- check_environment.py - validate Python/Node versions and npm availability.
- cleanup_logs.py - rotate and prune log files.
- csvupdate.py - normalise newly added casino event CSV files to the canonical format (logs to `logs/casino_calendar_maintenance.log`).
- debug_errors.py - inspect recent error messages for common issues.
- test_day_modal_fix.py - regression check for the day modal callback chain.
- verify_requirements.py - compare the local environment against requirements.txt.

## shell/

- setup.sh - bootstrap Python and Node dependencies on Unix-like systems.
- test.sh - orchestrate linting and the pytest suite.

## node/

- append-casino-event.mjs - Scriptable helper to append new events to the CSV.
- trim-old-casino-events.mjs - Scriptable helper to purge stale events.
- cleanup-node-modules.mjs - Clear stale npm staging directories on Windows.
- verify-package-json.mjs - Guard against invalid `package.json` content before installs.

## windows/

- setup.bat - Windows-friendly bootstrapper (also callable via root `setup.bat`).
- run_direct.bat - launch the Dash development server with environment setup (also callable via root `run.bat`).
- cleanup_logs.bat - purge log files on Windows.
- create_scheduled_cleanup.bat - set up a scheduled cleanup task.

Examples::

    python scripts/python/debug_errors.py --limit 20
    bash scripts/shell/test.sh
    node scripts/node/append-casino-event.mjs
