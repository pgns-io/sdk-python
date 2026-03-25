# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Pydantic v2 models for the pgns API."""

from __future__ import annotations

__all__ = [
    # Enums
    "DestinationType",
    "DeliveryStatus",
    "SourceType",
    # Auth
    "AuthTokens",
    # Domain models
    "User",
    "Roost",
    "Pigeon",
    "Destination",
    "DeliveryAttempt",
    # API Keys
    "ApiKeyResponse",
    "ApiKeyCreatedResponse",
    # Mutations
    "CreateRoost",
    "UpdateRoost",
    "ValidateSchemaResponse",
    "CreateDestination",
    "UpdateDestination",
    "UpdateProfileRequest",
    "CreateApiKeyRequest",
    "UpdateApiKeyRequest",
    "CreateApplication",
    "CreateEndpoint",
    "PublishMessage",
    # Responses
    "ReplayResponse",
    "PauseResponse",
    "SendResponse",
    "PublishResponse",
    # Pagination
    "PaginatedPigeons",
    "PaginatedDeliveryAttempts",
    # Templates
    "Template",
    "CreateTemplate",
    "UpdateTemplate",
    "PreviewTemplateRequest",
    "PreviewTemplateResponse",
    # Applications
    "Application",
    "Endpoint",
    # Agent Cards
    "AgentCard",
    "CreateAgentCard",
    "UpdateAgentCard",
    # Health
    "HealthStatus",
    "HealthMetrics",
    "HealthThresholds",
    "RoostHealth",
]

from enum import StrEnum
from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DestinationType(StrEnum):
    url = "url"
    slack = "slack"
    discord = "discord"
    teams = "teams"
    email = "email"
    sqs = "sqs"
    s3 = "s3"
    lambda_ = "lambda"


