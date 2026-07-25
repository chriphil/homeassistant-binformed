"""Minimal asynchronous client for the BInformed API.

Only ``POST /v1/notify`` is used: it is the *only* endpoint of the BInformed
API that accepts the ``X-API-Key`` header. Every management endpoint
(``/v1/me``, ``/v1/devices``, ``/v1/keys/rotate``, ...) requires a Bearer JWT
obtained through ``/v1/auth/login``, which this integration deliberately does
not handle.

That constraint also shapes how credentials are validated: see
:meth:`BInformedClient.async_validate_key`.

See https://binformed.gericos.com/api-docs for the full API documentation.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Self

import aiohttp
from yarl import URL

from .const import DEFAULT_BASE_URL, LOGGER, MAX_MESSAGE_LENGTH, MAX_TITLE_LENGTH

REQUEST_TIMEOUT = 10
API_KEY_HEADER = "X-API-Key"


class BInformedError(Exception):
    """Base error raised by the BInformed client."""


class BInformedConnectionError(BInformedError):
    """The BInformed API could not be reached."""


class BInformedAuthError(BInformedError):
    """The API key is missing, invalid or has been rotated (HTTP 401)."""


class BInformedAccountNotVerifiedError(BInformedError):
    """The account exists but its email address is not verified (HTTP 403)."""


class BInformedRateLimitError(BInformedError):
    """Too many requests were sent to the API (HTTP 429)."""


class BInformedValidationError(BInformedError):
    """The payload was rejected by the API (HTTP 400/422)."""


@dataclass(slots=True, frozen=True)
class NotifyResult:
    """Outcome of a POST /v1/notify call."""

    pushed: int
    failed: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> Self:
        """Build a result from the raw API payload."""
        return cls(
            pushed=int(payload.get("pushed", 0) or 0),
            failed=int(payload.get("failed", 0) or 0),
        )


class BInformedClient:
    """Thin wrapper around the BInformed REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        """Initialise the client."""
        self._session = session
        self._api_key = api_key
        self._base_url = URL(base_url.rstrip("/") + "/")

    async def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Perform a request and map HTTP errors onto typed exceptions."""
        url = self._base_url.join(URL(path.lstrip("/")))
        headers = {API_KEY_HEADER: self._api_key, "Accept": "application/json"}

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.request(
                    method, url, headers=headers, json=json
                )
                body = await response.text()
        except TimeoutError as err:
            raise BInformedConnectionError(
                f"Timeout while calling the BInformed API ({method} {path})"
            ) from err
        except aiohttp.ClientError as err:
            raise BInformedConnectionError(
                f"Error while calling the BInformed API ({method} {path}): {err}"
            ) from err

        if response.status == 401:
            raise BInformedAuthError("Invalid or revoked BInformed API key")
        if response.status == 403:
            raise BInformedAccountNotVerifiedError(
                "The BInformed account email address is not verified"
            )
        if response.status == 429:
            raise BInformedRateLimitError("BInformed API rate limit exceeded")
        if response.status in (400, 422):
            raise BInformedValidationError(
                f"BInformed API rejected the request: {body[:200]}"
            )
        if response.status >= 400:
            raise BInformedError(
                f"Unexpected BInformed API response {response.status}: {body[:200]}"
            )

        if not body:
            return {}
        try:
            payload = await response.json(content_type=None)
        except ValueError as err:
            raise BInformedError("BInformed API returned a malformed response") from err

        if not isinstance(payload, dict):
            raise BInformedError("BInformed API returned an unexpected payload")
        return payload

    async def async_validate_key(self) -> None:
        """Check that the API key is accepted, without notifying anyone.

        ``/v1/notify`` is the only endpoint that accepts an API key, so it is
        also the only place where a key can be verified. To avoid pushing a
        test notification to the user's devices, an intentionally incomplete
        body is posted: the API rejects it with a validation error *after*
        having authenticated the request.

        Therefore a validation error means the key was accepted, while
        :class:`BInformedAuthError`, :class:`BInformedAccountNotVerifiedError`
        and :class:`BInformedRateLimitError` propagate to the caller.
        """
        try:
            await self._request("POST", "v1/notify", json={})
        except BInformedValidationError:
            # Authentication passed, only the (deliberately empty) body failed.
            return

    async def async_notify(
        self,
        message: str,
        *,
        title: str | None = None,
        url: str | None = None,
    ) -> NotifyResult:
        """Send a notification to every device registered on the account."""
        if not message:
            raise BInformedValidationError("The notification message must not be empty")
        if len(message) > MAX_MESSAGE_LENGTH:
            raise BInformedValidationError(
                f"The notification message exceeds {MAX_MESSAGE_LENGTH} characters"
            )
        if title is not None and len(title) > MAX_TITLE_LENGTH:
            raise BInformedValidationError(
                f"The notification title exceeds {MAX_TITLE_LENGTH} characters"
            )
        if url is not None and not url.lower().startswith("https://"):
            raise BInformedValidationError("The notification url must use HTTPS")

        payload: dict[str, Any] = {"message": message}
        if title:
            payload["title"] = title
        if url:
            payload["url"] = url

        payload_response = await self._request("POST", "v1/notify", json=payload)
        result = NotifyResult.from_payload(payload_response)
        LOGGER.debug(
            "BInformed notification sent (pushed=%s, failed=%s)",
            result.pushed,
            result.failed,
        )
        return result
