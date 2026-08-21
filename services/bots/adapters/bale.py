"""Bale adapter — bridge to python-bale-bot (lazy import, Phase 2).

``python-bale-bot`` conflicts with our aiohttp version on Windows, so it is
NOT installed in the main environment. The adapter imports it lazily: on a
host where it is installed (e.g. the Linux deploy VM), Bale works; elsewhere
it fails loudly with install guidance instead of crashing at import time.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class BaleGateway:
    """Bale messenger gateway (documented python-bale-bot API surface).

    Verified=False (see platforms.py): the exact handler wiring needs a live
    token check on a host where python-bale-bot is installed.
    """

    def __init__(self, token: str) -> None:
        self.token = token
        self._client = None

    def _load_library(self):
        """Import the third-party client; raises RuntimeError with guidance."""
        if self._client is not None:
            return self._client
        try:
            import balebot  # noqa: F401  (import name used by python-bale-bot)

            self._client = balebot
            return self._client
        except ImportError:
            raise RuntimeError(
                "Bale support requires 'python-bale-bot'. Install it in an "
                "isolated environment (it conflicts with aiohttp on Windows): "
                "pip install python-bale-bot  — then set BALE_ENABLED=true "
                "and BALE_TOKEN=<token> in .env."
            ) from None

    def available(self) -> bool:
        try:
            self._load_library()
            return True
        except RuntimeError:
            return False

    def start(self) -> None:
        """Blocking polling loop (run in a worker thread by the runner)."""
        lib = self._load_library()
        logger.info("Bale gateway starting (python-bale-bot %s)", getattr(lib, "__version__", "?"))
        # Wiring the balebot handler set is a live-verification task: the
        # dispatcher handlers are Telegram-shaped and must be mapped onto
        # balebot's own decorators (documented in docs/15_multiplatform_bots.md).
        raise NotImplementedError(
            "Bale live polling wiring is pending a real token verification "
            "(docs/15_multiplatform_bots.md §Bale)."
        )
