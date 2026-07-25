"""Constants for the BInformed integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "binformed"

LOGGER: Final = logging.getLogger(__package__)

PLATFORMS: Final = [Platform.NOTIFY]

# Configuration keys
CONF_BASE_URL: Final = "base_url"

# Defaults
DEFAULT_NAME: Final = "BInformed"
DEFAULT_BASE_URL: Final = "https://api-binformed.gericos.com"

# Extra data accepted by the legacy `notify.binformed` service
ATTR_URL: Final = "url"

# Field limits enforced server-side by the BInformed API
MAX_MESSAGE_LENGTH: Final = 2000
MAX_TITLE_LENGTH: Final = 200
