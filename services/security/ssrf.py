"""SSRF protection for outbound HTTP requests."""

from __future__ import annotations

import ipaddress
import logging
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Allowed domains for external API calls
# NOTE: localhost and 127.0.0.1 are intentionally NOT in this allowlist.
# They are blocked by BLOCKED_NETWORKS below to prevent SSRF attacks.
ALLOWED_DOMAINS = {
    "power.larc.nasa.gov",
    "api.open-meteo.com",
    "catalogue.dataspace.copernicus.eu",
    "identity.dataspace.copernicus.eu",
    "cds.climate.copernicus.eu",
    "ads.atmosphere.copernicus.eu",
    "ewds.climate.copernicus.eu",
    "sepal.io",
}

# Blocked IP ranges (private, loopback, link-local)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]


def _is_ip_blocked(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in BLOCKED_NETWORKS)
    except ValueError:
        return True


def _resolve_hostname(hostname: str) -> list[str]:
    try:
        import socket

        return [ip[4].split(":")[0] for ip in socket.getaddrinfo(hostname, None)]
    except Exception:
        return []


def validate_url(url: str, allowed_domains: set[str] | None = None) -> bool:
    """Validate URL for SSRF protection.

    Checks:
    1. Scheme is http or https
    2. Hostname is in allowed domains
    3. Resolved IP is not in private/reserved ranges
    """
    if allowed_domains is None:
        allowed_domains = ALLOWED_DOMAINS

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            logger.warning("SSRF blocked: invalid scheme %s", parsed.scheme)
            return False

        hostname = parsed.hostname
        if not hostname:
            logger.warning("SSRF blocked: no hostname")
            return False

        if hostname not in allowed_domains:
            logger.warning("SSRF blocked: domain not allowed %s", hostname)
            return False

        ips = _resolve_hostname(hostname)
        for ip_str in ips:
            if _is_ip_blocked(ip_str):
                logger.warning("SSRF blocked: IP in blocked range %s", ip_str)
                return False

        return True
    except Exception as exc:
        logger.warning("SSRF validation error: %s", exc)
        return False


class SSRFProtectedClient:
    """HTTP client with SSRF protection."""

    def __init__(self, client: Any, allowed_domains: set[str] | None = None) -> None:
        self._client = client
        self._allowed_domains = allowed_domains or ALLOWED_DOMAINS

    async def request(self, method: str, url: str, **kwargs) -> Any:
        if not validate_url(url, self._allowed_domains):
            raise ValueError(f"SSRF protection: blocked request to {url}")
        return await self._client.request(method, url, **kwargs)

    def sync_request(self, method: str, url: str, **kwargs) -> Any:
        if not validate_url(url, self._allowed_domains):
            raise ValueError(f"SSRF protection: blocked request to {url}")
        return self._client.request(method, url, **kwargs)
