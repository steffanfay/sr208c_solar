import logging
from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SR208C integration from a config entry."""
    config = entry.data
    
    # Initialize the underlying Tuya open API connector
    openapi = TuyaOpenAPI(
        endpoint=f"https://openapi.tuya{config['region']}.com",
        access_id=config["api_key"],
        access_secret=config["api_secret"]
    )
    openapi.connect()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "connector": openapi,
        "device_ids": config["device_ids"].split(",")
    }

    # Forward setup routines onto platform files (sensor.py, switch.py, etc.)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True
