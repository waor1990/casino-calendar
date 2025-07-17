import sys
from pathlib import Path

import pytest

# Ensure app modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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
