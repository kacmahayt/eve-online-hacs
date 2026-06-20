"""EVE Online integration for Home Assistant."""
import logging
import time
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_CHARACTER_ID,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REFRESH_TOKEN,
    ESI_BASE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EVE Online from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = EVEOnlineCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class EVEOnlineCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from ESI API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize."""
        self.entry = entry
        self.character_id = entry.data[CONF_CHARACTER_ID]
        self.client_id = entry.data[CONF_CLIENT_ID]
        self.client_secret = entry.data[CONF_CLIENT_SECRET]
        self.refresh_token = entry.data[CONF_REFRESH_TOKEN]
        self.access_token = entry.data.get("access_token")
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    async def _async_update_data(self):
        """Fetch data from ESI API."""
        # Refresh access token if needed
        if not self.access_token:
            await self._refresh_access_token()

        data = {}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }

        try:
            # Character info
            char_data = await self._esi_request(
                f"/characters/{self.character_id}/", headers
            )
            data["character"] = char_data

            # Portrait
            data["portrait"] = await self._esi_request(
                f"/characters/{self.character_id}/portrait/", headers
            )

            # Corporation
            corp_id = char_data.get("corporation_id")
            if corp_id:
                data["corporation"] = await self._esi_request(
                    f"/corporations/{corp_id}/", headers
                )

            # Wallet
            wallet = await self._esi_request(
                f"/characters/{self.character_id}/wallet/", headers
            )
            if wallet is not None:
                data["wallet"] = wallet

            # Skills
            skills = await self._esi_request(
                f"/characters/{self.character_id}/skills/", headers
            )
            if skills is not None:
                data["skills"] = skills

            # Skill queue
            queue = await self._esi_request(
                f"/characters/{self.character_id}/skillqueue/", headers
            )
            if queue is not None:
                data["skill_queue"] = queue

            # Market orders
            orders = await self._esi_request(
                f"/characters/{self.character_id}/orders/", headers
            )
            if orders is not None:
                data["orders"] = orders

            # Online status
            online = await self._esi_request(
                f"/characters/{self.character_id}/online/", headers
            )
            if online is not None:
                data["online"] = online

            # Ship
            ship = await self._esi_request(
                f"/characters/{self.character_id}/ship/", headers
            )
            if ship is not None:
                data["ship"] = ship
                ship_type_id = ship.get("ship_type_id")
                if ship_type_id:
                    type_name = await self._esi_request(
                        f"/universe/types/{ship_type_id}/", headers
                    )
                    if type_name:
                        data["ship_type_name"] = type_name.get("name", "Unknown")

            # Location (solar system)
            location = await self._esi_request(
                f"/characters/{self.character_id}/location/", headers
            )
            if location is not None:
                data["location"] = location
                sys_id = location.get("solar_system_id")
                if sys_id:
                    sys_data = await self._esi_request(
                        f"/universe/systems/{sys_id}/", headers
                    )
                    if sys_data:
                        data["system_name"] = sys_data.get("name", "Unknown")

            # Jump fatigue
            fatigue = await self._esi_request(
                f"/characters/{self.character_id}/fatigue/", headers
            )
            if fatigue is not None:
                data["fatigue"] = fatigue

        except Exception as err:
            raise UpdateFailed(f"Error communicating with ESI: {err}")

        return data

    async def _esi_request(self, endpoint, headers):
        """Make an ESI API request with automatic token refresh on 401."""
        url = f"{ESI_BASE}{endpoint}"
        params = {"datasource": "tranquility"}

        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 401:
                await self._refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                async with self.session.get(url, headers=headers, params=params) as resp2:
                    if resp2.status == 200:
                        return await resp2.json()
                    return None
            elif resp.status == 200:
                return await resp.json()
            return None

    async def _refresh_access_token(self):
        """Refresh OAuth2 access token."""
        async with self.session.post(
            "https://login.eveonline.com/v2/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            auth=aiohttp.BasicAuth(self.client_id, self.client_secret),
        ) as resp:
            if resp.status != 200:
                raise UpdateFailed("Failed to refresh access token")
            token_data = await resp.json()
            self.access_token = token_data["access_token"]
            # Update config entry with new token
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={**self.entry.data, "access_token": self.access_token},
            )