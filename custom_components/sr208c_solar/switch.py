import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the SR208C switch platform."""
    connector = hass.data[DOMAIN][entry.entry_id]["connector"]
    device_ids = hass.data[DOMAIN][entry.entry_id]["device_ids"]
    
    entities = []
    for device_id in device_ids:
        entities.append(SR208CSystemSwitch(connector, device_id))
        
    async_add_entities(entities, True)

class SR208CSystemSwitch(SwitchEntity):
    """Representation of the main SR208C power switch."""

    def __init__(self, connector, device_id):
        self._connector = connector
        self._device_id = device_id
        self._attr_name = "SR208C System Power"
        self._attr_unique_id = f"{device_id}_switch_main"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs):
        """Turn the system switch on."""
        await self.hass.async_add_executor_job(self._send_command, True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the system switch off."""
        await self.hass.async_add_executor_job(self._send_command, False)
        self._attr_is_on = False
        self.async_write_ha_state()

    def _send_command(self, state: bool):
        payload = {"commands": [{"code": "switch", "value": state}]}
        self._connector.post(f"/v1.0/iot-03/devices/{self._device_id}/commands", payload)

    def update(self):
        """Fetch state from the cloud on a background thread."""
        try:
            response = self._connector.get(f"/v1.0/iot-03/devices/{self._device_id}/status")
            if response and response.get("success"):
                for item in response.get("result", []):
                    if item.get("code") == "switch":
                        self._attr_is_on = bool(item.get("value"))
        except Exception as err:
            _LOGGER.error("Error updating SR208C switch: %s", err)