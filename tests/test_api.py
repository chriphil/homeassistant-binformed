"""Tests for the BInformed API client."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import aiohttp
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.binformed.api import (
    BInformedAccountNotVerifiedError,
    BInformedAuthError,
    BInformedClient,
    BInformedConnectionError,
    BInformedError,
    BInformedRateLimitError,
    BInformedValidationError,
)
from custom_components.binformed.const import DEFAULT_BASE_URL

NOTIFY_URL = f"{DEFAULT_BASE_URL}/v1/notify"


@pytest.fixture
async def session(
    aioclient_mock: AiohttpClientMocker,
) -> AsyncGenerator[aiohttp.ClientSession]:
    """Return a mocked aiohttp session that is closed after the test."""
    client_session = aioclient_mock.create_session(asyncio.get_running_loop())
    yield client_session
    await client_session.close()


def _client(session: aiohttp.ClientSession) -> BInformedClient:
    return BInformedClient(session, "gn_testkey")


async def test_validate_key_uses_notify_without_sending(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """Validation probes /v1/notify with an empty body and no message.

    /v1/notify is the only endpoint accepting X-API-Key, so it is the only one
    that can validate a key. The 400 it returns for the empty body proves the
    key was accepted, and guarantees no notification reached the devices.
    """
    aioclient_mock.post(NOTIFY_URL, status=400, text="message is required")

    await _client(session).async_validate_key()

    assert len(aioclient_mock.mock_calls) == 1
    method, url, data, headers = aioclient_mock.mock_calls[0]
    assert method == "POST"
    assert str(url) == NOTIFY_URL
    assert data == {}
    assert headers["X-API-Key"] == "gn_testkey"


async def test_validate_key_accepts_success(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """A 2xx on the probe is also a valid key."""
    aioclient_mock.post(NOTIFY_URL, json={"ok": True, "pushed": 0, "failed": 0})

    await _client(session).async_validate_key()


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, BInformedAuthError),
        (403, BInformedAccountNotVerifiedError),
        (429, BInformedRateLimitError),
        (500, BInformedError),
    ],
)
async def test_validate_key_propagates_auth_errors(
    aioclient_mock: AiohttpClientMocker,
    session: aiohttp.ClientSession,
    status: int,
    expected: type[Exception],
) -> None:
    """Anything that is not a payload rejection means the key is unusable."""
    aioclient_mock.post(NOTIFY_URL, status=status, text="nope")

    with pytest.raises(expected):
        await _client(session).async_validate_key()


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, BInformedAuthError),
        (403, BInformedAccountNotVerifiedError),
        (429, BInformedRateLimitError),
        (400, BInformedValidationError),
        (500, BInformedError),
    ],
)
async def test_error_mapping(
    aioclient_mock: AiohttpClientMocker,
    session: aiohttp.ClientSession,
    status: int,
    expected: type[Exception],
) -> None:
    """HTTP status codes are mapped onto typed exceptions."""
    aioclient_mock.post(NOTIFY_URL, status=status, text="nope")

    with pytest.raises(expected):
        await _client(session).async_notify("Hello")


async def test_connection_error(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """Transport errors surface as connection errors."""
    aioclient_mock.post(NOTIFY_URL, exc=TimeoutError)

    with pytest.raises(BInformedConnectionError):
        await _client(session).async_validate_key()


async def test_notify_payload(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """Optional fields are only sent when provided."""
    aioclient_mock.post(NOTIFY_URL, json={"ok": True, "pushed": 2, "failed": 0})

    result = await _client(session).async_notify(
        "Hello", title="Alert", url="https://example.com"
    )

    assert (result.pushed, result.failed) == (2, 0)
    assert aioclient_mock.mock_calls[0][2] == {
        "message": "Hello",
        "title": "Alert",
        "url": "https://example.com",
    }


async def test_notify_omits_empty_fields(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """A bare message produces a single-key payload."""
    aioclient_mock.post(NOTIFY_URL, json={"ok": True, "pushed": 1, "failed": 0})

    await _client(session).async_notify("Hello")

    assert aioclient_mock.mock_calls[0][2] == {"message": "Hello"}


@pytest.mark.parametrize(
    ("message", "title", "url"),
    [
        ("", None, None),
        ("x" * 2001, None, None),
        ("Hello", "t" * 201, None),
        ("Hello", None, "http://example.com"),
    ],
)
async def test_notify_client_side_validation(
    aioclient_mock: AiohttpClientMocker,
    session: aiohttp.ClientSession,
    message: str,
    title: str | None,
    url: str | None,
) -> None:
    """Invalid payloads are rejected before hitting the network."""
    with pytest.raises(BInformedValidationError):
        await _client(session).async_notify(message, title=title, url=url)

    assert not aioclient_mock.mock_calls


async def test_custom_base_url(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """A trailing slash in the base URL does not break path joining."""
    aioclient_mock.post(
        "https://example.test/v1/notify", json={"ok": True, "pushed": 1, "failed": 0}
    )

    client = BInformedClient(session, "gn_x", "https://example.test/")
    await client.async_notify("Hello")

    assert str(aioclient_mock.mock_calls[0][1]) == "https://example.test/v1/notify"


async def test_malformed_response(
    aioclient_mock: AiohttpClientMocker, session: aiohttp.ClientSession
) -> None:
    """A non-JSON body raises a generic client error."""
    aioclient_mock.post(NOTIFY_URL, text="not json")

    with pytest.raises(BInformedError):
        await _client(session).async_notify("Hello")
