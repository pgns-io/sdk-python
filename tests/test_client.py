# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Tests for the synchronous PigeonsClient."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from pgns.client import PigeonsClient
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
    SAMPLE_API_KEY,
    SAMPLE_APPLICATION,
    SAMPLE_ARTIFACT,
    SAMPLE_CREATE_ARTIFACT_RESPONSE,
    SAMPLE_DESTINATION,
    SAMPLE_ENDPOINT,
    SAMPLE_PIGEON,
    SAMPLE_ROOST,
    SAMPLE_TEMPLATE,
    SAMPLE_USER,
    make_client,
)


class TestAuth:
    def test_auth_header_api_key(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == f"Bearer {API_KEY}"
            return httpx.Response(200, json=[])

        client = make_client(handler)
        client.list_roosts()

    def test_auth_header_access_token(self) -> None:
        token = "eyJhbG.test.token"

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == f"Bearer {token}"
            return httpx.Response(200, json=[])

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = PigeonsClient(BASE_URL, access_token=token, http_client=http)
        client.list_roosts()

    def test_logout(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/auth/logout"
            return httpx.Response(204)

        client = make_client(handler)
        client.logout()

    def test_401_refresh_retry(self) -> None:
        """On 401 with JWT auth, the client should refresh and retry."""
        call_count = 0
        tokens_data = {"access_token": "refreshed", "token_type": "Bearer", "expires_in": 3600}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if request.url.path == "/v1/auth/refresh":
                return httpx.Response(200, json=tokens_data)
            if call_count == 1:
                return httpx.Response(401, json={"error": "token expired"})
            return httpx.Response(200, json=[SAMPLE_ROOST])

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = PigeonsClient(BASE_URL, access_token="expired", http_client=http)
        roosts = client.list_roosts()
        assert len(roosts) == 1
        assert call_count == 3  # original + refresh + retry


class TestErrorHandling:
    def test_404_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"error": "not found"})

        client = make_client(handler)
        with pytest.raises(PigeonsError) as exc_info:
            client.get_roost("nonexistent")
        assert exc_info.value.status == 404
        assert exc_info.value.is_not_found()

    def test_500_raises(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, json={"error": "internal error"})

        client = make_client(handler)
        with pytest.raises(PigeonsError) as exc_info:
            client.list_roosts()
        assert exc_info.value.status == 500

    def test_non_json_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(502, content=b"Bad Gateway")

        client = make_client(handler)
        with pytest.raises(PigeonsError):
            client.list_roosts()


