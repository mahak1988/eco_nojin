"""Standard exception hierarchy for Eco Nojin services."""

from __future__ import annotations


class EcoNojinException(Exception):
    """Base exception for all Eco Nojin service errors."""

    def __init__(self, message: str, *, status_code: int = 500, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or self.__class__.__name__


class ServiceUnavailableException(EcoNojinException):
    def __init__(
        self, message: str = "Service temporarily unavailable", *, code: str | None = None
    ):
        super().__init__(message, status_code=503, code=code)


class NotFoundException(EcoNojinException):
    def __init__(self, message: str = "Resource not found", *, code: str | None = None):
        super().__init__(message, status_code=404, code=code)


class ValidationException(EcoNojinException):
    def __init__(self, message: str = "Validation failed", *, code: str | None = None):
        super().__init__(message, status_code=422, code=code)


class UnauthorizedException(EcoNojinException):
    def __init__(self, message: str = "Authentication required", *, code: str | None = None):
        super().__init__(message, status_code=401, code=code)


class ForbiddenException(EcoNojinException):
    def __init__(self, message: str = "Access denied", *, code: str | None = None):
        super().__init__(message, status_code=403, code=code)


class ConflictException(EcoNojinException):
    def __init__(self, message: str = "Resource conflict", *, code: str | None = None):
        super().__init__(message, status_code=409, code=code)
