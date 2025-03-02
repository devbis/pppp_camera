"""Support for IP Cameras."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from functools import cached_property

import aiopppp
import voluptuous as vol
from aiohttp import web
from aiopppp import NotConnectedError
from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    # CONF_VERIFY_SSL,
    # HTTP_BASIC_AUTHENTICATION,
    # HTTP_DIGEST_AUTHENTICATION,
    # CONF_IP_ADDRESS,
    # CONF_HOST,
    # CONF_AUTHENTICATION,
    # CONF_PASSWORD,
    # CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform

# from homeassistant.helpers.aiohttp_client import (
#     async_aiohttp_proxy_web,
#     async_get_clientsession,
# )
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import uuid

# from homeassistant.helpers.httpx_client import get_async_client
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
    # ATTR_MOVE_MODE, RELATIVE_MOVE, CONTINUOUS_MOVE, ABSOLUTE_MOVE, GOTOPRESET_MOVE, STOP_MOVE,
    # ATTR_CONTINUOUS_DURATION, ATTR_PRESET,
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


async def async_extract_image_from_mjpeg(stream: AsyncIterator[bytes]) -> bytes | None:
    """Take in a MJPEG stream object, return the jpg from it."""
    data = b""

    async for chunk in stream:
        data += chunk
        jpg_end = data.find(b"\xff\xd9")

        if jpg_end == -1:
            continue

        jpg_start = data.find(b"\xff\xd8")

        if jpg_start == -1:
            continue

        return data[jpg_start : jpg_end + 2]

    return None


class PPPPCamera(PPPPBaseEntity, Camera):
    """An implementation of a PPPP camera."""
    _attr_is_streaming = True

    def __init__(self, device: PPPPDevice) -> None:
    #     self,
    #     *,
    #     name: str | None = None,
    #     ip_address: str,
    #     # still_image_url: str | None,
    #     # authentication: str | None = None,
    #     username: str | None = None,
    #     password: str = "",
    #     # verify_ssl: bool = True,
    #     unique_id: str | None = None,
    #     device_info: DeviceInfo | None = None,
    # ) -> None:
        """Initialize a PPPP camera."""
        PPPPBaseEntity.__init__(self, device)
        Camera.__init__(self)

        self._attr_name = self.device.dev_id
        # self._authentication = authentication
        # self._camera_session = None
        self._camera_found = asyncio.Event()
        # self._still_image_url = still_image_url

        # self._auth = None
        # if (
        #     self._username
        #     and self._password
        #     and self._authentication == HTTP_BASIC_AUTHENTICATION
        # ):
        #     self._auth = aiohttp.BasicAuth(self._username, password=self._password)
        # self._verify_ssl = verify_ssl

        # if unique_id is not None:
        self._attr_unique_id = self.device.dev_id
        # if device_info is not None:
        #     self._attr_device_info = device_info

    @cached_property
    def use_stream_for_stills(self) -> bool:
        """Whether to use stream to generate stills."""
        return False

    async def stream_source(self) -> str:
        """Return the stream source."""

        LOGGER.error('getting stream_source()')
        return f'pppp://{self.device.host}'
        # url = URL(self._mjpeg_url)
        # if self._username:
        #     url = url.with_user(self._username)
        # if self._password:
        #     url = url.with_password(self._password)
        # return str(url)

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        LOGGER.info('Getting camera image')
        await self.instantiate_session()
        video_streaming = self.device.device.is_video_requested

        if not video_streaming:
            await self.device.device.start_video()
        LOGGER.info('Getting camera image')
        image_frame = await self.device.device.get_video_frame()
        if not video_streaming:
            await self.device.device.stop_video()
        return image_frame and image_frame.data

        # response = web.StreamResponse()
        # boundary = '--frame' + uuid.random_uuid_hex()
        # response.content_type = f'multipart/x-mixed-replace; boundary={boundary}'
        # response.content_length = 1000000000000
        # await response.prepare(request)
        #
        #
        # return await self._async_digest_or_fallback_camera_image()
        #
        # websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
        # try:
        #     async with asyncio.timeout(TIMEOUT):
        #         response = await websession.get(self._still_image_url, auth=self._auth)
        #
        #         return await response.read()
        #
        # except TimeoutError:
        #     LOGGER.error("Timeout getting camera image from %s", self.name)
        #
        # except aiohttp.ClientError as err:
        #     LOGGER.error("Error getting new camera image from %s: %s", self.name, err)
        #
        # return None

    # def _get_httpx_auth(self) -> httpx.Auth:
    #     """Return a httpx auth object."""
    #     username = "" if self._username is None else self._username
    #     digest_auth = self._authentication == HTTP_DIGEST_AUTHENTICATION
    #     cls = httpx.DigestAuth if digest_auth else httpx.BasicAuth
    #     return cls(username, self._password)

    # async def _async_digest_or_fallback_camera_image(self) -> bytes | None:
    #     """Return a still image response from the camera using digest authentication."""
    #     client = get_async_client(self.hass, verify_ssl=self._verify_ssl)
    #     auth = self._get_httpx_auth()
    #     try:
    #         if self._still_image_url:
    #             # Fallback to MJPEG stream if still image URL is not available
    #             with suppress(TimeoutError, httpx.HTTPError):
    #                 return (
    #                     await client.get(
    #                         self._still_image_url, auth=auth, timeout=TIMEOUT
    #                     )
    #                 ).content
    #
    #         async with client.stream(
    #             "get", self._mjpeg_url, auth=auth, timeout=TIMEOUT
    #         ) as stream:
    #             return await async_extract_image_from_mjpeg(
    #                 stream.aiter_bytes(BUFFER_SIZE)
    #             )
    #
    #     except TimeoutError:
    #         LOGGER.error("Timeout getting camera image from %s", self.name)
    #
    #     except httpx.HTTPError as err:
    #         LOGGER.error("Error getting new camera image from %s: %s", self.name, err)
    #
    #     return None

    # async def _handle_async_pppp_mjpeg_stream(
    #     self, request: web.Request
    # ) -> web.StreamResponse | None:
    #
    #     """Generate an HTTP MJPEG stream from the camera using digest authentication."""
    #     async with get_async_client(self.hass, verify_ssl=self._verify_ssl).stream(
    #         "get", self._mjpeg_url, auth=self._get_httpx_auth(), timeout=TIMEOUT
    #     ) as stream:
    #         response = web.StreamResponse(headers=stream.headers)
    #         await response.prepare(request)
    #         # Stream until we are done or client disconnects
    #         with suppress(TimeoutError, httpx.HTTPError):
    #             async for chunk in stream.aiter_bytes(BUFFER_SIZE):
    #                 if not self.hass.is_running:
    #                     break
    #                 async with asyncio.timeout(TIMEOUT):
    #                     await response.write(chunk)
    #     return response

    # def on_device_found(self, camera: aiopppp.types.Device):
    #     LOGGER.info('Device %s found', camera.dev_id)
    #     # self._camera_device = camera
    #     self._camera_found.set()

    # def on_device_disconnect(self, camera: aiopppp.types.Device):
    #     LOGGER.info('Device %s disconnected', camera.dev_id)
    #     self._camera_found.clear()
    #     if self._camera_session:
    #         self._camera_session = None
    #     if self._discovery_task:
    #         self._discovery_task.cancel()
    #         with suppress(asyncio.CancelledError):
    #             self._discovery_task.result()
    #         self._discovery_task = None

    async def instantiate_session(self):
        if not self.device.device.is_connected:
            await self.device.device.connect()

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Generate an HTTP MJPEG stream from the camera."""
        await self.instantiate_session()
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
                except (asyncio.TimeoutError, NotConnectedError) as err:
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
            self._camera_found.clear()
            await self.device.device.close()
            return response

        # # aiohttp don't support DigestAuth so we use httpx
        # if self._authentication == HTTP_DIGEST_AUTHENTICATION:
        #     return await self._handle_async_mjpeg_digest_stream(request)

        # connect to stream
        # websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
        # stream_coro = websession.get(self._mjpeg_url, auth=self._auth)
        #
        # return await async_aiohttp_proxy_web(self.hass, request, stream_coro)

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
