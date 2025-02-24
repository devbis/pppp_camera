"""Support for IP Cameras."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from functools import cached_property

from aiohttp import web
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.util import uuid
import aiopppp
import aiopppp.types

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    # CONF_AUTHENTICATION,
    CONF_PASSWORD,
    CONF_USERNAME,
    # CONF_VERIFY_SSL,
    # HTTP_BASIC_AUTHENTICATION,
    # HTTP_DIGEST_AUTHENTICATION,
    CONF_IP_ADDRESS, Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_aiohttp_proxy_web,
    async_get_clientsession,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.httpx_client import get_async_client

from .const import DOMAIN, LOGGER

TIMEOUT = 30
# BUFFER_SIZE = 102400


async def discover_camera(ip_address: str) -> aiopppp.types.Device:
    result = await aiopppp.connect(ip_address, timeout=TIMEOUT)
    LOGGER.info('Found %s', result and result.dev_id)
    return result


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a PPPP Camera based on a config entry."""

    device_address = entry.options[CONF_IP_ADDRESS]
    try:
        camera_info = await discover_camera(device_address)
        session = aiopppp.make_session(camera_info, on_device_lost=None)
        session.start()
        try:
            await session.device_is_ready.wait()
            # {'tz': -3, 'time': 3949367342, 'icut': 0, 'batValue': 90, 'batStatus': 1,
            #  'sysver': 'HQLS_HQT66DP_20240925 11:06:42', 'mcuver': '1.1.1.1', 'sensor': 'GC0329', 'isShow4KMenu': 0,
            #  'isShowIcutAuto': 1, 'rotmir': 0, 'signal': 100, 'lamp': 1}
            camera_properties = session.dev_properties
        finally:
            session.stop()
    except (asyncio.TimeoutError, TimeoutError) as ex:
        raise ConfigEntryNotReady(f"Timeout while connecting to {device_address}") from ex
    async_add_entities(
        [
            PPPPCamera(
                name=camera_info.dev_id.dev_id,
                username=entry.options.get(CONF_USERNAME),
                password=entry.options.get(CONF_PASSWORD),
                ip_address=device_address,
                # still_image_url=entry.options.get(CONF_STILL_IMAGE_URL),
                # verify_ssl=entry.options[CONF_VERIFY_SSL],
                unique_id=f'{camera_info.dev_id.dev_id}_{Platform.CAMERA.value}',
                device_info=DeviceInfo(
                    name=entry.title,
                    identifiers={(DOMAIN, entry.unique_id), },
                    hw_version=camera_properties.get('mcuver'),
                    sw_version=camera_properties.get('sysver'),
                    model=camera_info.dev_id.dev_id,
                    model_id=camera_properties.get('sensor'),
                ),
            )
        ]
    )

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


class PPPPCamera(Camera):
    """An implementation of a PPPP camera."""
    _attr_is_streaming = True

    def __init__(
        self,
        *,
        name: str | None = None,
        ip_address: str,
        # still_image_url: str | None,
        # authentication: str | None = None,
        username: str | None = None,
        password: str = "",
        # verify_ssl: bool = True,
        unique_id: str | None = None,
        device_info: DeviceInfo | None = None,
    ) -> None:
        """Initialize a MJPEG camera."""
        super().__init__()
        self._attr_name = name
        # self._authentication = authentication
        self._username = username
        self._password = password
        self._ip_address = ip_address
        self._discovery = None
        self._camera_device = None
        self._camera_session = None
        self._camera_found = asyncio.Event()
        self._discovery_task = None
        # self._still_image_url = still_image_url

        # self._auth = None
        # if (
        #     self._username
        #     and self._password
        #     and self._authentication == HTTP_BASIC_AUTHENTICATION
        # ):
        #     self._auth = aiohttp.BasicAuth(self._username, password=self._password)
        # self._verify_ssl = verify_ssl

        if unique_id is not None:
            self._attr_unique_id = unique_id
        if device_info is not None:
            self._attr_device_info = device_info

    @cached_property
    def use_stream_for_stills(self) -> bool:
        """Whether to use stream to generate stills."""
        return True

    async def stream_source(self) -> str:
        """Return the stream source."""

        return f'pppp://{self._ip_address}'
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

        await self._camera_session.device_is_ready.wait()
        video_streaming = self._camera_session.video_requested

        if not video_streaming:
            await self._camera_session.start_video()
        frame_buffer = self._camera_session.frame_buffer
        LOGGER.info('Getting camera image')
        image = await frame_buffer.get()
        LOGGER.info('Getting camera image: %s', image)
        if not video_streaming:
            await self._camera_session.stop_video()
        return image

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

    def on_device_found(self, camera: aiopppp.types.Device):
        LOGGER.info('Device %s found', camera.dev_id)
        self._camera_device = camera
        self._camera_found.set()

    def on_device_disconnect(self, camera: aiopppp.types.Device):
        LOGGER.info('Device %s disconnected', camera.dev_id)
        self._camera_found.clear()
        if self._camera_session:
            self._camera_session = None
        if self._discovery_task:
            self._discovery_task.cancel()
            with suppress(asyncio.CancelledError):
                self._discovery_task.result()
            self._discovery_task = None

    async def instantiate_session(self):
        if not self._discovery:
            self._discovery = aiopppp.Discovery(remote_addr=self._ip_address)
        if not self._discovery_task:
            self._discovery_task = asyncio.create_task(self._discovery.discover(self.on_device_found))
        if not self._camera_session:
            await self._camera_found.wait()
            self._camera_session = aiopppp.make_session(
                self._camera_device,
                login=self._username,
                password=self._password,
                on_device_lost=self.on_device_disconnect,
            )
            self._camera_session.start()

    async def handle_async_mjpeg_stream(
        self, request: web.Request
    ) -> web.StreamResponse | None:
        """Generate an HTTP MJPEG stream from the camera."""
        await self.instantiate_session()
        await self._camera_session.device_is_ready.wait()

        if not self._camera_session.video_requested:
            await self._camera_session.start_video()

        response = web.StreamResponse()
        boundary = '--frame' + uuid.random_uuid_hex()
        response.content_type = f'multipart/x-mixed-replace; boundary={boundary}'
        response.content_length = 1000000000000
        await response.prepare(request)

        frame_buffer = self._camera_session.frame_buffer

        try:
            while True:
                try:
                    frame = await asyncio.wait_for(frame_buffer.get(), timeout=10)
                except asyncio.TimeoutError:
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
            await asyncio.shield(self._camera_session.stop_video())
            self._camera_session.stop()
            self._camera_session = None
            return response

        # # aiohttp don't support DigestAuth so we use httpx
        # if self._authentication == HTTP_DIGEST_AUTHENTICATION:
        #     return await self._handle_async_mjpeg_digest_stream(request)

        # connect to stream
        # websession = async_get_clientsession(self.hass, verify_ssl=self._verify_ssl)
        # stream_coro = websession.get(self._mjpeg_url, auth=self._auth)
        #
        # return await async_aiohttp_proxy_web(self.hass, request, stream_coro)
