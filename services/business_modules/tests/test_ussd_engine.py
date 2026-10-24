"""Tests for the USSD/SMS gateway engine."""

import pytest

from services.business_modules.ussd.engine import (
    MESSAGES,
    GatewayType,
    Language,
    UssdHandler,
    UssdRequest,
    UssdResponse,
    get_ussd_handler,
)


class TestUssdResponse:
    """Tests for the response formatting."""

    def test_continuation_uses_con(self):
        response = UssdResponse(text="Choose one", end_session=False)
        assert response.to_africastalking_format() == "CON Choose one"

    def test_termination_uses_end(self):
        response = UssdResponse(text="Bye", end_session=True)
        assert response.to_africastalking_format() == "END Bye"

    def test_a_fresh_response_continues_the_session(self):
        assert UssdResponse(text="x").end_session is False


class TestTranslations:
    """Tests for the translation table."""

    def test_every_message_has_all_three_languages(self):
        for key, translations in MESSAGES.items():
            assert set(translations) == {Language.EN, Language.FA, Language.AR}, key

    def test_no_translation_is_empty(self):
        for key, translations in MESSAGES.items():
            for lang, text in translations.items():
                assert text, f"{key}/{lang}"

    def test_the_sms_limit_is_respected(self):
        """A feature-phone SMS carries at most 160 characters."""
        for key, translations in MESSAGES.items():
            for lang, text in translations.items():
                assert len(text) <= 160, f"{key}/{lang} is {len(text)} chars"


class TestUssdRequest:
    """Tests for the request dataclass."""

    def test_the_default_gateway_is_ussd(self):
        request = UssdRequest(
            session_id="s1", service_code="*384#", phone_number="+100", text=""
        )
        assert request.gateway == GatewayType.USSD

    def test_the_default_language_is_english(self):
        request = UssdRequest(
            session_id="s1", service_code="*384#", phone_number="+100", text=""
        )
        assert request.language == Language.EN


class TestUssdHandler:
    """Tests for the menu engine."""

    @pytest.fixture
    def engine(self):
        return UssdHandler()

    def test_the_factory_returns_a_handler(self):
        assert isinstance(get_ussd_handler(), UssdHandler)

    def _request(self, text: str, language: Language = Language.EN) -> UssdRequest:
        return UssdRequest(
            session_id="s1",
            service_code="*384#",
            phone_number="+100",
            text=text,
            language=language,
        )

    def test_the_first_request_returns_the_main_menu(self, engine):
        response = engine.handle(self._request(""))
        assert response.text
        assert not response.end_session

    def test_the_main_menu_lists_the_services(self, engine):
        response = engine.handle(self._request(""))
        assert "1." in response.text
        assert "2." in response.text

    def test_the_main_menu_is_localised(self, engine):
        english = engine.handle(self._request("", Language.EN)).text
        persian = engine.handle(self._request("", Language.FA)).text
        assert english != persian

    def test_option_zero_exits_the_session(self, engine):
        response = engine.handle(self._request("0"))
        assert response.end_session is True

    def test_an_unknown_option_ends_the_session(self, engine):
        """An invalid choice must not leave the user in a dead session."""
        response = engine.handle(self._request("99"))
        assert response.end_session is True
        assert response.text

    def test_a_menu_choice_continues_the_session(self, engine):
        for choice in ("1", "2", "3", "4", "5"):
            response = engine.handle(self._request(choice))
            assert response.end_session is False, choice
            assert response.text

    def test_a_submenu_input_is_handled(self, engine):
        response = engine.handle(self._request("1*35.7,51.4"))
        assert response.text

    def test_an_unknown_submenu_ends_the_session(self, engine):
        response = engine.handle(self._request("9*1"))
        assert response.end_session is True

    def test_the_response_is_formattable_for_the_gateway(self, engine):
        response = engine.handle(self._request("1"))
        formatted = response.to_africastalking_format()
        assert formatted.startswith("CON ")
