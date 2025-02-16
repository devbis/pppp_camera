"""Config flow to configure the PPPP Camera integration."""

from __future__ import annotations

# from http import HTTPStatus
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
    # CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_IP_ADDRESS,
    # CONF_PASSWORD,
    CONF_USERNAME,
    # CONF_VERIFY_SSL,
    # HTTP_BASIC_AUTHENTICATION,
    # HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import LOGGER, DOMAIN


@callback
def async_get_schema(
    defaults: dict[str, Any] | MappingProxyType[str, Any], show_name: bool = False
) -> vol.Schema:
    """Return MJPEG IP Camera schema."""
    schema = {
        vol.Required(CONF_IP_ADDRESS, default=defaults.get(CONF_IP_ADDRESS)): str,
        vol.Optional(
            CONF_USERNAME,
            description={"suggested_value": defaults.get(CONF_USERNAME)},
        ): str,
    }

    if show_name:
        schema = {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME)): str,
            **schema,
        }

    return vol.Schema(schema)


# def validate_url(
#     address: str,
#     # username: str | None,
#     # password: str,
#     # verify_ssl: bool,
#     # authentication: str = HTTP_BASIC_AUTHENTICATION,
# ) -> str:
#     """Test if the given setting works as expected."""
#     auth: HTTPDigestAuth | HTTPBasicAuth | None = None
#     if username and password:
#         if authentication == HTTP_DIGEST_AUTHENTICATION:
#             auth = HTTPDigestAuth(username, password)
#         else:
#             auth = HTTPBasicAuth(username, password)
#
#     response = requests.get(
#         url,
#         auth=auth,
#         stream=True,
#         timeout=10,
#         verify=verify_ssl,
#     )
#
#     if response.status_code == HTTPStatus.UNAUTHORIZED:
#         # If unauthorized, try again using digest auth
#         if authentication == HTTP_BASIC_AUTHENTICATION:
#             return validate_url(
#                 url, username, password, verify_ssl, HTTP_DIGEST_AUTHENTICATION
#             )
#         raise InvalidAuth
#
#     response.raise_for_status()
#     response.close()
#
#     return authentication
#

async def async_validate_input(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[dict[str, str], str]:
    """Manage MJPEG IP Camera options."""
    errors = {}
    return errors

    # field = "base"
    # # authentication = HTTP_BASIC_AUTHENTICATION
    # try:
    #     for field in (CONF_IP_ADDRESS,):
    #         if not (url := user_input.get(field)):
    #             continue
    #         # authentication = await hass.async_add_executor_job(
    #         #     validate_url,
    #         #     url,
    #         #     user_input.get(CONF_USERNAME),
    #         #     user_input[CONF_PASSWORD],
    #         #     user_input[CONF_VERIFY_SSL],
    #         # )
    # except InvalidAuth:
    #     errors["username"] = "invalid_auth"
    # except (OSError, HTTPError, Timeout):
    #     LOGGER.exception("Cannot connect to %s", user_input[CONF_IP_ADDRESS])
    #     errors[field] = "cannot_connect"
    #
    # return (errors, authentication)


class PPPPCameraFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for PPPP Camera."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> PPPPCameraFlowHandler:
        """Get the options flow for this handler."""
        return PPPPCameraOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await async_validate_input(self.hass, user_input)
            if not errors:
                self._async_abort_entries_match(
                    {CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS]}
                )

                # Storing data in option, to allow for changing them later
                # using an options flow.
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, user_input[CONF_IP_ADDRESS]),
                    data={},
                    options={
                        # CONF_AUTHENTICATION: authentication,
                        CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                        # CONF_PASSWORD: user_input[CONF_PASSWORD],
                        # CONF_STILL_IMAGE_URL: user_input.get(CONF_STILL_IMAGE_URL),
                        # CONF_USERNAME: user_input.get(CONF_USERNAME),
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
            errors = await async_validate_input(self.hass, user_input)
            if not errors:
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    if (
                        entry.entry_id != self.config_entry.entry_id
                        and entry.options[CONF_IP_ADDRESS] == user_input[CONF_IP_ADDRESS]
                    ):
                        errors = {CONF_IP_ADDRESS: "already_configured"}

                if not errors:
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, user_input[CONF_IP_ADDRESS]),
                        data={
                            # CONF_AUTHENTICATION: authentication,
                            CONF_IP_ADDRESS: user_input[CONF_IP_ADDRESS],
                            # CONF_PASSWORD: user_input[CONF_PASSWORD],
                            # CONF_STILL_IMAGE_URL: user_input.get(CONF_STILL_IMAGE_URL),
                            # CONF_USERNAME: user_input.get(CONF_USERNAME),
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
