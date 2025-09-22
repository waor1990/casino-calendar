"""Shared configuration for end-to-end tests."""

import pytest

pytestmark = pytest.mark.skip(reason="E2E tests rely on external browsers and visual tooling not available in CI")