class TestRoosts:
    def test_list_roosts(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts"
            return httpx.Response(200, json=[SAMPLE_ROOST])

        client = make_client(handler)
        roosts = client.list_roosts()
        assert len(roosts) == 1
        assert roosts[0].id == "roost_abc123"
        assert roosts[0].is_active is True

    def test_get_roost(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts/roost_abc123"
            return httpx.Response(200, json=SAMPLE_ROOST)

        client = make_client(handler)
        roost = client.get_roost("roost_abc123")
        assert roost.name == "Test Roost"

    def test_create_roost(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["name"] == "New Roost"
            assert "description" not in body  # exclude_none
            return httpx.Response(201, json={**SAMPLE_ROOST, "name": "New Roost"})

        client = make_client(handler)
        roost = client.create_roost(CreateRoost(name="New Roost"))
        assert roost.name == "New Roost"

    def test_update_roost(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body == {"name": "Updated"}  # exclude_unset
            return httpx.Response(200, json={**SAMPLE_ROOST, "name": "Updated"})

        client = make_client(handler)
        roost = client.update_roost("roost_abc123", UpdateRoost(name="Updated"))
        assert roost.name == "Updated"

    def test_delete_roost(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            return httpx.Response(204)

        client = make_client(handler)
        client.delete_roost("roost_abc123")


class TestPigeons:
    def test_list_pigeons(self) -> None:
        paginated = {"data": [SAMPLE_PIGEON], "next_cursor": None, "has_more": False}

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/pigeons"
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        result = client.list_pigeons()
        assert len(result.data) == 1
        assert result.has_more is False

    def test_list_pigeons_with_filters(self) -> None:
        paginated: dict[str, Any] = {"data": [], "next_cursor": None, "has_more": False}

        def handler(request: httpx.Request) -> httpx.Response:
            assert "roost_id=roost_abc123" in str(request.url)
            assert "limit=10" in str(request.url)
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        client.list_pigeons(roost_id="roost_abc123", limit=10)

    def test_replay_pigeon(self) -> None:
        replay = {"replayed": True, "pigeon_id": "pgn_abc123", "delivery_attempts": 2}

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/v1/pigeons/pgn_abc123/replay"
            return httpx.Response(200, json=replay)

        client = make_client(handler)
        result = client.replay_pigeon("pgn_abc123")
        assert result.replayed is True
        assert result.delivery_attempts == 2


class TestDestinations:
    def test_list_destinations(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts/roost_abc123/destinations"
            return httpx.Response(200, json=[SAMPLE_DESTINATION])

        client = make_client(handler)
        dests = client.list_destinations("roost_abc123")
        assert len(dests) == 1
        assert dests[0].destination_type.value == "url"

    def test_pause_destination(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["is_paused"] is True
            return httpx.Response(200, json={"is_paused": True})

        client = make_client(handler)
        result = client.pause_destination("dest_abc123", True)
        assert result.is_paused is True

    def test_delete_destination(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            return httpx.Response(204)

        client = make_client(handler)
        client.delete_destination("dest_abc123")


class TestApiKeys:
    def test_list_api_keys(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[SAMPLE_API_KEY])

        client = make_client(handler)
        keys = client.list_api_keys()
        assert len(keys) == 1
        assert keys[0].key_prefix == "pk_live_test1234"

    def test_create_api_key(self) -> None:
        created = {**SAMPLE_API_KEY, "key": "pk_live_fullkeyvalue1234567890abcdef12345678"}

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(201, json=created)

        client = make_client(handler)
        result = client.create_api_key()
        assert result.key.startswith("pk_live_")


class TestTemplates:
    def test_list_templates(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=[SAMPLE_TEMPLATE])

        client = make_client(handler)
        templates = client.list_templates()
        assert len(templates) == 1
        assert templates[0].name == "Test Template"

    def test_preview_template(self) -> None:
        from pgns.models import PreviewTemplateRequest

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["body"] == "{{ body }}"
            assert body["pigeon_id"] == "pgn_abc123"
            return httpx.Response(200, json={"rendered": "hello world"})

        client = make_client(handler)
        result = client.preview_template(
            PreviewTemplateRequest(body="{{ body }}", pigeon_id="pgn_abc123")
        )
        assert result.rendered == "hello world"


class TestSend:
    def test_send_signed_webhook(self) -> None:
        """send() computes HMAC-SHA256 and sets correct headers."""
        import hashlib
        import hmac as hmac_mod

        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url)
            captured["headers"] = dict(request.headers)
            captured["body"] = request.content.decode()
            return httpx.Response(
                200,
                json={"id": "pgn_test123", "status": "received", "destinations": 1},
            )

        client = make_client(handler)
        result = client.send(
            "rst_abc",
            event_type="order.created",
            payload={"order_id": "123"},
            signing_secret="test-secret",
        )

        assert result.id == "pgn_test123"
        assert result.status == "received"
        assert result.destinations == 1
        assert captured["url"].endswith("/r/rst_abc")
        assert captured["headers"]["x-pigeon-event-type"] == "order.created"
        assert captured["headers"]["x-pigeon-signature"].startswith("sha256=")

        # Verify the legacy HMAC is correct
        ts = captured["headers"]["x-pigeon-timestamp"]
        body = captured["body"]
        expected_sig = hmac_mod.new(
            b"test-secret",
            f"{ts}.{body}".encode(),
            hashlib.sha256,
        ).hexdigest()
        assert captured["headers"]["x-pigeon-signature"] == f"sha256={expected_sig}"

        # Verify Standard Webhooks headers
        import base64
        import re

        msg_id = captured["headers"]["webhook-id"]
        assert re.match(r"^msg_[0-9a-f-]{36}$", msg_id)
        assert captured["headers"]["webhook-timestamp"] == ts
        wh_sig = captured["headers"]["webhook-signature"]
        assert wh_sig.startswith("v1,")

        # Verify Standard Webhooks HMAC
        expected_std = base64.b64encode(
            hmac_mod.new(
                b"test-secret",
                f"{msg_id}.{ts}.{body}".encode(),
                hashlib.sha256,
            ).digest()
        ).decode()
        assert wh_sig == f"v1,{expected_std}"


class TestUserAndStats:
    def test_get_me(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/me"
            return httpx.Response(200, json=SAMPLE_USER)

        client = make_client(handler)
        user = client.get_me()
        assert user.email == "test@example.com"


class TestApplications:
    def test_list_applications(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/applications"
            return httpx.Response(200, json=[SAMPLE_APPLICATION])

        client = make_client(handler)
        apps = client.list_applications()
        assert len(apps) == 1
        assert apps[0].id == "app_abc123"
        assert apps[0].signing_key == "whsec_test123"

    def test_get_application(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/applications/app_abc123"
            return httpx.Response(200, json=SAMPLE_APPLICATION)

        client = make_client(handler)
        app = client.get_application("app_abc123")
        assert app.name == "Test Application"

    def test_create_application(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["name"] == "My App"
            assert "external_id" not in body  # exclude_none
            return httpx.Response(201, json={**SAMPLE_APPLICATION, "name": "My App"})

        client = make_client(handler)
        app = client.create_application(CreateApplication(name="My App"))
        assert app.name == "My App"

    def test_delete_application(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert request.url.path == "/v1/applications/app_abc123"
            return httpx.Response(204)

        client = make_client(handler)
        client.delete_application("app_abc123")


class TestEndpoints:
    def test_list_endpoints(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/applications/app_abc123/endpoints"
            return httpx.Response(200, json=[SAMPLE_ENDPOINT])

        client = make_client(handler)
        eps = client.list_endpoints("app_abc123")
        assert len(eps) == 1
        assert eps[0].customer_id == "cust_abc123"

    def test_list_endpoints_with_customer_filter(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "customer_id=cust_abc123" in str(request.url)
            return httpx.Response(200, json=[SAMPLE_ENDPOINT])

        client = make_client(handler)
        client.list_endpoints("app_abc123", customer_id="cust_abc123")

    def test_create_endpoint(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert body["url"] == "https://example.com/hook"
            assert body["customer_id"] == "cust_abc123"
            return httpx.Response(201, json=SAMPLE_ENDPOINT)

        client = make_client(handler)
        ep = client.create_endpoint(
            "app_abc123",
            CreateEndpoint(url="https://example.com/hook", customer_id="cust_abc123"),
        )
        assert ep.id == "ep_abc123"

    def test_delete_endpoint(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert request.url.path == "/v1/applications/app_abc123/endpoints/ep_abc123"
            return httpx.Response(204)

        client = make_client(handler)
        client.delete_endpoint("app_abc123", "ep_abc123")

    def test_list_endpoint_attempts(self) -> None:
        paginated: dict[str, Any] = {
            "data": [],
            "next_cursor": None,
            "has_more": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "/endpoints/ep_abc123/attempts" in request.url.path
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        result = client.list_endpoint_attempts("app_abc123", "ep_abc123")
        assert result.has_more is False

    def test_list_endpoint_attempts_with_pagination(self) -> None:
        paginated: dict[str, Any] = {
            "data": [],
            "next_cursor": None,
            "has_more": False,
        }

        def handler(request: httpx.Request) -> httpx.Response:
            assert "limit=10" in str(request.url)
            assert "cursor=abc" in str(request.url)
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        client.list_endpoint_attempts("app_abc123", "ep_abc123", limit=10, cursor="abc")


class TestPublishMessage:
    def test_publish_message(self) -> None:
        response_data = {"pigeon_id": "pgn_test123", "endpoints_matched": 3}

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/applications/app_abc123/messages"
            body = json.loads(request.content)
            assert body["event_type"] == "order.created"
            assert body["customer_id"] == "cust_abc123"
            assert body["data"] == {"order_id": "123"}
            return httpx.Response(200, json=response_data)

        client = make_client(handler)
        result = client.publish_message(
            "app_abc123",
            PublishMessage(
                event_type="order.created",
                customer_id="cust_abc123",
                data={"order_id": "123"},
            ),
        )
        assert result.pigeon_id == "pgn_test123"
        assert result.endpoints_matched == 3


class TestArtifacts:
    def test_create_artifact_dict(self) -> None:
        """create_artifact with dict data serializes to JSON."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["content-type"] == "application/json"
            assert request.content == b'{"key":"value"}'
            return httpx.Response(201, json=SAMPLE_CREATE_ARTIFACT_RESPONSE)

        client = make_client(handler)
        result = client.create_artifact({"key": "value"})
        assert result.artifact_id == "art_01HXYZ0123456789abcdefghij"
        assert result.access_token == "dGhpcyBpcyBhIHRva2Vu"

    def test_create_artifact_bytes(self) -> None:
        """create_artifact with bytes and custom content type."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["content-type"] == "application/octet-stream"
            assert request.content == b"\x00\x01\x02"
            return httpx.Response(201, json=SAMPLE_CREATE_ARTIFACT_RESPONSE)

        client = make_client(handler)
        result = client.create_artifact(b"\x00\x01\x02", content_type="application/octet-stream")
        assert result.size_bytes == 1024

    def test_create_artifact_with_headers(self) -> None:
        """create_artifact passes task_id, correlation_id, auto_delete."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["x-pgns-task-id"] == "task_abc123"
            assert request.headers["x-pgns-correlation-id"] == "corr_abc123"
            assert "auto_delete=true" in str(request.url)
            return httpx.Response(201, json=SAMPLE_CREATE_ARTIFACT_RESPONSE)

        client = make_client(handler)
        client.create_artifact(
            {"data": 1},
            task_id="task_abc123",
            correlation_id="corr_abc123",
            auto_delete=True,
        )

    def test_get_artifact_owner(self) -> None:
        """get_artifact with API key auth returns raw bytes."""
        body = b"raw artifact content"

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["authorization"] == f"Bearer {API_KEY}"
            assert request.url.path == "/v1/artifacts/art_01HXYZ0123456789abcdefghij"
            return httpx.Response(200, content=body)

        client = make_client(handler)
        data, _ct = client.get_artifact("art_01HXYZ0123456789abcdefghij")
        assert data == body

    def test_get_artifact_with_token(self) -> None:
        """get_artifact with token query param."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert "token=dGhpcyBpcyBhIHRva2Vu" in str(request.url)
            return httpx.Response(200, content=b"data")

        client = make_client(handler)
        data, _ct = client.get_artifact(
            "art_01HXYZ0123456789abcdefghij", token="dGhpcyBpcyBhIHRva2Vu"
        )
        assert data == b"data"

    def test_list_artifacts(self) -> None:
        """list_artifacts returns paginated response."""
        paginated = {"data": [SAMPLE_ARTIFACT], "next_cursor": None, "has_more": False}

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/artifacts"
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        result = client.list_artifacts()
        assert len(result.data) == 1
        assert result.data[0].id == "art_01HXYZ0123456789abcdefghij"
        assert result.has_more is False

    def test_list_artifacts_with_correlation_id(self) -> None:
        """list_artifacts with correlation_id filter."""
        paginated = {"data": [SAMPLE_ARTIFACT], "next_cursor": None, "has_more": False}

        def handler(request: httpx.Request) -> httpx.Response:
            assert "correlation_id=corr_abc123" in str(request.url)
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        client.list_artifacts(correlation_id="corr_abc123")

    def test_list_artifacts_with_task_id(self) -> None:
        """list_artifacts with task_id filter."""
        paginated: dict[str, object] = {"data": [], "next_cursor": None, "has_more": False}

        def handler(request: httpx.Request) -> httpx.Response:
            assert "task_id=task_abc123" in str(request.url)
            return httpx.Response(200, json=paginated)

        client = make_client(handler)
        client.list_artifacts(task_id="task_abc123")

    def test_delete_artifact(self) -> None:
        """delete_artifact sends DELETE and handles 204."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            assert request.url.path == "/v1/artifacts/art_01HXYZ0123456789abcdefghij"
            return httpx.Response(204)

        client = make_client(handler)
        client.delete_artifact("art_01HXYZ0123456789abcdefghij")

    def test_create_artifact_error_json_body(self) -> None:
        """create_artifact raises PigeonsError on 4xx with JSON error body."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                413, json={"error": "Artifact too large", "code": "artifact_too_large"}
            )

        client = make_client(handler)
        with pytest.raises(PigeonsError) as exc_info:
            client.create_artifact({"key": "value"})
        assert exc_info.value.status == 413
        assert "Artifact too large" in str(exc_info.value)

    def test_get_artifact_error_non_json_body(self) -> None:
        """get_artifact raises PigeonsError on 4xx with non-JSON body."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="Not Found")

        client = make_client(handler)
        with pytest.raises(PigeonsError) as exc_info:
            client.get_artifact("art_nonexistent")
        assert exc_info.value.status == 404
