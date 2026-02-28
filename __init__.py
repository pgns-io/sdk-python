"""pgns SDK — Python client for the pgns webhook relay API."""

from pgns.sdk._version import __version__
from pgns.sdk.async_client import AsyncPigeonsClient
from pgns.sdk.client import PigeonsClient
from pgns.sdk.errors import PigeonsAuthError, PigeonsError
from pgns.sdk.events import async_event_stream, event_stream
from pgns.sdk.models import (
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    AuthTokens,
    BillingLimits,
    BillingStatus,
    CheckoutRequest,
    CheckoutResponse,
    CreateApiKeyRequest,
    CreateDestination,
    CreateRoost,
    CreateTemplate,
    DashboardStats,
    DeliveryAttempt,
    DeliveryStatus,
    Destination,
    DestinationType,
    LoginRequest,
    MagicLinkRequest,
    MagicLinkResponse,
    MagicLinkVerifyRequest,
    PaginatedDeliveryAttempts,
    PaginatedPigeons,
    PauseResponse,
    Pigeon,
    PortalRequest,
    PortalResponse,
    PreviewTemplateRequest,
    PreviewTemplateResponse,
    ReplayResponse,
    Roost,
    SignupRequest,
    Template,
    UpdateApiKeyRequest,
    UpdateProfileRequest,
    UpdateRoost,
    UpdateTemplate,
    User,
)

__all__ = [
    "__version__",
    # Clients
    "PigeonsClient",
    "AsyncPigeonsClient",
    # Errors
    "PigeonsError",
    "PigeonsAuthError",
    # Events
    "event_stream",
    "async_event_stream",
    # Enums
    "DestinationType",
    "DeliveryStatus",
    # Auth
    "AuthTokens",
    "SignupRequest",
    "LoginRequest",
    "MagicLinkRequest",
    "MagicLinkVerifyRequest",
    "MagicLinkResponse",
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
    "UpdateProfileRequest",
    "CreateApiKeyRequest",
    "UpdateApiKeyRequest",
    # Responses
    "ReplayResponse",
    "DashboardStats",
    "PauseResponse",
    # Pagination
    "PaginatedPigeons",
    "PaginatedDeliveryAttempts",
    # Templates
    "Template",
    "CreateTemplate",
    "UpdateTemplate",
    "PreviewTemplateRequest",
    "PreviewTemplateResponse",
    # Billing
    "BillingLimits",
    "BillingStatus",
    "CheckoutRequest",
    "CheckoutResponse",
    "PortalRequest",
    "PortalResponse",
]
