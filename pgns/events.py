"""SSE event streaming for the pgns API."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Iterator

import httpx

_DEFAULT_RETRY_DELAY = 3.0


def event_stream(
    base_url: str,
    *,
    token: str | None = None,
    roost_id: str | None = None,
) -> Iterator[str]:
    """Connect to the pgns SSE event stream (synchronous).

    Yields each ``data:`` line as a string. Automatically reconnects on
    failure with a 3-second delay. Break out of the iterator to disconnect.

    Args:
        base_url: Base URL of the pgns API.
        token: Bearer token (API key or JWT) for authentication.
        roost_id: Restrict the stream to a single roost.

    Yields:
        Event data strings (JSON-encoded pigeon notifications).
    """
    url = f"{base_url.rstrip('/')}/v1/events"
    if roost_id:
        url += f"?roost_id={roost_id}"
    headers: dict[str, str] = {"Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    while True:
        try:
            with httpx.Client() as client:
                with client.stream("GET", url, headers=headers, timeout=None) as response:
                    response.raise_for_status()
                    buffer = ""
                    for chunk in response.iter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line.startswith("data:"):
                                yield line[5:].strip()
        except GeneratorExit:
            return
        except Exception:
            pass
        time.sleep(_DEFAULT_RETRY_DELAY)


async def async_event_stream(
    base_url: str,
    *,
    token: str | None = None,
    roost_id: str | None = None,
) -> AsyncIterator[str]:
    """Connect to the pgns SSE event stream (asynchronous).

    Async mirror of :func:`event_stream`.
    """
    url = f"{base_url.rstrip('/')}/v1/events"
    if roost_id:
        url += f"?roost_id={roost_id}"
    headers: dict[str, str] = {"Accept": "text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    while True:
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url, headers=headers, timeout=None) as response:
                    response.raise_for_status()
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line.startswith("data:"):
                                yield line[5:].strip()
        except GeneratorExit:
            return
        except Exception:
            pass
        await asyncio.sleep(_DEFAULT_RETRY_DELAY)
