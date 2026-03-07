"""Pydantic v2 models for the pgns API."""

from __future__ import annotations

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
    email = "email"


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


class UpdateRoost(BaseModel):
    name: str | None = None
    description: str | None = None
    secret: str | None = None
    source_type: SourceType | None = None
    is_active: bool | None = None


class CreateDestination(BaseModel):
    destination_type: DestinationType
    name: str | None = None
    config: dict[str, Any] | None = None
    filter_expression: str | None = None
    template: str | None = None
    retry_max: int | None = None
    retry_delay_ms: int | None = None
    retry_multiplier: float | None = None


class UpdateDestination(BaseModel):
    name: str | None = None
    config: dict[str, Any] | None = None
    filter_expression: str | None = None
    template: str | None = None
    transform_type: str | None = None
    transform_code: str | None = None


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
