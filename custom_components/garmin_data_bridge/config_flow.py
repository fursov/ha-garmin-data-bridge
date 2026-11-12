"""UI setup of independently authenticated Garmin profiles."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .auth import generate_token, token_digest
from .const import CONF_ENTITIES, CONF_PROFILE, CONF_TOKEN_DIGEST, DOMAIN, MAX_ENTITIES


def entity_schema(default: list[str] | None = None) -> vol.Schema:
    """Build a multiple-entity selection schema."""
    field = (
        vol.Required(CONF_ENTITIES, default=default)
        if default
        else vol.Required(CONF_ENTITIES)
    )
    return vol.Schema(
        {field: selector.EntitySelector(selector.EntitySelectorConfig(multiple=True))}
    )


def valid_entities(entities: list[str]) -> bool:
    """Require a small, non-duplicated allowlist."""
    return (
        bool(entities)
        and len(entities) <= MAX_ENTITIES
        and len(set(entities)) == len(entities)
    )


class GarminDataBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up an independent Garmin client credential."""

    VERSION = 1

    def __init__(self) -> None:
        """Keep the plaintext token only for the confirmation form."""
        self._profile: str | None = None
        self._entities: list[str] = []
        self._token: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select the entities before generating credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            entities = user_input[CONF_ENTITIES]
            if not valid_entities(entities):
                errors["base"] = "invalid_entities"
            elif not user_input[CONF_PROFILE].strip():
                errors["base"] = "invalid_profile"
            else:
                self._profile = user_input[CONF_PROFILE].strip()
                self._entities = entities
                self._token = generate_token()
                return await self.async_step_confirm()

        schema = vol.Schema(
            {
                vol.Required(CONF_PROFILE, default="My Garmin"): str,
                vol.Required(CONF_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the secret exactly once, then persist only its digest."""
        if self._token is None or self._profile is None:
            return self.async_abort(reason="invalid_setup")

        if user_input is not None:
            return self.async_create_entry(
                title=self._profile,
                data={
                    CONF_PROFILE: self._profile,
                    CONF_ENTITIES: self._entities,
                    CONF_TOKEN_DIGEST: token_digest(self._token),
                },
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"token": self._token},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GarminDataBridgeOptionsFlow:
        """Create a settings flow for changing the entity allowlist."""
        return GarminDataBridgeOptionsFlow()


class GarminDataBridgeOptionsFlow(config_entries.OptionsFlow):
    """Update selected entities without changing the profile token."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure entities shown to this client."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if valid_entities(user_input[CONF_ENTITIES]):
                return self.async_create_entry(data=user_input)
            errors["base"] = "invalid_entities"

        current = self.config_entry.options.get(
            CONF_ENTITIES, self.config_entry.data[CONF_ENTITIES]
        )
        return self.async_show_form(
            step_id="init",
            data_schema=entity_schema(current),
            errors=errors,
        )
