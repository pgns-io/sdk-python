# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Tests for the asynchronous AsyncPigeonsClient."""

from __future__ import annotations

import json

import httpx
import pytest

from pgns.async_client import AsyncPigeonsClient
from pgns.errors import PigeonsError
from pgns.models import (
    CreateApplication,
    CreateEndpoint,
    CreateRoost,
    PublishMessage,
    UpdateRoost,
)
from pgns.tests.conftest import (
    API_KEY,
    BASE_URL,
    SAMPLE_APPLICATION,
    SAMPLE_ARTIFACT,
    SAMPLE_CREATE_ARTIFACT_RESPONSE,
    SAMPLE_ENDPOINT,
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


@pytest.mark.asyncio
async def test_list_applications() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/applications"
        return httpx.Response(200, json=[SAMPLE_APPLICATION])

    client = make_async_client(handler)
    apps = await client.list_applications()
    assert len(apps) == 1
    assert apps[0].id == "app_abc123"


@pytest.mark.asyncio
async def test_create_application() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["name"] == "Async App"
        assert "external_id" not in body
        return httpx.Response(201, json={**SAMPLE_APPLICATION, "name": "Async App"})

    client = make_async_client(handler)
    app = await client.create_application(CreateApplication(name="Async App"))
    assert app.name == "Async App"


@pytest.mark.asyncio
async def test_delete_application() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/v1/applications/app_abc123"
        return httpx.Response(204)

    client = make_async_client(handler)
    await client.delete_application("app_abc123")


@pytest.mark.asyncio
async def test_list_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/applications/app_abc123/endpoints"
        return httpx.Response(200, json=[SAMPLE_ENDPOINT])

    client = make_async_client(handler)
    eps = await client.list_endpoints("app_abc123")
    assert len(eps) == 1
    assert eps[0].customer_id == "cust_abc123"


@pytest.mark.asyncio
async def test_create_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["url"] == "https://example.com/hook"
        return httpx.Response(201, json=SAMPLE_ENDPOINT)

    client = make_async_client(handler)
    ep = await client.create_endpoint(
        "app_abc123",
        CreateEndpoint(url="https://example.com/hook", customer_id="cust_abc123"),
    )
    assert ep.id == "ep_abc123"


@pytest.mark.asyncio
async def test_publish_message() -> None:
    response_data = {"pigeon_id": "pgn_test123", "endpoints_matched": 3}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/applications/app_abc123/messages"
        body = json.loads(request.content)
        assert body["event_type"] == "order.created"
        return httpx.Response(200, json=response_data)

    client = make_async_client(handler)
    result = await client.publish_message(
        "app_abc123",
        PublishMessage(
            event_type="order.created",
            customer_id="cust_abc123",
            data={"order_id": "123"},
        ),
    )
    assert result.pigeon_id == "pgn_test123"
    assert result.endpoints_matched == 3


# -- Artifacts ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_artifact_dict() -> None:
    """create_artifact with dict data serializes to JSON."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"] == "application/json"
        assert request.content == b'{"key":"value"}'
        return httpx.Response(201, json=SAMPLE_CREATE_ARTIFACT_RESPONSE)

    client = make_async_client(handler)
    result = await client.create_artifact({"key": "value"})
    assert result.artifact_id == "art_01HXYZ0123456789abcdefghij"
    assert result.access_token == "dGhpcyBpcyBhIHRva2Vu"


@pytest.mark.asyncio
async def test_create_artifact_bytes() -> None:
    """create_artifact with bytes and custom content type."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"] == "application/octet-stream"
        assert request.content == b"\x00\x01\x02"
        return httpx.Response(201, json=SAMPLE_CREATE_ARTIFACT_RESPONSE)

    client = make_async_client(handler)
    result = await client.create_artifact(b"\x00\x01\x02", content_type="application/octet-stream")
    assert result.size_bytes == 1024


