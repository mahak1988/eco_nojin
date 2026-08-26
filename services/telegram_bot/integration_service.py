"""TelegramIntegrationService - advanced telegram bot features"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

class CommandType(str, Enum):
    START = "/start"
    HELP = "/help"
    ADVISOR = "/advisor"
    WEATHER = "/weather"
    CROP = "/crop"
    MARKET = "/market"
    REPORT = "/report"

@dataclass
class TelegramUser:
    user_id: int
    username: Optional[str] = None
    village_id: Optional[str] = None
    language: str = "fa"
    is_premium: bool = False
    registered_at: datetime = None

@dataclass
class TelegramMessage:
    message_id: int
    user: TelegramUser
    text: str
    command: Optional[CommandType] = None
    reply_to: Optional[int] = None

class TelegramIntegrationService:
    """
    سرویس یکپارچه ربات تلگرام
    
    قابلیت‌ها:
    - مدیریت دستورات (/advisor, /weather, /crop)
    - یکپارچه‌سازی با scientific_motors
    - ارسال اعلان‌ها
    - مدیریت کاربران
    - گزارش‌گیری از تعاملات
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """ثبت handler های پیش‌فرض"""
        self._handlers[CommandType.START] = self._handle_start
        self._handlers[CommandType.HELP] = self._handle_help
        self._handlers[CommandType.ADVISOR] = self._handle_advisor
        self._handlers[CommandType.WEATHER] = self._handle_weather
        self._handlers[CommandType.CROP] = self._handle_crop
        self._handlers[CommandType.MARKET] = self._handle_market
    
    async def process_message(self, message: TelegramMessage) -> str:
        """پردازش پیام ورودی"""
        # تشخیص دستور
        if message.text.startswith('/'):
            cmd_str = message.text.split()[0].split('@')[0]
            try:
                command = CommandType(cmd_str)
                handler = self._handlers.get(command)
                if handler:
                    return await handler(message)
            except ValueError:
                pass
        
        # پیام عادی - استفاده از AI advisor
        return await self._handle_free_text(message)
    
    async def _handle_start(self, message: TelegramMessage) -> str:
        return (
            f"سلام {message.user.username or 'کاربر'}! 👋\n\n"
            "به ربات Eco Nojin خوش آمدید.\n\n"
            "دستورات موجود:\n"
            "/advisor - مشاوره کشاورزی\n"
            "/weather - وضعیت آب و هوا\n"
            "/crop - توصیه کشت\n"
            "/market - قیمت بازار\n"
            "/help - راهنما"
        )
    
    async def _handle_help(self, message: TelegramMessage) -> str:
        return (
            "📚 راهنمای ربات Eco Nojin\n\n"
            "این ربات به شما در موارد زیر کمک می‌کند:\n"
            "• مشاوره کشاورزی هوشمند\n"
            "• پایش ماهواره‌ای زمین\n"
            "• پیش‌بینی آب و هوا\n"
            "• توصیه‌های کاشت و داشت\n"
            "• اطلاعات بازار محلی"
        )
    
    async def _handle_advisor(self, message: TelegramMessage) -> str:
        """مشاوره کشاورزی"""
        try:
            from services.bots.unified_service import UnifiedBotService
            bot_service = UnifiedBotService(self.db)
            question = ' '.join(message.text.split()[1:]) or "وضعیت زمین من چطور است؟"
            advice = await bot_service.get_advice(question, message.user.village_id)
            return f"🌾 مشاوره کشاورزی:\n\n{advice}"
        except Exception as e:
            return f"⚠️  خطا در دریافت مشاوره: {e}"
    
    async def _handle_weather(self, message: TelegramMessage) -> str:
        """وضعیت آب و هوا"""
        try:
            from engine.hydroma.climate import et_calculator
            # شبیه‌سازی
            return (
                "🌤 وضعیت آب و هوای منطقه:\n\n"
                "• دما: ۲۸ درجه سانتی‌گراد\n"
                "• رطوبت: ۴۵٪\n"
                "• باد: ۱۲ km/h\n"
                "• پیش‌بینی فردا: آفتابی ☀️"
            )
        except Exception:
            return "⚠️  سرویس آب و هوا در دسترس نیست"
    
    async def _handle_crop(self, message: TelegramMessage) -> str:
        """توصیه کشت"""
        return (
            "🌱 توصیه کشت فصل جاری:\n\n"
            "بر اساس شرایط اقلیمی و خاک منطقه شما:\n"
            "• گندم (پاییز)\n"
            "• جو (پاییز)\n"
            "• سبزیجات بهاره\n\n"
            "برای توصیه دقیق‌تر، اطلاعات زمین خود را ثبت کنید."
        )
    
    async def _handle_market(self, message: TelegramMessage) -> str:
        """قیمت بازار"""
        try:
            from services.marketplace.service import MarketplaceService
            # شبیه‌سازی
            return (
                "💰 قیمت محصولات در بازار محلی:\n\n"
                "• گندم: ۱۵,۰۰۰ تومان/کیلو\n"
                "• جو: ۱۲,۰۰۰ تومان/کیلو\n"
                "• زعفران: ۴۵,۰۰۰,۰۰۰ تومان/کیلو\n"
                "• پسته: ۸۵۰,۰۰۰ تومان/کیلو"
            )
        except Exception:
            return "⚠️  اطلاعات بازار در دسترس نیست"
    
    async def _handle_free_text(self, message: TelegramMessage) -> str:
        """پردازش متن آزاد با AI"""
        try:
            from services.bots.unified_service import UnifiedBotService
            bot_service = UnifiedBotService(self.db)
            advice = await bot_service.get_advice(message.text, message.user.village_id)
            return advice
        except Exception:
            return "متوجه نشدم. لطفاً از /help برای دیدن دستورات استفاده کنید."
    
    async def send_notification(
        self, user_id: int, message: str, priority: str = "normal",
    ) -> bool:
        """ارسال اعلان به کاربر"""
        # در production: استفاده از Telegram Bot API
        print(f"[Telegram] To {user_id}: {message[:50]}...")
        return True
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """آمار تعاملات کاربر"""
        return {
            "user_id": user_id,
            "total_messages": 42,
            "commands_used": 15,
            "last_active": datetime.now(timezone.utc).isoformat(),
        }
    