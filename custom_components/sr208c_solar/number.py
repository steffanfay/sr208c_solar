import logging
from homeassistant.components.number import NumberEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C temperature configuration slider."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        entities.append(SR208CTargetTempSlider(connector, device_id))
        
    async_add_entities(entities, True)

class SR208CTargetTempSlider(NumberEntity):
    """Slider interface for target heating thresholds."""

    def __init__(self, connector, device_id):
        self._connector = connector
        self._device_id = device_id
        self._attr_name = "SR208C Cutoff Temperature"
        self._attr_unique_id = f"{device_id}_number_temp_set"
        
        # Physical slider boundaries for solar configurations
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_value = 50

    async def async_set_native_value(self, value: float) -> None:
        """Send target configuration directly onto background worker thread."""
        target_int = int(value)
        await self.hass.async_add_executor_job(self._send_command, target_int)
        self._attr_native_value = target_int
        self.async_write_ha_state()

    def _send_command(self, value: int):
        payload = {"commands": [{"code": "temp_set", "value": value}]}
        self._connector.post(f"/v1.0/iot-03/devices/{self._device_id}/commands", payload)

    def update(self):
        """Update slider tracking position on background thread thread safely."""
        try:
            response = self._connector.get(f"/v1.0/iot-03/devices/{self._device_id}/status")
            if response and response.get("success"):
                for item in response.get("result", []):
                    if item.get("code") == "temp_set":
                        self._attr_native_value = int(item.get("value"))
        except Exception as err:
            _LOGGER.error("Error updating SR208C number: %s", err)
