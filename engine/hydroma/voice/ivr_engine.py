"""IVR (Interactive Voice Response) engine.

Provides voice menu navigation for low-literacy users.
Similar to USSD but with voice prompts and DTMF input.
"""

from dataclasses import dataclass
from enum import Enum

from .tts_provider import VoiceLanguage, get_tts_provider


class IVRState(Enum):
    """IVR menu states."""

    MAIN_MENU = "main_menu"
    SOIL_ANALYSIS = "soil_analysis"
    CROP_ADVICE = "crop_advice"
    MARKET_PRICES = "market_prices"
    WEATHER = "weather"
    ASK_EXPERT = "ask_expert"
    GOODBYE = "goodbye"


@dataclass
class IVRResponse:
    """Response from IVR system."""

    prompt_text: str
    prompt_audio: bytes | None = None
    state: IVRState = IVRState.MAIN_MENU
    end_call: bool = False
    valid_inputs: list = None

    def __post_init__(self):
        if self.valid_inputs is None:
            self.valid_inputs = []


@dataclass
class IVRSession:
    """Active IVR session."""

    session_id: str
    phone_number: str
    language: VoiceLanguage = VoiceLanguage.EN
    state: IVRState = IVRState.MAIN_MENU
    input_history: list = None

    def __post_init__(self):
        if self.input_history is None:
            self.input_history = []


# IVR menu prompts in multiple languages
IVR_PROMPTS = {
    "main_menu": {
        VoiceLanguage.EN: (
            "Welcome to Eco Nojin. "
            "Press 1 for soil analysis. "
            "Press 2 for crop advice. "
            "Press 3 for market prices. "
            "Press 4 for weather. "
            "Press 5 to ask an expert. "
            "Press 0 to exit."
        ),
        VoiceLanguage.FA: (
            "به اکو نوژین خوش آمدید. "
            "برای تحلیل خاک عدد ۱ را فشار دهید. "
            "برای مشاوره کشت عدد ۲ را فشار دهید. "
            "برای قیمت بازار عدد ۳ را فشار دهید. "
            "برای آب و هوا عدد ۴ را فشار دهید. "
            "برای سوال از کارشناس عدد ۵ را فشار دهید. "
            "برای خروج عدد ۰ را فشار دهید."
        ),
        VoiceLanguage.AR: (
            "مرحباً بكم في إيكو نوجين. "
            "اضغط 1 لتحليل التربة. "
            "اضغط 2 لنصيحة المحاصيل. "
            "اضغط 3 لأسعار السوق. "
            "اضغط 4 للطقس. "
            "اضغط 5 لسؤال خبير. "
            "اضغط 0 للخروج."
        ),
    },
    "soil_analysis": {
        VoiceLanguage.EN: "Please say the coordinates of your field, for example: 36.8, 54.4",
        VoiceLanguage.FA: "لطفاً مختصات مزرعه خود را بگویید، مثلاً: ۳۶.۸، ۵۴.۴",
        VoiceLanguage.AR: "يرجى قول إحداثيات حقلك، على سبيل المثال: 36.8، 54.4",
    },
    "crop_advice": {
        VoiceLanguage.EN: "Please say your region: north, central, south, or west",
        VoiceLanguage.FA: "لطفاً منطقه خود را بگویید: شمال، مرکز، جنوب، یا غرب",
        VoiceLanguage.AR: "يرجى قول منطقتك: الشمال، الوسط، الجنوب، أو الغرب",
    },
    "market_prices": {
        VoiceLanguage.EN: "Please say the product name: wheat, barley, saffron, or dates",
        VoiceLanguage.FA: "لطفاً نام محصول را بگویید: گندم، جو، زعفران، یا خرما",
        VoiceLanguage.AR: "يرجى قول اسم المنتج: القمح، الشعير، الزعفران، أو التمر",
    },
    "weather": {
        VoiceLanguage.EN: "Please say your city name",
        VoiceLanguage.FA: "لطفاً نام شهر خود را بگویید",
        VoiceLanguage.AR: "يرجى قول اسم مدينتك",
    },
    "ask_expert": {
        VoiceLanguage.EN: "Please ask your question after the beep",
        VoiceLanguage.FA: "لطفاً سوال خود را بعد از بوق بپرسید",
        VoiceLanguage.AR: "يرجى طرح سؤالك بعد الصفارة",
    },
    "goodbye": {
        VoiceLanguage.EN: "Thank you for calling Eco Nojin. Goodbye!",
        VoiceLanguage.FA: "از تماس شما با اکو نوژین متشکریم. خداحافظ!",
        VoiceLanguage.AR: "شكراً لاتصالك بإيكو نوجين. مع السلامة!",
    },
}


