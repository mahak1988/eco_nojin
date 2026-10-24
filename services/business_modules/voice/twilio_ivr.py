"""Twilio IVR integration for telephony.

Provides real phone call and SMS capabilities via Twilio API.

Requirements:
- ``pip install twilio``
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER env variables

Fallback: If Twilio credentials are missing, all operations
return mock results with a logged warning.
"""

import hashlib
import hmac
import logging
import os
from dataclasses import dataclass
from xml.sax.saxutils import escape as xml_escape

from services.api_gateway.errors import safe_error_detail

logger = logging.getLogger(__name__)


def verify_twilio_signature(
    url: str,
    params: dict[str, str],
    signature: str,
    auth_token: str,
) -> bool:
    """Validate a Twilio webhook signature (constant-time).

    Twilio signs ``HMAC-SHA1(auth_token, url + concat(sorted(k+v)))`` and sends
    the hex digest in ``X-Twilio-Signature``. The URL must be the one Twilio
    called — behind a TLS-terminating proxy that is the public URL, not
    ``request.url`` (the caller passes it in).
    """
    if not signature or not auth_token:
        return False
    data = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    expected = hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected.encode("utf-8"), signature.encode("utf-8"))


@dataclass
class TwilioConfig:
    account_sid: str = ""
    auth_token: str = ""
    phone_number: str = ""

    def __post_init__(self):
        if not self.account_sid:
            self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        if not self.auth_token:
            self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        if not self.phone_number:
            self.phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "")

    def is_configured(self) -> bool:
        """Check if Twilio credentials are present."""
        return bool(self.account_sid and self.auth_token and self.phone_number)


class TwilioIVRIntegration:
    """Twilio-based IVR and SMS integration."""

    def __init__(self, config: TwilioConfig | None = None):
        self.config = config or TwilioConfig()
        self._client = None
        self._is_real = False

        if self.config.is_configured:
            try:
                from twilio.rest import Client

                self._client = Client(self.config.account_sid, self.config.auth_token)
                self._is_real = True
                logger.info("Twilio client initialized")
            except ImportError:
                logger.warning("twilio package not installed — using mock mode")
            except Exception as exc:
                logger.warning("Twilio init failed — using mock mode: %s", exc)

    @property
    def is_real_provider(self) -> bool:
        return self._is_real

    def get_config_info(self) -> dict:
        return {
            "configured": self.config.is_configured,
            "phone_number": self.config.phone_number[:6] + "***"
            if self.config.phone_number
            else None,
            "provider": "twilio" if self._is_real else "mock",
        }

    def _is_ready(self) -> bool:
        if not self.config.is_configured:
            logger.warning(
                "Twilio not configured — set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER"
            )
            return False
        if self._client is None:
            logger.warning("Twilio client not initialized — using mock mode")
            return False
        return True

    def make_call(self, phone_number: str, twiml: str) -> dict:
        """Initiate a phone call via Twilio.

        Returns dict with call_sid, status, and message.
        """
        if not self._is_ready():
            return {
                "call_sid": f"MOCK-CALL-{os.urandom(4).hex()}",
                "status": "mock",
                "phone_number": phone_number,
                "twiml": twiml,
                "message": "Mock call — configure Twilio for real telephony",
            }

        try:
            call = self._client.calls.create(
                twiml=twiml,
                to=phone_number,
                from_=self.config.phone_number,
            )
            return {
                "call_sid": call.sid,
                "status": call.status,
                "phone_number": phone_number,
                "twiml": twiml,
            }
        except Exception as exc:
            logger.warning("Twilio call failed: %s", exc)
            return {
                "call_sid": f"ERROR-{os.urandom(4).hex()}",
                "status": "error",
                "error": safe_error_detail(exc),
            }

    def send_sms(self, to: str, body: str) -> dict:
        """Send SMS via Twilio.

        Returns dict with message_sid, status, and phone_number.
        """
        if not self._is_ready():
            return {
                "message_sid": f"MOCK-MSG-{os.urandom(4).hex()}",
                "status": "mock",
                "to": to,
                "body": body,
                "message": "Mock SMS — configure Twilio for real SMS",
            }

        try:
            message = self._client.messages.create(
                body=body,
                to=to,
                from_=self.config.phone_number,
            )
            return {
                "message_sid": message.sid,
                "status": message.status,
                "to": to,
                "body": body,
            }
        except Exception as exc:
            logger.warning("Twilio SMS failed: %s", exc)
            return {
                "message_sid": f"ERROR-{os.urandom(4).hex()}",
                "status": "error",
                "error": safe_error_detail(exc),
            }

    def get_call_status(self, call_sid: str) -> dict:
        """Check call status."""
        if not self._is_ready():
            return {
                "call_sid": call_sid,
                "status": "mock",
                "message": "Mock status — configure Twilio for real status",
            }

        try:
            call = self._client.calls(call_sid).fetch()
            return {
                "call_sid": call.sid,
                "status": call.status,
                "from": call.from_,
                "to": call.to,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
                "duration": call.duration,
            }
        except Exception as exc:
            logger.warning("Twilio call status failed: %s", exc)
            return {
                "call_sid": call_sid,
                "status": "error",
                "error": safe_error_detail(exc),
            }

    def get_available_numbers(self, country_code: str = "IR") -> list:
        """List available phone numbers."""
        if not self._is_ready():
            return []
        try:
            numbers = self._client.available_phone_numbers(country_code).local.list(limit=10)
            return [
                {"phone_number": n.phone_number, "region": n.locality, "type": n.type}
                for n in numbers
            ]
        except Exception as exc:
            logger.warning("Twilio number lookup failed: %s", exc)
            return []

    def generate_twiml_ivr(self, menu_text: str, gather_action: str, language: str = "en") -> str:
        """Generate TwiML for IVR menu with DTMF input.

        Every interpolated value is XML-escaped (SEC-05): the menu text comes
        from the IVR engine and the language from a request enum, and TwiML is
        XML — an unescaped ``<``/``&`` would break the document or, if any of
        it is ever user-influenced, inject verbs.
        """
        menu = xml_escape(menu_text)
        action = xml_escape(gather_action, {'"': "&quot;"})
        lang = xml_escape(language, {'"': "&quot;"})
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="{lang}">{menu}</Say>
    <Gather input="dtmf" action="{action}" timeout="10">
        <Say voice="Polly.Joanna" language="{lang}">Press a digit.</Say>
    </Gather>
    <Say voice="Polly.Joanna" language="{lang}">Goodbye.</Say>
</Response>"""

    def generate_twiml_say(self, text: str, language: str = "en") -> str:
        """Generate simple TwiML that says text (XML-escaped, SEC-05)."""
        body = xml_escape(text)
        lang = xml_escape(language, {'"': "&quot;"})
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna" language="{lang}">{body}</Say>
</Response>"""


_twilio_ivr: TwilioIVRIntegration | None = None


def get_twilio_ivr() -> TwilioIVRIntegration:
    """Return the singleton Twilio IVR integration instance."""
    global _twilio_ivr
    if _twilio_ivr is None:
        _twilio_ivr = TwilioIVRIntegration()
    return _twilio_ivr
