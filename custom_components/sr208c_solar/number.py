import logging
from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import UnitOfTemperature
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

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    
    # Force UI slider steps to only jump in blocks of 5 degrees
    _attr_native_step = 5

    def __init__(self, coordinator, connector, device_id):
        """Initialize the target temperature configuration slider."""
        super().__init__(coordinator)
        self._connector = connector
        self._device_id = device_id
        
        self._attr_name = "Heater Set Temperature"
        self._attr_unique_id = f"{device_id}_number_temp_set"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name="SR208C Solar Water Heater",
            manufacturer="Sunsun / Wililo",
            model="SR208C",
            sw_version="Tuya Wi-Fi v1.0",
        )

    @property
    def native_value(self) -> float:
        """Pull the active set configuration value straight from coordinator database memory."""
        device_data = self.coordinator.data.get(self._device_id, {})
        val = device_data.get("temp_set")
        if val is None:
            val = device_data.get("3")
            
        if val is not None:
            # Round state value to nearest multiple of 5 for frontend consistency
            return float(round(float(val) / 5) * 5)
        return 50.0

    async def async_set_native_value(self, value: float) -> None:
        """Asynchronously push the target slider threshold up to the panel in 5-degree blocks."""
        # Enforce strict 5-degree rounding blocks mathematically
        target_int = int(round(value / 5) * 5)
        
        # Guard clause: Stop execution early if target matches current value to save API limits
        if target_int == int(self.native_value):
            return

        # Move network I/O to native async execution loops
        success = await self._async_send_command(target_int)
        
        if success:
            # Optimistically update memory values locally to prevent dashboard slider jumping
            device_data = self.coordinator.data.setdefault(self._device_id, {})
            device_data["temp_set"] = target_int
            device_data["3"] = target_int
            self.async_write_ha_state()
            
            # Forces coordinator loop refresh to ensure local sync with the cloud state
            await self.coordinator.async_request_refresh()

    async def _async_send_command(self, value: int) -> bool:
        """Asynchronous HTTP post pushing payload states natively back up to the panel."""
        payload = {
            "commands": [
                {
                    "code": "temp_set",
                    "value": value
                }
            ]
        }
        try:
            response = await self._connector.post(f"/v1.0/iot-03/devices/{self._device_id}/commands", payload)
            
            if not response or not response.get("success"):
                _LOGGER.error("Tuya Cloud rejected target set temperature update payload: %s", response)
                return False
            return True
        except Exception as err:
            _LOGGER.error("Failed to commit target slider change back to SR208C panel hardware: %s", err)
            return False
