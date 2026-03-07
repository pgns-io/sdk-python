"""Errors raised by the pgns SDK."""

from __future__ import annotations


class PigeonsError(Exception):
    """Error returned by the pgns API."""

    def __init__(self, message: str, status: int, code: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def __repr__(self) -> str:
        return f"PigeonsError({self.args[0]!r}, status={self.status}, code={self.code!r})"

    def is_not_found(self) -> bool:
        return self.status == 404

    def is_unauthorized(self) -> bool:
        return self.status == 401


class PigeonsAuthError(PigeonsError):
    """Raised when authentication fails and cannot be refreshed."""

    def __init__(self, message: str = "Session expired") -> None:
        super().__init__(message, 401)


class WebhookVerificationError(PigeonsError):
    """Raised when webhook signature verification fails."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message, 400, code=code)
