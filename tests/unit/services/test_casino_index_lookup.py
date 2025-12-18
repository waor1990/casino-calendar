from casino_calendar.services.casino_index import load_casino_index


def test_load_casino_index_enriches_missing_color(monkeypatch):
    sample_data = [
        {"name": "Lucky Eagle Casino", "address": "Example"},
        {"name": "Custom Casino", "color": "#123456", "distance": "Close"},
        "ignore-me",
    ]

    def fake_get_config(filename):
        assert filename.endswith("casino_index.json")
        return sample_data

    monkeypatch.setattr("casino_calendar.services.casino_index.get_config", fake_get_config)

    entries = load_casino_index()

    assert len(entries) == 2
    assert entries[0]["name"] == "Lucky Eagle Casino"
    assert entries[0]["color"]  # color is populated from casino palette
    assert entries[1]["color"] == "#123456"


def test_load_casino_index_handles_invalid_root(monkeypatch, caplog):
    monkeypatch.setattr("casino_calendar.services.casino_index.get_config", lambda filename: "oops")

    with caplog.at_level("ERROR", logger="casino_calendar.services.casino_index"):
        entries = load_casino_index()

    assert entries == []
