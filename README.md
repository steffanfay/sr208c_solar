# Home Assistant SR208C Solar Water Heater Integration

This custom Home Assistant integration allows you to seamlessly monitor and control the **SR208C Solar Thermal Water Heater Controller** via the Tuya Cloud API using the thread-isolated `tuya-connector-python` library. 

Unlike basic read-only alternatives, this repository employs a centralized **Data Update Coordinator** pattern to securely read multi-relay temperature telemetry and write state adjustments without spamming or triggering Tuya API rate limiting thresholds.

## Features
- **Centralized Data Coordinator**: Single API status lookup cycles every 30 seconds to update all entities simultaneously.
- **Thread-Isolated Initialization**: Completely isolates blocking I/O calls (`openapi.connect` and `urllib3`) from the main event loop to ensure system stability.
- **Optimistic State Tracking**: Dashboard control items update immediately in the UI upon click, eliminating delay or "rubber-banding."
- **Supported Control Surfaces**:
  - `sensor`: Linear 0.1x scaling for Tank Bottom (`T2`) and pre-configured hooks for Tank Top (`T3`).
  - `switch`: Control over the main System Power loop.
  - `select`: Operational system profile modes (`cold`, `heating`, `auto`).
  - `number`: Native adjustable cutoff temperature slider formatted in degrees Celsius (°C).

## Limitations
- **Unsupported**:
  - Collector temperature T1
  - Circulation pump R1/PWM
  - Multiple devices are theoretically supported, but untested

---

## Installation

### Manual Installation
1. Download this repository's contents.
2. Place the directory files directly inside your Home Assistant configuration directory under:
   `/config/custom_components/sr208c_solar/`
3. Restart Home Assistant.

### HACS (Recommended)
1. Navigate to **HACS → Integrations** inside Home Assistant.
2. Click the **three dots** in the top right corner and choose **Custom repositories**.
3. Paste your repository URL: `https://github.com/steffanfay/sr208c_solar`
4. Select **Integration** as the category and click **Add**.
5. Download the integration, then restart your Home Assistant instance.

---

## Configuration

### **Option 1: UI Setup (Recommended)**
1. Navigate to **Settings → Devices & Services → Add Integration**.
2. Search for **SR208C Solar Water Heater**.
3. Enter your Tuya Cloud Developer credentials in the popup form:
   - **API Key** (Access ID)
   - **API Secret** (Access Secret)
   - **Region** (e.g., `us`, `eu`, `cn`)
   - **Device IDs** (Comma-separated list if tracking multiple units)
4. Click **Submit**. Every switch, slider, and temperature line will automatically bundle together under a single, unified device profile.

### **Option 2: Configuration via `configuration.yaml`**
Alternatively, you can choose to define your connection string profile manually via code lines:

```yaml
# Example configuration.yaml entry
sr208c_solar:
  api_key: "your_tuya_developer_api_key"
  api_secret: "your_tuya_developer_api_secret"
  region: "us"
  device_ids:
    - "your_device_ids_comma_separated"
```
*Note: Restart your Home Assistant instance after saving your changes to the `configuration.yaml` file.*

---

## Updating Options
- If configured via the **UI Flow**, you can reconfigure or swap credential strings on the fly by going to:
  **Settings → Devices & Services → SR208C Solar Water Heater → Configure**.
- If using **configuration.yaml**, edit the configuration keys and restart Home Assistant.

---

## Troubleshooting

### Temperature Readings show up as `Unknown`
- Ensure your device has **Controllable device** permissions toggled active inside your Tuya Developer Portal layout.
- The `T3` (Tank Top) sensor will gracefully report as `Unknown` if you do not have an active NTC probe wired into the physical terminal block screws or if it is disabled inside your local hardware menu.

### System Power Switch instantly turns back off
- When set to `heating` mode, the SR208C checks for resistance across the **`HR` afterheating output terminal** to protect against floating lines. If you do not have an auxiliary heater or an external isolation relay wired to the `HR` block, the hardware firmware will automatically force the switch back to `OFF` for safety. Switch the operational mode back to `auto` or `cold` to maintain a stable, persistent `ON` loop for your `R1` solar pump lines.

---

## Contributing
Contributions, optimization pull requests, and additional hardware data point mapping expansions are welcome! Feel free to open an issue or submit a pull request against the `main` branch code line.

---

## License
This project is licensed under the MIT License - see the root folder validation properties for details.
