#!/usr/bin/env python3
"""
Simple test script to verify the Casino Calendar application can be imported and run.
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
    from app_components.logging_config import setup_logger

    print("✓ Logging config imported successfully")

    from app_components.data import load_event_data

    print("✓ Data module imported successfully")

    from app_components.layout import create_layout

    print("✓ Layout module imported successfully")

    from app_components.callbacks import register_callbacks

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
