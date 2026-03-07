"""Tests for the synchronous PigeonsClient."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from pgns.sdk.client import PigeonsClient
from pgns.sdk.errors import PigeonsError
from pgns.sdk.models import (
    CreateRoost,
    UpdateRoost,
)
from pgns.sdk.tests.conftest import (
    API_KEY,
    BASE_URL,
    SAMPLE_API_KEY,
    SAMPLE_DESTINATION,
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
        from pgns.sdk.models import PreviewTemplateRequest

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
