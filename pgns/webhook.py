"""Webhook signature verification for pgns consumers."""

from __future__ import annotations

import base64
import hashlib
import hmac as hmac_mod
import json
import time
from collections.abc import Callable
from typing import Any

from pgns.sdk.errors import WebhookVerificationError

type _HeaderGetter = Callable[[str], str | None]

DEFAULT_TOLERANCE_SECONDS = 300


class Webhook:
    """Verify incoming webhook signatures from pgns."""

    def __init__(
        self, secret: str, *, tolerance_in_seconds: int = DEFAULT_TOLERANCE_SECONDS
    ) -> None:
        self._secret = secret
        self._tolerance = tolerance_in_seconds
        self._key_bytes = self._decode_secret(secret)

    def verify(self, body: str | bytes, headers: dict[str, str]) -> Any:
        """Verify the webhook signature and return the parsed JSON payload.

        Raises ``WebhookVerificationError`` on failure.
        """
        body_str = body.decode() if isinstance(body, bytes) else body

        get = self._make_getter(headers)

        webhook_sig = get("webhook-signature")
        if webhook_sig is not None:
            return self._verify_standard_webhooks(body_str, get, webhook_sig)

        pigeon_sig = get("x-pigeon-signature")
        if pigeon_sig is not None:
            return self._verify_legacy(body_str, get, pigeon_sig)

        raise WebhookVerificationError("No signature header found", "MISSING_HEADER")

    def _verify_standard_webhooks(
        self,
        body: str,
        get: _HeaderGetter,
        sig_header: str,
    ) -> Any:
        if not sig_header.startswith("v1,"):
            raise WebhookVerificationError(
                "Invalid webhook-signature format: missing v1, prefix",
                "INVALID_FORMAT",
            )
        b64_sig = sig_header[3:]

        msg_id = get("webhook-id")
        if msg_id is None:
            raise WebhookVerificationError("Missing webhook-id header", "MISSING_HEADER")

        timestamp = get("webhook-timestamp")
        if timestamp is None:
            raise WebhookVerificationError("Missing webhook-timestamp header", "MISSING_HEADER")

        self._check_timestamp(timestamp)

        signed_payload = f"{msg_id}.{timestamp}.{body}".encode()
        mac = hmac_mod.new(self._key_bytes, signed_payload, hashlib.sha256).digest()
        expected = base64.b64encode(mac).decode()

        if not hmac_mod.compare_digest(expected, b64_sig):
            raise WebhookVerificationError("Signature mismatch", "SIGNATURE_MISMATCH")

        return json.loads(body)

    def _verify_legacy(
        self,
        body: str,
        get: _HeaderGetter,
        sig_header: str,
    ) -> Any:
        if not sig_header.startswith("sha256="):
            raise WebhookVerificationError(
                "Invalid X-Pigeon-Signature format: missing sha256= prefix",
                "INVALID_FORMAT",
            )
        hex_digest = sig_header[7:]

        timestamp = get("x-pigeon-timestamp")
        if timestamp is not None:
            self._check_timestamp(timestamp)

        payload = f"{timestamp}.{body}" if timestamp else body
        signed_payload = payload.encode()
        mac = hmac_mod.new(self._key_bytes, signed_payload, hashlib.sha256).digest()
        expected = mac.hex()

        if not hmac_mod.compare_digest(expected, hex_digest):
            raise WebhookVerificationError("Signature mismatch", "SIGNATURE_MISMATCH")

        return json.loads(body)

    def _check_timestamp(self, ts: str) -> None:
        try:
            timestamp = int(ts)
        except ValueError:
            raise WebhookVerificationError("Invalid timestamp", "INVALID_FORMAT") from None
        now = int(time.time())
        if abs(now - timestamp) > self._tolerance:
            raise WebhookVerificationError("Timestamp outside tolerance", "TIMESTAMP_EXPIRED")

    @staticmethod
    def _decode_secret(secret: str) -> bytes:
        if secret.startswith("whsec_"):
            return base64.b64decode(secret[6:])
        if len(secret) == 64 and all(c in "0123456789abcdefABCDEF" for c in secret):
            return bytes.fromhex(secret)
        return secret.encode()

    @staticmethod
    def _make_getter(headers: dict[str, str]) -> _HeaderGetter:
        lower_map = {k.lower(): v for k, v in headers.items()}
        return lambda name: lower_map.get(name.lower())
