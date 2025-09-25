"""Config flow to configure the PPPP Camera integration."""

from __future__ import annotations

import asyncio
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from aiopppp import find_device
from homeassistant.config_entries import (
    SOURCE_DISCOVERY,
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_DEVICE_ID,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers import selector

from .const import DOMAIN, LOGGER, SOURCE_DISCOVERY_CONFIRM
from .config_helpers import get_defaults


@callback
def async_get_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any], 
    host_readonly: bool = False
) -> vol.Schema:
    """Return PPPP Camera schema."""
    # Conditionally set host field type
    host_type = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT, read_only=host_readonly))
        
    schema = {
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST)): host_type,
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
    dev_descriptor = None

    try:
        ip_address = user_input[CONF_HOST]
        dev_descriptor = await find_device(ip_address)
    except (TimeoutError, asyncio.TimeoutError):
        LOGGER.exception("Cannot connect to %s", user_input[CONF_HOST])
        errors[field] = "cannot_connect"

    return errors, dev_descriptor.dev_id.dev_id if dev_descriptor else ''

class PPPPCameraFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for PPPP Camera."""

    VERSION = 1

    # @staticmethod
    # @callback
    # def async_get_options_flow(
    #     config_entry: ConfigEntry,
    # ) -> OptionsFlow:
    #     """Get the options flow for this handler."""
    #     return PPPPCameraOptionsFlowHandler()

    async def async_step_integration_discovery(
        self, discovery_info: DiscoveryInfoType
    ) -> ConfigFlowResult:
        """Handle discovery of a PPPP camera."""
        host = discovery_info[CONF_HOST]
        device_id = discovery_info[CONF_DEVICE_ID]
        name = f"{device_id} ({host})"

        # Check if already configured
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        # Check if host is already configured with different device ID
        self._async_abort_entries_match({CONF_HOST: host})

        # Set placeholders for the discovery form
        self.context["title_placeholders"] = {
            CONF_NAME: name,
        }

        self.context["discovery_info"] = discovery_info;

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, 
        user_input: dict[str, Any] | None = None,
        discovery_info: DiscoveryInfoType | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery of PPPP camera."""
        errors: dict[str, str] = {}

        discovery_info = self.context["discovery_info"]

        # Get defaults for username/password
        defaults = get_defaults(self.hass)
        default_username = defaults.get(CONF_USERNAME)
        default_password = defaults.get(CONF_PASSWORD)

        if user_input is not None:
            # Ensure we use the discovered host, not any user input for host
            data = {
                CONF_HOST: discovery_info[CONF_HOST],
                CONF_USERNAME: user_input.get(CONF_USERNAME, default_username),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD, default_password),
            }

            errors, dev_id = await async_validate_input(self.hass, data)
            
            if not errors:
                # Verify the device ID matches what we discovered
                if dev_id == discovery_info[CONF_DEVICE_ID]:
                    return self.async_create_entry(
                        title=discovery_info[CONF_DEVICE_ID],
                        data={},
                        options={
                            CONF_HOST: discovery_info[CONF_HOST],
                            CONF_USERNAME: data[CONF_USERNAME],
                            CONF_PASSWORD: data[CONF_PASSWORD],
                        },
                    )
                else:
                    errors["base"] = "device_mismatch"
        
        # Prepare defaults for the form including the discovered host
        form_defaults = {
            CONF_HOST: discovery_info[CONF_HOST],
            CONF_USERNAME: default_username,
            CONF_PASSWORD: default_password,
        }

        # Use the same schema as manual flow but with readonly host
        return self.async_show_form(
            step_id=SOURCE_DISCOVERY_CONFIRM,
            data_schema=async_get_schema(form_defaults, host_readonly=True),
            errors=errors,
            description_placeholders={
                CONF_NAME: discovery_info[CONF_DEVICE_ID],
                CONF_HOST: discovery_info[CONF_HOST],
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        # Get defaults for username/password
        defaults = get_defaults(self.hass)
        default_username = defaults.get(CONF_USERNAME)
        default_password = defaults.get(CONF_PASSWORD)

        if user_input is not None:
            errors, dev_id = await async_validate_input(self.hass, user_input)
            if not errors:
                self._async_abort_entries_match(
                    {CONF_HOST: user_input[CONF_HOST]}
                )

                await self.async_set_unique_id(dev_id, raise_on_progress=False)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=dev_id,
                    data={},
                    options={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_USERNAME: user_input.get(CONF_USERNAME, default_username),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, default_password),
                    },
                )
        else:
            user_input = {
                CONF_USERNAME: default_username,
                CONF_PASSWORD: default_password,
            }

        return self.async_show_form(
            step_id=SOURCE_USER,
            data_schema=async_get_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        # Get defaults for username/password
        defaults = get_defaults(self.hass)
        default_username = defaults.get(CONF_USERNAME)
        default_password = defaults.get(CONF_PASSWORD)

        if user_input is not None:
            errors, dev_id = await async_validate_input(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(dev_id, raise_on_progress=False)
                self._abort_if_unique_id_mismatch()

                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    options={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_USERNAME: user_input.get(CONF_USERNAME, default_username),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, default_password),
                    },
                )
        else:
            user_input = {
                    CONF_HOST: self._get_reconfigure_entry().options[CONF_HOST],
                    CONF_USERNAME: self._get_reconfigure_entry().options[CONF_USERNAME],
                    CONF_PASSWORD: self._get_reconfigure_entry().options[CONF_PASSWORD],
                }

        return self.async_show_form(
            step_id=SOURCE_RECONFIGURE,
            data_schema=async_get_schema(user_input),
            errors=errors,
            description_placeholders={
                CONF_NAME: self._get_reconfigure_entry().unique_id,
                CONF_HOST: self._get_reconfigure_entry().options[CONF_HOST],
            },
        )


# class PPPPCameraOptionsFlowHandler(OptionsFlow):
#     """Handle PPPP Camera options."""

#     async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> ConfigFlowResult:
#         """Manage PPPP Camera options."""
#         errors: dict[str, str] = {}

#        # Get defaults for username/password
#        defaults = get_defaults(self.hass)
#        default_username = defaults.get(CONF_USERNAME)
#        default_password = defaults.get(CONF_PASSWORD)

#         if user_input is not None:
#             errors, dev_id = await async_validate_input(self.hass, user_input)
#             if not errors:
#                 for entry in self.hass.config_entries.async_entries(DOMAIN):
#                     if (
#                         entry.entry_id != self.config_entry.entry_id
#                         and entry.options[CONF_HOST] == user_input[CONF_HOST]
#                     ):
#                         errors = {CONF_HOST: "already_configured"}

#                 if not errors:
#                     return self.async_create_entry(
#                         title=dev_id,
#                         data={
#                             CONF_HOST: user_input[CONF_HOST],
#                             CONF_USERNAME: user_input.get(CONF_USERNAME, default_username),
#                             CONF_PASSWORD: user_input.get(CONF_PASSWORD, default_password),
#                         },
#                     )
#         else:
#             user_input = {}

#         return self.async_show_form(
#             step_id="init",
#             data_schema=async_get_schema(user_input or self.config_entry.options),
#             errors=errors,
#         )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
