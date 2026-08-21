"""Tests for USSD/SMS Gateway."""

from fastapi.testclient import TestClient

from engine.hydroma.ussd.engine import Language, UssdRequest, get_ussd_handler
from engine.hydroma.ussd.sms_parser import SmsCommandType, SmsParser, get_sms_parser
from services.api_gateway.main import app

client = TestClient(app)


class TestUssdEngine:
    """Test USSD menu flows."""

    def test_main_menu_shown_on_first_request(self):
        """Verify main menu is shown on first USSD request."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-1",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="",
            language=Language.EN,
        )
        response = handler.handle(request)

        assert not response.end_session
        assert "Eco Nojin Services" in response.text
        assert "1. Soil Analysis" in response.text

    def test_main_menu_fa_language(self):
        """Verify Persian menu works."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-2",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="",
            language=Language.FA,
        )
        response = handler.handle(request)

        assert "خدمات اکو نوژین" in response.text
        assert "تحلیل خاک" in response.text

    def test_main_menu_ar_language(self):
        """Verify Arabic menu works."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-3",
            service_code="*384*73#",
            phone_number="+966501234567",
            text="",
            language=Language.AR,
        )
        response = handler.handle(request)

        assert "خدمات إيكو نوجين" in response.text

    def test_exit_option(self):
        """Verify exit option ends session."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-4",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="0",
            language=Language.EN,
        )
        response = handler.handle(request)

        assert response.end_session
        assert "Thank you" in response.text

    def test_soil_analysis_flow(self):
        """Verify complete soil analysis flow."""
        handler = get_ussd_handler()

        # Step 1: Select soil analysis
        request1 = UssdRequest(
            session_id="test-5",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="1",
            language=Language.EN,
        )
        response1 = handler.handle(request1)
        assert not response1.end_session
        assert "coordinates" in response1.text.lower()

        # Step 2: Provide coordinates
        request2 = UssdRequest(
            session_id="test-5",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="1*36.8,54.4",
            language=Language.EN,
        )
        response2 = handler.handle(request2)
        assert response2.end_session
        assert "36.80" in response2.text
        assert "54.40" in response2.text

    def test_invalid_input_handling(self):
        """Verify invalid input is handled gracefully."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-6",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="9",  # Invalid option
            language=Language.EN,
        )
        response = handler.handle(request)

        assert response.end_session
        assert "Invalid" in response.text

    def test_invalid_coordinates_rejected(self):
        """Verify invalid coordinates are rejected."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-7",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="1*999,999",  # Invalid
            language=Language.EN,
        )
        response = handler.handle(request)

        assert response.end_session
        assert "Invalid" in response.text

    def test_market_price_flow(self):
        """Verify market price flow."""
        handler = get_ussd_handler()
        request = UssdRequest(
            session_id="test-8",
            service_code="*384*73#",
            phone_number="+989123456789",
            text="3*1",  # Market -> Wheat
            language=Language.EN,
        )
        response = handler.handle(request)

        assert response.end_session
        assert "Wheat" in response.text
        assert "0.35" in response.text


class TestSmsParser:
    """Test SMS command parsing."""

    def test_parse_soil_command(self):
        """Verify SOIL command parsing."""
        parser = get_sms_parser()
        result = parser.parse("SOIL 36.8 54.4")

        assert result["type"] == SmsCommandType.SOIL
        assert "36.8 54.4" in result["args"]

    def test_parse_help_command(self):
        """Verify HELP command."""
        parser = get_sms_parser()
        result = parser.parse("HELP")

        assert result["type"] == SmsCommandType.HELP

    def test_process_soil_command(self):
        """Verify SOIL command processing."""
        parser = get_sms_parser()
        response = parser.process("+989123456789", "SOIL 36.8 54.4")

        assert "36.80" in response
        assert "54.40" in response
        assert "NDVI" in response

    def test_process_price_command(self):
        """Verify PRICE command."""
        parser = get_sms_parser()
        response = parser.process("+989123456789", "PRICE wheat")

        assert "wheat" in response.lower()
        assert "0.35" in response

    def test_process_weather_command(self):
        """Verify WEATHER command."""
        parser = get_sms_parser()
        response = parser.process("+989123456789", "WEATHER tehran")

        assert "tehran" in response.lower()
        assert "25" in response

    def test_process_ask_command(self):
        """Verify ASK command."""
        parser = get_sms_parser()
        response = parser.process("+989123456789", "ASK how to make compost")

        assert len(response) <= 140  # SMS length limit

    def test_language_switch(self):
        """Verify LANG command changes user language."""
        parser = SmsParser()
        response = parser.process("+989123456789", "LANG fa")

        assert "فارسی" in response

        # Subsequent HELP should be in Persian
        help_response = parser.process("+989123456789", "HELP")
        assert "دستورات" in help_response

    def test_unknown_command(self):
        """Verify unknown commands are handled."""
        parser = get_sms_parser()
        response = parser.process("+989123456789", "XYZFOO")

        assert "Unknown" in response or "HELP" in response


class TestUssdApiEndpoints:
    """Test USSD API endpoints."""

    def test_ussd_endpoint(self):
        """Verify USSD endpoint works."""
        response = client.post(
            "/api/v1/ussd/ussd",
            json={
                "session_id": "test-api-1",
                "service_code": "*384*73#",
                "phone_number": "+989123456789",
                "text": "",
                "language": "en",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "Eco Nojin Services" in data["text"]
        assert data["end_session"] is False

    def test_sms_endpoint(self):
        """Verify SMS endpoint works."""
        response = client.post(
            "/api/v1/ussd/sms",
            json={
                "phone_number": "+989123456789",
                "message": "PRICE wheat",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "wheat" in data["response"].lower()
        assert data["char_count"] <= 160

    def test_ussd_health_endpoint(self):
        """Verify USSD health endpoint."""
        response = client.get("/api/v1/ussd/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "ussd_code" in data
        assert data["ussd_code"] == "*384*73#"

    def test_menu_preview_endpoint(self):
        """Verify menu preview endpoint."""
        response = client.get("/api/v1/ussd/menu/preview?language=fa")

        assert response.status_code == 200
        data = response.json()
        assert "خدمات اکو نوژین" in data["menu_text"]

    def test_health_reports_inclusive_access(self):
        """Verify main health endpoint reports inclusive access."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "inclusive_access" in data
        assert data["inclusive_access"]["ussd_feature_phone"] is True
        assert data["inclusive_access"]["sms_commands"] is True
