import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "pppp_camera"
PLATFORMS: Final = [Platform.CAMERA]

LOGGER = logging.getLogger(__package__)

ATTR_PAN = "pan"
ATTR_TILT = "tilt"
ATTR_MOVE_MODE = "move_mode"
ATTR_CONTINUOUS_DURATION = "continuous_duration"
ATTR_PRESET = "preset"

CONTINUOUS_MOVE = "ContinuousMove"
RELATIVE_MOVE = "RelativeMove"
ABSOLUTE_MOVE = "AbsoluteMove"
GOTOPRESET_MOVE = "GotoPreset"
STOP_MOVE = "Stop"

DIR_UP = "UP"
DIR_DOWN = "DOWN"
DIR_LEFT = "LEFT"
DIR_RIGHT = "RIGHT"

SERVICE_PTZ = "ptz"
SERVICE_REBOOT = "reboot"
