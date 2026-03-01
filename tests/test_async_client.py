"""Tests for the asynchronous AsyncPigeonsClient."""

from __future__ import annotations

import json

import httpx
import pytest

from pgns.sdk.async_client import AsyncPigeonsClient
from pgns.sdk.errors import PigeonsError
from pgns.sdk.models import CreateRoost, UpdateRoost
from pgns.sdk.tests.conftest import (
    API_KEY,
    BASE_URL,
    SAMPLE_PIGEON,
    SAMPLE_ROOST,
    SAMPLE_USER,
    make_async_client,
)


@pytest.mark.asyncio
async def test_list_roosts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {API_KEY}"
        return httpx.Response(200, json=[SAMPLE_ROOST])

    client = make_async_client(handler)
    roosts = await client.list_roosts()
    assert len(roosts) == 1
    assert roosts[0].id == "roost_abc123"


@pytest.mark.asyncio
async def test_create_roost() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["name"] == "Async Roost"
        return httpx.Response(201, json={**SAMPLE_ROOST, "name": "Async Roost"})

    client = make_async_client(handler)
    roost = await client.create_roost(CreateRoost(name="Async Roost"))
    assert roost.name == "Async Roost"


@pytest.mark.asyncio
async def test_update_roost_exclude_unset() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body == {"name": "Updated"}
        return httpx.Response(200, json={**SAMPLE_ROOST, "name": "Updated"})

    client = make_async_client(handler)
    roost = await client.update_roost("roost_abc123", UpdateRoost(name="Updated"))
    assert roost.name == "Updated"


@pytest.mark.asyncio
async def test_delete_roost_204() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(204)

    client = make_async_client(handler)
    await client.delete_roost("roost_abc123")


@pytest.mark.asyncio
async def test_error_handling() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "not found"})

    client = make_async_client(handler)
    with pytest.raises(PigeonsError) as exc_info:
        await client.get_roost("nonexistent")
    assert exc_info.value.status == 404


@pytest.mark.asyncio
async def test_list_pigeons_paginated() -> None:
    paginated = {"data": [SAMPLE_PIGEON], "next_cursor": "abc", "has_more": True}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=paginated)

    client = make_async_client(handler)
    result = await client.list_pigeons(roost_id="roost_abc123", limit=1)
    assert len(result.data) == 1
    assert result.has_more is True
    assert result.next_cursor == "abc"


@pytest.mark.asyncio
async def test_401_refresh_retry() -> None:
    call_count = 0
    tokens_data = {"access_token": "refreshed", "token_type": "Bearer", "expires_in": 3600}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if request.url.path == "/v1/auth/refresh":
            return httpx.Response(200, json=tokens_data)
        if call_count == 1:
            return httpx.Response(401, json={"error": "token expired"})
        return httpx.Response(200, json=SAMPLE_USER)

    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport)
    client = AsyncPigeonsClient(BASE_URL, access_token="expired", http_client=http)
    user = await client.get_me()
    assert user.email == "test@example.com"
