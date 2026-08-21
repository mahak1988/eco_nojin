"""WhatsApp Business Cloud API adapter (Phase 10 — second bot wave).

Honest skeleton: registered in the bot factory only when WHATSAPP_TOKEN is
present. Uses the Meta Cloud API over httpx; the handler pipeline is shared
with the other platforms (core.dispatcher). Not activated by default.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from services.bots.core.dispatcher import BotAdapter  # noqa: F401  (shared base)

META_API = "https://graph.facebook.com/v20.0"


class WhatsAppAdapter:
    """Minimal Meta Cloud API adapter (token-gated)."""

    platform = "whatsapp"

    def __init__(self, token: Optional[str] = None, phone_number_id: Optional[str] = None) -> None:
        self.token = token or os.getenv("WHATSAPP_TOKEN", "")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

    @property
    def available(self) -> bool:
        """Adapter is only usable with both credentials present."""
        return bool(self.token and self.phone_number_id)

    def send_text(self, to: str, text: str) -> Dict[str, Any]:
        """Send a text message via the Cloud API."""
        if not self.available:
            raise RuntimeError("WhatsApp adapter not configured (WHATSAPP_TOKEN/PHONE_NUMBER_ID)")
        import httpx

        url = f"{META_API}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        resp = httpx.post(url, headers={"Authorization": f"Bearer {self.token}"}, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Webhook verification handshake (Meta sends token + challenge)."""
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        if mode == "subscribe" and token == verify_token:
            return challenge
        return None

    def parse_inbound(self, body: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract inbound messages from a webhook payload (honest parser)."""
        messages: List[Dict[str, str]] = []
        entries = body.get("entry") or []
        for entry in entries:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for msg in value.get("messages") or []:
                    if msg.get("type") == "text":
                        messages.append(
                            {
                                "from": msg.get("from", ""),
                                "text": (msg.get("text") or {}).get("body", ""),
                                "message_id": msg.get("id", ""),
                            }
                        )
        return messages
