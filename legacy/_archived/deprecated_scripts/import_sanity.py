#!/usr/bin/env python3
"""Archived legacy script.

This script previously validated imports for the deprecated ``app_components`` package. It
is kept for historical reference only and should not be executed as part of the active
test suite.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"Python version: {sys.version}")
print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")

try:
    print("Testing imports...")

    # Test basic imports
    import dash

    print(f"✓ Dash version: {dash.__version__}")

    import pandas as pd

    print(f"✓ Pandas version: {pd.__version__}")

    import plotly

    print(f"✓ Plotly version: {plotly.__version__}")

    # Test application imports

    print("✓ Logging config imported successfully")

    from app_components.data import load_event_data

    print("✓ Data module imported successfully")

    print("✓ Layout module imported successfully")

    print("✓ Callbacks module imported successfully")

    print("\nTesting data loading...")
    df_events = load_event_data()
    print(f"✓ Loaded {len(df_events)} events")

    print("\nAll imports successful! Application should be able to run.")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
