import logging
from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SR208C integration from a config entry."""
    config = entry.data
    
    # Instantiate the connection profile container
    openapi = TuyaOpenAPI(
        endpoint=f"https://openapi.tuya{config['region']}.com",
        access_id=config["api_key"],
        access_secret=config["api_secret"]
    )

    # FIX: Move the blocking connect() call into Home Assistant's thread executor
    await hass.async_add_executor_job(openapi.connect)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "connector": openapi,
        "device_ids": config["device_ids"].split(",")
    }

    # Forward setup routines safely onto platform modules
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