class DeliveryStatus(StrEnum):
    pending = "pending"
    delivering = "delivering"
    delivered = "delivered"
    failed = "failed"
    retrying = "retrying"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class AuthTokens(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class User(BaseModel):
    id: str
    email: str
    name: str
    plan: str
    mfa_enabled: bool
    created_at: str
    updated_at: str


class SourceType(StrEnum):
    github = "github"
    stripe = "stripe"
    shopify = "shopify"
    slack = "slack"
    discord = "discord"
    svix = "svix"
    pigeon = "pigeon"
    linear = "linear"
    sentry = "sentry"


class Roost(BaseModel):
    id: str
    name: str
    description: str
    secret: str | None = None
    source_type: SourceType | None = None
    schema: dict[str, Any] | None = None  # type: ignore[assignment]  # shadows BaseModel.schema()
    agent_card_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class Pigeon(BaseModel):
    id: str
    roost_id: str
    source_ip: str
    request_method: str
    content_type: str
    headers: dict[str, Any]
    body_json: Any | None = None
    body_raw: list[int] | None = None
    request_query: dict[str, Any] | None = None
    replayed_from: str | None = None
    delivery_status: DeliveryStatus
    received_at: str
    correlation_id: str | None = None
    reply_to_pigeon_id: str | None = None


class Destination(BaseModel):
    id: str
    roost_id: str
    name: str
    destination_type: DestinationType
    config: dict[str, Any]
    filter_expression: str
    template: str
    retry_max: int
    retry_delay_ms: int
    retry_multiplier: float
    is_paused: bool
    is_verified: bool
    reply_roost_id: str | None = None
    reply_timeout_ms: int | None = None
    created_at: str
    updated_at: str


class DeliveryAttempt(BaseModel):
    id: str
    pigeon_id: str
    destination_id: str
    status: DeliveryStatus
    attempt_number: int
    response_status: int | None = None
    response_body: str | None = None
    response_headers: dict[str, str] | None = None
    error_message: str | None = None
    attempted_at: str
    next_retry_at: str | None = None


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------


class ApiKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    last_used: str | None = None
    revoked_at: str | None = None
    created_at: str


class ApiKeyCreatedResponse(BaseModel):
    id: str
    key: str
    key_prefix: str
    name: str
    created_at: str


# ---------------------------------------------------------------------------
# Mutation requests
# ---------------------------------------------------------------------------


class CreateRoost(BaseModel):
    name: str
    description: str | None = None
    secret: str | None = None
    source_type: SourceType | None = None
    schema: dict[str, Any] | None = None  # type: ignore[assignment]
    agent_card_id: str | None = None


class UpdateRoost(BaseModel):
    name: str | None = None
    description: str | None = None
    secret: str | None = None
    source_type: SourceType | None = None
    schema: dict[str, Any] | None = None  # type: ignore[assignment]
    agent_card_id: str | None = None
    is_active: bool | None = None


class ValidateSchemaResponse(BaseModel):
    valid: bool
    errors: list[str]


class CreateDestination(BaseModel):
    destination_type: DestinationType
    name: str | None = None
    config: dict[str, Any] | None = None
    filter_expression: str | None = None
    template: str | None = None
    retry_max: int | None = None
    retry_delay_ms: int | None = None
    retry_multiplier: float | None = None
    reply_roost_id: str | None = None
    reply_timeout_ms: int | None = None


class UpdateDestination(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    filter_expression: str | None = None
    template: str | None = None
    transform_type: str | None = None
    transform_code: str | None = None
    reply_roost_id: str | None = None
    reply_timeout_ms: int | None = None


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    email: str | None = None


class CreateApiKeyRequest(BaseModel):
    name: str | None = None


class UpdateApiKeyRequest(BaseModel):
    name: str


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class ReplayResponse(BaseModel):
    replayed: bool
    pigeon_id: str
    delivery_attempts: int


class PauseResponse(BaseModel):
    is_paused: bool


class SendResponse(BaseModel):
    id: str
    status: str
    destinations: int


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginatedPigeons(BaseModel):
    data: list[Pigeon]
    next_cursor: str | None = None
    has_more: bool


class PaginatedDeliveryAttempts(BaseModel):
    data: list[DeliveryAttempt]
    next_cursor: str | None = None
    has_more: bool


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


class Template(BaseModel):
    id: str
    name: str
    description: str
    body: str
    created_at: str
    updated_at: str


class CreateTemplate(BaseModel):
    name: str
    description: str | None = None
    body: str | None = None


class UpdateTemplate(BaseModel):
    name: str | None = None
    description: str | None = None
    body: str | None = None


class PreviewTemplateRequest(BaseModel):
    body: str
    pigeon_id: str


class PreviewTemplateResponse(BaseModel):
    rendered: str


# ---------------------------------------------------------------------------
# Applications (Outbound Webhooks)
# ---------------------------------------------------------------------------


class Application(BaseModel):
    id: str
    user_id: str
    roost_id: str
    external_id: str | None = None
    name: str
    metadata: dict[str, Any]
    signing_key: str
    created_at: str
    updated_at: str


class CreateApplication(BaseModel):
    name: str
    external_id: str | None = None
    metadata: dict[str, Any] | None = None


class Endpoint(BaseModel):
    id: str
    application_id: str
    destination_id: str
    customer_id: str
    subscribed_events: list[str]
    signing_secret: str | None = None
    metadata: dict[str, Any]
    created_at: str
    updated_at: str


class CreateEndpoint(BaseModel):
    url: str
    customer_id: str
    subscribed_events: list[str] | None = None
    signing_secret: str | None = None
    metadata: dict[str, Any] | None = None


class PublishMessage(BaseModel):
    event_type: str
    customer_id: str
    data: Any


class PublishResponse(BaseModel):
    pigeon_id: str
    endpoints_matched: int


# ---------------------------------------------------------------------------
# Agent Cards (A2A)
# ---------------------------------------------------------------------------


class AgentCard(BaseModel):
    id: str
    name: str
    description: str
    url: str
    version: str
    provider: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    skills: list[Any] | None = None
    default_input_modes: list[str] | None = None
    default_output_modes: list[str] | None = None
    security_schemes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool = True
    created_at: str
    updated_at: str


class CreateAgentCard(BaseModel):
    name: str
    url: str
    description: str | None = None
    version: str | None = None
    provider: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    skills: list[Any] | None = None
    default_input_modes: list[str] | None = None
    default_output_modes: list[str] | None = None
    security_schemes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class UpdateAgentCard(BaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None
    version: str | None = None
    provider: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    skills: list[Any] | None = None
    default_input_modes: list[str] | None = None
    default_output_modes: list[str] | None = None
    security_schemes: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthStatus(StrEnum):
    green = "green"
    yellow = "yellow"
    red = "red"
    unknown = "unknown"


class HealthMetrics(BaseModel):
    total_attempts: int
    delivered: int
    failed: int
    retrying: int
    success_rate: float
    avg_retries: float
    dlq_rate: float


class HealthThresholds(BaseModel):
    green_min_success_rate: float
    green_max_avg_retries: float
    green_max_dlq_rate: float
    yellow_min_success_rate: float
    yellow_max_avg_retries: float
    yellow_max_dlq_rate: float


class RoostHealth(BaseModel):
    roost_id: str
    status: HealthStatus
    metrics: HealthMetrics
    thresholds: HealthThresholds
    window_days: int