class IVREngine:
    """IVR menu navigation engine."""

    def __init__(self):
        self.tts = get_tts_provider()

    def start_session(
        self, session_id: str, phone_number: str, language: VoiceLanguage = VoiceLanguage.EN
    ) -> IVRSession:
        """Start a new IVR session."""
        return IVRSession(
            session_id=session_id,
            phone_number=phone_number,
            language=language,
            state=IVRState.MAIN_MENU,
        )

    def get_prompt(self, session: IVRSession) -> IVRResponse:
        """Get the prompt for current state."""
        state_key = session.state.value
        prompt_text = IVR_PROMPTS.get(state_key, {}).get(
            session.language, IVR_PROMPTS[state_key][VoiceLanguage.EN]
        )

        # Generate TTS audio (mock)
        tts_result = self.tts.synthesize(prompt_text, session.language)

        end_call = session.state == IVRState.GOODBYE

        return IVRResponse(
            prompt_text=prompt_text,
            prompt_audio=tts_result.audio_data,
            state=session.state,
            end_call=end_call,
        )

    def handle_dtmf(self, session: IVRSession, digit: str) -> IVRResponse:
        """Handle DTMF (phone keypad) input."""
        session.input_history.append(digit)

        if session.state == IVRState.MAIN_MENU:
            if digit == "0":
                session.state = IVRState.GOODBYE
            elif digit == "1":
                session.state = IVRState.SOIL_ANALYSIS
            elif digit == "2":
                session.state = IVRState.CROP_ADVICE
            elif digit == "3":
                session.state = IVRState.MARKET_PRICES
            elif digit == "4":
                session.state = IVRState.WEATHER
            elif digit == "5":
                session.state = IVRState.ASK_EXPERT
            else:
                # Invalid input, repeat main menu
                pass

        return self.get_prompt(session)

    def handle_voice_input(self, session: IVRSession, text: str) -> IVRResponse:
        """Handle voice input (after STT)."""
        session.input_history.append(text)

        # Mock response based on state
        response_text = f"Received: {text}"

        if session.state == IVRState.SOIL_ANALYSIS:
            response_text = f"Soil analysis for coordinates {text} is being processed."
        elif session.state == IVRState.CROP_ADVICE:
            response_text = f"Crop advice for region {text} is being prepared."
        elif session.state == IVRState.MARKET_PRICES:
            response_text = f"Market price for {text} is being fetched."
        elif session.state == IVRState.WEATHER:
            response_text = f"Weather for {text} is being fetched."
        elif session.state == IVRState.ASK_EXPERT:
            response_text = (
                f"Your question: {text}. Answer: Please consult local extension officer."
            )

        tts_result = self.tts.synthesize(response_text, session.language)

        return IVRResponse(
            prompt_text=response_text,
            prompt_audio=tts_result.audio_data,
            state=session.state,
            end_call=False,
        )

    def end_session(self, session: IVRSession) -> IVRResponse:
        """End the IVR session."""
        session.state = IVRState.GOODBYE
        return self.get_prompt(session)


# Singleton
_ivr_engine: IVREngine | None = None


def get_ivr_engine() -> IVREngine:
    """Get singleton IVR engine."""
    global _ivr_engine
    if _ivr_engine is None:
        _ivr_engine = IVREngine()
    return _ivr_engine
