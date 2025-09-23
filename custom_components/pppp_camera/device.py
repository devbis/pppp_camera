"""PPPP device abstraction."""

from __future__ import annotations

import asyncio
import contextlib

import aiopppp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant


class PPPPDevice:
    """Manages a PPPP device."""

    device: aiopppp.Device

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the device."""
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry
        self._original_options = dict(config_entry.options)
        self.available: bool = True
        self.info: dict = {}
        self.platforms: list[Platform] = []

        self._connected_num = 0
        self._dt_diff_seconds: float = 0

    async def _async_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle options update."""
        if self._original_options != entry.options:
            hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

    @property
    def host(self) -> str:
        """Return the host of this device."""
        return self.config_entry.options[CONF_HOST]

    @property
    def username(self) -> str:
        """Return the username of this device."""
        return self.config_entry.options.get(CONF_USERNAME)

    @property
    def password(self) -> str:
        """Return the password of this device."""
        return self.config_entry.options.get(CONF_PASSWORD)

    @property
    def dev_id(self) -> str:
        """Return the dev_id of this device."""
        return self.device.descriptor.dev_id.dev_id

    async def connect(self):
        """Connect to the device."""
        self._connected_num += 1
        if not self.device.is_connected:
            await self.device.connect()

    async def close(self):
        """Close the connection to the device."""
        if self.device._session is None or not self._connected_num:
            self._connected_num = 0
            return

        self._connected_num -= 1
        if self._connected_num == 0:
            await asyncio.sleep(1);
            await self.device.close()

    async def async_setup(self) -> None:
        """Set up the device."""
        self.device = get_device(
            self.hass,
            host=self.config_entry.options[CONF_HOST],
            username=self.config_entry.options[CONF_USERNAME],
            password=self.config_entry.options[CONF_PASSWORD],
        )

        async with self.ensure_connected():
            self.info = self.device.properties

        self.config_entry.async_on_unload(
            self.config_entry.add_update_listener(self._async_update_listener)
        )

    async def async_stop(self, event=None):
        """Shut it all down."""
        await self.device.close()

    async def async_white_light_toggle(self, data):
        """Turn on the white light."""
        async with self.ensure_connected():
            await self.device.session.toggle_whitelight(data)

    async def async_white_light_on(self, data):
        """Turn on the white light."""
        await self.async_white_light_toggle(1)

    async def async_white_light_off(self, data):
        """Turn on the white light."""
        await self.async_white_light_toggle(0)

    async def async_ir_light_toggle(self, data):
        """Turn on the white light."""
        async with self.ensure_connected():
            await self.device.session.toggle_ir(data)

    async def async_ir_light_on(self, data):
        """Turn on the white light."""
        await self.async_ir_light_toggle(1)

    async def async_ir_light_off(self, data):
        """Turn on the white light."""
        await self.async_ir_light_toggle(0)

    async def async_reboot(self, data) -> None:
        """Send out a SystemReboot command."""
        async with self.ensure_connected():
            await self.device.reboot()


    @contextlib.asynccontextmanager
    async def ensure_connected(self):
        """Ensure the device is connected."""
        await self.connect()
        try:
            yield self
        finally:
            await self.close()

    async def async_manually_set_date_and_time(self) -> None:
        """Set Date and Time Manually using SetSystemDateAndTime command."""
        pass

        # device_mgmt = await self.device.create_devicemgmt_service()
        #
        # # Retrieve DateTime object from camera to use as template for Set operation
        # device_time = await device_mgmt.GetSystemDateAndTime()
        #
        # system_date = dt_util.utcnow()
        # LOGGER.debug("System date (UTC): %s", system_date)
        #
        # dt_param = device_mgmt.create_type("SetSystemDateAndTime")
        # dt_param.DateTimeType = "Manual"
        # # Retrieve DST setting from system
        # dt_param.DaylightSavings = bool(time.localtime().tm_isdst)
        # dt_param.UTCDateTime = {
        #     "Date": {
        #         "Year": system_date.year,
        #         "Month": system_date.month,
        #         "Day": system_date.day,
        #     },
        #     "Time": {
        #         "Hour": system_date.hour,
        #         "Minute": system_date.minute,
        #         "Second": system_date.second,
        #     },
        # }
        # # Retrieve timezone from system
        # system_timezone = str(system_date.astimezone().tzinfo)
        # timezone_names: list[str | None] = [system_timezone]
        # if (time_zone := device_time.TimeZone) and system_timezone != time_zone.TZ:
        #     timezone_names.append(time_zone.TZ)
        # timezone_names.append(None)
        # timezone_max_idx = len(timezone_names) - 1
        # LOGGER.debug(
        #     "%s: SetSystemDateAndTime: timezone_names:%s", self.name, timezone_names
        # )
        # for idx, timezone_name in enumerate(timezone_names):
        #     dt_param.TimeZone = timezone_name
        #     LOGGER.debug("%s: SetSystemDateAndTime: %s", self.name, dt_param)
        #     try:
        #         await device_mgmt.SetSystemDateAndTime(dt_param)
        #         LOGGER.debug("%s: SetSystemDateAndTime: success", self.name)
        #     # Some cameras don't support setting the timezone and will throw an IndexError
        #     # if we try to set it. If we get an error, try again without the timezone.
        #     except (IndexError, Fault):
        #         if idx == timezone_max_idx:
        #             raise
        #     else:
        #         return

    async def async_check_date_and_time(self) -> None:
        """Warns if device and system date not synced."""

        pass
        # LOGGER.debug("%s: Setting up the ONVIF device management service", self.name)
        # device_mgmt = await self.device.create_devicemgmt_service()
        # system_date = dt_util.utcnow()
        #
        # LOGGER.debug("%s: Retrieving current device date/time", self.name)
        # try:
        #     device_time = await device_mgmt.GetSystemDateAndTime()
        # except RequestError as err:
        #     LOGGER.warning(
        #         "Couldn't get device '%s' date/time. Error: %s", self.name, err
        #     )
        #     return
        #
        # if not device_time:
        #     LOGGER.debug(
        #         """Couldn't get device '%s' date/time.
        #         GetSystemDateAndTime() return null/empty""",
        #         self.name,
        #     )
        #     return
        #
        # LOGGER.debug("%s: Device time: %s", self.name, device_time)
        #
        # tzone = dt_util.get_default_time_zone()
        # cdate = device_time.LocalDateTime
        # if device_time.UTCDateTime:
        #     tzone = dt_util.UTC
        #     cdate = device_time.UTCDateTime
        # elif device_time.TimeZone:
        #     tzone = await dt_util.async_get_time_zone(device_time.TimeZone.TZ) or tzone
        #
        # if cdate is None:
        #     LOGGER.warning("%s: Could not retrieve date/time on this camera", self.name)
        #     return
        #
        # try:
        #     cam_date = dt.datetime(
        #         cdate.Date.Year,
        #         cdate.Date.Month,
        #         cdate.Date.Day,
        #         cdate.Time.Hour,
        #         cdate.Time.Minute,
        #         cdate.Time.Second,
        #         0,
        #         tzone,
        #     )
        # except ValueError as err:
        #     LOGGER.warning(
        #         "%s: Could not parse date/time from camera: %s", self.name, err
        #     )
        #     return
        #
        # cam_date_utc = cam_date.astimezone(dt_util.UTC)
        #
        # LOGGER.debug(
        #     "%s: Device date/time: %s | System date/time: %s",
        #     self.name,
        #     cam_date_utc,
        #     system_date,
        # )
        #
        # dt_diff = cam_date - system_date
        # self._dt_diff_seconds = dt_diff.total_seconds()
        #
        # # It could be off either direction, so we need to check the absolute value
        # if abs(self._dt_diff_seconds) < 5:
        #     return
        #
        # if device_time.DateTimeType != "Manual":
        #     self._async_log_time_out_of_sync(cam_date_utc, system_date)
        #     return
        #
        # # Set Date and Time ourselves if Date and Time is set manually in the camera.
        # try:
        #     await self.async_manually_set_date_and_time()
        # except (RequestError, TransportError, IndexError, Fault):
        #     LOGGER.warning("%s: Could not sync date/time on this camera", self.name)
        #     self._async_log_time_out_of_sync(cam_date_utc, system_date)

    # @callback
    # def _async_log_time_out_of_sync(
    #     self, cam_date_utc: dt.datetime, system_date: dt.datetime
    # ) -> None:
    #     """Log a warning if the camera and system date/time are not synced."""
    #     LOGGER.warning(
    #         (
    #             "The date/time on %s (UTC) is '%s', "
    #             "which is different from the system '%s', "
    #             "this could lead to authentication issues"
    #         ),
    #         self.name,
    #         cam_date_utc,
    #         system_date,
    #     )


    # async def async_perform_ptz(
    #     self,
    #     profile: Profile,
    #     distance,
    #     speed,
    #     move_mode,
    #     continuous_duration,
    #     preset,
    #     pan=None,
    #     tilt=None,
    #     zoom=None,
    # ):
    #     """Perform a PTZ action on the camera."""
    #     if not self.capabilities.ptz:
    #         LOGGER.warning("PTZ actions are not supported on device '%s'", self.name)
    #         return
    #
    #     ptz_service = await self.device.create_ptz_service()
    #
    #     pan_val = distance * PAN_FACTOR.get(pan, 0)
    #     tilt_val = distance * TILT_FACTOR.get(tilt, 0)
    #     zoom_val = distance * ZOOM_FACTOR.get(zoom, 0)
    #     speed_val = speed
    #     preset_val = preset
    #     LOGGER.debug(
    #         (
    #             "Calling %s PTZ | Pan = %4.2f | Tilt = %4.2f | Zoom = %4.2f | Speed ="
    #             " %4.2f | Preset = %s"
    #         ),
    #         move_mode,
    #         pan_val,
    #         tilt_val,
    #         zoom_val,
    #         speed_val,
    #         preset_val,
    #     )
    #     try:
    #         req = ptz_service.create_type(move_mode)
    #         req.ProfileToken = profile.token
    #         if move_mode == CONTINUOUS_MOVE:
    #             # Guard against unsupported operation
    #             if not profile.ptz or not profile.ptz.continuous:
    #                 LOGGER.warning(
    #                     "ContinuousMove not supported on device '%s'", self.name
    #                 )
    #                 return
    #
    #             velocity = {}
    #             if pan is not None or tilt is not None:
    #                 velocity["PanTilt"] = {"x": pan_val, "y": tilt_val}
    #             if zoom is not None:
    #                 velocity["Zoom"] = {"x": zoom_val}
    #
    #             req.Velocity = velocity
    #
    #             await ptz_service.ContinuousMove(req)
    #             await asyncio.sleep(continuous_duration)
    #             req = ptz_service.create_type("Stop")
    #             req.ProfileToken = profile.token
    #             await ptz_service.Stop(
    #                 {"ProfileToken": req.ProfileToken, "PanTilt": True, "Zoom": False}
    #             )
    #         elif move_mode == RELATIVE_MOVE:
    #             # Guard against unsupported operation
    #             if not profile.ptz or not profile.ptz.relative:
    #                 LOGGER.warning(
    #                     "RelativeMove not supported on device '%s'", self.name
    #                 )
    #                 return
    #
    #             req.Translation = {
    #                 "PanTilt": {"x": pan_val, "y": tilt_val},
    #                 "Zoom": {"x": zoom_val},
    #             }
    #             req.Speed = {
    #                 "PanTilt": {"x": speed_val, "y": speed_val},
    #                 "Zoom": {"x": speed_val},
    #             }
    #             await ptz_service.RelativeMove(req)
    #         elif move_mode == ABSOLUTE_MOVE:
    #             # Guard against unsupported operation
    #             if not profile.ptz or not profile.ptz.absolute:
    #                 LOGGER.warning(
    #                     "AbsoluteMove not supported on device '%s'", self.name
    #                 )
    #                 return
    #
    #             req.Position = {
    #                 "PanTilt": {"x": pan_val, "y": tilt_val},
    #                 "Zoom": {"x": zoom_val},
    #             }
    #             req.Speed = {
    #                 "PanTilt": {"x": speed_val, "y": speed_val},
    #                 "Zoom": {"x": speed_val},
    #             }
    #             await ptz_service.AbsoluteMove(req)
    #         elif move_mode == GOTOPRESET_MOVE:
    #             # Guard against unsupported operation
    #             if not profile.ptz or not profile.ptz.presets:
    #                 LOGGER.warning(
    #                     "Absolute Presets not supported on device '%s'", self.name
    #                 )
    #                 return
    #             if preset_val not in profile.ptz.presets:
    #                 LOGGER.warning(
    #                     (
    #                         "PTZ preset '%s' does not exist on device '%s'. Available"
    #                         " Presets: %s"
    #                     ),
    #                     preset_val,
    #                     self.name,
    #                     ", ".join(profile.ptz.presets),
    #                 )
    #                 return
    #
    #             req.PresetToken = preset_val
    #             req.Speed = {
    #                 "PanTilt": {"x": speed_val, "y": speed_val},
    #                 "Zoom": {"x": speed_val},
    #             }
    #             await ptz_service.GotoPreset(req)
    #         elif move_mode == STOP_MOVE:
    #             await ptz_service.Stop(req)
    #     except ONVIFError as err:
    #         if "Bad Request" in err.reason:
    #             LOGGER.warning("Device '%s' doesn't support PTZ", self.name)
    #         else:
    #             LOGGER.error("Error trying to perform PTZ action: %s", err)


def get_device(
    hass: HomeAssistant,
    host: str,
    username: str | None,
    password: str | None,
) -> aiopppp.Device:
    """Get Device instance."""
    return aiopppp.Device(
        host,
        username=username,
        password=password,
    )
