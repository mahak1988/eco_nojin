"""USSD/SMS Gateway Engine.

Processes USSD menu flows and SMS commands, returning text responses
suitable for basic feature phones (160 chars for SMS, 182 for USSD).

Supports 3 languages: en, fa, ar (based on user preference).
"""

from dataclasses import dataclass
from enum import Enum


class GatewayType(Enum):
    """Type of incoming request."""

    USSD = "ussd"
    SMS = "sms"


class Language(Enum):
    """Supported languages for USSD/SMS."""

    EN = "en"
    FA = "fa"
    AR = "ar"


@dataclass
class UssdRequest:
    """USSD request from telco."""

    session_id: str
    service_code: str  # e.g. "*384*73#"
    phone_number: str
    text: str  # USSD input so far (empty for first request)
    gateway: GatewayType = GatewayType.USSD
    language: Language = Language.EN


@dataclass
class UssdResponse:
    """USSD response to send back."""

    text: str
    end_session: bool = False  # True = CON, False = END

    def to_africastalking_format(self) -> str:
        """Format for Africa's Talking USSD gateway."""
        prefix = "END" if self.end_session else "CON"
        return f"{prefix} {self.text}"


# ============================================================================
# TRANSLATIONS
# ============================================================================
MESSAGES: dict[str, dict[Language, str]] = {
    # Main menu
    "main_menu": {
        Language.EN: "CON Eco Nojin Services\n1. Soil Analysis\n2. Crop Advice\n3. Market Prices\n4. Weather\n5. Ask Expert\n0. Exit",
        Language.FA: "CON خدمات اکو نوژین\n1. تحلیل خاک\n2. مشاوره کشت\n3. قیمت بازار\n4. آب و هوا\n5. سوال از کارشناس\n0. خروج",
        Language.AR: "CON خدمات إيكو نوجين\n1. تحليل التربة\n2. نصيحة المحاصيل\n3. أسعار السوق\n4. الطقس\n5. اسأل خبير\n0. خروج",
    },
    "invalid_input": {
        Language.EN: "END Invalid input. Please dial *384*73# again.",
        Language.FA: "END ورودی نامعتبر. لطفاً دوباره *384*73# را شماره‌گیری کنید.",
        Language.AR: "END إدخال غير صالح. يرجى الاتصال بـ *384*73# مرة أخرى.",
    },
    "goodbye": {
        Language.EN: "END Thank you for using Eco Nojin!",
        Language.FA: "END از استفاده از اکو نوژین متشکریم!",
        Language.AR: "END شكراً لاستخدام إيكو نوجين!",
    },
    # Soil analysis
    "soil_prompt_coords": {
        Language.EN: "CON Enter coordinates as: lat,lon\nExample: 36.8,54.4",
        Language.FA: "CON مختصات را وارد کنید: عرض،طول\nمثال: 36.8,54.4",
        Language.AR: "CON أدخل الإحداثيات: عرض،طول\nمثال: 36.8,54.4",
    },
    "soil_result_template": {
        Language.EN: "END Soil Analysis ({lat},{lon})\nNDVI: {ndvi}\nStatus: {status}\nAdvice: {advice}",
        Language.FA: "END تحلیل خاک ({lat},{lon})\nشاخص گیاهی: {ndvi}\nوضعیت: {status}\nتوصیه: {advice}",
        Language.AR: "END تحليل التربة ({lat},{lon})\nمؤشر الغطاء: {ndvi}\nالحالة: {status}\nنصيحة: {advice}",
    },
    # Crop advice
    "crop_prompt_region": {
        Language.EN: "CON Select region:\n1. North (Golestan)\n2. Central (Isfahan)\n3. South (Fars)\n4. West (Kurdistan)",
        Language.FA: "CON منطقه را انتخاب کنید:\n1. شمال (گلستان)\n2. مرکز (اصفهان)\n3. جنوب (فارس)\n4. غرب (کردستان)",
        Language.AR: "CON اختر المنطقة:\n1. الشمال (غلستان)\n2. الوسط (أصفهان)\n3. الجنوب (فارس)\n4. الغرب (كردستان)",
    },
    "crop_advice_template": {
        Language.EN: "END Crop advice for {region}:\nBest: {crops}\nPlanting: {season}\nWater: {water}",
        Language.FA: "END مشاوره کشت برای {region}:\nبهترین: {crops}\nزمان کاشت: {season}\nآب: {water}",
        Language.AR: "END نصيحة المحاصيل لـ {region}:\nالأفضل: {crops}\nالزراعة: {season}\nالماء: {water}",
    },
    # Market prices
    "market_prompt": {
        Language.EN: "CON Select product:\n1. Wheat\n2. Barley\n3. Saffron\n4. Pistachio\n5. Dates",
        Language.FA: "CON محصول را انتخاب کنید:\n1. گندم\n2. جو\n3. زعفران\n4. پسته\n5. خرما",
        Language.AR: "CON اختر المنتج:\n1. القمح\n2. الشعير\n3. الزعفران\n4. الفستق\n5. التمر",
    },
    "price_template": {
        Language.EN: "END {product} price:\n{price} USD/kg\nTrend: {trend}\nMarket: {market}",
        Language.FA: "END قیمت {product}:\n{price} دلار/کیلو\nروند: {trend}\nبازار: {market}",
        Language.AR: "END سعر {product}:\n{price} دولار/كجم\nالاتجاه: {trend}\nالسوق: {market}",
    },
    # Weather
    "weather_prompt": {
        Language.EN: "CON Select city:\n1. Tehran\n2. Mashhad\n3. Isfahan\n4. Shiraz\n5. Tabriz",
        Language.FA: "CON شهر را انتخاب کنید:\n1. تهران\n2. مشهد\n3. اصفهان\n4. شیراز\n5. تبریز",
        Language.AR: "CON اختر المدينة:\n1. طهران\n2. مشهد\n3. أصفهان\n4. شيراز\n5. تبريز",
    },
    "weather_template": {
        Language.EN: "END Weather {city}:\nTemp: {temp}°C\nRain: {rain}mm\nForecast: {forecast}",
        Language.FA: "END آب و هوای {city}:\nدما: {temp}°C\nباران: {rain}mm\nپیش‌بینی: {forecast}",
        Language.AR: "END الطقس {city}:\nالحرارة: {temp}°C\nالمطر: {rain}mm\nالتوقعات: {forecast}",
    },
    # AI question
    "ai_prompt": {
        Language.EN: "CON Type your question (max 100 chars):",
        Language.FA: "CON سوال خود را بنویسید (حداکثر 100 کاراکتر):",
        Language.AR: "CON اكتب سؤالك (100 حرف كحد أقصى):",
    },
    "ai_response_template": {
        Language.EN: "END Answer: {answer}",
        Language.FA: "END پاسخ: {answer}",
        Language.AR: "END الإجابة: {answer}",
    },
}


