# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Tests for health check client methods."""

from __future__ import annotations

import json

import httpx
import pytest

from pgns.models import HealthThresholds, RoostHealth
from pgns.tests.conftest import make_async_client, make_client

SAMPLE_HEALTH: dict[str, object] = {
    "roost_id": "roost_abc123",
    "status": "green",
    "metrics": {
        "total_attempts": 100,
        "delivered": 99,
        "failed": 1,
        "retrying": 0,
        "success_rate": 0.99,
        "avg_retries": 0.5,
        "dlq_rate": 0.01,
    },
    "thresholds": {
        "green_min_success_rate": 0.99,
        "green_max_avg_retries": 1.2,
        "green_max_dlq_rate": 0.01,
        "yellow_min_success_rate": 0.95,
        "yellow_max_avg_retries": 2.0,
        "yellow_max_dlq_rate": 0.05,
    },
    "window_days": 7,
}

SAMPLE_THRESHOLDS: dict[str, float] = {
    "green_min_success_rate": 0.99,
    "green_max_avg_retries": 1.2,
    "green_max_dlq_rate": 0.01,
    "yellow_min_success_rate": 0.95,
    "yellow_max_avg_retries": 2.0,
    "yellow_max_dlq_rate": 0.05,
}


class TestHealthSync:
    def test_get_roost_health(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts/roost_abc123/health"
            return httpx.Response(200, json=SAMPLE_HEALTH)

        client = make_client(handler)
        health = client.get_roost_health("roost_abc123")
        assert isinstance(health, RoostHealth)
        assert health.status == "green"
        assert health.metrics.delivered == 99
        assert health.window_days == 7

    def test_get_health_thresholds(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts/roost_abc123/health-thresholds"
            return httpx.Response(200, json=SAMPLE_THRESHOLDS)

        client = make_client(handler)
        thresholds = client.get_health_thresholds("roost_abc123")
        assert isinstance(thresholds, HealthThresholds)
        assert thresholds.green_min_success_rate == 0.99

    def test_set_health_thresholds(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert request.url.path == "/v1/roosts/roost_abc123/health-thresholds"
            body = json.loads(request.content)
            assert body["green_min_success_rate"] == 0.98
            return httpx.Response(200, json={**SAMPLE_THRESHOLDS, "green_min_success_rate": 0.98})

        client = make_client(handler)
        data = HealthThresholds(**{**SAMPLE_THRESHOLDS, "green_min_success_rate": 0.98})
        result = client.set_health_thresholds("roost_abc123", data)
        assert result.green_min_success_rate == 0.98


class TestHealthAsync:
    @pytest.mark.asyncio
    async def test_get_roost_health(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts/roost_abc123/health"
            return httpx.Response(200, json=SAMPLE_HEALTH)

        client = make_async_client(handler)
        health = await client.get_roost_health("roost_abc123")
        assert isinstance(health, RoostHealth)
        assert health.status == "green"
        assert health.metrics.delivered == 99
        assert health.window_days == 7

    @pytest.mark.asyncio
    async def test_get_health_thresholds(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/roosts/roost_abc123/health-thresholds"
            return httpx.Response(200, json=SAMPLE_THRESHOLDS)

        client = make_async_client(handler)
        thresholds = await client.get_health_thresholds("roost_abc123")
        assert isinstance(thresholds, HealthThresholds)
        assert thresholds.green_min_success_rate == 0.99

    @pytest.mark.asyncio
    async def test_set_health_thresholds(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert request.url.path == "/v1/roosts/roost_abc123/health-thresholds"
            body = json.loads(request.content)
            assert body["green_min_success_rate"] == 0.98
            return httpx.Response(200, json={**SAMPLE_THRESHOLDS, "green_min_success_rate": 0.98})

        client = make_async_client(handler)
        data = HealthThresholds(**{**SAMPLE_THRESHOLDS, "green_min_success_rate": 0.98})
        result = await client.set_health_thresholds("roost_abc123", data)
        assert result.green_min_success_rate == 0.98
