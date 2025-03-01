"""Config flow to configure the PPPP Camera integration."""

from __future__ import annotations

import asyncio
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    # CONF_NAME,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .camera import discover_camera
from .const import LOGGER, DOMAIN


@callback
def async_get_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any], show_name: bool = False
) -> vol.Schema:
    """Return PPPP Camera schema."""
    schema = {
        vol.Required(CONF_IP_ADDRESS, default=defaults.get(CONF_IP_ADDRESS)): str,
        vol.Optional(
            CONF_USERNAME,
            description={"suggested_value": defaults.get(CONF_USERNAME)},
        ): str,
        vol.Optional(
            CONF_PASSWORD,
            description={"suggested_value": defaults.get(CONF_PASSWORD)},
        ): str,
    }

    return vol.Schema(schema)


async def async_validate_input(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[dict[str, str], str]:
    """Manage PPPP Camera options."""
    errors = {}
    field = "base"
    camera_info = None

    try:
        ip_address = user_input[CONF_IP_ADDRESS]
        camera_info = await discover_camera(ip_address)
    except (TimeoutError, asyncio.TimeoutError):
        LOGGER.exception("Cannot connect to %s", user_input[CONF_IP_ADDRESS])
        errors[field] = "cannot_connect"

    return errors, camera_info.dev_id.dev_id


class PPPPCameraFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for PPPP Camera."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return PPPPCameraOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, dev_id = await async_validate_input(self.hass, user_input)
            if not errors:
                self._async_abort_entries_match(
                    {CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS]}
                )

                # Storing data in option, to allow for changing them later
                # using an options flow.
                return self.async_create_entry(
                    title=dev_id,
                    data={},
                    options={
                        CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                        CONF_USERNAME: user_input.get(CONF_USERNAME),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                        # CONF_STILL_IMAGE_URL: user_input.get(CONF_STILL_IMAGE_URL),
                        # CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=async_get_schema(user_input, show_name=True),
            errors=errors,
        )


class PPPPCameraOptionsFlowHandler(OptionsFlow):
    """Handle PPPP Camera options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage PPPP Camera options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors, dev_id = await async_validate_input(self.hass, user_input)
            if not errors:
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        entry.entry_id != self.config_entry.entry_id
                        and entry.options[CONF_IP_ADDRESS] == user_input[CONF_IP_ADDRESS]
                    ):
                        errors = {CONF_IP_ADDRESS: "already_configured"}

                if not errors:
                    return self.async_create_entry(
                        title=dev_id,
                        data={
                            CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                            CONF_USERNAME: user_input.get(CONF_USERNAME),
                            CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                            # CONF_STILL_IMAGE_URL: user_input.get(CONF_STILL_IMAGE_URL),
                            # CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                        },
                    )
        else:
            user_input = {}

        return self.async_show_form(
            step_id="init",
            data_schema=async_get_schema(user_input or self.config_entry.options),
            errors=errors,
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
