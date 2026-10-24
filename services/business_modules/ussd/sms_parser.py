"""SMS Command Parser.

Supports commands like:
  SOIL 36.8 54.4
  CROP north
  PRICE wheat
  WEATHER tehran
  ASK How to make compost?
"""

import re
from enum import Enum

from .engine import Language


class SmsCommandType(Enum):
    """SMS command types."""

    SOIL = "soil"
    CROP = "crop"
    PRICE = "price"
    WEATHER = "weather"
    ASK = "ask"
    HELP = "help"
    LANG = "lang"
    UNKNOWN = "unknown"


SMS_RESPONSES: dict[str, dict[Language, str]] = {
    "help": {
        Language.EN: "Eco Nojin SMS commands:\nSOIL lat lon\nCROP region\nPRICE product\nWEATHER city\nASK question\nLANG en|fa|ar",
        Language.FA: "دستورات پیامک اکو نوژین:\nSOIL عرض طول\nCROP منطقه\nPRICE محصول\nWEATHER شهر\nASK سوال\nLANG en|fa|ar",
        Language.AR: "أوامر SMS إيكو نوجين:\nSOIL عرض طول\nCROP منطقة\nPRICE منتج\nWEATHER مدينة\nASK سؤال\nLANG en|fa|ar",
    },
    "lang_set": {
        Language.EN: "Language set to English. Reply HELP for commands.",
        Language.FA: "زبان به فارسی تغییر کرد. برای دستورات HELP را ارسال کنید.",
        Language.AR: "تم تعيين اللغة إلى العربية. أرسل HELP للأوامر.",
    },
    "unknown": {
        Language.EN: "Unknown command. Reply HELP for available commands.",
        Language.FA: "دستور ناشناخته. برای دستورات موجود HELP را ارسال کنید.",
        Language.AR: "أمر غير معروف. أرسل HELP للأوامر المتاحة.",
    },
}


