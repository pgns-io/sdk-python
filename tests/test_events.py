"""Tests for SSE event streaming."""

from __future__ import annotations


def test_parse_sse_lines() -> None:
    """Verify the data: prefix stripping logic used by the event stream."""
    lines = [
        'data: {"id":"p1","roost_id":"r1"}',
        "",
        'data: {"id":"p2","roost_id":"r1"}',
        ": keepalive",
        "event: message",
    ]
    results: list[str] = []
    for line in lines:
        if line.startswith("data:"):
            results.append(line[5:].strip())

    assert len(results) == 2
    assert '"p1"' in results[0]
    assert '"p2"' in results[1]


def test_empty_data_line() -> None:
    """A data: line with no payload should yield an empty string."""
    line = "data:"
    result = line[5:].strip()
    assert result == ""


def test_data_with_extra_whitespace() -> None:
    """Whitespace after data: should be stripped."""
    line = 'data:   {"id":"p1"}  '
    result = line[5:].strip()
    assert result == '{"id":"p1"}'
