"""Fixtures for the BInformed tests."""

from __future__ import annotations

from collections.abc import Generator
from hashlib import sha256
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.binformed.const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN
from homeassistant.const import CONF_API_KEY

API_KEY = "gn_testkey"
API_KEY_HASH = sha256(API_KEY.encode()).hexdigest()
ENTRY_TITLE = "BInformed"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a configured BInformed config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=ENTRY_TITLE,
        unique_id=API_KEY_HASH,
        data={CONF_API_KEY: API_KEY, CONF_BASE_URL: DEFAULT_BASE_URL},
    )


@pytest.fixture
def mock_setup_entry() -> Generator[None]:
    """Prevent the integration from actually being set up."""
    with patch(
        "custom_components.binformed.async_setup_entry", return_value=True
    ) as mock:
        yield mock
