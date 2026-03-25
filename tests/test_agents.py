# Copyright (c) 2026 PGNS LLC
# SPDX-License-Identifier: MIT

"""Tests for the agent pattern helpers module."""

from __future__ import annotations

from pgns.agents import (
    CORRELATION_ID_HEADER,
    correlation_headers,
    extract_correlation_id,
    validate_correlation_id,
)


class TestValidateCorrelationId:
    def test_valid_simple(self) -> None:
        assert validate_correlation_id("abc-123") is True

    def test_valid_printable_ascii(self) -> None:
        assert validate_correlation_id("req_!@#$%^&*()") is True

    def test_valid_max_length(self) -> None:
        assert validate_correlation_id("a" * 128) is True

    def test_invalid_empty(self) -> None:
        assert validate_correlation_id("") is False

    def test_invalid_too_long(self) -> None:
        assert validate_correlation_id("a" * 129) is False

    def test_invalid_space(self) -> None:
        assert validate_correlation_id("has space") is False

    def test_invalid_non_ascii(self) -> None:
        assert validate_correlation_id("café") is False


class TestCorrelationHeaders:
    def test_valid_id(self) -> None:
        result = correlation_headers("req-123")
        assert result == {CORRELATION_ID_HEADER: "req-123"}

    def test_none(self) -> None:
        assert correlation_headers(None) == {}

    def test_invalid_id(self) -> None:
        assert correlation_headers("has space") == {}

    def test_spreadable(self) -> None:
        headers = {"Content-Type": "application/json", **correlation_headers("cid-1")}
        assert headers[CORRELATION_ID_HEADER] == "cid-1"


class TestExtractCorrelationId:
    def test_pgns_header(self) -> None:
        headers = {"X-Pgns-CorrelationId": "pgns-123"}
        assert extract_correlation_id(headers) == "pgns-123"

    def test_standard_fallback(self) -> None:
        headers = {"X-Correlation-ID": "corr-456"}
        assert extract_correlation_id(headers) == "corr-456"

    def test_request_id_fallback(self) -> None:
        headers = {"X-Request-ID": "req-789"}
        assert extract_correlation_id(headers) == "req-789"

    def test_priority_order(self) -> None:
        headers = {
            "X-Pgns-CorrelationId": "pgns-first",
            "X-Correlation-ID": "corr-second",
            "X-Request-ID": "req-third",
        }
        assert extract_correlation_id(headers) == "pgns-first"

    def test_case_insensitive(self) -> None:
        headers = {"x-pgns-correlationid": "lower-case"}
        assert extract_correlation_id(headers) == "lower-case"

    def test_no_header(self) -> None:
        headers = {"Content-Type": "application/json"}
        assert extract_correlation_id(headers) is None

    def test_invalid_value_returns_none(self) -> None:
        headers = {"X-Pgns-CorrelationId": "has space"}
        assert extract_correlation_id(headers) is None

    def test_skips_invalid_fallback_tries_next(self) -> None:
        headers = {"X-Correlation-ID": "has space", "X-Request-ID": "valid-req-id"}
        assert extract_correlation_id(headers) == "valid-req-id"

    def test_invalid_pgns_header_blocks_fallbacks(self) -> None:
        headers = {"X-Pgns-CorrelationId": "has space", "X-Request-ID": "valid-req-id"}
        assert extract_correlation_id(headers) is None
