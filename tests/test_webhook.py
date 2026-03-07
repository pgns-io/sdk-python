from __future__ import annotations

import base64
import hashlib
import hmac as hmac_mod
import time

import pytest

from pgns.sdk.errors import WebhookVerificationError
from pgns.sdk.webhook import Webhook

SECRET = "test-secret"


def _now_ts() -> str:
    return str(int(time.time()))


def _standard_headers(
    secret: str,
    body: str,
    *,
    timestamp: str | None = None,
    msg_id: str = "msg_test-id",
) -> dict[str, str]:
    ts = timestamp or _now_ts()
    signed_payload = f"{msg_id}.{ts}.{body}".encode()
    mac = hmac_mod.new(secret.encode(), signed_payload, hashlib.sha256).digest()
    b64 = base64.b64encode(mac).decode()
    return {
        "webhook-id": msg_id,
        "webhook-timestamp": ts,
        "webhook-signature": f"v1,{b64}",
    }


def _legacy_headers(
    secret: str,
    body: str,
    *,
    timestamp: str | None = None,
) -> dict[str, str]:
    ts = timestamp or _now_ts()
    payload = f"{ts}.{body}"
    mac = hmac_mod.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    return {
        "X-Pigeon-Signature": f"sha256={mac.hex()}",
        "X-Pigeon-Timestamp": ts,
    }


class TestStandardWebhooks:
    def test_verify_valid(self) -> None:
        body = '{"event":"test"}'
        headers = _standard_headers(SECRET, body)
        wh = Webhook(SECRET)
        result = wh.verify(body, headers)
        assert result == {"event": "test"}

    def test_reject_tampered_body(self) -> None:
        body = '{"event":"test"}'
        headers = _standard_headers(SECRET, body)
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="Signature mismatch"):
            wh.verify('{"event":"tampered"}', headers)

    def test_reject_wrong_secret(self) -> None:
        body = '{"event":"test"}'
        headers = _standard_headers(SECRET, body)
        wh = Webhook("wrong-secret")
        with pytest.raises(WebhookVerificationError, match="Signature mismatch"):
            wh.verify(body, headers)

    def test_reject_expired_timestamp(self) -> None:
        body = '{"event":"test"}'
        old_ts = str(int(time.time()) - 600)
        headers = _standard_headers(SECRET, body, timestamp=old_ts)
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="Timestamp outside tolerance"):
            wh.verify(body, headers)

    def test_custom_tolerance(self) -> None:
        body = '{"event":"test"}'
        old_ts = str(int(time.time()) - 600)
        headers = _standard_headers(SECRET, body, timestamp=old_ts)
        wh = Webhook(SECRET, tolerance_in_seconds=700)
        result = wh.verify(body, headers)
        assert result == {"event": "test"}

    def test_reject_missing_webhook_id(self) -> None:
        body = '{"event":"test"}'
        headers = _standard_headers(SECRET, body)
        del headers["webhook-id"]
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="Missing webhook-id"):
            wh.verify(body, headers)

    def test_reject_missing_webhook_timestamp(self) -> None:
        body = '{"event":"test"}'
        headers = _standard_headers(SECRET, body)
        del headers["webhook-timestamp"]
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="Missing webhook-timestamp"):
            wh.verify(body, headers)

    def test_reject_invalid_format(self) -> None:
        body = '{"event":"test"}'
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="missing v1, prefix"):
            wh.verify(
                body,
                {
                    "webhook-id": "msg_1",
                    "webhook-timestamp": _now_ts(),
                    "webhook-signature": "bad-format",
                },
            )


class TestLegacyFormat:
    def test_verify_valid(self) -> None:
        body = '{"event":"test"}'
        headers = _legacy_headers(SECRET, body)
        wh = Webhook(SECRET)
        result = wh.verify(body, headers)
        assert result == {"event": "test"}

    def test_reject_tampered_body(self) -> None:
        body = '{"event":"test"}'
        headers = _legacy_headers(SECRET, body)
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="Signature mismatch"):
            wh.verify('{"event":"tampered"}', headers)

    def test_reject_expired_timestamp(self) -> None:
        body = '{"event":"test"}'
        old_ts = str(int(time.time()) - 600)
        headers = _legacy_headers(SECRET, body, timestamp=old_ts)
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="Timestamp outside tolerance"):
            wh.verify(body, headers)

    def test_reject_invalid_format(self) -> None:
        body = '{"event":"test"}'
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="missing sha256= prefix"):
            wh.verify(body, {"X-Pigeon-Signature": "bad-format"})


class TestFormatDetection:
    def test_prefers_standard_when_both_present(self) -> None:
        body = '{"event":"test"}'
        std = _standard_headers(SECRET, body)
        lgc = _legacy_headers(SECRET, body)
        combined = {**lgc, **std}
        wh = Webhook(SECRET)
        result = wh.verify(body, combined)
        assert result == {"event": "test"}

    def test_missing_header_raises(self) -> None:
        wh = Webhook(SECRET)
        with pytest.raises(WebhookVerificationError, match="No signature header found"):
            wh.verify("{}", {})


class TestHeaderCaseInsensitivity:
    def test_uppercase_headers(self) -> None:
        body = '{"event":"test"}'
        headers = _standard_headers(SECRET, body)
        upper = {k.upper(): v for k, v in headers.items()}
        wh = Webhook(SECRET)
        result = wh.verify(body, upper)
        assert result == {"event": "test"}


class TestKeyDecoding:
    def test_whsec_prefix(self) -> None:
        import os

        raw_key = os.urandom(32)
        b64 = base64.b64encode(raw_key).decode()
        whsec_secret = f"whsec_{b64}"

        body = '{"event":"test"}'
        ts = _now_ts()
        msg_id = "msg_whsec-test"
        signed_payload = f"{msg_id}.{ts}.{body}".encode()
        mac = hmac_mod.new(raw_key, signed_payload, hashlib.sha256).digest()
        sig = base64.b64encode(mac).decode()

        headers = {
            "webhook-id": msg_id,
            "webhook-timestamp": ts,
            "webhook-signature": f"v1,{sig}",
        }

        wh = Webhook(whsec_secret)
        result = wh.verify(body, headers)
        assert result == {"event": "test"}

    def test_hex_key(self) -> None:
        import os

        raw_key = os.urandom(32)
        hex_secret = raw_key.hex()

        body = '{"event":"test"}'
        ts = _now_ts()
        msg_id = "msg_hex-test"
        signed_payload = f"{msg_id}.{ts}.{body}".encode()
        mac = hmac_mod.new(raw_key, signed_payload, hashlib.sha256).digest()
        sig = base64.b64encode(mac).decode()

        headers = {
            "webhook-id": msg_id,
            "webhook-timestamp": ts,
            "webhook-signature": f"v1,{sig}",
        }

        wh = Webhook(hex_secret)
        result = wh.verify(body, headers)
        assert result == {"event": "test"}

    def test_bytes_body(self) -> None:
        body = b'{"event":"test"}'
        headers = _standard_headers(SECRET, body.decode())
        wh = Webhook(SECRET)
        result = wh.verify(body, headers)
        assert result == {"event": "test"}
