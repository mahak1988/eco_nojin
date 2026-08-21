"""
Hydroma Nojin Telegram Bot - Main bot logic.

Commands:
/start - Welcome message
/analyze lat lon area - Full land analysis
/crops lat lon - Crop recommendations
/calendar lat lon crop - Planting calendar
/carbon lat lon area - Carbon potential
/help - Command guide
"""
import asyncio
import logging
from typing import Optional

try:
    from aiogram import Bot, Dispatcher, F
    from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.filters import Command, CommandStart
    AIogram_AVAILABLE = True
except ImportError:
    AIogram_AVAILABLE = False
    print("  [BOT] aiogram not installed. Run: pip install aiogram")

from .i18n import t, detect_language
from .integration import get_bot_integration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hydroma_bot")


class HydromaTelegramBot:
    """Main Telegram Bot class."""

    def __init__(self, bot_token: str):
        if not AIogram_AVAILABLE:
            raise RuntimeError("aiogram not installed")
        
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher()
        self.integration = get_bot_integration()
        
        # User language storage (in production: use Redis/DB)
        self.user_languages = {}
        
        self._setup_handlers()

    def _setup_handlers(self):
        """Register command handlers."""
        
        @self.dp.message(CommandStart())
        async def cmd_start(message: Message):
            """Handle /start command."""
            lang = detect_language(message.text or "")
            self.user_languages[message.from_user.id] = lang
            
            await message.answer(t(lang, "welcome"))

        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            """Handle /help command."""
            lang = self.user_languages.get(message.from_user.id, "en")
            await message.answer(t(lang, "welcome"))

        @self.dp.message(Command("analyze"))
        async def cmd_analyze(message: Message):
            """Handle /analyze command - full land analysis."""
            lang = self.user_languages.get(message.from_user.id, "en")
            
            # Parse arguments
            try:
                parts = message.text.split()
                if len(parts) < 4:
                    await message.answer(t(lang, "analyze_usage"))
                    return
                
                latitude = float(parts[1])
                longitude = float(parts[2])
                area_ha = float(parts[3])
                crop_id = parts[4] if len(parts) > 4 else "wheat"
                
                # Validate coordinates
                if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                    await message.answer(t(lang, "invalid_coords"))
                    return
                
            except (ValueError, IndexError):
                await message.answer(t(lang, "invalid_coords"))
                return
            
            # Send "analyzing" message
            status_msg = await message.answer(t(lang, "analyzing"))
            
            try:
                # Run analysis
                results = await self.integration.analyze_land(
                    latitude=latitude,
                    longitude=longitude,
                    area_ha=area_ha,
                    crop_id=crop_id,
                    lang=lang,
                )
                
                # Format response
                response = self._format_analysis(results, lang)
                
                # Edit status message with results
                await status_msg.edit_text(response)
                
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                await status_msg.edit_text(t(lang, "error"))

        @self.dp.message(Command("crops"))
        async def cmd_crops(message: Message):
            """Handle /crops command."""
            lang = self.user_languages.get(message.from_user.id, "en")
            await message.answer(f"🌾 Crop recommendations coming soon!\n\nUse /analyze for full analysis.")

        @self.dp.message(Command("carbon"))
        async def cmd_carbon(message: Message):
            """Handle /carbon command."""
            lang = self.user_languages.get(message.from_user.id, "en")
            await message.answer(f"🌱 Carbon potential analysis coming soon!\n\nUse /analyze for full analysis.")

    def _format_analysis(self, results: dict, lang: str) -> str:
        """Format analysis results for Telegram message."""
        
        loc = results.get("location", {})
        sat = results.get("satellite", {})
        crops = results.get("crops", {})
        carbon = results.get("carbon", {})
        
        lines = [
            f"✅ {t(lang, 'analysis_complete')}",
            "",
            f"📍 {t(lang, 'location')}: {loc.get('lat', 0):.4f}, {loc.get('lon', 0):.4f}",
            f"📏 Area: {loc.get('area_ha', 0)} ha",
            "",
        ]
        
        # Satellite data
        if "error" not in sat:
            lines.extend([
                f"🛰️ Satellite Analysis:",
                f"   • Vegetation: {sat.get('vegetation_health', 'N/A')}",
                f"   • Biomass: {sat.get('biomass_t_ha', 0):.1f} t/ha",
                f"   • Soil moisture: {sat.get('soil_moisture', 0):.2f}",
                "",
            ])
        
        # Crops
        if "error" not in crops:
            lines.extend([
                f"🌾 {t(lang, 'best_crops')}:",
                f"   • {', '.join(crops.get('recommended', []))}",
                "",
            ])
        
        # Carbon
        if "error" not in carbon:
            lines.extend([
                f"🌱 {t(lang, 'carbon_potential')}:",
                f"   • Annual: {carbon.get('annual_tCO2e_ha', 0):.2f} tCO2e/ha/yr",
                f"   • Total: {carbon.get('total_tCO2e', 0):.0f} tCO2e",
                f"   • Value: ${carbon.get('total_value_usd', 0):,.0f}",
                f"   • Additionality: {carbon.get('additionality', 'N/A')}",
                "",
            ])
        
        lines.append(f"💡 {t(lang, 'recommendations')}:")
        lines.append("   • Consider no-till practices")
        lines.append("   • Add cover crops for soil health")
        lines.append("   • Monitor soil moisture weekly")
        
        return "\n".join(lines)

    async def start(self):
        """Start the bot."""
        logger.info("🚀 Starting Hydroma Telegram Bot...")
        
        # Set bot commands
        await self.bot.set_my_commands([
            ("start", "Welcome message"),
            ("help", "Command guide"),
            ("analyze", "Full land analysis"),
            ("crops", "Crop recommendations"),
            ("calendar", "Planting calendar"),
            ("carbon", "Carbon potential"),
            ("irrigate", "Irrigation schedule"),
            ("erosion", "Erosion risk"),
        ])
        
        logger.info("✅ Bot commands registered")
        
        # Start polling
        await self.dp.start_polling(self.bot)

    async def stop(self):
        """Stop the bot."""
        await self.bot.session.close()
        logger.info("👋 Bot stopped")


def main():
    """Entry point."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        print("\nPlease create a .env file with:")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("\nTo get a token:")
        print("  1. Message @BotFather on Telegram")
        print("  2. Send /newbot")
        print("  3. Follow instructions")
        print("  4. Copy the token to .env")
        return
    
    bot = HydromaTelegramBot(bot_token)
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")


if __name__ == "__main__":
    main()