"""Integration tests for Bots"""
import pytest

from services.bots.unified_service import (
    BotMessage,
    BotPlatform,
    MessageType,
    UnifiedBotService,
)


@pytest.mark.asyncio
class TestBotsIntegration:
    async def test_unified_service_creation(self, db_session):
        service = UnifiedBotService(db_session)
        assert service is not None

    async def test_message_creation(self):
        msg = BotMessage(
            platform=BotPlatform.TELEGRAM,
            chat_id="test_123",
            message_type=MessageType.TEXT,
            content="Hello World",
        )
        assert msg.platform == BotPlatform.TELEGRAM
        assert msg.timestamp is not None

    async def test_send_without_adapter(self, db_session):
        service = UnifiedBotService(db_session)
        msg = BotMessage(
            platform=BotPlatform.BALE,
            chat_id="test",
            message_type=MessageType.TEXT,
            content="test",
        )
        result = await service.send_message(msg)
        assert not result.success
        assert "No adapter" in result.error
