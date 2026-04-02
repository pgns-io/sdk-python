# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Shared helpers for sync and async clients."""

from __future__ import annotations

from typing import Any

import httpx

from pgns.errors import PigeonsError


def _auth_headers(api_key: str | None, access_token: str | None) -> dict[str, str]:
    """Build the Authorization header dict."""
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}


def _raise_for_status(response: httpx.Response) -> None:
    """Raise PigeonsError if the response is not successful."""
    if not response.is_success:
        try:
            body = response.json()
            message = body.get("error", response.reason_phrase or "Unknown error")
            code = body.get("code")
        except Exception:
            message = response.reason_phrase or "Unknown error"
            code = None
        raise PigeonsError(message, response.status_code, code=code)


def _handle_response(response: httpx.Response) -> Any:
    """Parse an httpx response, raising PigeonsError on non-2xx."""
    if response.status_code == 204:
        return None
    _raise_for_status(response)
    return response.json()


def _handle_raw_response(response: httpx.Response) -> bytes:
    """Return raw bytes from a successful response, raising PigeonsError on non-2xx."""
    _raise_for_status(response)
    return response.content
