"""Constants for integration_blueprint."""
# Base component constants
NAME = "PoLED integration"
DOMAIN = "zvirce_home_poled"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "2.0.0"
ATTRIBUTION = ""
ISSUE_URL = "https://github.com/matevzsi/ZvirceHome/issues"

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
CONF_USERNAME = "username"
CONF_HOST = "host"
CONF_USER_ID = "user_id"
CONF_LIGHTS = "lights"
CONF_COVERS = "covers"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_HOST = "192.168.88.99"
DEFAULT_USER_ID = 0

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a PoLED integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
