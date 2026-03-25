# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""pgns SDK — Python client for the pgns webhook relay API.

Prefer importing from specific submodules::

    from pgns.client import PigeonsClient
    from pgns.async_client import AsyncPigeonsClient
    from pgns.models import Roost, Destination
    from pgns.errors import PigeonsError
    from pgns.webhook import Webhook
    from pgns.events import event_stream
    from pgns.types import DestinationType, DeliveryStatus

Root-level imports (``from pgns.sdk import PigeonsClient``) are deprecated
and will be removed in a future release.
"""

from __future__ import annotations

import importlib
import warnings

from pgns._version import __version__

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
    "SourceType",
    # Auth
    "AuthTokens",
    # Domain models
    "User",
    "Roost",
    "Pigeon",
    "Destination",
    "DeliveryAttempt",
    "Application",
    "Endpoint",
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
    # Agent Cards
    "AgentCard",
    "CreateAgentCard",
    "UpdateAgentCard",
    # Health
    "HealthStatus",
    "HealthMetrics",
    "HealthThresholds",
    "RoostHealth",
    # Agent helpers
    "CORRELATION_ID_HEADER",
    "CORRELATION_ID_PATTERN",
    "validate_correlation_id",
    "correlation_headers",
    "extract_correlation_id",
]

# Mapping of every public name to its canonical submodule.
_DEPRECATED_IMPORTS: dict[str, str] = {
    # Clients
    "PigeonsClient": "pgns.sdk.client",
    "AsyncPigeonsClient": "pgns.sdk.async_client",
    # Errors
    "PigeonsError": "pgns.sdk.errors",
    "PigeonsAuthError": "pgns.sdk.errors",
    "WebhookVerificationError": "pgns.sdk.errors",
    # Webhook
    "Webhook": "pgns.sdk.webhook",
    # Events
    "event_stream": "pgns.sdk.events",
    "async_event_stream": "pgns.sdk.events",
    # Enums
    "DestinationType": "pgns.sdk.models",
    "DeliveryStatus": "pgns.sdk.models",
    "SourceType": "pgns.sdk.models",
    # Auth
    "AuthTokens": "pgns.sdk.models",
    # Domain models
    "User": "pgns.sdk.models",
    "Roost": "pgns.sdk.models",
    "Pigeon": "pgns.sdk.models",
    "Destination": "pgns.sdk.models",
    "DeliveryAttempt": "pgns.sdk.models",
    "Application": "pgns.sdk.models",
    "Endpoint": "pgns.sdk.models",
    # API Keys
    "ApiKeyResponse": "pgns.sdk.models",
    "ApiKeyCreatedResponse": "pgns.sdk.models",
    # Mutations
    "CreateRoost": "pgns.sdk.models",
    "UpdateRoost": "pgns.sdk.models",
    "CreateDestination": "pgns.sdk.models",
    "UpdateDestination": "pgns.sdk.models",
    "UpdateProfileRequest": "pgns.sdk.models",
    "CreateApiKeyRequest": "pgns.sdk.models",
    "UpdateApiKeyRequest": "pgns.sdk.models",
    "CreateApplication": "pgns.sdk.models",
    "CreateEndpoint": "pgns.sdk.models",
    "PublishMessage": "pgns.sdk.models",
    # Responses
    "ReplayResponse": "pgns.sdk.models",
    "PauseResponse": "pgns.sdk.models",
    "SendResponse": "pgns.sdk.models",
    "PublishResponse": "pgns.sdk.models",
    # Pagination
    "PaginatedPigeons": "pgns.sdk.models",
    "PaginatedDeliveryAttempts": "pgns.sdk.models",
    # Templates
    "Template": "pgns.sdk.models",
    "CreateTemplate": "pgns.sdk.models",
    "UpdateTemplate": "pgns.sdk.models",
    "PreviewTemplateRequest": "pgns.sdk.models",
    "PreviewTemplateResponse": "pgns.sdk.models",
    # Agent Cards
    "AgentCard": "pgns.sdk.models",
    "CreateAgentCard": "pgns.sdk.models",
    "UpdateAgentCard": "pgns.sdk.models",
    # Health
    "HealthStatus": "pgns.sdk.models",
    "HealthMetrics": "pgns.sdk.models",
    "HealthThresholds": "pgns.sdk.models",
    "RoostHealth": "pgns.sdk.models",
    # Agent helpers
    "CORRELATION_ID_HEADER": "pgns.sdk.agents",
    "CORRELATION_ID_PATTERN": "pgns.sdk.agents",
    "validate_correlation_id": "pgns.sdk.agents",
    "correlation_headers": "pgns.sdk.agents",
    "extract_correlation_id": "pgns.sdk.agents",
}


def __getattr__(name: str) -> object:
    module_path = _DEPRECATED_IMPORTS.get(name)
    if module_path is not None:
        module = importlib.import_module(module_path)
        obj = getattr(module, name)
        warnings.warn(
            f"Importing '{name}' from 'pgns.sdk' is deprecated. "
            f"Use 'from {module_path} import {name}' instead. "
            "Root-level imports will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        return obj
    raise AttributeError(f"module 'pgns.sdk' has no attribute {name!r}")
