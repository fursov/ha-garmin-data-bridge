"""Expose selected states to clients with scoped, independent credentials."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import GarminDataBridgeView
from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the HTTP view once, even if multiple profiles exist."""
    hass.data.setdefault(DOMAIN, {})
    hass.http.register_view(GarminDataBridgeView())
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Make a configured profile available to the API."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Immediately revoke the profile when it is unloaded."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
