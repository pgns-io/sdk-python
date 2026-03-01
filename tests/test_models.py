"""Tests for Pydantic model serialization and validation."""

from __future__ import annotations

from typing import Any

import pytest

from pgns.sdk.models import (
    AuthTokens,
    CreateDestination,
    CreateRoost,
    DeliveryAttempt,
    DeliveryStatus,
    Destination,
    DestinationType,
    PaginatedPigeons,
    Pigeon,
    Roost,
    UpdateRoost,
    User,
)


class TestEnums:
    def test_destination_type_values(self) -> None:
        assert DestinationType.url.value == "url"
        assert DestinationType.slack.value == "slack"
        assert DestinationType.discord.value == "discord"
        assert DestinationType.email.value == "email"

    def test_delivery_status_values(self) -> None:
        assert DeliveryStatus.pending.value == "pending"
        assert DeliveryStatus.delivered.value == "delivered"
        assert DeliveryStatus.failed.value == "failed"


class TestResponseModels:
    def test_roost_from_json(self) -> None:
        data = {
            "id": "r1",
            "name": "Test",
            "description": "desc",
            "secret": None,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        roost = Roost.model_validate(data)
        assert roost.id == "r1"
        assert roost.secret is None
        assert roost.is_active is True

    def test_pigeon_from_json(self) -> None:
        data = {
            "id": "p1",
            "roost_id": "r1",
            "source_ip": "1.2.3.4",
            "request_method": "POST",
            "content_type": "application/json",
            "headers": {"x-foo": "bar"},
            "body_json": {"key": "value"},
            "body_raw": None,
            "request_query": None,
            "filtered": False,
            "replayed_from": None,
            "delivery_status": "delivered",
            "received_at": "2024-01-01T00:00:00Z",
        }
        pigeon = Pigeon.model_validate(data)
        assert pigeon.delivery_status == DeliveryStatus.delivered
        assert pigeon.headers["x-foo"] == "bar"

    def test_destination_from_json(self) -> None:
        data = {
            "id": "d1",
            "roost_id": "r1",
            "destination_type": "slack",
            "config": {"webhook_url": "https://hooks.slack.com/..."},
            "filter_expression": "",
            "template": "",
            "retry_max": 5,
            "retry_delay_ms": 1000,
            "retry_multiplier": 2.0,
            "is_paused": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        dest = Destination.model_validate(data)
        assert dest.destination_type == DestinationType.slack

    def test_user_from_json(self) -> None:
        data = {
            "id": "u1",
            "email": "a@b.com",
            "name": "Alice",
            "plan": "pro",
            "tos_accepted_at": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        user = User.model_validate(data)
        assert user.plan == "pro"
        assert user.tos_accepted_at is None

    def test_auth_tokens(self) -> None:
        data = {"access_token": "tok", "token_type": "Bearer", "expires_in": 3600}
        tokens = AuthTokens.model_validate(data)
        assert tokens.expires_in == 3600

    def test_paginated_pigeons(self) -> None:
        pigeon_data: dict[str, Any] = {
            "id": "p1",
            "roost_id": "r1",
            "source_ip": "1.2.3.4",
            "request_method": "POST",
            "content_type": "application/json",
            "headers": {},
            "body_json": None,
            "body_raw": None,
            "request_query": None,
            "filtered": False,
            "replayed_from": None,
            "delivery_status": "pending",
            "received_at": "2024-01-01T00:00:00Z",
        }
        data = {"data": [pigeon_data], "next_cursor": "cur_123", "has_more": True}
        page = PaginatedPigeons.model_validate(data)
        assert len(page.data) == 1
        assert page.next_cursor == "cur_123"
        assert page.has_more is True

    def test_delivery_attempt(self) -> None:
        data = {
            "id": "da1",
            "pigeon_id": "p1",
            "destination_id": "d1",
            "status": "failed",
            "attempt_number": 3,
            "response_status": 500,
            "response_body": "Internal Server Error",
            "error_message": "timeout",
            "attempted_at": "2024-01-01T00:01:00Z",
            "next_retry_at": "2024-01-01T00:02:00Z",
        }
        attempt = DeliveryAttempt.model_validate(data)
        assert attempt.status == DeliveryStatus.failed
        assert attempt.attempt_number == 3


class TestRequestModels:
    def test_create_roost_exclude_none(self) -> None:
        req = CreateRoost(name="Test")
        dumped = req.model_dump(exclude_none=True)
        assert dumped == {"name": "Test"}

    def test_update_roost_exclude_unset(self) -> None:
        req = UpdateRoost(name="Updated")
        dumped = req.model_dump(exclude_unset=True)
        assert dumped == {"name": "Updated"}
        assert "description" not in dumped
        assert "is_active" not in dumped

    def test_create_destination_full(self) -> None:
        req = CreateDestination(
            destination_type=DestinationType.url,
            config={"url": "https://example.com"},
            retry_max=3,
        )
        dumped = req.model_dump(exclude_none=True)
        assert dumped["destination_type"] == "url"
        assert dumped["retry_max"] == 3
        assert "filter_expression" not in dumped

    def test_model_validation_error(self) -> None:
        with pytest.raises(ValueError):
            Roost.model_validate({"id": "r1"})  # missing required fields
