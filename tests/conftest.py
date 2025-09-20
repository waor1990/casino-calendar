import sys
from pathlib import Path

import pytest

# Ensure app modules are importable
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


CASINOS = ["ilani", "Lucky Eagle Casino"]
OFFER_TYPES = ["Giveaway", "Free-Play"]


@pytest.fixture(params=CASINOS)
def casino(request):
    """Return a casino name for parametrized tests."""

    return request.param


@pytest.fixture(params=OFFER_TYPES)
def offer_type(request):
    """Return an offer type for parametrized tests."""

    return request.param
