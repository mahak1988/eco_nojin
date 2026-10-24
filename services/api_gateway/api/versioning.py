"""API Versioning for Eco Nojin.

Provides path-based versioning: /api/v1/resource, /api/v2/resource
Default version: v1 (backward compatible)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import APIRouter, Request


class ApiVersion(StrEnum):
    V1 = "v1"
    V2 = "v2"


DEFAULT_API_VERSION = ApiVersion.V1

_VERSION_HEADER = "X-API-Version"
_WARNING_HEADER = "Warning"


def get_version_from_request(request: Request) -> ApiVersion:
    """Extract API version from path, query param, or Accept header."""
    path_parts = request.url.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[0] == "api" and path_parts[1] in (
        ApiVersion.V1.value,
        ApiVersion.V2.value,
    ):
        return ApiVersion(path_parts[1])
    version_param = request.query_params.get("version")
    if version_param and version_param in (
        ApiVersion.V1.value,
        ApiVersion.V2.value,
    ):
        return ApiVersion(version_param)
    accept_header = request.headers.get("Accept", "")
    for version in ApiVersion:
        if f"application/vnd.api+{version.value}" in accept_header:
            return version
    return DEFAULT_API_VERSION


def add_version_middleware(app: Any) -> None:
    """Add middleware to inject version info into responses."""

    @app.middleware("http")
    async def version_middleware(request: Request, call_next):
        version = get_version_from_request(request)
        response = await call_next(request)
        response.headers[_VERSION_HEADER] = version.value
        if version != DEFAULT_API_VERSION:
            response.headers[_WARNING_HEADER] = (
                f'299 - "Using deprecated API version {version.value}; '
                f'migrate to {DEFAULT_API_VERSION.value}"'
            )
        return response


class VersionedRouter:
    """Helper to create versioned routers."""

    def __init__(self, version: ApiVersion, prefix: str = "") -> None:
        self.version = version
        self._router = APIRouter(prefix=f"/api/{version.value}{prefix}")

    @property
    def router(self) -> APIRouter:
        return self._router

    def get(self, path: str, **kwargs: Any):
        def decorator(func):
            self._router.get(path, **kwargs)(func)
            return func
        return decorator

    def post(self, path: str, **kwargs: Any):
        def decorator(func):
            self._router.post(path, **kwargs)(func)
            return func
        return decorator

    def put(self, path: str, **kwargs: Any):
        def decorator(func):
            self._router.put(path, **kwargs)(func)
            return func
        return decorator

    def delete(self, path: str, **kwargs: Any):
        def decorator(func):
            self._router.delete(path, **kwargs)(func)
            return func
        return decorator
