"""Shared async HTTP client for the Hevy API.

Provides:
- ``BASE_URL`` — the Hevy API root.
- ``HevyAPIError`` — structured error raised on non-2xx responses.
- ``hevy_request`` — the single entry point every tool uses to hit the API.
- ``close_client`` — best-effort cleanup for the module-level client.
"""

from __future__ import annotations

import httpx

from hevy.utils.auth import get_credentials

BASE_URL = "https://api.hevyapp.com"


class HevyAPIError(Exception):
    """Raised when the Hevy API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, endpoint: str):
        self.status_code = status_code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"Hevy API {status_code} at {endpoint}: {message}")


_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return the module-level ``httpx.AsyncClient``, creating it on first use."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    return _client


async def close_client() -> None:
    """Close the module-level client if it was created. Safe to call multiple times."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _humanize_error(status_code: int, err: str, raw_body: str) -> str:
    """Map a Hevy status code + parsed error string to a human-readable message."""
    err = err or raw_body or ""
    err = err.strip()
    if status_code == 400:
        return f"Bad request: {err}" if err else "Invalid request"
    if status_code == 401:
        return f"Unauthorized: {err}" if err else "Unauthorized"
    if status_code == 403:
        return f"Forbidden: {err}" if err else "Forbidden"
    if status_code == 404:
        return f"Not found: {err}" if err else "Not found"
    if status_code == 409:
        return f"Conflict: {err}" if err else "Conflict"
    if status_code == 429:
        return f"Rate limited: {err}" if err else "Rate limited"
    if status_code >= 500:
        return "Hevy server error"
    return f"HTTP {status_code}: {err}" if err else f"HTTP {status_code}"


async def hevy_request(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_body: dict | None = None,
) -> dict | list | None:
    """Perform an authenticated request against the Hevy API.

    Args:
        method: HTTP method (``GET``, ``POST``, ``PUT``, ``DELETE``, ...).
        path: Path starting with ``/`` (e.g. ``/v1/user/info``). Prepended with ``BASE_URL``.
        params: Optional query params. ``None``-valued keys are filtered out.
        json_body: Optional JSON request body. Only sent when provided.

    Returns:
        Parsed JSON (``dict`` or ``list``) on 2xx, or ``None`` if the body is empty.

    Raises:
        HevyAPIError: On non-2xx responses, with a human-readable ``message``.
    """
    creds = await get_credentials()
    api_key = creds.get("api_key", "")
    headers = {
        "api-key": api_key,
        "Accept": "application/json",
    }

    kwargs: dict = {"headers": headers}
    if params is not None:
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
    if json_body is not None:
        kwargs["json"] = json_body

    url = f"{BASE_URL}{path}"
    client = _get_client()
    response = await client.request(method, url, **kwargs)

    if 200 <= response.status_code < 300:
        content_length = response.headers.get("content-length")
        if content_length == "0" or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return None

    # Non-2xx: try to extract a structured error message from the body.
    err_text = ""
    raw_body = response.text or ""
    try:
        body = response.json()
        if isinstance(body, dict):
            err_text = (
                body.get("error")
                or body.get("message")
                or body.get("detail")
                or ""
            )
            if not isinstance(err_text, str):
                err_text = str(err_text)
    except ValueError:
        err_text = raw_body

    message = _humanize_error(response.status_code, err_text, raw_body)
    raise HevyAPIError(response.status_code, message, path)
