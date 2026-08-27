"""Integration tests for Telegram Bot"""
import pytest

from services.telegram_bot.integration_service import (
    TelegramIntegrationService,
    TelegramMessage,
    TelegramUser,
)


@pytest.mark.asyncio
class TestTelegramIntegration:
    async def test_service_creation(self, db_session):
        """بررسی ایجاد service"""
        service = TelegramIntegrationService(db_session)
        assert service is not None
        assert hasattr(service, 'process_message')
        assert hasattr(service, 'send_notification')
        assert hasattr(service, 'get_user_stats')

    async def test_user_creation(self):
        """بررسی ایجاد TelegramUser با default values"""
        # تست با default values
        user = TelegramUser(user_id=123)
        assert user.user_id == 123
        assert user.username is None
        assert user.village_id is None
        assert user.language == "fa"
        assert user.is_premium is False

        # تست با تمام فیلدها
        user2 = TelegramUser(
            user_id=456,
            username="test_user",
            village_id="hejij",
            language="fa",
            is_premium=True,
        )
        assert user2.username == "test_user"
        assert user2.village_id == "hejij"

    async def test_message_creation(self):
        """بررسی ایجاد TelegramMessage"""
        user = TelegramUser(user_id=123, username="test_user", village_id="hejij")
        message = TelegramMessage(
            message_id=1,
            user=user,
            text="/start",
        )
        assert message.message_id == 1
        assert message.text == "/start"
        assert message.command is None
        assert message.reply_to is None

    async def test_start_command(self, db_session):
        """بررسی پردازش دستور /start"""
        service = TelegramIntegrationService(db_session)
        user = TelegramUser(user_id=123, username="test_user", village_id="hejij")
        message = TelegramMessage(message_id=1, user=user, text="/start")
        response = await service.process_message(message)
        assert response is not None
        assert len(response) > 0
        # باید شامل کلمه خوش‌آمدگویی باشد
        assert "خوش آمدید" in response or "سلام" in response or "Eco Nojin" in response

    async def test_help_command(self, db_session):
        """بررسی پردازش دستور /help"""
        service = TelegramIntegrationService(db_session)
        user = TelegramUser(user_id=123, username="test_user", village_id="hejij")
        message = TelegramMessage(message_id=2, user=user, text="/help")
        response = await service.process_message(message)
        assert response is not None
        assert "راهنما" in response or "/advisor" in response

    async def test_advisor_command(self, db_session):
        """بررسی پردازش دستور /advisor"""
        service = TelegramIntegrationService(db_session)
        user = TelegramUser(user_id=123, village_id="hejij")
        message = TelegramMessage(message_id=3, user=user, text="/advisor وضعیت زمین")
        response = await service.process_message(message)
        assert response is not None

    async def test_free_text(self, db_session):
        """بررسی پردازش متن آزاد"""
        service = TelegramIntegrationService(db_session)
        user = TelegramUser(user_id=123, village_id="hejij")
        message = TelegramMessage(message_id=4, user=user, text="سلام")
        response = await service.process_message(message)
        assert response is not None
        assert len(response) > 0

    async def test_user_stats(self, db_session):
        """بررسی دریافت آمار کاربر"""
        service = TelegramIntegrationService(db_session)
        stats = await service.get_user_stats(user_id=123)
        assert stats is not None
        assert "user_id" in stats
        assert stats["user_id"] == 123

    async def test_send_notification(self, db_session):
        """بررسی ارسال اعلان"""
        service = TelegramIntegrationService(db_session)
        success = await service.send_notification(
            user_id=123,
            message="Test notification",
            priority="normal",
        )
        assert success is True
