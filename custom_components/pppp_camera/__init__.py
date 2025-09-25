"""The PPPP IP Camera integration."""

import select
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP,
    Platform,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PLATFORM,
    CONF_DISCOVERY,
    CONF_ENABLED,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .camera import PPPPCamera
from .discovery import async_start_discovery
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_DEFAULTS,
    CONF_IP,
    CONF_DURATION,
    CONF_INTERVAL,
    CONF_LAMP,
)


from .device import PPPPDevice

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_DEFAULTS, default={}): vol.Schema(
                    {
                        vol.Optional(CONF_USERNAME, default="admin"): cv.string,
                        vol.Optional(CONF_PASSWORD, default="6666"): cv.string,
                    }
                ),
                vol.Optional(CONF_PLATFORM, default={}): vol.Schema(
                    {
                        vol.Optional(CONF_LAMP, default=Platform.SWITCH): vol.In(
                            [Platform.SWITCH, Platform.LIGHT, Platform.BUTTON]
                        ),
                    }
                ),
                vol.Optional(CONF_DISCOVERY, default={}): vol.Schema(
                    {
                        vol.Optional(CONF_ENABLED, default=True): cv.boolean,
                        vol.Optional(CONF_DURATION, default=10): cv.positive_int,
                        vol.Optional(CONF_INTERVAL, default=600): cv.positive_int,
                        vol.Optional(CONF_IP): vol.Any(cv.string, [cv.string]),
                    }
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
"""
configuration.yaml example:

pppp_camera:
    defaults:
        username: admin
        password: 6666
    platform:
        lamp: switch    # switch or light, button
    discovery:
        enabled: true
        duration: 10    # seconds to listen for devices during each discovery
        interval: 600   # seconds between discovery attempts
        ip:             # list of IPs to limit discovery to
            - 192.168.1.1
            - 192.168.1.2
            - 192.168.1.3
        # or single IP can also be specified (usually broadcast address)
        ip: 192.168.1.255
        # if 'ip' is not specified, discovery will listen on all interfaces
"""


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    # init storage for registries
    hass.data[DOMAIN] = {}

    # load optional global registry config
    if DOMAIN in config:
        conf = config[DOMAIN]
        hass.data[DOMAIN]["config"] = conf

    await async_start_discovery(hass)

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

    device.platforms = [
        Platform.CAMERA,
        Platform.BUTTON,
        Platform.LIGHT,
        Platform.SWITCH,
    ]

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
