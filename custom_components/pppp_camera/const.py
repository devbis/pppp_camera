import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "pppp_camera"
PLATFORMS: Final = [Platform.CAMERA]

LOGGER = logging.getLogger(__package__)
