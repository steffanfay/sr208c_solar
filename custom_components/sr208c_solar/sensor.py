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
        # Re-mapped to align exactly with SR208C standard firmware DP string codes
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Collector Temperature T1", "temp_top", "26"))
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Tank Temperature Bottom T2", "temp_bottom", "22"))
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Tank Temperature Top T3", "temp_outside", "21"))
        
    async_add_entities(entities, False)

class SR208CCoordinatorSensor(CoordinatorEntity, SensorEntity):
    """Representation of an SR208C Sensor tracking point fed by the coordinator."""

    def __init__(self, coordinator, device_id, sensor_name, standard_code, numeric_fallback):
        super().__init__(coordinator)
        self._device_id = device_id
        self._standard_code = standard_code
        self._numeric_fallback = numeric_fallback
        
        self._attr_name = f"SR208C {sensor_name}"
        self._attr_unique_id = f"{device_id}_sensor_{standard_code}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Read value from coordinator storage and apply the 0.1 scaling factor."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        # 1. Try pulling via standard Tuya firmware string names (e.g., 'temp_top')
        raw_val = device_data.get(self._standard_code)
        
        # 2. If missing, look for a strict numeric index fallback (e.g., '26')
        if raw_val is None:
            raw_val = device_data.get(self._numeric_fallback)

        if raw_val is not None:
            try:
                # Apply the mandatory 0.1 decimal scaling factor used by solar controllers
                return float(raw_val) * 0.1
            except (ValueError, TypeError):
                _LOGGER.warning("Could not convert raw sensor value %s to float", raw_val)
                return None
                
        return None
