# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Synchronous client for the pgns API."""

from __future__ import annotations

__all__ = ["PigeonsClient"]

import threading
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

import httpx

from pgns._client import _auth_headers, _handle_response
from pgns.errors import PigeonsAuthError, PigeonsError
from pgns.models import (
    AgentCard,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    Application,
    AuthTokens,
    CreateAgentCard,
    CreateApiKeyRequest,
    CreateApplication,
    CreateDestination,
    CreateEndpoint,
    CreateRoost,
    CreateTemplate,
    Destination,
    Endpoint,
    HealthThresholds,
    PaginatedDeliveryAttempts,
    PaginatedPigeons,
    PauseResponse,
    Pigeon,
    PreviewTemplateRequest,
    PreviewTemplateResponse,
    PublishMessage,
    PublishResponse,
    ReplayResponse,
    Roost,
    RoostHealth,
    SendResponse,
    Template,
    UpdateAgentCard,
    UpdateApiKeyRequest,
    UpdateDestination,
    UpdateProfileRequest,
    UpdateRoost,
    UpdateTemplate,
    User,
    ValidateSchemaResponse,
)


class PigeonsClient:
    """Synchronous client for the pgns webhook relay API.

    Supports two authentication modes:
    - **API key** — pass ``api_key`` for server-side usage.
    - **JWT** — pass ``access_token``.
      Expired tokens are refreshed automatically on ``401``.

    Example::

        client = PigeonsClient(
            "https://api.pgns.io",
            api_key="pk_live_...",
        )
        roosts = client.list_roosts()
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        access_token: str | None = None,
        on_token_refresh: Callable[[AuthTokens], None] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._access_token = access_token
        self._on_token_refresh = on_token_refresh
        self._http = http_client or httpx.Client()
        self._refresh_lock = threading.Lock()

    # -- Credential setters ---------------------------------------------------

    def set_access_token(self, token: str) -> None:
        self._access_token = token

    def set_api_key(self, key: str) -> None:
        self._api_key = key

    # -- Internal helpers -----------------------------------------------------

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            **_auth_headers(self._api_key, self._access_token),
        }

    def _refresh_token(self) -> AuthTokens:
        with self._refresh_lock:
            response = self._http.post(
                f"{self._base_url}/v1/auth/refresh",
                headers={"Content-Type": "application/json"},
            )
            data = _handle_response(response)
            tokens = AuthTokens.model_validate(data)
            self._access_token = tokens.access_token
            if self._on_token_refresh:
                self._on_token_refresh(tokens)
            return tokens

    def _request(self, method: str, path: str, *, json: Any = None) -> Any:
        response = self._http.request(
            method,
            f"{self._base_url}{path}",
            headers=self._headers(),
            json=json,
        )
        if response.status_code == 401 and not self._api_key:
            try:
                tokens = self._refresh_token()
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {tokens.access_token}",
                }
                response = self._http.request(
                    method,
                    f"{self._base_url}{path}",
                    headers=headers,
                    json=json,
                )
                return _handle_response(response)
            except PigeonsError:
                raise
            except Exception as exc:
                self._access_token = None
                raise PigeonsAuthError() from exc
        return _handle_response(response)

    def _unauth_request(self, method: str, path: str, *, json: Any = None) -> Any:
        response = self._http.request(
            method,
            f"{self._base_url}{path}",
            headers={"Content-Type": "application/json"},
            json=json,
        )
        return _handle_response(response)

    # -- Auth -----------------------------------------------------------------

    def refresh(self) -> AuthTokens:
        """Refresh the access token using the httpOnly refresh cookie."""
        raw = self._unauth_request("POST", "/v1/auth/refresh")
        tokens = AuthTokens.model_validate(raw)
        self._access_token = tokens.access_token
        if self._on_token_refresh:
            self._on_token_refresh(tokens)
        return tokens

    def logout(self) -> None:
        """Revoke the refresh token and clear stored credentials."""
        self._request("POST", "/v1/auth/logout")
        self._access_token = None

    # -- Roosts ---------------------------------------------------------------

    def list_roosts(self) -> list[Roost]:
        """List all roosts for the authenticated user."""
        data = self._request("GET", "/v1/roosts")
        return [Roost.model_validate(r) for r in data]

    def get_roost(self, roost_id: str) -> Roost:
        """Get a roost by ID."""
        data = self._request("GET", f"/v1/roosts/{quote(roost_id, safe='')}")
        return Roost.model_validate(data)

    def create_roost(self, data: CreateRoost) -> Roost:
        """Create a new roost (webhook endpoint)."""
        raw = self._request("POST", "/v1/roosts", json=data.model_dump(exclude_none=True))
        return Roost.model_validate(raw)

    def update_roost(self, roost_id: str, data: UpdateRoost) -> Roost:
        """Update a roost's name, description, secret, or active state."""
        raw = self._request(
            "PATCH",
            f"/v1/roosts/{quote(roost_id, safe='')}",
            json=data.model_dump(exclude_unset=True),
        )
        return Roost.model_validate(raw)

    def delete_roost(self, roost_id: str) -> None:
        """Delete a roost and all its destinations."""
        self._request("DELETE", f"/v1/roosts/{quote(roost_id, safe='')}")

    def validate_roost_schema(
        self, roost_id: str, payload: dict[str, Any]
    ) -> ValidateSchemaResponse:
        """Validate a payload against a roost's JSON Schema."""
        raw = self._request(
            "POST",
            f"/v1/roosts/{quote(roost_id, safe='')}/schema/validate",
            json={"payload": payload},
        )
        return ValidateSchemaResponse.model_validate(raw)

    # -- Pigeons --------------------------------------------------------------

    def list_pigeons(
        self,
        *,
        roost_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PaginatedPigeons:
        """List pigeons, optionally filtered by roost."""
        params: list[str] = []
        if roost_id:
            params.append(f"roost_id={quote(roost_id, safe='')}")
        if limit is not None:
            params.append(f"limit={limit}")
        if cursor:
            params.append(f"cursor={quote(cursor, safe='')}")
        qs = f"?{'&'.join(params)}" if params else ""
        data = self._request("GET", f"/v1/pigeons{qs}")
        return PaginatedPigeons.model_validate(data)

    def get_pigeon(self, pigeon_id: str) -> Pigeon:
        """Get a single pigeon by ID."""
        data = self._request("GET", f"/v1/pigeons/{quote(pigeon_id, safe='')}")
        return Pigeon.model_validate(data)

    def get_pigeon_deliveries(
        self,
        pigeon_id: str,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PaginatedDeliveryAttempts:
        """List all delivery attempts for a pigeon."""
        params: list[str] = []
        if limit is not None:
            params.append(f"limit={limit}")
        if cursor:
            params.append(f"cursor={quote(cursor, safe='')}")
        qs = f"?{'&'.join(params)}" if params else ""
        data = self._request("GET", f"/v1/pigeons/{quote(pigeon_id, safe='')}/deliveries{qs}")
        return PaginatedDeliveryAttempts.model_validate(data)

    def replay_pigeon(self, pigeon_id: str) -> ReplayResponse:
        """Re-deliver a pigeon to all active destinations."""
        data = self._request("POST", f"/v1/pigeons/{quote(pigeon_id, safe='')}/replay")
        return ReplayResponse.model_validate(data)

    # -- Destinations ---------------------------------------------------------

    def list_destinations(self, roost_id: str) -> list[Destination]:
        """List all destinations for a roost."""
        data = self._request("GET", f"/v1/roosts/{quote(roost_id, safe='')}/destinations")
        return [Destination.model_validate(d) for d in data]

    def get_destination(self, destination_id: str) -> Destination:
        """Get a destination by ID."""
        data = self._request("GET", f"/v1/destinations/{quote(destination_id, safe='')}")
        return Destination.model_validate(data)

    def create_destination(self, roost_id: str, data: CreateDestination) -> Destination:
        """Add a new destination to a roost."""
        raw = self._request(
            "POST",
            f"/v1/roosts/{quote(roost_id, safe='')}/destinations",
            json=data.model_dump(exclude_none=True),
        )
        return Destination.model_validate(raw)

    def pause_destination(self, destination_id: str, is_paused: bool) -> PauseResponse:
        """Pause or unpause delivery to a destination."""
        data = self._request(
            "PATCH",
            f"/v1/destinations/{quote(destination_id, safe='')}/pause",
            json={"is_paused": is_paused},
        )
        return PauseResponse.model_validate(data)

    def update_destination(self, destination_id: str, data: UpdateDestination) -> Destination:
        """Update a destination's name or configuration."""
        raw = self._request(
            "PATCH",
            f"/v1/destinations/{quote(destination_id, safe='')}",
            json=data.model_dump(exclude_unset=True),
        )
        return Destination.model_validate(raw)

    def delete_destination(self, destination_id: str) -> None:
        """Permanently delete a destination."""
        self._request("DELETE", f"/v1/destinations/{quote(destination_id, safe='')}")

    # -- API Keys -------------------------------------------------------------

    def list_api_keys(self) -> list[ApiKeyResponse]:
        """List all API keys for the authenticated user."""
        data = self._request("GET", "/v1/api-keys")
        return [ApiKeyResponse.model_validate(k) for k in data]

    def get_api_key(self, key_id: str) -> ApiKeyResponse:
        """Get an API key by ID (does not return the full key value)."""
        data = self._request("GET", f"/v1/api-keys/{quote(key_id, safe='')}")
        return ApiKeyResponse.model_validate(data)

    def create_api_key(self, data: CreateApiKeyRequest | None = None) -> ApiKeyCreatedResponse:
        """Create a new API key. The full key is only in this response."""
        body = data.model_dump(exclude_none=True) if data else {}
        raw = self._request("POST", "/v1/api-keys", json=body)
        return ApiKeyCreatedResponse.model_validate(raw)

    def update_api_key(self, key_id: str, data: UpdateApiKeyRequest) -> ApiKeyResponse:
        """Rename an API key."""
        raw = self._request(
            "PATCH",
            f"/v1/api-keys/{quote(key_id, safe='')}",
            json=data.model_dump(),
        )
        return ApiKeyResponse.model_validate(raw)

    def delete_api_key(self, key_id: str) -> None:
        """Permanently revoke and delete an API key."""
        self._request("DELETE", f"/v1/api-keys/{quote(key_id, safe='')}")

    # -- Templates ------------------------------------------------------------

    def list_templates(self) -> list[Template]:
        """List all templates for the authenticated user."""
        data = self._request("GET", "/v1/templates")
        return [Template.model_validate(t) for t in data]

    def get_template(self, template_id: str) -> Template:
        """Get a template by ID."""
        data = self._request("GET", f"/v1/templates/{quote(template_id, safe='')}")
        return Template.model_validate(data)

    def create_template(self, data: CreateTemplate) -> Template:
        """Create a new template."""
        raw = self._request("POST", "/v1/templates", json=data.model_dump(exclude_none=True))
        return Template.model_validate(raw)

    def update_template(self, template_id: str, data: UpdateTemplate) -> Template:
        """Update a template."""
        raw = self._request(
            "PATCH",
            f"/v1/templates/{quote(template_id, safe='')}",
            json=data.model_dump(exclude_unset=True),
        )
        return Template.model_validate(raw)

    def delete_template(self, template_id: str) -> None:
        """Delete a template."""
        self._request("DELETE", f"/v1/templates/{quote(template_id, safe='')}")

    def preview_template(self, data: PreviewTemplateRequest) -> PreviewTemplateResponse:
        """Render a template with a pigeon's data."""
        raw = self._request("POST", "/v1/templates/preview", json=data.model_dump())
        return PreviewTemplateResponse.model_validate(raw)

    # -- User -----------------------------------------------------------------

    def get_me(self) -> User:
        """Get the authenticated user's profile."""
        data = self._request("GET", "/v1/me")
        return User.model_validate(data)

    def update_me(self, data: UpdateProfileRequest) -> User:
        """Update the authenticated user's profile."""
        raw = self._request("PATCH", "/v1/me", json=data.model_dump(exclude_unset=True))
        return User.model_validate(raw)

    # -- Applications (Outbound Webhooks) ------------------------------------

    def list_applications(self) -> list[Application]:
        """List all outbound webhook applications."""
        data = self._request("GET", "/v1/applications")
        return [Application.model_validate(a) for a in data]

    def get_application(self, app_id: str) -> Application:
        """Get an application by ID."""
        data = self._request("GET", f"/v1/applications/{quote(app_id, safe='')}")
        return Application.model_validate(data)

    def create_application(self, data: CreateApplication) -> Application:
        """Create a new outbound webhook application."""
        raw = self._request("POST", "/v1/applications", json=data.model_dump(exclude_none=True))
        return Application.model_validate(raw)

    def delete_application(self, app_id: str) -> None:
        """Delete an application."""
        self._request("DELETE", f"/v1/applications/{quote(app_id, safe='')}")

    # -- Endpoints -----------------------------------------------------------

    def list_endpoints(self, app_id: str, *, customer_id: str | None = None) -> list[Endpoint]:
        """List endpoints for an application, optionally filtered by customer."""
        qs = f"?customer_id={quote(customer_id, safe='')}" if customer_id else ""
        data = self._request("GET", f"/v1/applications/{quote(app_id, safe='')}/endpoints{qs}")
        return [Endpoint.model_validate(e) for e in data]

    def create_endpoint(self, app_id: str, data: CreateEndpoint) -> Endpoint:
        """Create a new endpoint within an application."""
        raw = self._request(
            "POST",
            f"/v1/applications/{quote(app_id, safe='')}/endpoints",
            json=data.model_dump(exclude_none=True),
        )
        return Endpoint.model_validate(raw)

    def delete_endpoint(self, app_id: str, endpoint_id: str) -> None:
        """Delete an endpoint."""
        self._request(
            "DELETE",
            f"/v1/applications/{quote(app_id, safe='')}/endpoints/{quote(endpoint_id, safe='')}",
        )

    def list_endpoint_attempts(
        self,
        app_id: str,
        endpoint_id: str,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> PaginatedDeliveryAttempts:
        """List delivery attempts for an endpoint."""
        params: list[str] = []
        if limit is not None:
            params.append(f"limit={limit}")
        if cursor:
            params.append(f"cursor={quote(cursor, safe='')}")
        qs = f"?{'&'.join(params)}" if params else ""
        app = quote(app_id, safe="")
        ep = quote(endpoint_id, safe="")
        data = self._request("GET", f"/v1/applications/{app}/endpoints/{ep}/attempts{qs}")
        return PaginatedDeliveryAttempts.model_validate(data)

    # -- Messages ------------------------------------------------------------

    def publish_message(self, app_id: str, data: PublishMessage) -> PublishResponse:
        """Publish an event to matching customer endpoints."""
        raw = self._request(
            "POST",
            f"/v1/applications/{quote(app_id, safe='')}/messages",
            json=data.model_dump(),
        )
        return PublishResponse.model_validate(raw)

    # -- Send (Inbound Webhook) -----------------------------------------------

    def send(
        self,
        roost_id: str,
        *,
        event_type: str,
        payload: Any,
        signing_secret: str,
        extra_headers: dict[str, str] | None = None,
    ) -> SendResponse:
        """Send a signed webhook to a roost.

        Computes dual signatures: legacy ``X-Pigeon-Signature`` (hex) and
        Standard Webhooks ``webhook-signature`` (base64). Both header sets
        are sent for backward compatibility.
        """
        import base64
        import hashlib
        import hmac as hmac_mod
        import json
        import time
        import uuid

        body = json.dumps(payload, separators=(",", ":"))
        timestamp = str(int(time.time()))
        msg_id = f"msg_{uuid.uuid4()}"

        # Decode signing key
        if signing_secret.startswith("whsec_"):
            key_bytes = base64.b64decode(signing_secret[6:])
        else:
            key_bytes = signing_secret.encode()

        # Legacy signature: HMAC-SHA256("{timestamp}.{body}") → hex
        legacy_sig = hmac_mod.new(
            key_bytes,
            f"{timestamp}.{body}".encode(),
            hashlib.sha256,
        ).hexdigest()

        # Standard Webhooks signature: HMAC-SHA256("{msg_id}.{timestamp}.{body}") → base64
        std_sig = base64.b64encode(
            hmac_mod.new(
                key_bytes,
                f"{msg_id}.{timestamp}.{body}".encode(),
                hashlib.sha256,
            ).digest()
        ).decode()

        headers = dict(extra_headers or {})
        headers.update(
            {
                "Content-Type": "application/json",
                "X-Pigeon-Signature": f"sha256={legacy_sig}",
                "X-Pigeon-Timestamp": timestamp,
                "X-Pigeon-Event-Type": event_type,
                "webhook-id": msg_id,
                "webhook-timestamp": timestamp,
                "webhook-signature": f"v1,{std_sig}",
            }
        )

        response = self._http.post(
            f"{self._base_url}/r/{quote(roost_id, safe='')}",
            headers=headers,
            content=body,
        )
        data = _handle_response(response)
        return SendResponse.model_validate(data)

    # -- Agent Cards ----------------------------------------------------------

    def list_agents(self) -> list[AgentCard]:
        """List all agent cards for the authenticated user."""
        data = self._request("GET", "/v1/agents")
        return [AgentCard.model_validate(a) for a in data]

    def create_agent(self, data: CreateAgentCard) -> AgentCard:
        """Create a new agent card."""
        raw = self._request("POST", "/v1/agents", json=data.model_dump(exclude_none=True))
        return AgentCard.model_validate(raw)

    def get_agent(self, agent_id: str) -> AgentCard:
        """Get an agent card by ID."""
        raw = self._request("GET", f"/v1/agents/{quote(agent_id, safe='')}")
        return AgentCard.model_validate(raw)

    def update_agent(self, agent_id: str, data: UpdateAgentCard) -> AgentCard:
        """Update an agent card."""
        raw = self._request(
            "PATCH",
            f"/v1/agents/{quote(agent_id, safe='')}",
            json=data.model_dump(exclude_unset=True),
        )
        return AgentCard.model_validate(raw)

    def delete_agent(self, agent_id: str) -> None:
        """Delete an agent card."""
        self._request("DELETE", f"/v1/agents/{quote(agent_id, safe='')}")

    # -- Health ---------------------------------------------------------------

    def get_roost_health(self, roost_id: str) -> RoostHealth:
        """Get health metrics for a roost over the last 7-day window."""
        raw = self._request("GET", f"/v1/roosts/{quote(roost_id, safe='')}/health")
        return RoostHealth.model_validate(raw)

    def get_health_thresholds(self, roost_id: str) -> HealthThresholds:
        """Get the health thresholds configured for a roost."""
        raw = self._request("GET", f"/v1/roosts/{quote(roost_id, safe='')}/health-thresholds")
        return HealthThresholds.model_validate(raw)

    def set_health_thresholds(self, roost_id: str, data: HealthThresholds) -> HealthThresholds:
        """Set custom health thresholds for a roost."""
        raw = self._request(
            "PUT",
            f"/v1/roosts/{quote(roost_id, safe='')}/health-thresholds",
            json=data.model_dump(),
        )
        return HealthThresholds.model_validate(raw)
