import sys
from pathlib import Path

import chromedriver_autoinstaller
import pytest
from freezegun import freeze_time

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dash.testing.application_runners import import_app  # noqa: E402

try:
    # Install chromedriver in the current working directory to avoid
    # permission issues on Windows where the package directory may
    # require elevated privileges.
    chromedriver_autoinstaller.install(cwd=True)
except (ValueError, PermissionError, RuntimeError):
    pytest.skip(
        "Chrome browser is not available or could not be installed",
        allow_module_level=True,
    )


@freeze_time("2025-04-10")
def test_event_blocks_open_modal(dash_duo):
    app = import_app("app")
    dash_duo.start_server(app)

    dash_duo.wait_for_element(".event-block-grid", timeout=15)
    event_blocks = dash_duo.find_elements(".event-block-grid")
    assert event_blocks, "No event blocks found"

    for block in event_blocks:
        block.click()
        dash_duo.wait_for_element("#event-modal.modal.show", timeout=10)
        modal = dash_duo.find_element("#event-modal")
        assert "show" in modal.get_attribute("class"), "Modal did not open"
        dash_duo.find_element("#close-modal").click()
        dash_duo.wait_for_no_elements("#event-modal.modal.show", timeout=10)
