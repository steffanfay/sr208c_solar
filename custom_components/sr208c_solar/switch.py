import logging
import functools
import asyncio
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C switch platform via the central data coordinator."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    # Create or reuse a shared lock for connector access across entities
    lock = hass.data[DOMAIN][entry.entry_id].get("connector_lock")
    if lock is None:
        lock = hass.data[DOMAIN][entry.entry_id]["connector_lock"] = asyncio.Lock()

    for device_id in device_ids:
        entities.append(SR208CSystemSwitch(coordinator, connector, device_id, lock))
        
    async_add_entities(entities, False)

class SR208CSystemSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the main SR208C power switch tracking via Coordinator."""

    def __init__(self, coordinator, connector, device_id, lock: asyncio.Lock):
        """Initialize the switch module linked directly to the data loop."""
        super().__init__(coordinator)
        self._connector = connector
        self._device_id = device_id
        self._lock = lock
        
        # Unique identifying parameters for the Home Assistant entity registry
        self._attr_name = "Heater Relay State HR"
        self._attr_unique_id = f"{device_id}_switch_main"
        self._attr_icon = "mdi:water-boiler"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)}, # Links entities sharing this exact ID
            name="SR208C Solar Water Heater",
            manufacturer="Sunsun / Wililo",          # The manufacturing parent standard
            model="SR208C",
            sw_version="Tuya Wi-Fi v1.0",
        )

    @property
    def is_on(self) -> bool:
        """Extract the real-time switch status directly from coordinator memory cache."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        # Check by code name string first, fall back to literal index if mapped by number
        val = device_data.get("switch")
        if val is None:
            val = device_data.get("1")  # Common alternate numeric DP index mapping for main switches
            
        return bool(val)

    async def async_turn_on(self, **kwargs) -> None:
        """Fire a secure command to change state on the background executor thread."""
        payload = {
            "commands": [
                {
                    "code": "switch",
                    "value": True
                }
            ]
        }
        try:
            # Serialize access to connector to avoid concurrent blocking calls
            async with self._lock:
                response = await self.hass.async_add_executor_job(
                    functools.partial(
                        self._connector.post,
                        f"/v1.0/iot-03/devices/{self._device_id}/commands",
                        payload,
                    )
                )
            if not response or not response.get("success"):
                _LOGGER.error("Tuya Cloud rejected the switch mutation payload execution: %s", response)
        except Exception as err:
            _LOGGER.error("Failed to commit network switch change to SR208C panel hardware: %s", err)
        
        # Optimistically update the internal state registry cache locally for responsiveness
        device_data = self.coordinator.data.setdefault(self._device_id, {})
        device_data["switch"] = True
        device_data["1"] = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Fire a secure command to change state on the background executor thread."""
        payload = {
            "commands": [
                {
                    "code": "switch",
                    "value": False
                }
            ]
        }
        try:
            # Serialize access to connector to avoid concurrent blocking calls
            async with self._lock:
                response = await self.hass.async_add_executor_job(
                    functools.partial(
                        self._connector.post,
                        f"/v1.0/iot-03/devices/{self._device_id}/commands",
                        payload,
                    )
                )
            if not response or not response.get("success"):
                _LOGGER.error("Tuya Cloud rejected the switch mutation payload execution: %s", response)
        except Exception as err:
            _LOGGER.error("Failed to commit network switch change to SR208C panel hardware: %s", err)
        
        # Optimistically update the internal state registry cache locally for responsiveness
        device_data = self.coordinator.data.setdefault(self._device_id, {})
        device_data["switch"] = False
        device_data["1"] = False
        self.async_write_ha_state()

    # _send_command removed; async_turn_on/off now run the blocking SDK calls in the
    # executor directly to prevent putrequest from being called inside the event loop.
