import logging
from datetime import timedelta
from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SR208C integration using a unified Data Coordinator."""
    config = entry.data
    
    def _initialize_tuya_session():
        openapi = TuyaOpenAPI(
            endpoint=f"https://openapi.tuya{config['region']}.com",
            access_id=config["api_key"],
            access_secret=config["api_secret"]
        )
        openapi.connect()
        return openapi

    try:
        openapi_connected = await hass.async_add_executor_job(_initialize_tuya_session)
    except Exception as err:
        _LOGGER.error("Failed to authenticate with Tuya APIs: %s", err)
        return False

    device_ids = config["device_ids"].split(",")

    # This function fetches ALL device data in a single API call
    async def async_update_data():
        def _fetch_all_statuses():
            data = {}
            for device_id in device_ids:
                response = openapi_connected.get(f"/v1.0/iot-03/devices/{device_id}/status")
                if response and response.get("success"):
                    # Store data mapped by device_id
                    data[device_id] = {item["code"]: item["value"] for item in response.get("result", [])}
                else:
                    _LOGGER.warning("Tuya cloud rejected state poll for %s: %s", device_id, response)
            return data

        try:
            return await hass.async_add_executor_job(_fetch_all_statuses)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tuya Cloud: {err}")

    # Set up the Coordinator to update automatically every 30 seconds
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SR208C Data Coordinator",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    # Trigger the first refresh before adding entities so data isn't 'Unknown' on boot
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "connector": openapi_connected,
        "coordinator": coordinator,
        "device_ids": device_ids
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True
