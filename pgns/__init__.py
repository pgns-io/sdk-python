"""pgns SDK — Python client for the pgns webhook relay API."""

from pgns.sdk._version import __version__
from pgns.sdk.async_client import AsyncPigeonsClient
from pgns.sdk.client import PigeonsClient
from pgns.sdk.errors import PigeonsAuthError, PigeonsError, WebhookVerificationError
from pgns.sdk.events import async_event_stream, event_stream
from pgns.sdk.models import (
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    AuthTokens,
    CreateApiKeyRequest,
    CreateDestination,
    CreateRoost,
    CreateTemplate,
    DeliveryAttempt,
    DeliveryStatus,
    Destination,
    DestinationType,
    PaginatedDeliveryAttempts,
    PaginatedPigeons,
    PauseResponse,
    Pigeon,
    PreviewTemplateRequest,
    PreviewTemplateResponse,
    ReplayResponse,
    Roost,
    SendResponse,
    Template,
    UpdateApiKeyRequest,
    UpdateDestination,
    UpdateProfileRequest,
    UpdateRoost,
    UpdateTemplate,
    User,
)
from pgns.sdk.webhook import Webhook

__all__ = [
    "__version__",
    # Clients
    "PigeonsClient",
    "AsyncPigeonsClient",
    # Errors
    "PigeonsError",
    "PigeonsAuthError",
    "WebhookVerificationError",
    # Webhook
    "Webhook",
    # Events
    "event_stream",
    "async_event_stream",
    # Enums
    "DestinationType",
    "DeliveryStatus",
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
    "CreateDestination",
    "UpdateDestination",
    "UpdateProfileRequest",
    "CreateApiKeyRequest",
    "UpdateApiKeyRequest",
    # Responses
    "ReplayResponse",
    "PauseResponse",
    "SendResponse",
    # Pagination
    "PaginatedPigeons",
    "PaginatedDeliveryAttempts",
    # Templates
    "Template",
    "CreateTemplate",
    "UpdateTemplate",
    "PreviewTemplateRequest",
    "PreviewTemplateResponse",
]
