"""Shared helpers for sync and async clients."""

from __future__ import annotations

from typing import Any

import httpx

from pgns.sdk.errors import PigeonsError


def _auth_headers(api_key: str | None, access_token: str | None) -> dict[str, str]:
    """Build the Authorization header dict."""
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}


def _handle_response(response: httpx.Response) -> Any:
    """Parse an httpx response, raising PigeonsError on non-2xx."""
    if response.status_code == 204:
        return None
    if not response.is_success:
        try:
            body = response.json()
            message = body.get("error", response.reason_phrase or "Unknown error")
        except Exception:
            message = response.reason_phrase or "Unknown error"
        raise PigeonsError(message, response.status_code)
    return response.json()
