"""The BInformed integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import (
    BInformedAccountNotVerifiedError,
    BInformedAuthError,
    BInformedClient,
    BInformedConnectionError,
    BInformedError,
    BInformedRateLimitError,
)
from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN, PLATFORMS

CONFIG_SCHEMA = cv.platform_only_config_schema(DOMAIN)

type BInformedConfigEntry = ConfigEntry[BInformedClient]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the BInformed component.

    Nothing is configured here: the integration is set up either through a
    config entry or through the legacy ``notify`` platform. Declaring this
    function is what registers the domain in ``hass.config.components``, so
    that translated error messages are available to the legacy service too.
    """
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BInformedConfigEntry) -> bool:
    """Set up BInformed from a config entry."""
    client = BInformedClient(
        async_get_clientsession(hass),
        entry.data[CONF_API_KEY],
        entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
    )

    try:
        await client.async_validate_key()
    except BInformedConnectionError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="cannot_connect"
        ) from err
    except BInformedAuthError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="invalid_auth"
        ) from err
    except BInformedAccountNotVerifiedError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="account_not_verified"
        ) from err
    except BInformedRateLimitError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="rate_limited"
        ) from err
    except BInformedError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="unknown"
        ) from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BInformedConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
