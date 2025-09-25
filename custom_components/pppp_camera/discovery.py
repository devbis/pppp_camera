"""Discovery for PPPP cameras."""

import asyncio
from ipaddress import ip_network, ip_address
from typing import List

from aiopppp import Discovery, DeviceDescriptor
from homeassistant.config_entries import (
    SOURCE_INTEGRATION_DISCOVERY,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_DISCOVERY,
    CONF_ENABLED,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.discovery_flow import async_create_flow
from homeassistant.components import network

from .const import DOMAIN, LOGGER, CONF_IP, CONF_DURATION, CONF_INTERVAL
from .config_helpers import get_discovery_config


async def async_start_discovery(hass: HomeAssistant) -> None:
    """Start the background discovery process."""

    # Get discovery configuration
    discovery_config = get_discovery_config(hass)
    enabled = discovery_config.get(CONF_ENABLED, True)  # Default to enabled
    interval = discovery_config.get(CONF_INTERVAL, 600)  # Default to 10 minutes

    if not enabled:
        LOGGER.info("PPPP camera discovery is disabled in configuration")
        return

    async def discovery_loop() -> None:
        """Run discovery loop indefinitely."""
        while True:
            try:
                await PPPPDiscovery(hass).async_run_discovery()
            except Exception as err:
                LOGGER.error("Error during PPPP camera discovery: %s", err)
            await asyncio.sleep(interval)

    hass.loop.create_task(discovery_loop())


class PPPPDiscovery:
    """Class to manage PPPP camera discovery."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the discovery class."""
        self.hass = hass
        self.discovered_devices = set[str]()

    async def async_run_discovery(self) -> None:
        """Run PPPP camera discovery periodically."""

        # Get discovery configuration
        discovery_config = get_discovery_config(self.hass)
        duration = discovery_config.get(CONF_DURATION, 10)  # Default to 10 seconds
        custom_ips = discovery_config.get(CONF_IP)

        # Determine which IPs to use for discovery
        discovery_ips = (
            self._get_custom_ips(custom_ips)
            if custom_ips
            else await self._async_get_broadcast_ips()
        )

        if not discovery_ips:
            LOGGER.warning(
                "No discovery IPs found, PPPP camera discovery will not run."
            )
            return

        def device_callback(device: DeviceDescriptor):
            self._discovered_device_callback(device.addr, device.dev_id.dev_id)

        for ip in discovery_ips:
            LOGGER.info("Starting discovery on IP: %s", ip)

            discovery = Discovery(ip)
            task = asyncio.create_task(discovery.discover(device_callback, period=3))
            try:
                await asyncio.sleep(duration)
            finally:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    LOGGER.debug("Discovery task for IP %s cancelled", ip)

    def _discovered_device_callback(self, host: str, device_id: str) -> None:
        """Handle discovered PPPP camera device."""

        if device_id in self.discovered_devices:
            LOGGER.debug("Already discovered device ID %s, ignoring.", device_id)
            return

        LOGGER.info("Discovered PPPP camera at %s with device ID: %s", host, device_id)

        # Create a discovery flow using the proper helper
        discovery_info = {
            CONF_HOST: host,
            CONF_DEVICE_ID: device_id,
        }

        async_create_flow(
            self.hass,
            DOMAIN,
            context={"source": SOURCE_INTEGRATION_DISCOVERY},
            data=discovery_info,
        )

        self.discovered_devices.add(device_id)

    def _get_custom_ips(self, custom_ips) -> List[str]:
        """Process custom IP configuration into a list of valid IPs."""

        # Handle both string and list of strings
        if isinstance(custom_ips, str):
            custom_ips = [custom_ips]

        def is_valid_ip(ip_config: str) -> bool:
            """Check if IP address is valid."""
            try:
                ip_address(ip_config)
                return True
            except ValueError:
                LOGGER.warning(
                    "Invalid IP address in discovery configuration: %s", ip_config
                )
                return False

        # Filter valid IPs and log valid ones
        valid_ips = [ip for ip in custom_ips if is_valid_ip(ip)]

        if not valid_ips:
            LOGGER.error(
                "No valid IP addresses provided in configuration: %s", custom_ips
            )
            raise HomeAssistantError("No valid IP addresses provided in configuration")

        LOGGER.info("Using %d custom discovery IPs: %s", len(valid_ips), valid_ips)
        return valid_ips

    async def _async_get_broadcast_ips(self) -> List[str]:
        """Get broadcast IPs for all enabled HA network adapters."""
        broadcast_ips = []

        try:
            adapters = await network.async_get_adapters(self.hass)

            for adapter in adapters:
                # Skip disabled adapters
                if not adapter.get("enabled", False):
                    continue

                # Process IPv4 addresses only (broadcast is IPv4 concept)
                for ip_info in adapter.get("ipv4", []):
                    local_ip = ip_info["address"]
                    network_prefix = ip_info["network_prefix"]

                    try:
                        # Create IP network from address and prefix
                        ip_net = ip_network(
                            f"{local_ip}/{network_prefix}", strict=False
                        )

                        # Get broadcast address
                        broadcast_ip = str(ip_net.broadcast_address)

                        if broadcast_ip not in broadcast_ips:
                            broadcast_ips.append(broadcast_ip)
                            LOGGER.debug(
                                "Found broadcast IP %s for adapter %s (%s/%s)",
                                broadcast_ip,
                                adapter["name"],
                                local_ip,
                                network_prefix,
                            )

                    except ValueError as err:
                        LOGGER.warning(
                            "Failed to calculate broadcast IP for %s/%s on adapter %s: %s",
                            local_ip,
                            network_prefix,
                            adapter["name"],
                            err,
                        )

        except Exception as err:
            LOGGER.error("Failed to get network adapters: %s", err)
            raise HomeAssistantError(f"Failed to get broadcast IPs: {err}")

        if not broadcast_ips:
            LOGGER.error("No broadcast IPs found on any network adapters.")
            raise HomeAssistantError("No broadcast IPs found on any network adapters.")

        LOGGER.info("Found %d broadcast IPs: %s", len(broadcast_ips), broadcast_ips)
        return broadcast_ips
