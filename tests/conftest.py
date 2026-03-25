# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Shared test fixtures for the pgns SDK."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from pgns.async_client import AsyncPigeonsClient
from pgns.client import PigeonsClient

BASE_URL = "https://api.pgns.io"
API_KEY = "pk_live_test1234567890abcdefghijklmnopqrstuvwxyz1234"


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> PigeonsClient:
    """Create a sync PigeonsClient backed by a mock transport."""
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return PigeonsClient(BASE_URL, api_key=API_KEY, http_client=http_client)


def make_async_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> AsyncPigeonsClient:
    """Create an async PigeonsClient backed by a mock transport."""
    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    return AsyncPigeonsClient(BASE_URL, api_key=API_KEY, http_client=http_client)


SAMPLE_ROOST: dict[str, Any] = {
    "id": "roost_abc123",
    "name": "Test Roost",
    "description": "A test roost",
    "secret": None,
    "is_active": True,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

SAMPLE_PIGEON: dict[str, Any] = {
    "id": "pgn_abc123",
    "roost_id": "roost_abc123",
    "source_ip": "127.0.0.1",
    "request_method": "POST",
    "content_type": "application/json",
    "headers": {"content-type": "application/json"},
    "body_json": {"hello": "world"},
    "body_raw": None,
    "request_query": None,
    "replayed_from": None,
    "delivery_status": "delivered",
    "received_at": "2024-01-01T00:00:00Z",
}

SAMPLE_DESTINATION: dict[str, Any] = {
    "id": "dest_abc123",
    "roost_id": "roost_abc123",
    "name": "My Webhook",
    "destination_type": "url",
    "config": {"url": "https://example.com/webhook"},
    "filter_expression": "",
    "template": "",
    "retry_max": 5,
    "retry_delay_ms": 1000,
    "retry_multiplier": 2.0,
    "is_paused": False,
    "is_verified": True,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

SAMPLE_API_KEY: dict[str, Any] = {
    "id": "key_abc123",
    "key_prefix": "pk_live_test1234",
    "name": "Default",
    "last_used": None,
    "revoked_at": None,
    "created_at": "2024-01-01T00:00:00Z",
}

SAMPLE_USER: dict[str, Any] = {
    "id": "user_abc123",
    "email": "test@example.com",
    "name": "Test User",
    "plan": "free",
    "mfa_enabled": False,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

SAMPLE_TEMPLATE: dict[str, Any] = {
    "id": "tmpl_abc123",
    "name": "Test Template",
    "description": "A test template",
    "body": "{{ body }}",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

SAMPLE_APPLICATION: dict[str, Any] = {
    "id": "app_abc123",
    "user_id": "user_abc123",
    "roost_id": "roost_abc123",
    "external_id": None,
    "name": "Test Application",
    "metadata": {},
    "signing_key": "whsec_test123",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}

SAMPLE_ENDPOINT: dict[str, Any] = {
    "id": "ep_abc123",
    "application_id": "app_abc123",
    "destination_id": "dest_abc123",
    "customer_id": "cust_abc123",
    "subscribed_events": ["order.created", "order.updated"],
    "signing_secret": None,
    "metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
}
