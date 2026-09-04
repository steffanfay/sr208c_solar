# SR208C Solar Water Heater — Home Assistant Integration

GitHub: https://github.com/steffanfay/sr208c_solar

![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![Issues](https://img.shields.io/github/issues/steffanfay/sr208c_solar)
![Repo Size](https://img.shields.io/github/repo-size/steffanfay/sr208c_solar)

Lightweight Home Assistant integration to monitor and control the SR208C Solar Thermal Water Heater via the Tuya Cloud API. Key benefits: single-coordinator polling, conservative API usage, and safe handling of blocking Tuya SDK calls.

Table of contents
- Features
- Requirements & Compatibility
- Quick start
- Configuration (UI and YAML)
- Entities exposed
- Troubleshooting
- Development / Contributing
- Changelog & License

## Features
- Centralized DataUpdateCoordinator to minimize API calls and keep entities in sync
- Safe handling of blocking Tuya SDK calls (runs synchronous SDK in executor and serializes access with an asyncio.Lock)
- Optimistic local state updates for responsive UI
- Target temperature number entity uses 5°C step blocks to conserve API calls

## Requirements & Compatibility
- Home Assistant: recommended 2023.6+ (should work on recent HA releases)
- Python: 3.10+
- Dependency: tuya-connector-python (bundled or provided by the integration)

If you rely on unusual Tuya regions or a different SDK, the integration may require minor adjustments.

## Quick start (3 steps)
1. Install the integration (HACS or manual copy into /config/custom_components/sr208c_solar/).
2. Restart Home Assistant.
3. Add the integration via Settings → Devices & Services → Add Integration → "SR208C Solar Water Heater" and enter your Tuya developer credentials.

## Configuration

YAML example (optional):

```yaml
sr208c_solar:
  api_key: "your_tuya_developer_api_key"
  api_secret: "your_tuya_developer_api_secret"
  region: "us"
  scan_interval_minutes: 15
  device_ids:
    - "device_id_1"
    - "device_id_2"
```

UI Setup (recommended):
- Settings → Devices & Services → Add Integration → Search "SR208C Solar Water Heater" → enter API Key, API Secret, Region, Device IDs, Polling interval

Configuration keys
- api_key (string) — Tuya Access ID
- api_secret (string) — Tuya Access Secret
- region (string) — e.g. us, eu, cn
- scan_interval_minutes (int) — polling interval in minutes (default 15)
- device_ids (list) — list of Tuya device IDs to monitor

## Entities exposed
The integration exposes the following entity types (per device):

| Entity | Purpose | DP keys / Notes |
|---|---:|---|
| sensor.temp_bottom (T2) | Tank bottom temperature | DP key: `temp_bottom` (fallback `22`), value scaled by 0.1, unit °C |
| sensor.temp_outside (T3) | Tank top / outside temperature | DP key: `temp_outside` (fallback `21`), value scaled by 0.1, unit °C; may be Unknown if probe missing |
| switch.heater_relay (HR) | Main system power relay | DP key: `switch` (fallback `1`) |
| select.mode | Operational mode | Options: `cold`, `heating`, `auto` — DP key `mode` (fallback `2`) |
| number.temp_set | Target heater set temperature | DP key: `temp_set` (fallback `3`), enforced 5°C step blocks |

Note: DP numeric fallbacks (1,2,3,21,22, etc.) reflect alternate Tuya datapoint mappings observed on some firmwares.

## Troubleshooting

- "Caught blocking call to putrequest" in Home Assistant logs: prior versions invoked urllib3 synchronously inside the event loop. This integration runs the blocking Tuya SDK methods inside hass.async_add_executor_job and uses an asyncio.Lock to serialize access; update to the latest version of this integration.
- Target temperature rounding: the number entity enforces 5°C blocks to reduce API usage.
- Unknown sensor values: ensure the device is set to "Controllable" in the Tuya developer portal and that physical probes are present and enabled.
- Switch immediately turns off: SR208C hardware may force HR off if it detects an open/floating output; check wiring and operational mode.

If you need help, open an issue: https://github.com/steffanfay/sr208c_solar/issues

## Development / Contributing

- Fork the repository and open a pull request against main.
- Local development: copy the integration folder to your HA config's `custom_components/` and restart Home Assistant for iteration.
- Tests: none included; add unit or integration tests in `tests/` if you implement new functionality.
- When contributing, include a brief changelog entry and tests where practical.

## Changelog & Releases
- Releases and changelog are published on the GitHub Releases page: https://github.com/steffanfay/sr208c_solar/releases

## License
- MIT — see LICENSE in the repository root for details (SPDX: MIT)

