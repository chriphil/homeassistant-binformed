"""BInformed notification support.

Two entry points are provided:

* ``BInformedNotifyEntity`` - the modern notify entity, created from a config
  entry and driven with the ``notify.send_message`` action.
* ``BInformedNotificationService`` - the legacy ``notify.<name>`` service, kept
  for YAML configurations and existing automations. It additionally accepts an
  ``url`` field inside ``data``.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
    PLATFORM_SCHEMA as NOTIFY_PLATFORM_SCHEMA,
    BaseNotificationService,
    NotifyEntity,
    NotifyEntityFeature,
)
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import BInformedConfigEntry
from .api import (
    BInformedAccountNotVerifiedError,
    BInformedAuthError,
    BInformedClient,
    BInformedConnectionError,
    BInformedError,
    BInformedRateLimitError,
    BInformedValidationError,
)
from .const import ATTR_URL, CONF_BASE_URL, DEFAULT_BASE_URL, DEFAULT_NAME, DOMAIN

PLATFORM_SCHEMA = NOTIFY_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): cv.url,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def _as_home_assistant_error(err: BInformedError) -> HomeAssistantError:
    """Translate a client error into a user facing Home Assistant error."""
    if isinstance(err, BInformedAuthError):
        key = "invalid_auth"
    elif isinstance(err, BInformedAccountNotVerifiedError):
        key = "account_not_verified"
    elif isinstance(err, BInformedRateLimitError):
        key = "rate_limited"
    elif isinstance(err, BInformedConnectionError):
        key = "cannot_connect"
    elif isinstance(err, BInformedValidationError):
        return HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="invalid_payload",
            translation_placeholders={"error": str(err)},
        )
    else:
        key = "send_failed"
    return HomeAssistantError(translation_domain=DOMAIN, translation_key=key)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> BInformedNotificationService:
    """Set up the legacy BInformed notification service from YAML."""
    return BInformedNotificationService(
        BInformedClient(
            async_get_clientsession(hass),
            config[CONF_API_KEY],
            config.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BInformedConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the BInformed notify entity from a config entry."""
    async_add_entities([BInformedNotifyEntity(entry)])


class BInformedNotificationService(BaseNotificationService):
    """Legacy notification service, configured through ``configuration.yaml``."""

    def __init__(self, client: BInformedClient) -> None:
        """Initialise the service."""
        self._client = client

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a notification through BInformed."""
        data = kwargs.get(ATTR_DATA) or {}
        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)

        try:
            await self._client.async_notify(
                message, title=title, url=data.get(ATTR_URL)
            )
        except BInformedError as err:
            raise _as_home_assistant_error(err) from err


class BInformedNotifyEntity(NotifyEntity):
    """Notify entity backed by a BInformed config entry."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, entry: BInformedConfigEntry) -> None:
        """Initialise the entity."""
        self._client = entry.runtime_data
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="BInformed",
            name=entry.title,
        )

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a notification through BInformed."""
        try:
            await self._client.async_notify(message, title=title)
        except BInformedError as err:
            raise _as_home_assistant_error(err) from err
