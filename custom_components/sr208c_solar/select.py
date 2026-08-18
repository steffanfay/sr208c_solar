import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C mode select platform via the central data coordinator."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        entities.append(SR208CModeSelect(coordinator, connector, device_id))
        
    async_add_entities(entities, False)

class SR208CModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of the system operation mode selector tracking via Coordinator."""

    def __init__(self, coordinator, connector, device_id):
        """Initialize the selector tied to the coordinator loop."""
        super().__init__(coordinator)
        self._connector = connector
        self._device_id = device_id
        
        self._attr_name = "SR208C Operation Mode"
        self._attr_unique_id = f"{device_id}_select_mode"
        self._attr_options = ["cold", "heating", "auto"]

    @property
    def current_option(self) -> str:
        """Extract the selected system profile option directly from cached data."""
        device_data = self.coordinator.data.get(self._device_id, {})
        val = device_data.get("mode")
        if val is None:
            # Common alternative DP numeric indexing for modes
            val = device_data.get("2")
            
        if val is not None:
            return str(val).lower()
        return "auto"

    async def async_select_option(self, option: str) -> None:
        """Submit the selected mode configuration back to Tuya Cloud APIs."""
        await self.hass.async_add_executor_job(self._send_command, option)
        
        # Optimistically save state inside the central dictionary for instantaneous UI tracking
        device_data = self.coordinator.data.setdefault(self._device_id, {})
        device_data["mode"] = option
        device_data["2"] = option
        self.async_write_ha_state()

    def _send_command(self, option: str) -> None:
        """Synchronous write function execution passing raw parameter strings up to the cloud."""
        payload = {
            "commands": [
                {
                    "code": "mode",
                    "value": option
                }
            ]
        }
        try:
            response = self._connector.post(f"/v1.0/iot-03/devices/{self._device_id}/commands", payload)
            if not response or not response.get("success"):
                _LOGGER.error("Tuya Cloud rejected the operation mode payload command: %s", response)
        except Exception as err:
            _LOGGER.error("Failed to push configuration mode change to SR208C panel hardware: %s", err)
