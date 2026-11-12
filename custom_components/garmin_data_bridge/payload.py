"""Serialize only explicitly selected Home Assistant state fields."""

from typing import Any

MAX_LABEL_LENGTH = 32
MAX_UNIT_LENGTH = 16
MAX_VALUE_LENGTH = 64


def serialize_entities(hass: Any, entities: list[str]) -> list[dict[str, Any]]:
    """Build an allowlisted display payload without leaking attributes."""
    items: list[dict[str, Any]] = []
    for index, entity_id in enumerate(entities, start=1):
        state = hass.states.get(entity_id)
        if state is None:
            items.append(
                {
                    "slot": index,
                    "label": entity_id[:MAX_LABEL_LENGTH],
                    "value": None,
                    "unit": None,
                    "status": "unavailable",
                }
            )
            continue

        label = str(state.attributes.get("friendly_name") or entity_id)
        unit = state.attributes.get("unit_of_measurement")
        available = state.state not in ("unknown", "unavailable")
        items.append(
            {
                "slot": index,
                "label": label[:MAX_LABEL_LENGTH],
                "value": str(state.state)[:MAX_VALUE_LENGTH] if available else None,
                "unit": str(unit)[:MAX_UNIT_LENGTH] if unit is not None else None,
                "status": "ok" if available else "unavailable",
            }
        )
    return items
