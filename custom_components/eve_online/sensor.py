"""Sensor platform for EVE Online integration."""
import logging
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up EVE Online sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        EVECharacterSensor(coordinator),
        EVEWalletSensor(coordinator),
        EVESPSensor(coordinator),
        EVESkillQueueSensor(coordinator),
        EVEMarketOrdersSensor(coordinator),
        EVECorporationSensor(coordinator),
        EVESecurityStatusSensor(coordinator),
        EVEPortraitSensor(coordinator),
        EVEOnlineSensor(coordinator),
        EVEShipSensor(coordinator),
        EVESystemSensor(coordinator),
        EVEFatigueSensor(coordinator),
        EVEOmegaSensor(coordinator),
    ]

    async_add_entities(entities)


def _format_isk(amount):
    """Format ISK amount."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "0 ISK"
    if amount >= 1_000_000_000:
        return f"{amount / 1_000_000_000:.2f} B ISK"
    elif amount >= 1_000_000:
        return f"{amount / 1_000_000:.2f} M ISK"
    elif amount >= 1_000:
        return f"{amount / 1_000:.2f} K ISK"
    return f"{amount:.2f} ISK"


def _format_skill_time(end_time_str):
    """Format skill end time to human readable."""
    try:
        end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        remaining = end_time - now
        if remaining.total_seconds() <= 0:
            return "Completed"
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "Unknown"


class EVEBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for EVE Online."""

    def __init__(self, coordinator):
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.character_id)},
            "name": f"EVE Online — {coordinator.character_id}",
            "manufacturer": "CCP Games",
            "model": "EVE Online Character",
        }


class EVECharacterSensor(EVEBaseSensor):
    """Character name sensor."""

    _attr_name = "EVE Character"
    _attr_icon = "mdi:account"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_character"

    @property
    def native_value(self):
        char = self.coordinator.data.get("character", {})
        return char.get("name", "Unknown")

    @property
    def extra_state_attributes(self):
        char = self.coordinator.data.get("character", {})
        return {
            "character_id": char.get("character_id"),
            "corporation_id": char.get("corporation_id"),
            "birthday": char.get("birthday"),
            "security_status": round(char.get("security_status", 0), 2),
        }


class EVEWalletSensor(EVEBaseSensor):
    """Wallet balance sensor."""

    _attr_name = "EVE Wallet"
    _attr_icon = "mdi:wallet"
    _attr_native_unit_of_measurement = "ISK"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_wallet"

    @property
    def native_value(self):
        return self.coordinator.data.get("wallet")

    @property
    def extra_state_attributes(self):
        wallet = self.coordinator.data.get("wallet")
        if wallet is not None:
            return {"formatted": _format_isk(wallet)}
        return {}


class EVESPSensor(EVEBaseSensor):
    """Total SP sensor."""

    _attr_name = "EVE Total SP"
    _attr_icon = "mdi:brain"
    _attr_native_unit_of_measurement = "SP"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_total_sp"

    @property
    def native_value(self):
        skills = self.coordinator.data.get("skills", {})
        return skills.get("total_sp", 0)

    @property
    def extra_state_attributes(self):
        skills = self.coordinator.data.get("skills", {})
        return {
            "total_sp_formatted": f"{skills.get('total_sp', 0):,} SP",
            "unallocated_sp": skills.get("unallocated_sp", 0),
        }


