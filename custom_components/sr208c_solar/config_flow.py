import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class SR208CConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SR208C Solar Water Heater."""
    VERSION = 3

    async def async_step_user(self, user_input=None):
        """Handle the initial setup form step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Solar Water Heater", data=user_input)

        data_schema = vol.Schema({
            vol.Required("api_key"): str,
            vol.Required("api_secret"): str,
            vol.Required("region", default="us"): vol.In(["us", "eu", "cn"]),
            vol.Required("scan_interval_minutes", default=15): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Required("device_ids"): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_reconfigure(self, user_input=None):
        """Handle a reconfiguration flow initialized by the user."""
        entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            # You can inject validation or connection tests here if required
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **user_input}
                )

        # Pre-populate the form keys using the existing configuration values
        data_schema = vol.Schema({
            vol.Required("api_key", default=entry.data.get("api_key")): str,
            vol.Required("api_secret", default=entry.data.get("api_secret")): str,
            vol.Required("region", default=entry.data.get("region", "us")): vol.In(["us", "eu", "cn"]),
            vol.Required("scan_interval_minutes", default=entry.data.get("scan_interval_minutes", 15)): vol.All(
                vol.Coerce(int), vol.Range(min=1)
            ),
            vol.Required("device_ids", default=entry.data.get("device_ids")): str,
        })

        return self.async_show_form(step_id="reconfigure", data_schema=data_schema, errors=errors)
