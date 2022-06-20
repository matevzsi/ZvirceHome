"""Constants for integration_blueprint."""
# Base component constants
NAME = "PoLED integration"
DOMAIN = "zvirce_home"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = ""
ISSUE_URL = ""

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
#BINARY_SENSOR = "binary_sensor"
#SENSOR = "sensor"
#SWITCH = "switch"
COVER = "cover"
LIGHT = "light"
#PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH]
PLATFORMS = [LIGHT, COVER]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "0"

# Defaults
DEFAULT_NAME = DOMAIN

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a PoLED integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
