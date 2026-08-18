import logging
from homeassistant.components.select import SelectEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C mode select platform."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        entities.append(SR208CModeSelect(connector, device_id))
        
    async_add_entities(entities, True)

class SR208CModeSelect(SelectEntity):
    """Representation of the system operation mode selector."""

    def __init__(self, connector, device_id):
        self._connector = connector
        self._device_id = device_id
        self._attr_name = "SR208C Operation Mode"
        self._attr_unique_id = f"{device_id}_select_mode"
        self._attr_options = ["cold", "heating", "auto"]
        self._attr_current_option = "auto"

    async def async_select_option(self, option: str) -> None:
        """Submit the selected mode change to the Tuya API."""
        await self.hass.async_add_executor_job(self._send_command, option)
        self._attr_current_option = option
        self.async_write_ha_state()

    def _send_command(self, option: str):
        payload = {"commands": [{"code": "mode", "value": option}]}
        self._connector.post(f"/v1.0/iot-03/devices/{self._device_id}/commands", payload)

    def update(self):
        """Synchronize selection configurations on a background thread."""
        try:
            response = self._connector.get(f"/v1.0/iot-03/devices/{self._device_id}/status")
            if response and response.get("success"):
                for item in response.get("result", []):
                    if item.get("code") == "mode":
                        self._attr_current_option = str(item.get("value")).lower()
        except Exception as err:
            _LOGGER.error("Error updating SR208C select: %s", err)