from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .device import PPPPDevice


class PPPPBaseEntity(Entity):
    """Base class common to all PPPP entities."""

    def __init__(self, device: PPPPDevice) -> None:
        """Initialize the PPPP entity."""
        self.device: PPPPDevice = device

    @property
    def available(self):
        """Return True if device is available."""
        return self.device.available

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""

        camera_properties = self.device.device.properties
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.dev_id)},
            hw_version=camera_properties.get('mcuver'),
            sw_version=camera_properties.get('sysver'),
            model=self.device.dev_id,
            model_id=camera_properties.get('sensor'),
        )