class SmsParser:
    """Parse and process SMS commands."""

    def __init__(self):
        self._user_languages: dict[str, Language] = {}  # phone -> language

    def get_user_language(self, phone: str) -> Language:
        """Get user's preferred language (default: English)."""
        return self._user_languages.get(phone, Language.EN)

    def set_user_language(self, phone: str, lang: Language) -> None:
        """Set user's preferred language."""
        self._user_languages[phone] = lang

    def parse(self, message: str) -> dict:
        """Parse SMS message into command and arguments."""
        message = message.strip()
        if not message:
            return {"type": SmsCommandType.UNKNOWN, "args": []}

        parts = message.split(maxsplit=1)
        command = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""

        command_map = {
            "SOIL": SmsCommandType.SOIL,
            "CROP": SmsCommandType.CROP,
            "PRICE": SmsCommandType.PRICE,
            "WEATHER": SmsCommandType.WEATHER,
            "ASK": SmsCommandType.ASK,
            "HELP": SmsCommandType.HELP,
            "LANG": SmsCommandType.LANG,
        }

        cmd_type = command_map.get(command, SmsCommandType.UNKNOWN)
        return {
            "type": cmd_type,
            "command": command,
            "args": args,
            "raw": message,
        }

    def process(self, phone: str, message: str) -> str:
        """Process SMS command and return response text."""
        parsed = self.parse(message)
        lang = self.get_user_language(phone)

        cmd_type = parsed["type"]
        args = parsed["args"]

        if cmd_type == SmsCommandType.HELP:
            return SMS_RESPONSES["help"][lang]

        if cmd_type == SmsCommandType.LANG:
            lang_code = args.strip().lower()
            if lang_code in ["en", "fa", "ar"]:
                new_lang = Language(lang_code)
                self.set_user_language(phone, new_lang)
                return SMS_RESPONSES["lang_set"][new_lang]
            return "Invalid language. Use: en, fa, ar"

        if cmd_type == SmsCommandType.SOIL:
            return self._process_soil(args, lang)

        if cmd_type == SmsCommandType.CROP:
            return self._process_crop(args, lang)

        if cmd_type == SmsCommandType.PRICE:
            return self._process_price(args, lang)

        if cmd_type == SmsCommandType.WEATHER:
            return self._process_weather(args, lang)

        if cmd_type == SmsCommandType.ASK:
            return self._process_ask(args, lang)

        return SMS_RESPONSES["unknown"][lang]

    def _process_soil(self, args: str, lang: Language) -> str:
        """Process SOIL lat lon command."""
        try:
            parts = re.split(r"[\s,]+", args.strip())
            if len(parts) != 2:
                raise ValueError("Need 2 coordinates")
            lat, lon = float(parts[0]), float(parts[1])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Out of range")
        except Exception:
            return "Invalid coordinates. Format: SOIL 36.8 54.4"

        # Mock response
        ndvi = 0.45 + (lat % 1) * 0.1
        status = "Good" if ndvi > 0.5 else "Stressed"
        if lang == Language.FA:
            status = "خوب" if ndvi > 0.5 else "تحت تنش"
        elif lang == Language.AR:
            status = "جيد" if ndvi > 0.5 else "مجهد"

        return f"Soil ({lat:.2f},{lon:.2f}): NDVI={ndvi:.2f}, {status}"

    def _process_crop(self, args: str, lang: Language) -> str:
        """Process CROP region command."""
        region = args.strip().lower()
        if not region:
            return "Usage: CROP <region>. Example: CROP north"

        crops = {
            "north": "Rice, Wheat (Oct-Nov)",
            "central": "Wheat, Saffron (Nov-Dec)",
            "south": "Dates, Citrus (Sep-Oct)",
            "west": "Grapes, Walnuts (Oct-Nov)",
        }

        for key, value in crops.items():
            if key in region:
                return f"{key.title()}: {value}"

        return f"Region '{args}' not found. Try: north, central, south, west"

    def _process_price(self, args: str, lang: Language) -> str:
        """Process PRICE product command."""
        product = args.strip().lower()
        if not product:
            return "Usage: PRICE <product>. Example: PRICE wheat"

        prices = {
            "wheat": 0.35,
            "barley": 0.28,
            "saffron": 850,
            "pistachio": 12,
            "dates": 3.5,
        }

        for key, price in prices.items():
            if key in product:
                trend = "stable" if price < 5 else "rising"
                return f"{key.title()}: ${price:.2f}/kg (trend: {trend})"

        return f"Product '{args}' not found. Try: wheat, barley, saffron, pistachio, dates"

    def _process_weather(self, args: str, lang: Language) -> str:
        """Process WEATHER city command."""
        city = args.strip().lower()
        if not city:
            return "Usage: WEATHER <city>. Example: WEATHER tehran"

        weather = {
            "tehran": (25, 0, "Sunny"),
            "mashhad": (22, 5, "Rain"),
            "isfahan": (28, 0, "Hot"),
            "shiraz": (30, 0, "Clear"),
            "tabriz": (18, 10, "Cool"),
        }

        for key, (temp, rain, forecast) in weather.items():
            if key in city:
                return f"{key.title()}: {temp}°C, {rain}mm rain, {forecast}"

        return f"City '{args}' not found. Try: tehran, mashhad, isfahan, shiraz, tabriz"

    def _process_ask(self, args: str, lang: Language) -> str:
        """Process ASK question command."""
        question = args.strip()
        if not question:
            return "Usage: ASK <question>"

        # Mock AI response (140 chars max for SMS)
        answer = (
            f"AI: For '{question[:40]}...' consult local extension officer for detailed guidance."
        )
        return answer[:140]


# Singleton
_parser: SmsParser | None = None


def get_sms_parser() -> SmsParser:
    """Get singleton SMS parser."""
    global _parser
    if _parser is None:
        _parser = SmsParser()
    return _parser
