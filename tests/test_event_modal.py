from dash.testing.application_runners import import_app
from freezegun import freeze_time


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
