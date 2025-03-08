"""Support for IP Cameras."""

from __future__ import annotations

import asyncio
from functools import cached_property

import aiopppp
import voluptuous as vol
from aiohttp import web
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import uuid

from .const import (
    ATTR_PAN,
    ATTR_TILT,
    DIR_DOWN,
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
    DOMAIN,
    LOGGER,
    SERVICE_PTZ,
    # ATTR_MOVE_MODE,
    # RELATIVE_MOVE,
    # CONTINUOUS_MOVE,
    # ABSOLUTE_MOVE,
    # GOTOPRESET_MOVE,
    # STOP_MOVE,
    # ATTR_CONTINUOUS_DURATION,
    # ATTR_PRESET,
    SERVICE_REBOOT,
)
from .device import PPPPDevice
from .entity import PPPPBaseEntity

TIMEOUT = 30
# BUFFER_SIZE = 102400


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a PPPP Camera based on a config entry."""

    device: PPPPDevice = hass.data[DOMAIN][config_entry.unique_id]

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_PTZ,
        {
            vol.Optional(ATTR_PAN): vol.In([DIR_LEFT, DIR_RIGHT]),
            vol.Optional(ATTR_TILT): vol.In([DIR_UP, DIR_DOWN]),
            # vol.Optional(ATTR_ZOOM): vol.In([ZOOM_OUT, ZOOM_IN]),
            # vol.Optional(ATTR_DISTANCE, default=0.1): cv.small_float,
            # vol.Optional(ATTR_SPEED, default=0.5): cv.small_float,
            # vol.Optional(ATTR_MOVE_MODE, default=RELATIVE_MOVE): vol.In(
            #     [
            #         CONTINUOUS_MOVE,
            #         RELATIVE_MOVE,
            #         ABSOLUTE_MOVE,
            #         GOTOPRESET_MOVE,
            #         STOP_MOVE,
            #     ]
            # ),
            # vol.Optional(ATTR_CONTINUOUS_DURATION, default=0.5): cv.small_float,
            # vol.Optional(ATTR_PRESET, default="0"): cv.string,
        },
        "async_perform_ptz",
    )
    platform.async_register_entity_service(
        SERVICE_REBOOT,
        None,
        "async_perform_reboot",
    )

    async_add_entities([PPPPCamera(device)])

# async def async_extract_image_from_mjpeg(stream: AsyncIterator[bytes]) -> bytes | None:
#     """Take in a MJPEG stream object, return the jpg from it."""
#     data = b""
#
#     async for chunk in stream:
#         data += chunk
#         jpg_end = data.find(b"\xff\xd9")
#
#         if jpg_end == -1:
#             continue
#
#         jpg_start = data.find(b"\xff\xd8")
#
#         if jpg_start == -1:
#             continue
#
#         return data[jpg_start : jpg_end + 2]
#
#     return None


class PPPPCamera(PPPPBaseEntity, Camera):
    """An implementation of a PPPP camera."""
    _attr_is_streaming = True

    def __init__(self, device: PPPPDevice) -> None:
        """Initialize a PPPP camera."""
        PPPPBaseEntity.__init__(self, device)
        Camera.__init__(self)

        self._attr_name = self.device.dev_id
        self._attr_unique_id = f'{self.device.dev_id}_camera'

    @cached_property
    def use_stream_for_stills(self) -> bool:
        """Whether to use stream to generate stills."""
        return False

    # async def stream_source(self) -> str:
    #     """Return the stream source."""
    #
    #     return None  # must be None as it doesn't expose any urls

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        LOGGER.info('Getting camera image')
        async with self.device.ensure_connected():
            video_streaming = self.device.device.is_video_requested

            if not video_streaming:
                await self.device.device.start_video()
            LOGGER.info('Getting camera image')
            image_frame = await self.device.device.get_video_frame()
            if not video_streaming:
                await self.device.device.stop_video()
        return image_frame and image_frame.data

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Generate an HTTP MJPEG stream from the camera."""
        async with self.device.ensure_connected():
            LOGGER.info(f'{self.device.device.is_video_requested=}')
            if not self.device.device.is_video_requested:
                await self.device.device.start_video()

            response = web.StreamResponse()
            boundary = '--frame' + uuid.random_uuid_hex()
            response.content_type = f'multipart/x-mixed-replace; boundary={boundary}'
            response.content_length = 1000000000000
            await response.prepare(request)

            try:
                while True:
                    try:
                        frame = await asyncio.wait_for(self.device.device.get_video_frame(), timeout=10)
                    except (asyncio.TimeoutError, aiopppp.NotConnectedError) as err:
                        LOGGER.warning('Error getting video frame: %s %s', err, type(err))
                        break
                    if not frame:
                        LOGGER.warning('Error getting video frame: empty frame')
                        break
                    header = f'--{boundary}\r\n'.encode()
                    header += b'Content-Length: %d\r\n' % len(frame.data)
                    header += b'Content-Type: image/jpeg\r\n\r\n'

                    try:
                        await response.write(header)
                        await response.write(frame.data)
                    except (TimeoutError, ConnectionResetError):
                        break
            finally:
                LOGGER.info('%s camera stream closed', self.name)
                return response

    async def async_perform_ptz(
        self,
        # distance,
        # speed,
        # move_mode,
        # continuous_duration,
        # preset,
        pan=None,
        tilt=None,
        # zoom=None,
    ) -> None:
        """Perform a PTZ action on the camera."""
        async with self.device.ensure_connected():
            if pan:
                await self.device.device.session.step_rotate(pan)
            elif tilt:
                await self.device.device.session.step_tilt(tilt)

        # await self.device.async_perform_ptz(
        #     self.profile,
        #     distance,
        #     speed,
        #     move_mode,
        #     continuous_duration,
        #     preset,
        #     pan,
        #     tilt,
        #     zoom,
        # )

    async def async_perform_reboot(
            self,
    ) -> None:
        """Perform a PTZ action on the camera."""
        await self.device.device.session.reboot()
