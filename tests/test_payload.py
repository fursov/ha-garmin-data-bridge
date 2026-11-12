"""Read-only payload contract; no Home Assistant dependency required."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

MODULE = Path(__file__).resolve().parents[1] / (
    "custom_components/garmin_data_bridge/payload.py"
)
SPEC = importlib.util.spec_from_file_location("garmin_payload", MODULE)
assert SPEC is not None and SPEC.loader is not None
payload = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(payload)


class FakeStates:
    """Minimal state machine fixture."""

    def __init__(self, items: dict) -> None:
        self.items = items

    def get(self, entity_id: str):
        """Get only an explicitly selected state."""
        return self.items.get(entity_id)


def test_allowlist_never_includes_extra_entities_or_attributes() -> None:
    """A client must never receive unrelated states or sensitive attributes."""
    hass = SimpleNamespace(
        states=FakeStates(
            {
                "sensor.outside": SimpleNamespace(
                    state="4.2",
                    attributes={
                        "friendly_name": "Outside",
                        "unit_of_measurement": "°C",
                        "latitude": "SECRET",
                    },
                ),
                "person.private": SimpleNamespace(
                    state="home", attributes={"secret": "hidden"}
                ),
            }
        )
    )
    data = payload.serialize_entities(hass, ["sensor.outside"])
    assert data == [
        {
            "slot": 1,
            "label": "Outside",
            "value": "4.2",
            "unit": "°C",
            "status": "ok",
        }
    ]
    assert "SECRET" not in str(data)
    assert "person.private" not in str(data)
    assert "entity_id" not in data[0]


def test_missing_and_unavailable_entities_are_explicit() -> None:
    """Stale data must not be presented as fresh."""
    hass = SimpleNamespace(
        states=FakeStates(
            {
                "sensor.bad": SimpleNamespace(
                    state="unavailable", attributes={"friendly_name": "Bad"}
                )
            }
        )
    )
    data = payload.serialize_entities(hass, ["sensor.missing", "sensor.bad"])
    assert len(data) == 2
    assert data[0]["status"] == "unavailable"
    assert data[0]["value"] is None
    assert data[1]["status"] == "unavailable"
    assert data[1]["value"] is None
