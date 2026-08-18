import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C slider parameters via the central data coordinator."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        entities.append(SR208CTargetTempSlider(coordinator, connector, device_id))
        
    async_add_entities(entities, False)

class SR208CTargetTempSlider(CoordinatorEntity, NumberEntity):
    """Slider interface for target heating thresholds linked via Coordinator."""

    def __init__(self, coordinator, connector, device_id):
        """Initialize the target temperature configuration slider."""
        super().__init__(coordinator)
        self._connector = connector
        self._device_id = device_id
        
        self._attr_name = "Heater Cutoff Temperature"
        self._attr_unique_id = f"{device_id}_number_temp_set"
        
        # Safe thermal cutoff boundaries for SR208C plumbing loops
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_entity_category = EntityCategory.CONFIG 

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)}, # Links entities sharing this exact ID
            name="SR208C Solar Water Heater",
            manufacturer="Sunsun / Wililo",          # The manufacturing parent standard
            model="SR208C",
            sw_version="Tuya Wi-Fi v1.0",
        )

    @property
    def native_value(self) -> float:
        """Pull the active cutoff configuration value straight from coordinator database memory."""
        device_data = self.coordinator.data.get(self._device_id, {})
        val = device_data.get("temp_set")
        if val is None:
            # Common alternative DP numeric indexing for target temperature settings
            val = device_data.get("3")
            
        if val is not None:
            return float(val)
        return 50.0

    async def async_set_native_value(self, value: float) -> None:
        """Offload the target slider threshold integer onto background worker thread pools."""
        target_int = int(value)
        await self.hass.async_add_executor_job(self._send_command, target_int)
        
        # Optimistically update memory values locally to prevent dashboard slider jumping
        device_data = self.coordinator.data.setdefault(self._device_id, {})
        device_data["temp_set"] = target_int
        device_data["3"] = target_int
        self.async_write_ha_state()

    def _send_command(self, value: int) -> None:
        """Synchronous write function pushing the slider limit value back up to the panel."""
        payload = {
            "commands": [
                {
                    "code": "temp_set",
                    "value": value
                }
            ]
        }
        try:
            response = self._connector.post(f"/v1.0/iot-03/devices/{self._device_id}/commands", payload)
            if not response or not response.get("success"):
                _LOGGER.error("Tuya Cloud rejected target cutoff temperature update payload: %s", response)
        except Exception as err:
            _LOGGER.error("Failed to commit target slider change back to SR208C panel hardware: %s", err)