def get_message(key: str, lang: Language, **kwargs) -> str:
    """Get translated message with optional formatting."""
    template = MESSAGES.get(key, {}).get(lang, MESSAGES[key][Language.EN])
    if kwargs:
        return template.format(**kwargs)
    return template


# ============================================================================
# USSD MENU HANDLER
# ============================================================================
class UssdHandler:
    """Handles USSD menu flows."""

    def handle(self, request: UssdRequest) -> UssdResponse:
        """Route USSD request to appropriate handler based on text."""
        text = request.text.strip()
        lang = request.language

        # Main menu (first request or just service code)
        if text == "" or text == " ":
            return UssdResponse(text=get_message("main_menu", lang))

        parts = text.split("*")

        # Level 1: main menu selection
        if len(parts) == 1:
            choice = parts[0]
            if choice == "0":
                return UssdResponse(text=get_message("goodbye", lang), end_session=True)
            elif choice == "1":
                return UssdResponse(text=get_message("soil_prompt_coords", lang))
            elif choice == "2":
                return UssdResponse(text=get_message("crop_prompt_region", lang))
            elif choice == "3":
                return UssdResponse(text=get_message("market_prompt", lang))
            elif choice == "4":
                return UssdResponse(text=get_message("weather_prompt", lang))
            elif choice == "5":
                return UssdResponse(text=get_message("ai_prompt", lang))
            else:
                return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

        # Level 2: sub-menu input
        if len(parts) == 2:
            menu, input_val = parts[0], parts[1]

            if menu == "1":
                return self._handle_soil(input_val, lang)
            elif menu == "2":
                return self._handle_crop(input_val, lang)
            elif menu == "3":
                return self._handle_market(input_val, lang)
            elif menu == "4":
                return self._handle_weather(input_val, lang)
            elif menu == "5":
                return self._handle_ai(input_val, lang)

        return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

    def _handle_soil(self, coords_str: str, lang: Language) -> UssdResponse:
        """Process soil analysis request."""
        try:
            # Parse "lat,lon"
            parts = coords_str.split(",")
            if len(parts) != 2:
                raise ValueError("Invalid format")
            lat, lon = float(parts[0]), float(parts[1])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Out of range")
        except Exception:
            return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

        # In production, call Satellite API. For research, mock response.
        ndvi = 0.45 + (lat % 1) * 0.1
        if ndvi > 0.5:
            status = "Good" if lang == Language.EN else ("خوب" if lang == Language.FA else "جيد")
            advice = (
                "Maintain practices"
                if lang == Language.EN
                else ("روش‌ها را حفظ کنید" if lang == Language.FA else "حافظ على الممارسات")
            )
        else:
            status = (
                "Stressed"
                if lang == Language.EN
                else ("تحت تنش" if lang == Language.FA else "مجهد")
            )
            advice = (
                "Add compost"
                if lang == Language.EN
                else ("کمپوست اضافه کنید" if lang == Language.FA else "أضف السماد")
            )

        text = get_message(
            "soil_result_template",
            lang,
            lat=f"{lat:.2f}",
            lon=f"{lon:.2f}",
            ndvi=f"{ndvi:.2f}",
            status=status,
            advice=advice,
        )
        return UssdResponse(text=text, end_session=True)

    def _handle_crop(self, region_choice: str, lang: Language) -> UssdResponse:
        """Process crop advice request."""
        regions = {
            "1": {"name": "North/Golestan", "name_fa": "شمال/گلستان", "name_ar": "الشمال/غلستان"},
            "2": {"name": "Central/Isfahan", "name_fa": "مرکز/اصفهان", "name_ar": "الوسط/أصفهان"},
            "3": {"name": "South/Fars", "name_fa": "جنوب/فارس", "name_ar": "الجنوب/فارس"},
            "4": {"name": "West/Kurdistan", "name_fa": "غرب/کردستان", "name_ar": "الغرب/كردستان"},
        }

        if region_choice not in regions:
            return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

        region = regions[region_choice]
        region_name = region[f"name_{lang.value}"]

        # Mock crop data
        crops = {
            "1": {"en": "Rice, Wheat", "fa": "برنج، گندم", "ar": "الأرز، القمح"},
            "2": {"en": "Wheat, Saffron", "fa": "گندم، زعفران", "ar": "القمح، الزعفران"},
            "3": {"en": "Dates, Citrus", "fa": "خرما، مرکبات", "ar": "التمر، الحمضيات"},
            "4": {"en": "Grapes, Walnuts", "fa": "انگور، گردو", "ar": "العنب، الجوز"},
        }
        seasons = {
            "1": {"en": "Oct-Nov", "fa": "مهر-آبان", "ar": "أكتوبر-نوفمبر"},
            "2": {"en": "Nov-Dec", "fa": "آبان-آذر", "ar": "نوفمبر-ديسمبر"},
            "3": {"en": "Sep-Oct", "fa": "شهریور-مهر", "ar": "سبتمبر-أكتوبر"},
            "4": {"en": "Oct-Nov", "fa": "مهر-آبان", "ar": "أكتوبر-نوفمبر"},
        }
        water = {
            "1": {"en": "High", "fa": "زیاد", "ar": "عالي"},
            "2": {"en": "Medium", "fa": "متوسط", "ar": "متوسط"},
            "3": {"en": "Low", "fa": "کم", "ar": "منخفض"},
            "4": {"en": "Medium", "fa": "متوسط", "ar": "متوسط"},
        }

        text = get_message(
            "crop_advice_template",
            lang,
            region=region_name,
            crops=crops[region_choice][lang.value],
            season=seasons[region_choice][lang.value],
            water=water[region_choice][lang.value],
        )
        return UssdResponse(text=text, end_session=True)

    def _handle_market(self, product_choice: str, lang: Language) -> UssdResponse:
        """Process market price request."""
        products = {
            "1": {"name": {"en": "Wheat", "fa": "گندم", "ar": "القمح"}, "price": 0.35},
            "2": {"name": {"en": "Barley", "fa": "جو", "ar": "الشعير"}, "price": 0.28},
            "3": {"name": {"en": "Saffron", "fa": "زعفران", "ar": "الزعفران"}, "price": 850},
            "4": {"name": {"en": "Pistachio", "fa": "پسته", "ar": "الفستق"}, "price": 12},
            "5": {"name": {"en": "Dates", "fa": "خرما", "ar": "التمر"}, "price": 3.5},
        }

        if product_choice not in products:
            return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

        product = products[product_choice]
        product_name = product["name"][lang.value]

        # Mock trend data
        trends = {
            "1": {"en": "Stable", "fa": "پایدار", "ar": "مستقر"},
            "2": {"en": "Rising", "fa": "صعودی", "ar": "صاعد"},
            "3": {"en": "High", "fa": "بالا", "ar": "مرتفع"},
            "4": {"en": "Rising", "fa": "صعودی", "ar": "صاعد"},
            "5": {"en": "Stable", "fa": "پایدار", "ar": "مستقر"},
        }

        text = get_message(
            "price_template",
            lang,
            product=product_name,
            price=f"{product['price']:.2f}",
            trend=trends[product_choice][lang.value],
            market="Tehran"
            if lang == Language.EN
            else ("تهران" if lang == Language.FA else "طهران"),
        )
        return UssdResponse(text=text, end_session=True)

    def _handle_weather(self, city_choice: str, lang: Language) -> UssdResponse:
        """Process weather request."""
        cities = {
            "1": {"en": "Tehran", "fa": "تهران", "ar": "طهران"},
            "2": {"en": "Mashhad", "fa": "مشهد", "ar": "مشهد"},
            "3": {"en": "Isfahan", "fa": "اصفهان", "ar": "أصفهان"},
            "4": {"en": "Shiraz", "fa": "شیراز", "ar": "شيراز"},
            "5": {"en": "Tabriz", "fa": "تبریز", "ar": "تبريز"},
        }

        if city_choice not in cities:
            return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

        city_name = cities[city_choice][lang.value]

        # Mock weather data
        temps = {"1": 25, "2": 22, "3": 28, "4": 30, "5": 18}
        rains = {"1": 0, "2": 5, "3": 0, "4": 0, "5": 10}
        forecasts = {
            "1": {"en": "Sunny 3 days", "fa": "آفتابی 3 روز", "ar": "مشمس 3 أيام"},
            "2": {"en": "Rain tomorrow", "fa": "باران فردا", "ar": "مطر غداً"},
            "3": {"en": "Hot week", "fa": "هفته گرم", "ar": "أسبوع حار"},
            "4": {"en": "Clear skies", "fa": "آسمان صاف", "ar": "سماء صافية"},
            "5": {"en": "Cool & wet", "fa": "خنک و مرطوب", "ar": "بارد ورطب"},
        }

        text = get_message(
            "weather_template",
            lang,
            city=city_name,
            temp=temps[city_choice],
            rain=rains[city_choice],
            forecast=forecasts[city_choice][lang.value],
        )
        return UssdResponse(text=text, end_session=True)

    def _handle_ai(self, question: str, lang: Language) -> UssdResponse:
        """Process AI question (simplified)."""
        question = question.strip()
        if not question:
            return UssdResponse(text=get_message("invalid_input", lang), end_session=True)

        # In production, call AI assistant API
        # For research, return mock answer (truncated to 140 chars)
        mock_answers = {
            Language.EN: f"AI: {question[:30]}... Best practice is to consult local extension officer for detailed guidance.",
            Language.FA: f"هوش مصنوعی: {question[:30]}... بهترین روش مشورت با کارشناس محلی است.",
            Language.AR: f"AI: {question[:30]}... أفضل ممارسة استشارة المرشد المحلي.",
        }

        answer = mock_answers[lang][:140]
        text = get_message("ai_response_template", lang, answer=answer)
        return UssdResponse(text=text, end_session=True)


# Singleton
_handler: UssdHandler | None = None


def get_ussd_handler() -> UssdHandler:
    """Get singleton USSD handler."""
    global _handler
    if _handler is None:
        _handler = UssdHandler()
    return _handler
