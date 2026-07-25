"""Config flow for the BInformed integration."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    BInformedAccountNotVerifiedError,
    BInformedAuthError,
    BInformedClient,
    BInformedConnectionError,
    BInformedError,
    BInformedRateLimitError,
)
from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DEFAULT_NAME, DOMAIN, LOGGER

API_KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
URL_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.URL))


class BInformedConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BInformed."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: ask for the API key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input.get(CONF_BASE_URL) or DEFAULT_BASE_URL
            api_key = user_input[CONF_API_KEY].strip()
            client = BInformedClient(
                async_get_clientsession(self.hass), api_key, base_url
            )
            try:
                await client.async_validate_key()
            except BInformedConnectionError:
                errors["base"] = "cannot_connect"
            except BInformedAuthError:
                errors[CONF_API_KEY] = "invalid_auth"
            except BInformedAccountNotVerifiedError:
                errors["base"] = "account_not_verified"
            except BInformedRateLimitError:
                errors["base"] = "rate_limited"
            except BInformedError:
                LOGGER.exception(
                    "Unexpected error while validating the BInformed API key"
                )
                errors["base"] = "unknown"
            else:
                # The API key is the only credential available, and no endpoint
                # exposes the account identity to it. Hashing the key gives a
                # stable id that keeps the same key from being added twice.
                await self.async_set_unique_id(sha256(api_key.encode()).hexdigest())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or DEFAULT_NAME,
                    data={CONF_API_KEY: api_key, CONF_BASE_URL: base_url},
                )

        schema: dict[Any, Any] = {
            vol.Required(CONF_API_KEY): API_KEY_SELECTOR,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        }
        if self.show_advanced_options:
            schema[vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL)] = URL_SELECTOR

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(schema), user_input or {}
            ),
            errors=errors,
        )
