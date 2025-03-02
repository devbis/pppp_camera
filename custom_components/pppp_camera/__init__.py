"""The MJPEG IP Camera integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
# from homeassistant.helpers.typing import ConfigType

from .camera import PPPPCamera
from .button import RebootButton
from .const import DOMAIN, PLATFORMS

# from .const import CONF_MJPEG_URL, CONF_STILL_IMAGE_URL, DOMAIN, PLATFORMS
# from .util import filter_urllib3_logging

__all__ = [
    # "CONF_MJPEG_URL",
    # "CONF_STILL_IMAGE_URL",
    "PPPPCamera",
    "RebootButton",
    # "filter_urllib3_logging",
]

from .device import PPPPDevice

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


# async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#     """Set up the PPPP Camera integration."""
#     # filter_urllib3_logging()
#     return True


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

    device.platforms = [Platform.BUTTON, Platform.CAMERA]
    # device.platforms = [Platform.CAMERA]

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
