"""Read-only external API for selected Home Assistant states."""

from datetime import UTC, datetime

from aiohttp import web

from homeassistant.components.http import HomeAssistantView

from .auth import verify_bearer_header
from .const import API_PATH, CONF_ENTITIES, CONF_TOKEN_DIGEST, DOMAIN, MAX_ENTITIES
from .payload import serialize_entities

NO_STORE_HEADERS = {
    "Cache-Control": "no-store",
    "Pragma": "no-cache",
    "X-Content-Type-Options": "nosniff",
}


class GarminDataBridgeView(HomeAssistantView):
    """Return a token-scoped subset of the Home Assistant state machine."""

    url = API_PATH
    name = "api:garmin_data_bridge:data"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        """Authorize every request before querying states."""
        hass = request.app["hass"]
        header = request.headers.get("Authorization", "")

        matched_entry = None
        for entry in hass.data.get(DOMAIN, {}).values():
            if verify_bearer_header(header, entry.data[CONF_TOKEN_DIGEST]):
                matched_entry = entry
                break

        if matched_entry is None:
            raise web.HTTPUnauthorized(
                headers={
                    **NO_STORE_HEADERS,
                    "WWW-Authenticate": 'Bearer realm="Garmin Data Bridge"',
                }
            )

        selected = matched_entry.options.get(
            CONF_ENTITIES, matched_entry.data[CONF_ENTITIES]
        )
        items = serialize_entities(hass, selected[:MAX_ENTITIES])
        return web.json_response(
            {
                "version": 1,
                "generated_at": datetime.now(UTC).isoformat(),
                "items": items,
            },
            headers=NO_STORE_HEADERS,
        )
