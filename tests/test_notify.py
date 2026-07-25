"""Tests for the BInformed notify entity and legacy service."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.binformed.api import (
    BInformedAuthError,
    BInformedRateLimitError,
    NotifyResult,
)
from custom_components.binformed.const import DOMAIN
from homeassistant.components.notify import (
    ATTR_MESSAGE,
    ATTR_TITLE,
    DOMAIN as NOTIFY_DOMAIN,
    SERVICE_SEND_MESSAGE,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component


def _patch_notify(**kwargs):
    """Patch the outgoing notification call."""
    kwargs.setdefault("return_value", NotifyResult(pushed=1, failed=0))
    return patch(
        "custom_components.binformed.api.BInformedClient.async_notify", **kwargs
    )


async def _setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    """Set up the config entry and return the created notify entity id."""
    entry.add_to_hass(hass)
    with patch(
        "custom_components.binformed.BInformedClient.async_validate_key",
        return_value=None,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    entity_ids = hass.states.async_entity_ids(NOTIFY_DOMAIN)
    assert len(entity_ids) == 1
    return entity_ids[0]


async def test_entry_setup_and_unload(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The config entry creates exactly one notify entity and unloads cleanly."""
    await _setup_entry(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_send_message(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """notify.send_message forwards message and title to the API."""
    entity_id = await _setup_entry(hass, mock_config_entry)

    with _patch_notify() as notify:
        await hass.services.async_call(
            NOTIFY_DOMAIN,
            SERVICE_SEND_MESSAGE,
            {"entity_id": entity_id, ATTR_MESSAGE: "Boiler down", ATTR_TITLE: "Alarm"},
            blocking=True,
        )

    notify.assert_awaited_once_with("Boiler down", title="Alarm")


@pytest.mark.parametrize("side_effect", [BInformedAuthError, BInformedRateLimitError])
async def test_send_message_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    side_effect: type[Exception],
) -> None:
    """API errors surface as HomeAssistantError."""
    entity_id = await _setup_entry(hass, mock_config_entry)

    with (
        _patch_notify(side_effect=side_effect),
        pytest.raises(HomeAssistantError),
    ):
        await hass.services.async_call(
            NOTIFY_DOMAIN,
            SERVICE_SEND_MESSAGE,
            {"entity_id": entity_id, ATTR_MESSAGE: "Boom"},
            blocking=True,
        )


async def test_setup_entry_invalid_key(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """An invalid API key puts the entry in the error state."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.binformed.BInformedClient.async_validate_key",
        side_effect=BInformedAuthError,
    ):
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_legacy_service(hass: HomeAssistant) -> None:
    """The YAML platform registers notify.<name> and forwards data.url."""
    assert await async_setup_component(
        hass,
        NOTIFY_DOMAIN,
        {
            NOTIFY_DOMAIN: [
                {
                    "platform": DOMAIN,
                    "name": "binformed_yaml",
                    "api_key": "gn_yaml",
                }
            ]
        },
    )
    await hass.async_block_till_done()

    assert hass.services.has_service(NOTIFY_DOMAIN, "binformed_yaml")

    with _patch_notify() as notify:
        await hass.services.async_call(
            NOTIFY_DOMAIN,
            "binformed_yaml",
            {
                ATTR_MESSAGE: "Leak detected",
                ATTR_TITLE: "Water",
                "data": {"url": "https://example.com/leak"},
            },
            blocking=True,
        )

    notify.assert_awaited_once_with(
        "Leak detected", title="Water", url="https://example.com/leak"
    )


async def test_legacy_service_error_is_translated(hass: HomeAssistant) -> None:
    """Errors raised by the YAML service resolve to a translated message."""
    assert await async_setup_component(
        hass,
        NOTIFY_DOMAIN,
        {
            NOTIFY_DOMAIN: [
                {"platform": DOMAIN, "name": "binformed_yaml", "api_key": "gn_yaml"}
            ]
        },
    )
    await hass.async_block_till_done()

    with (
        _patch_notify(side_effect=BInformedAuthError),
        pytest.raises(HomeAssistantError) as err,
    ):
        await hass.services.async_call(
            NOTIFY_DOMAIN,
            "binformed_yaml",
            {ATTR_MESSAGE: "Boom"},
            blocking=True,
        )

    assert str(err.value).startswith(
        "The BInformed API key is invalid or has been rotated"
    )
