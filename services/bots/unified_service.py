"""Unified BotService - orchestrates all bot platforms"""
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class BotPlatform(str, Enum):
    BALE = "bale"
    RUBIKA = "rubika"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    DOCUMENT = "document"

@dataclass
class BotMessage:
    platform: BotPlatform
    chat_id: str
    message_type: MessageType
    content: str
    metadata: dict[str, Any] | None = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)

@dataclass
class BotResponse:
    success: bool
    message_id: str | None = None
    error: str | None = None

class UnifiedBotService:
    """
    سرویس یکپارچه برای مدیریت تمام پلتفرم‌های bot
    
    قابلیت‌ها:
    - ارسال پیام به چندین پلتفرم
    - مدیریت صف پیام‌ها
    - ثبت لاگ پیام‌ها
    - یکپارچه‌سازی با AdviceService (AI)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._adapters = {}

    async def register_adapter(self, platform: BotPlatform, adapter):
        """ثبت adapter برای یک پلتفرم"""
        self._adapters[platform] = adapter
        return True

    async def send_message(self, message: BotMessage) -> BotResponse:
        """ارسال پیام از طریق پلتفرم مشخص"""
        adapter = self._adapters.get(message.platform)
        if not adapter:
            return BotResponse(success=False, error=f"No adapter for {message.platform}")

        try:
            # Log message to database
            await self._log_message(message)

            # Send via adapter
            if hasattr(adapter, 'send_message'):
                result = await adapter.send_message(
                    chat_id=message.chat_id,
                    content=message.content,
                    msg_type=message.message_type.value,
                )
                return BotResponse(success=True, message_id=str(result))
            else:
                return BotResponse(success=False, error="Adapter has no send_message")
        except Exception as e:
            return BotResponse(success=False, error=str(e))

    async def broadcast(
        self, message: BotMessage, platforms: list[BotPlatform] | None = None
    ) -> dict[BotPlatform, BotResponse]:
        """ارسال پیام به چندین پلتفرم"""
        target_platforms = platforms or list(self._adapters.keys())
        results = {}

        for platform in target_platforms:
            platform_msg = BotMessage(
                platform=platform,
                chat_id=message.chat_id,
                message_type=message.message_type,
                content=message.content,
                metadata=message.metadata,
            )
            results[platform] = await self.send_message(platform_msg)

        return results

    async def _log_message(self, message: BotMessage):
        """ثبت لاگ پیام در دیتابیس"""
        try:
            # ساده‌سازی: فقط log در console
            # در production باید جدول bot_message_logs داشته باشیم
            print(f"[BotLog] {message.platform.value}: {message.content[:50]}...")
        except Exception:
            pass

    async def get_advice(self, question: str, village_id: str | None = None) -> str:
        """دریافت مشاوره از AI"""
        try:
            from services.bots.core.ai import AdviceService
            advice_service = AdviceService(self.db)
            return await advice_service.get_advice(question, village_id)
        except Exception as e:
            return f"AI service unavailable: {e}"
