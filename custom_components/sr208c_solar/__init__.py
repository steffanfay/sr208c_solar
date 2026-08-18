import logging
from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SR208C integration from a config entry."""
    config = entry.data
    
    # Define an entirely self-contained worker function for our thread pool
    def _initialize_tuya_session():
        """Isolate both instantiation and network token discovery on a background thread."""
        openapi = TuyaOpenAPI(
            endpoint=f"https://openapi.tuya{config['region']}.com",
            access_id=config["api_key"],
            access_secret=config["api_secret"]
        )
        # Connect initiates the token swap API calls using urllib3 natively
        openapi.connect()
        return openapi

    try:
        # Offload the entire workflow to the background executor
        openapi_connected = await hass.async_add_executor_job(_initialize_tuya_session)
    except Exception as err:
        _LOGGER.error("Failed to authenticate and connect to Tuya APIs: %s", err)
        return False

    # Store verified session
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "connector": openapi_connected,
        "device_ids": config["device_ids"].split(",")
    }

    # Pass setup over to the entities
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
