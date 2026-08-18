import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class SR208CConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SR208C Solar Thermal Controller."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup form step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Solar Controller", data=user_input)

        data_schema = vol.Schema({
            vol.Required("api_key"): str,
            vol.Required("api_secret"): str,
            vol.Required("region", default="us"): vol.In(["us", "eu", "cn"]),
            vol.Required("device_ids"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)