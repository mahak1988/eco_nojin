"""
Locale Detection Middleware for Eco Nojin
==========================================
Detects user locale from Accept-Language header and sets request.state.locale.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from engine.hydroma.config.settings import get_settings

logger = logging.getLogger("econojin.middleware.locale")


class LocaleMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and set user locale."""

    def __init__(self, app):
        super().__init__(app)
        self._rtl_languages_cache: Optional[list[str]] = None

    def _get_settings(self):
        """Get current settings (allows for testing with overridden settings)."""
        return get_settings()

    def _parse_accept_language(self, header: str) -> list[tuple]:
        """
        Parse Accept-Language header into list of (language, quality) tuples.
        Example: "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"
        Returns: [("fa", 1.0), ("en", 0.8)]
        """
        if not header:
            return []

        languages = []
        for part in header.split(","):
            part = part.strip()
            if ";" in part:
                lang, q_part = part.split(";", 1)
                lang = lang.strip()
                try:
                    q = float(q_part.split("=")[1])
                except (ValueError, IndexError):
                    q = 1.0
            else:
                lang = part
                q = 1.0

            # Extract primary language code (e.g., "fa-IR" -> "fa")
            primary_lang = lang.split("-")[0].lower()
            languages.append((primary_lang, q))

        # Sort by quality descending
        languages.sort(key=lambda x: x[1], reverse=True)
        return languages

    def _get_best_match(self, accept_lang: str) -> str:
        """Get best matching supported language from Accept-Language header."""
        settings = self._get_settings()
        supported = [
            lang.strip() for lang in settings.supported_languages.split(",") if lang.strip()
        ]
        default = settings.default_language

        parsed = self._parse_accept_language(accept_lang)

        for lang, _ in parsed:
            if lang in supported:
                return lang

        return default

    def _get_rtl_languages(self) -> list[str]:
        """Get RTL languages from settings (cached)."""
        if self._rtl_languages_cache is None:
            settings = self._get_settings()
            self._rtl_languages_cache = [
                lang.strip() for lang in settings.rtl_languages.split(",") if lang.strip()
            ]
        return self._rtl_languages_cache

    async def dispatch(self, request: Request, call_next):
        """Process request and set locale."""
        # Get Accept-Language header
        accept_language = request.headers.get("accept-language", "")

        # Determine locale
        locale = self._get_best_match(accept_language)

        # Store in request state for use in route handlers
        request.state.locale = locale
        request.state.is_rtl = locale in self._get_rtl_languages()

        # Add locale to response headers
        response = await call_next(request)
        response.headers["X-Content-Language"] = locale
        response.headers["X-Content-Direction"] = "rtl" if request.state.is_rtl else "ltr"

        return response
