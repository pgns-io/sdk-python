"""Synchronous client for the pgns API."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

import httpx

from pgns.sdk._client import _auth_headers, _handle_response
from pgns.sdk.errors import PigeonsAuthError, PigeonsError
from pgns.sdk.models import (
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    AuthTokens,
    BillingStatus,
    CheckoutRequest,
    CheckoutResponse,
    CreateApiKeyRequest,
    CreateDestination,
    CreateRoost,
    CreateTemplate,
    DashboardStats,
    Destination,
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


class PigeonsClient:
    """Synchronous client for the pgns webhook relay API.

    Supports two authentication modes:
    - **API key** — pass ``api_key`` for server-side usage.
    - **JWT** — call :meth:`login` / :meth:`signup`, or pass ``access_token``.
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

    def signup(self, data: SignupRequest) -> AuthTokens:
        """Create a new account. Stores tokens on the client."""
        raw = self._unauth_request("POST", "/v1/auth/signup", json=data.model_dump())
        tokens = AuthTokens.model_validate(raw)
        self._access_token = tokens.access_token
        if self._on_token_refresh:
            self._on_token_refresh(tokens)
        return tokens

    def login(self, data: LoginRequest) -> AuthTokens:
        """Authenticate with email and password. Stores tokens on the client."""
        raw = self._unauth_request("POST", "/v1/auth/login", json=data.model_dump())
        tokens = AuthTokens.model_validate(raw)
        self._access_token = tokens.access_token
        if self._on_token_refresh:
            self._on_token_refresh(tokens)
        return tokens

    def request_magic_link(self, data: MagicLinkRequest) -> MagicLinkResponse:
        """Send a magic-link email."""
        raw = self._unauth_request("POST", "/v1/auth/magic-link", json=data.model_dump())
        return MagicLinkResponse.model_validate(raw)

    def verify_magic_link(self, data: MagicLinkVerifyRequest) -> AuthTokens:
        """Exchange a magic-link token for auth tokens."""
        raw = self._unauth_request("POST", "/v1/auth/magic-link/verify", json=data.model_dump())
        tokens = AuthTokens.model_validate(raw)
        self._access_token = tokens.access_token
        if self._on_token_refresh:
            self._on_token_refresh(tokens)
        return tokens

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

    # -- Billing --------------------------------------------------------------

    def create_checkout(self, data: CheckoutRequest) -> CheckoutResponse:
        """Create a Stripe checkout session."""
        raw = self._request("POST", "/v1/billing/checkout", json=data.model_dump())
        return CheckoutResponse.model_validate(raw)

    def create_portal(self, data: PortalRequest) -> PortalResponse:
        """Create a Stripe customer portal session."""
        raw = self._request("POST", "/v1/billing/portal", json=data.model_dump())
        return PortalResponse.model_validate(raw)

    def billing_status(self) -> BillingStatus:
        """Get the current billing status and limits."""
        data = self._request("GET", "/v1/billing/status")
        return BillingStatus.model_validate(data)

    # -- User -----------------------------------------------------------------

    def get_me(self) -> User:
        """Get the authenticated user's profile."""
        data = self._request("GET", "/v1/me")
        return User.model_validate(data)

    def update_me(self, data: UpdateProfileRequest) -> User:
        """Update the authenticated user's profile."""
        raw = self._request("PATCH", "/v1/me", json=data.model_dump(exclude_unset=True))
        return User.model_validate(raw)

    def get_stats(self) -> DashboardStats:
        """Get aggregated dashboard statistics."""
        data = self._request("GET", "/v1/stats")
        return DashboardStats.model_validate(data)
