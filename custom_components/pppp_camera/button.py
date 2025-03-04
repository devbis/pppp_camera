"""PPPP Buttons."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import PPPPDevice
from .entity import PPPPBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PPPP button based on a config entry."""
    device = hass.data[DOMAIN][config_entry.unique_id]
    async_add_entities([RebootButton(device)])  # , SetSystemDateAndTimeButton(device)])


class RebootButton(PPPPBaseEntity, ButtonEntity):
    """Defines a PPPP reboot button."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: PPPPDevice) -> None:
        """Initialize the button entity."""
        super().__init__(device)
        self._attr_name = f"{self.device.dev_id} Reboot"
        self._attr_unique_id = f"{self.device.dev_id}_reboot"

    async def async_press(self) -> None:
        """Send out a SystemReboot command."""
        if self.device.device.is_connected:
            await self.device.device.reboot()
        else:
            async with self.device.device as device:
                await device.reboot()


# class SetSystemDateAndTimeButton(PPPPBaseEntity, ButtonEntity):
#     """Defines a PPPP SetSystemDateAndTime button."""
#
#     _attr_entity_category = EntityCategory.CONFIG
#
#     def __init__(self, device: PPPPDevice) -> None:
#         """Initialize the button entity."""
#         super().__init__(device)
#         self._attr_name = f"{self.device.dev_id} Set System Date and Time"
#         self._attr_unique_id = f"{self.device.dev_id}_setsystemdatetime"
#
#     async def async_press(self) -> None:
#         """Send out a SetSystemDateAndTime command."""
#         await self.device.async_manually_set_date_and_time()
