"""Helpers for configuration handling."""

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_DISCOVERY, CONF_PLATFORM

from .const import CONF_DEFAULTS, DOMAIN


def get_config(hass: HomeAssistant) -> dict[str, Any]:
    """Get configuration for DOMAIN."""
    return hass.data.get(DOMAIN, {}).get("config", {})

def get_defaults(hass: HomeAssistant) -> dict[str, Any]:
    """Get configuration for DOMAIN."""
    return get_config(hass).get(CONF_DEFAULTS, {})

def get_discovery_config(hass: HomeAssistant) -> dict[str, Any]:
    """Get configuration for DOMAIN."""
    return get_config(hass).get(CONF_DISCOVERY, {})

def get_platform_config(hass: HomeAssistant) -> dict[str, Any]:
    """Get configuration for DOMAIN."""
    return get_config(hass).get(CONF_PLATFORM, {})
