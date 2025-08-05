from pathlib import Path

import chromedriver_autoinstaller
import pytest
from dash import Dash, html
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

chromedriver_autoinstaller.install()


def _webdriver_available() -> bool:
    try:
        opts = Options()
        opts.add_argument("--headless=new")
        driver = Chrome(options=opts)
        driver.quit()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _webdriver_available(), reason="chromedriver not available")
def test_accent_elements_switch_to_primary_dark(dash_duo, tmp_path):
    screenshot_dir = Path(tmp_path) / "screenshots"
    screenshot_dir.mkdir()

    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Button("x", className="modal-close"),
                    html.Div("event", className="event-block-day"),
                ],
                className="modal-content",
            ),
            html.Div("Label", className="event-label-title", id="event-label"),
            html.Button("hover", className="day-click-area", id="hover-area"),
        ]
    )
    dash_duo.start_server(app)

    dash_duo.wait_for_element(".modal-close")
    modal_close = dash_duo.find_element(".modal-close")
    event_label = dash_duo.find_element("#event-label")
    event_block = dash_duo.find_element(".event-block-day")
    hover_area = dash_duo.find_element("#hover-area")

    def css_var_to_rgb(name):
        return dash_duo.driver.execute_script(
            "var s=getComputedStyle(document.documentElement).getPropertyValue(arguments[0]).trim();"
            "var d=document.createElement('div');d.style.color=s;document.body.appendChild(d);"
            "var c=getComputedStyle(d).color;d.remove();return c;",
            name,
        )

    def get_color(el, prop):
        return dash_duo.driver.execute_script(
            "return getComputedStyle(arguments[0])[arguments[1]];", el, prop
        )

    accent_rgb = css_var_to_rgb("--color-accent")
    assert get_color(modal_close, "backgroundColor") == accent_rgb
    assert get_color(event_label, "color") == accent_rgb
    assert get_color(event_block, "borderTopColor") == accent_rgb

    dash_duo.driver.save_screenshot(str(screenshot_dir / "light.png"))

    dash_duo.driver.execute_script(
        "document.documentElement.setAttribute('data-theme','dark');"
    )
    ActionChains(dash_duo.driver).move_to_element(hover_area).perform()

    primary_dark_rgb = css_var_to_rgb("--color-primary-dark")
    assert get_color(modal_close, "backgroundColor") == primary_dark_rgb
    assert get_color(event_label, "color") == primary_dark_rgb
    assert get_color(event_block, "borderTopColor") == primary_dark_rgb
    assert get_color(hover_area, "backgroundColor") == primary_dark_rgb

    dash_duo.driver.save_screenshot(str(screenshot_dir / "dark.png"))
