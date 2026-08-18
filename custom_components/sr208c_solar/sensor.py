import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C sensors using the data coordinator."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Collector Temperature T1", "26"))
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Tank Temperature Bottom T2", "22"))
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Tank Temperature Top T3", "21"))
        
    async_add_entities(entities, False)

class SR208CCoordinatorSensor(CoordinatorEntity, SensorEntity):
    """Representation of an SR208C Sensor tracking point fed by the coordinator."""

    def __init__(self, coordinator, device_id, sensor_name, dp_code):
        super().__init__(coordinator)
        self._device_id = device_id
        self._dp_code = dp_code
        
        self._attr_name = f"SR208C {sensor_name}"
        self._attr_unique_id = f"{device_id}_sensor_{dp_code}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Read value from coordinator storage and apply the 0.1 scaling factor."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        # Fallback tracking if Tuya API keys return values by numeric string index IDs instead of string codes
        raw_val = device_data.get(self._dp_code)
        if raw_val is None:
            # Look up by alternative DP codes map if necessary
            dp_map = {"26": "temp_collector", "22": "temp_tank_bottom", "21": "temp_tank_top"}
            raw_val = device_data.get(dp_map.get(self._dp_code))

        if raw_val is not None:
            return float(raw_val) * 0.1
        return None
