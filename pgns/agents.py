# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Agent pattern helpers for correlation ID propagation and validation.

These utilities make it easy to thread correlation IDs through multi-agent
pipelines when sending and receiving webhooks via pgns::

    from pgns.agents import extract_correlation_id, correlation_headers

    # Extract from inbound request headers
    cid = extract_correlation_id(request.headers)

    # Forward to outbound call
    requests.post(url, headers=correlation_headers(cid))
"""

from __future__ import annotations

__all__ = [
    "CORRELATION_ID_HEADER",
    "CORRELATION_ID_PATTERN",
    "validate_correlation_id",
    "correlation_headers",
    "extract_correlation_id",
]

import re
from collections.abc import Mapping

CORRELATION_ID_HEADER = "X-Pgns-CorrelationId"
"""Header name used by pgns for correlation ID propagation."""

_FALLBACK_HEADERS = ("X-Correlation-ID", "X-Request-ID")
"""Headers checked (in order) when the primary header is absent."""

CORRELATION_ID_PATTERN: re.Pattern[str] = re.compile(r"[\x21-\x7E]{1,128}")
"""Printable ASCII, 1–128 characters — the server-enforced format."""


def validate_correlation_id(cid: str) -> bool:
    """Return ``True`` if *cid* matches the pgns correlation ID format."""
    return bool(CORRELATION_ID_PATTERN.fullmatch(cid))


def correlation_headers(correlation_id: str | None) -> dict[str, str]:
    """Build a headers dict containing ``X-Pgns-CorrelationId`` if *correlation_id* is valid.

    Returns an empty dict when the value is ``None`` or fails validation,
    so callers can safely spread the result into an existing headers mapping::

        headers = {"Content-Type": "application/json", **correlation_headers(cid)}
    """
    if correlation_id is not None and validate_correlation_id(correlation_id):
        return {CORRELATION_ID_HEADER: correlation_id}
    return {}


def extract_correlation_id(headers: Mapping[str, str]) -> str | None:
    """Extract a correlation ID from a headers mapping.

    Checks the following headers in priority order:

    1. ``X-Pgns-CorrelationId`` (pgns native)
    2. ``X-Correlation-ID`` (common convention)
    3. ``X-Request-ID`` (fallback)

    Header lookup is case-insensitive. Returns ``None`` if no header is
    present or the value fails validation.
    """
    lower = {k.lower(): v for k, v in headers.items()}
    for name in (CORRELATION_ID_HEADER, *_FALLBACK_HEADERS):
        value = lower.get(name.lower())
        if value is not None:
            if validate_correlation_id(value):
                return value
            if name == CORRELATION_ID_HEADER:
                return None
            # else continue to next fallback
    return None
