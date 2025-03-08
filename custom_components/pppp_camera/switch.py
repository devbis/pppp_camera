"""PPPP switches for controlling cameras."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import PPPPDevice
from .entity import PPPPBaseEntity


@dataclass(frozen=True, kw_only=True)
class PPPPSwitchEntityDescription(SwitchEntityDescription):
    """Describes PPPP switch entity."""

    turn_on_fn: Callable[
        [PPPPDevice], Callable[[Any], Coroutine[Any, Any, None]]
    ]
    turn_off_fn: Callable[
        [PPPPDevice], Callable[[Any], Coroutine[Any, Any, None]]
    ]
    turn_on_data: Any
    turn_off_data: Any
    supported_fn: Callable[[PPPPDevice], bool]


SWITCHES: tuple[PPPPSwitchEntityDescription, ...] = (
    PPPPSwitchEntityDescription(
        key="white_lamp",
        translation_key="white_lamp",
        turn_on_data=None,
        turn_off_data=None,
        turn_on_fn=lambda device: device.async_white_light_on,
        turn_off_fn=lambda device: device.async_white_light_off,
        supported_fn=lambda device: True,
    ),
    PPPPSwitchEntityDescription(
        key="ir_lamp",
        translation_key="ir_lamp",
        turn_on_data=None,
        turn_off_data=None,
        turn_on_fn=lambda device: device.async_ir_light_on,
        turn_off_fn=lambda device: device.async_ir_light_off,
        supported_fn=lambda device: True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a PPPP switch platform."""
    device = hass.data[DOMAIN][config_entry.unique_id]

    async_add_entities(
        PPPPSwitch(device, description)
        for description in SWITCHES
        if description.supported_fn(device)
    )


class PPPPSwitch(PPPPBaseEntity, SwitchEntity):
    """A PPPP switch."""

    entity_description: PPPPSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self, device: PPPPDevice, description: PPPPSwitchEntityDescription
    ) -> None:
        """Initialize the switch."""
        super().__init__(device)

        self._attr_is_on = False
        self._attr_unique_id = f"{self.device.dev_id}_{description.key}"
        self._attr_name = description.translation_key
        self.entity_description = description

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on switch."""
        self._attr_is_on = True
        await self.entity_description.turn_on_fn(self.device)(
            self.entity_description.turn_on_data
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off switch."""
        self._attr_is_on = False
        await self.entity_description.turn_off_fn(self.device)(
            self.entity_description.turn_off_data
        )
