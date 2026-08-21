"""Rubika adapter — guarded stub (Phase 2).

Rubika's bot protocol differs from Telegram's (phone-session based,
different message model), so it cannot reuse the aiogram dispatcher
byte-for-byte. Rather than ship unverified glue, this adapter reports the
exact state and points to the study needed. Enabled only when the operator
explicitly sets RUBIKA_ENABLED=true — and even then it fails loudly.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RubikaGateway:
    """Rubika gateway — pending a live integration study (Verified=False)."""

    def __init__(self, token: str) -> None:
        self.token = token

    def available(self) -> bool:
        # No verified client exists yet; never claim availability.
        return False

    def start(self) -> None:
        raise NotImplementedError(
            "Rubika integration is not implemented yet: its bot protocol is "
            "not Telegram-compatible (phone-session auth, different message "
            "model). See docs/15_multiplatform_bots.md §Rubika for the "
            "required integration study. Set RUBIKA_ENABLED=false until then."
        )
