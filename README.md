# Zvirce SmartHome (PoLED) Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Custom integration for Zvirce SmartHome PoLED gateway, enabling control of lights and covers (blinds) through Home Assistant.

## Features

- **Full Light Control**: Support for RGBW lights, color temperature, brightness, and on/off control
- **Cover/Blind Control**: Position and tilt angle control for window coverings
- **Easy Configuration**: User-friendly config flow through Home Assistant UI
- **Flexible Channel Management**: Enable/disable and rename individual light and cover channels
- **Local Polling**: Direct communication with your PoLED gateway on your local network

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/zvirce_home_poled` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Zvirce SmartHome"
4. Enter your PoLED gateway details:
   - **IP Address**: The IP address of your PoLED gateway (e.g., `192.168.88.99`)
   - **User ID**: The user ID to use (default: `0`)

The integration will automatically discover all available lights and covers from your gateway.

### Configuring Channels

After initial setup, you can customize which channels are enabled and their names:

1. Go to **Settings** → **Devices & Services**
2. Find the "Zvirce SmartHome" integration
3. Click **Configure**
4. Choose either:
   - **Configure Lights**: Enable/disable and rename light channels
   - **Configure Covers**: Enable/disable and rename cover channels

## Supported Devices

- **Lights**: RGBW lights, color temperature lights, dimmable lights, on/off lights
- **Covers**: Blinds with position and tilt angle control

## Light Types

The integration automatically detects the light type based on the PoLED group configuration:
- **RGBW**: Full color control with warm/cold white
- **Color Temperature**: Adjustable white color temperature
- **Brightness**: Dimmable white lights
- **On/Off**: Simple on/off control

## Cover Features

Each cover provides:
- **Position control**: Open/close to specific position (0-100%)
- **Tilt control**: Adjust slat angle (0-100%)
- **Stop command**: Stop movement at current position

Note: Each physical cover creates two entities:
- Main entity: Controls position
- Tilt entity (prefixed with "Naklon"): Controls tilt angle only

## Troubleshooting

### Cannot Connect to Gateway

- Verify the IP address is correct
- Ensure the PoLED gateway is powered on and connected to your network
- Check that Home Assistant can reach the gateway (same network/VLAN)
- Try pinging the gateway from your Home Assistant host

### Entities Not Appearing

- Check if the channels are enabled in the integration configuration
- Verify the user ID is correct
- Restart Home Assistant after making configuration changes

### Entities Not Updating

- The integration polls the gateway every 2 seconds
- Check the Home Assistant logs for any error messages
- Verify network connectivity to the gateway

## Development

This integration uses:
- **Config Flow**: Modern Home Assistant configuration through UI
- **DataUpdateCoordinator**: Efficient polling and state management
- **UDP Communication**: Direct protocol communication with PoLED gateway

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Developed for the Zvirce SmartHome PoLED gateway system.

