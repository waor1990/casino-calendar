"""Repository-wide pytest bootstrap to sanitize import paths early.

This ensures that tests executed from any location (including helper scripts
outside ``tests/``) do not accidentally import NumPy from a local source
checkout or leak user-site packages ahead of the project's virtualenv.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from casino_calendar.bootstrap import bootstrap_environment

bootstrap_environment(PROJECT_ROOT)
os.environ.setdefault("CASINO_MINIMAL_TEST_LOG", "1")
