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
        # Added a boolean flag to isolate the T1 collector scaling equation
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Collector Temperature T1", "temp_top", "26", is_collector=True))
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Tank Temperature Bottom T2", "temp_bottom", "22"))
        
        # T3 configuration fix: checking alternate standard 'temp_outside' or 'countdown_left' blocks
        entities.append(SR208CCoordinatorSensor(coordinator, device_id, "Tank Temperature Top T3", "temp_outside", "21"))
        
    async_add_entities(entities, False)

class SR208CCoordinatorSensor(CoordinatorEntity, SensorEntity):
    """Representation of an SR208C Sensor tracking point fed by the coordinator."""

    def __init__(self, coordinator, device_id, sensor_name, standard_code, numeric_fallback, is_collector=False):
        super().__init__(coordinator)
        self._device_id = device_id
        self._standard_code = standard_code
        self._numeric_fallback = numeric_fallback
        self._is_collector = is_collector
        
        self._attr_name = f"SR208C {sensor_name}"
        self._attr_unique_id = f"{device_id}_sensor_{standard_code}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self):
        """Read value from coordinator storage and apply the correct firmware scale factors."""
        device_data = self.coordinator.data.get(self._device_id, {})
        
        raw_val = device_data.get(self._standard_code)
        if raw_val is None:
            raw_val = device_data.get(self._numeric_fallback)

        if raw_val is not None:
            try:
                float_val = float(raw_val)
                
                # Apply negative-offset calculation if this is the roof collector (T1)
                if self._is_collector:
                    # If Tuya passes values like 1109 (representing 10.9C on the shifted scale)
                    if float_val > 500:
                        return (float_val - 1000) * 0.1
                    else:
                        # Fallback for alternative sub-versions using raw offset
                        return float_val * 0.1
                
                # Standard scaling used for tank nodes (T2, T3)
                return float_val * 0.1
                
            except (ValueError, TypeError):
                _LOGGER.warning("Could not convert raw sensor value %s to float", raw_val)
                return None
                
        return None
