"""Tests for the BInformed config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.binformed.api import (
    BInformedAccountNotVerifiedError,
    BInformedAuthError,
    BInformedConnectionError,
    BInformedError,
    BInformedRateLimitError,
)
from custom_components.binformed.const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import API_KEY, API_KEY_HASH, ENTRY_TITLE


def _patch_validate(**kwargs):
    kwargs.setdefault("return_value", None)
    return patch(
        "custom_components.binformed.config_flow.BInformedClient.async_validate_key",
        **kwargs,
    )


async def test_user_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """A valid API key creates an entry and is stored trimmed."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with _patch_validate():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: f"  {API_KEY}  ", CONF_NAME: ENTRY_TITLE}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ENTRY_TITLE
    assert result["data"] == {CONF_API_KEY: API_KEY, CONF_BASE_URL: DEFAULT_BASE_URL}
    assert result["result"].unique_id == API_KEY_HASH


@pytest.mark.parametrize(
    ("side_effect", "field", "error"),
    [
        (BInformedConnectionError, "base", "cannot_connect"),
        (BInformedAuthError, CONF_API_KEY, "invalid_auth"),
        (BInformedAccountNotVerifiedError, "base", "account_not_verified"),
        (BInformedRateLimitError, "base", "rate_limited"),
        (BInformedError, "base", "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    side_effect: type[Exception],
    field: str,
    error: str,
) -> None:
    """Errors are shown on the form, and the flow can be retried."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with _patch_validate(side_effect=side_effect):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: API_KEY}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {field: error}

    with _patch_validate():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: API_KEY}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_duplicate_key_aborts(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The same API key cannot be configured twice."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    with _patch_validate():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: API_KEY}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
