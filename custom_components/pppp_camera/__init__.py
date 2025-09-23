"""The PPPP IP Camera integration."""

import select
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .camera import PPPPCamera
from .const import DOMAIN, PLATFORMS

__all__ = [
    "PPPPCamera",
]

from .device import PPPPDevice

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional("default_username", default="admin"): cv.string,
                vol.Optional("default_password", default="6666"): cv.string,
                vol.Optional("lamp_entity_type", default="switch"): vol.In(["switch", "light", "button"]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # init storage for registries
    hass.data[DOMAIN] = {}

    # load optional global registry config
    if DOMAIN in config:
        conf = config[DOMAIN]
        hass.data[DOMAIN]["config"] = conf

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    device = PPPPDevice(hass, config_entry)
    try:
        await device.async_setup()
    except TimeoutError as err:
        await device.device.close()
        raise ConfigEntryNotReady(
            f"Could not connect to camera {device.device.ip_address}: {err}"
        ) from err

    hass.data[DOMAIN][config_entry.unique_id] = device

    device.platforms = [Platform.CAMERA, Platform.BUTTON, Platform.LIGHT, Platform.SWITCH]

    # if 'lamp' in device.device.properties:
    #     # Get lamp_entity_type from config.yaml
    #     lamp_type = hass.data[DOMAIN].get("config", {}).get("lamp_entity_type", "switch")

    #     match lamp_type:
    #         case "light":
    #             device.platforms += [Platform.LIGHT]
    #         case "button":
    #             device.platforms += [Platform.BUTTON]
    #         case "switch":
    #             device.platforms += [Platform.SWITCH]

    await hass.config_entries.async_forward_entry_setups(config_entry, device.platforms)

    # Reload entry when its updated.
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))
    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, device.async_stop)
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)