@pytest.mark.asyncio
async def test_create_artifact_with_headers() -> None:
    """create_artifact passes task_id, correlation_id, auto_delete."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-pgns-task-id"] == "task_abc123"
        assert request.headers["x-pgns-correlation-id"] == "corr_abc123"
        assert "auto_delete=true" in str(request.url)
        return httpx.Response(201, json=SAMPLE_CREATE_ARTIFACT_RESPONSE)

    client = make_async_client(handler)
    await client.create_artifact(
        {"data": 1},
        task_id="task_abc123",
        correlation_id="corr_abc123",
        auto_delete=True,
    )


@pytest.mark.asyncio
async def test_get_artifact_owner() -> None:
    """get_artifact with API key auth returns raw bytes."""
    body = b"raw artifact content"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {API_KEY}"
        assert request.url.path == "/v1/artifacts/art_01HXYZ0123456789abcdefghij"
        return httpx.Response(200, content=body)

    client = make_async_client(handler)
    data, _ct = await client.get_artifact("art_01HXYZ0123456789abcdefghij")
    assert data == body


@pytest.mark.asyncio
async def test_get_artifact_with_token() -> None:
    """get_artifact with token query param."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "token=dGhpcyBpcyBhIHRva2Vu" in str(request.url)
        return httpx.Response(200, content=b"data")

    client = make_async_client(handler)
    data, _ct = await client.get_artifact(
        "art_01HXYZ0123456789abcdefghij", token="dGhpcyBpcyBhIHRva2Vu"
    )
    assert data == b"data"


@pytest.mark.asyncio
async def test_list_artifacts() -> None:
    """list_artifacts returns paginated response."""
    paginated = {"data": [SAMPLE_ARTIFACT], "next_cursor": None, "has_more": False}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/artifacts"
        return httpx.Response(200, json=paginated)

    client = make_async_client(handler)
    result = await client.list_artifacts()
    assert len(result.data) == 1
    assert result.data[0].id == "art_01HXYZ0123456789abcdefghij"
    assert result.has_more is False


@pytest.mark.asyncio
async def test_list_artifacts_with_correlation_id() -> None:
    """list_artifacts with correlation_id filter."""
    paginated = {"data": [SAMPLE_ARTIFACT], "next_cursor": None, "has_more": False}

    def handler(request: httpx.Request) -> httpx.Response:
        assert "correlation_id=corr_abc123" in str(request.url)
        return httpx.Response(200, json=paginated)

    client = make_async_client(handler)
    await client.list_artifacts(correlation_id="corr_abc123")


@pytest.mark.asyncio
async def test_list_artifacts_with_task_id() -> None:
    """list_artifacts with task_id filter."""
    paginated: dict[str, object] = {"data": [], "next_cursor": None, "has_more": False}

    def handler(request: httpx.Request) -> httpx.Response:
        assert "task_id=task_abc123" in str(request.url)
        return httpx.Response(200, json=paginated)

    client = make_async_client(handler)
    await client.list_artifacts(task_id="task_abc123")


@pytest.mark.asyncio
async def test_delete_artifact() -> None:
    """delete_artifact sends DELETE and handles 204."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/v1/artifacts/art_01HXYZ0123456789abcdefghij"
        return httpx.Response(204)

    client = make_async_client(handler)
    await client.delete_artifact("art_01HXYZ0123456789abcdefghij")


@pytest.mark.asyncio
async def test_create_artifact_error_json_body() -> None:
    """create_artifact raises PigeonsError on 4xx with JSON error body."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            413, json={"error": "Artifact too large", "code": "artifact_too_large"}
        )

    client = make_async_client(handler)
    with pytest.raises(PigeonsError) as exc_info:
        await client.create_artifact({"key": "value"})
    assert exc_info.value.status == 413
    assert "Artifact too large" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_artifact_error_non_json_body() -> None:
    """get_artifact raises PigeonsError on 4xx with non-JSON body."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    client = make_async_client(handler)
    with pytest.raises(PigeonsError) as exc_info:
        await client.get_artifact("art_nonexistent")
    assert exc_info.value.status == 404