class EVESkillQueueSensor(EVEBaseSensor):
    """Skill queue sensor."""

    _attr_name = "EVE Skill Queue"
    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_skill_queue"

    @property
    def native_value(self):
        queue = self.coordinator.data.get("skill_queue", [])
        return len(queue)

    @property
    def extra_state_attributes(self):
        queue = self.coordinator.data.get("skill_queue", [])
        if not queue:
            return {"status": "Empty"}

        last_item = queue[-1]
        try:
            finish = datetime.fromisoformat(last_item["finish_date"].replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            is_active = finish > now
        except Exception:
            is_active = False

        return {
            "status": "Training" if is_active else "Idle",
            "time_remaining": _format_skill_time(last_item.get("finish_date", "")),
            "queue": [
                {
                    "skill_id": item.get("skill_id"),
                    "level": item.get("finished_level"),
                    "time_remaining": _format_skill_time(item.get("finish_date", "")),
                }
                for item in queue[:10]
            ],
        }


class EVEMarketOrdersSensor(EVEBaseSensor):
    """Market orders sensor."""

    _attr_name = "EVE Market Orders"
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_orders"

    @property
    def native_value(self):
        orders = self.coordinator.data.get("orders", [])
        active = [o for o in orders if o.get("state") == "open"]
        return len(active)

    @property
    def extra_state_attributes(self):
        orders = self.coordinator.data.get("orders", [])
        active = [o for o in orders if o.get("state") == "open"]
        buy = [o for o in active if o.get("is_buy_order")]
        sell = [o for o in active if not o.get("is_buy_order")]

        buy_value = sum(o.get("price", 0) * o.get("volume_remain", 0) for o in buy)
        sell_value = sum(o.get("price", 0) * o.get("volume_remain", 0) for o in sell)

        return {
            "total": len(orders),
            "active": len(active),
            "buy_orders": len(buy),
            "sell_orders": len(sell),
            "buy_value": _format_isk(buy_value),
            "sell_value": _format_isk(sell_value),
        }


class EVECorporationSensor(EVEBaseSensor):
    """Corporation sensor."""

    _attr_name = "EVE Corporation"
    _attr_icon = "mdi:domain"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_corporation"

    @property
    def native_value(self):
        corp = self.coordinator.data.get("corporation", {})
        return corp.get("name", "Unknown")

    @property
    def extra_state_attributes(self):
        corp = self.coordinator.data.get("corporation", {})
        return {
            "ticker": corp.get("ticker", ""),
            "member_count": corp.get("member_count", 0),
            "alliance_id": corp.get("alliance_id"),
        }


class EVESecurityStatusSensor(EVEBaseSensor):
    """Security status sensor."""

    _attr_name = "EVE Security Status"
    _attr_icon = "mdi:shield"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_security"

    @property
    def native_value(self):
        char = self.coordinator.data.get("character", {})
        return round(char.get("security_status", 0), 2)


class EVEPortraitSensor(EVEBaseSensor):
    """Character portrait with name."""

    _attr_name = "EVE Portrait"
    _attr_icon = "mdi:account-circle"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_portrait"

    @property
    def native_value(self):
        char = self.coordinator.data.get("character", {})
        return char.get("name", "Unknown")

    @property
    def entity_picture(self):
        portrait = self.coordinator.data.get("portrait", {})
        return portrait.get("px256x256")


class EVEOnlineSensor(EVEBaseSensor):
    """Online status sensor."""

    _attr_name = "EVE Online Status"
    _attr_icon = "mdi:account-check"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_online"

    @property
    def native_value(self):
        online = self.coordinator.data.get("online", {})
        return online.get("online", False)

    @property
    def extra_state_attributes(self):
        online = self.coordinator.data.get("online", {})
        attrs = {}
        last_login = online.get("last_login")
        last_logout = online.get("last_logout")
        if last_login:
            attrs["last_login"] = last_login
        if last_logout:
            attrs["last_logout"] = last_logout
        return attrs


class EVEShipSensor(EVEBaseSensor):
    """Current ship sensor."""

    _attr_name = "EVE Ship"
    _attr_icon = "mdi:rocket-launch"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_ship"

    @property
    def native_value(self):
        name = self.coordinator.data.get("ship_type_name")
        if name:
            return name
        ship = self.coordinator.data.get("ship", {})
        return ship.get("ship_name", "Unknown")

    @property
    def extra_state_attributes(self):
        ship = self.coordinator.data.get("ship", {})
        return {
            "ship_name": ship.get("ship_name", ""),
            "ship_type_id": ship.get("ship_type_id"),
        }


class EVESystemSensor(EVEBaseSensor):
    """Current solar system sensor."""

    _attr_name = "EVE System"
    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_system"

    @property
    def native_value(self):
        return self.coordinator.data.get("system_name", "Unknown")

    @property
    def extra_state_attributes(self):
        loc = self.coordinator.data.get("location", {})
        attrs = {}
        sys_id = loc.get("solar_system_id")
        if sys_id:
            attrs["solar_system_id"] = sys_id
        station_id = loc.get("station_id")
        if station_id:
            attrs["station_id"] = station_id
        structure_id = loc.get("structure_id")
        if structure_id:
            attrs["structure_id"] = structure_id
        return attrs


class EVEFatigueSensor(EVEBaseSensor):
    """Jump fatigue sensor."""

    _attr_name = "EVE Jump Fatigue"
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_fatigue"

    @property
    def native_value(self):
        fatigue = self.coordinator.data.get("fatigue", {})
        expiry = fatigue.get("jump_fatigue_expire_date")
        if not expiry:
            return "None"
        try:
            expire = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if expire <= now:
                return "None"
            remaining = expire - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            if remaining.days > 0:
                return f"{remaining.days}d {hours}h"
            return f"{hours}h {minutes}m"
        except Exception:
            return "Unknown"

    @property
    def extra_state_attributes(self):
        fatigue = self.coordinator.data.get("fatigue", {})
        return {
            "jump_fatigue_expire_date": fatigue.get("jump_fatigue_expire_date", ""),
            "last_jump_date": fatigue.get("last_jump_date", ""),
        }


class EVEOmegaSensor(EVEBaseSensor):
    """Omega/Alpha status sensor."""

    _attr_name = "EVE Account Status"
    _attr_icon = "mdi:crown"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.character_id}_omega"

    @property
    def native_value(self):
        implants = self.coordinator.data.get("implants", [])
        clones = self.coordinator.data.get("clones", {})
        jc = clones.get("jump_clones", [])

        # Omega has implants or multiple jump clones
        if implants and len(implants) > 0:
            return "Omega"
        if len(jc) > 1:
            return "Omega"
        # Alpha if we have data but no Omega signs
        if implants is not None and clones is not None:
            return "Alpha"
        return "Unknown"

    @property
    def extra_state_attributes(self):
        implants = self.coordinator.data.get("implants", [])
        clones = self.coordinator.data.get("clones", {})
        jc = clones.get("jump_clones", [])
        return {
            "implants_count": len(implants) if implants else 0,
            "jump_clones_count": len(jc) if jc else 0,
        }