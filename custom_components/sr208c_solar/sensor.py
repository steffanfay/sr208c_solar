import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C temperature telemetry sensors."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        # Generate the full stack of physical tracking lines for each controller
        entities.append(SR208CTemperatureSensor(connector, device_id, "Collector Temperature T1", "26"))
        entities.append(SR208CTemperatureSensor(connector, device_id, "Tank Temperature Bottom T2", "22"))
        entities.append(SR208CTemperatureSensor(connector, device_id, "Tank Temperature Top T3", "21"))
        
    async_add_entities(entities, True)

class SR208CTemperatureSensor(SensorEntity):
    """Representation of an SR208C physical temperature tracking point."""

    def __init__(self, connector, device_id, sensor_name, dp_code):
        self._connector = connector
        self._device_id = device_id
        self._dp_code = dp_code
        
        # UI Presentation & Registry Hooks
        self._attr_name = f"SR208C {sensor_name}"
        self._attr_unique_id = f"{device_id}_sensor_{dp_code}"
        
        # Native telemetry properties to unlock deep long-term history tracking
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_native_value = None

    def update(self):
        """Query Tuya Cloud APIs to extract and scale real-time states."""
        try:
            response = self._connector.get(f"/v1.0/iot-03/devices/{self._device_id}/status")
            if response and response.get("success"):
                status_list = response.get("result", [])
                for item in status_list:
                    if str(item.get("code")) == self._dp_code or str(item.get("id")) == self._dp_code:
                        raw_val = item.get("value")
                        if raw_val is not None:
                            # Apply mandatory 0.1 decimal scaling factor used by SR208C
                            self._attr_native_value = float(raw_val) * 0.1
                            return
            else:
                _LOGGER.warning("Tuya cloud rejected sensor status read request: %s", response)
        except Exception as err:
            _LOGGER.error("Failed to parse SR208C sensor telemetry data point %s: %s", self._dp_code, err)
