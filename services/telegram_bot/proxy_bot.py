"""
Hydroma Telegram Bot - Proxy-aware version for Iran deployment.

This version automatically detects and uses local proxies:
- v2rayN (socks5://os.environ.get('HOST', '127.0.0.1'):10808)
- Clash (socks5://os.environ.get('HOST', '127.0.0.1'):7891)
- Hiddify (socks5://os.environ.get('HOST', '127.0.0.1'):2080)
- Any custom proxy via TELEGRAM_PROXY env var

Usage:
    1. Start your VPN (v2rayN, Clash, etc.)
    2. Run: python -m services.telegram_bot.proxy_bot
"""
import asyncio
import logging
import os
import socket

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("proxy_bot")


# =====================================================================
# Proxy Detection
# =====================================================================

PROXY_CANDIDATES = [
    # (name, protocol, host, port)
    ("v2rayN", "socks5", "os.environ.get('HOST', '127.0.0.1')", 10808),
    ("v2rayN-HTTP", "http", "os.environ.get('HOST', '127.0.0.1')", 10809),
    ("Clash", "socks5", "os.environ.get('HOST', '127.0.0.1')", 7891),
    ("Clash-HTTP", "http", "os.environ.get('HOST', '127.0.0.1')", 7890),
    ("Hiddify", "socks5", "os.environ.get('HOST', '127.0.0.1')", 2080),
    ("Oblivion", "socks5", "os.environ.get('HOST', '127.0.0.1')", 8086),
    ("Shadowsocks", "socks5", "os.environ.get('HOST', '127.0.0.1')", 1080),
    ("Tor", "socks5", "os.environ.get('HOST', '127.0.0.1')", 9050),
]


def check_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a port is open."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def detect_active_proxy() -> str | None:
    """Auto-detect running local proxy."""
    # First check environment variable
    env_proxy = os.getenv("TELEGRAM_PROXY")
    if env_proxy:
        logger.info(f"Using proxy from env: {env_proxy}")
        return env_proxy

    # Then scan local proxies
    for name, proto, host, port in PROXY_CANDIDATES:
        if check_port(host, port):
            proxy_url = f"{proto}://{host}:{port}"
            logger.info(f"✅ Detected active proxy: {name} → {proxy_url}")
            return proxy_url

    return None


# =====================================================================
# Main Bot Function
# =====================================================================

async def main():
    """Run Telegram bot with proxy support."""

    # 1. Load token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "YOUR_REAL_TOKEN_HERE":
        logger.error("❌ TELEGRAM_BOT_TOKEN not set in .env")
        logger.error("   1. Get token from @BotFather on Telegram")
        logger.error("   2. Add to .env: TELEGRAM_BOT_TOKEN=your_token")
        return

    # 2. Detect proxy
    proxy_url = detect_active_proxy()

    if not proxy_url:
        logger.warning("⚠️  No active proxy detected!")
        logger.warning("   Please start your VPN (v2rayN, Clash, etc.)")
        logger.warning("   Or set TELEGRAM_PROXY in .env")
        logger.warning("")
        logger.warning("Trying direct connection (will likely fail in Iran)...")
    else:
        logger.info(f"🌐 Using proxy: {proxy_url}")

    # 3. Create bot with proxy
    try:
        from aiogram import Bot, Dispatcher
        from aiogram.client.session.aiohttp import AiohttpSession
        from aiogram.types import BotCommand
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("   Run: pip install aiogram python-dotenv aiohttp-socks")
        return

    # Create session with proxy
    if proxy_url:
        if proxy_url.startswith("socks"):
            try:
                from aiohttp_socks import ProxyConnector
                connector = ProxyConnector.from_url(proxy_url)
                session = AiohttpSession()
                # Patch the connector
                session._connector = connector
            except ImportError:
                logger.error("❌ aiohttp-socks not installed")
                logger.error("   Run: pip install aiohttp-socks")
                return
        else:
            session = AiohttpSession()
    else:
        session = AiohttpSession()

    # 4. Create bot
    bot = Bot(token=token, session=session)
    dp = Dispatcher()

    # 5. Import integration
    try:
        from .integration import get_bot_integration
        integration = get_bot_integration()
        logger.info("✅ Scientific motors loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load motors: {e}")
        return

    # 6. Setup handlers
    @dp.message(lambda m: m.text and m.text.startswith("/start"))
    async def cmd_start(message):
        await message.answer(
            "🌱 به اکو نوژین خوش آمدید!\n\n"
            "دستورات:\n"
            "/analyze lat lon area - تحلیل کامل\n"
            "/help - راهنما"
        )

    @dp.message(lambda m: m.text and m.text.startswith("/analyze"))
    async def cmd_analyze(message):
        """Handle /analyze lat lon area command."""
        try:
            parts = message.text.split()
            if len(parts) < 4:
                await message.answer(
                    "❌ فرمت صحیح:\n/analyze 35.0 51.0 50"
                )
                return

            lat, lon, area = float(parts[1]), float(parts[2]), float(parts[3])

            # Validate
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                await message.answer("❌ مختصات نامعتبر")
                return

            status_msg = await message.answer("🔬 در حال تحلیل... (۱۰-۳۰ ثانیه)")

            results = await integration.analyze_land(
                latitude=lat,
                longitude=lon,
                area_ha=area,
                crop_id="wheat",
                lang="fa",
            )

            # Format response
            sat = results.get("satellite", {})
            crops = results.get("crops", {})
            carbon = results.get("carbon", {})

            response = (
                f"✅ تحلیل کامل شد!\n\n"
                f"📍 {lat:.4f}, {lon:.4f} ({area} ha)\n\n"
                f"🛰️ Satellite:\n"
                f"   • Vegetation: {sat.get('vegetation_health', 'N/A')}\n"
                f"   • Biomass: {sat.get('biomass_t_ha', 0):.1f} t/ha\n"
                f"   • Soil moisture: {sat.get('soil_moisture', 0):.2f}\n\n"
                f"🌾 Crops: {', '.join(crops.get('recommended', []))}\n\n"
                f"🌱 Carbon:\n"
                f"   • Annual: {carbon.get('annual_tCO2e_ha', 0):.2f} tCO2e/ha\n"
                f"   • Total: {carbon.get('total_tCO2e', 0):.0f} tCO2e\n"
                f"   • Value: ${carbon.get('total_value_usd', 0):,.0f}\n"
            )

            await status_msg.edit_text(response)

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            await message.answer(f"❌ خطا: {str(e)[:100]}")

    @dp.message(lambda m: m.text and m.text.startswith("/help"))
    async def cmd_help(message):
        await message.answer(
            "📚 راهنما:\n\n"
            "/start - خوش‌آمد\n"
            "/analyze lat lon area - تحلیل زمین\n"
            "   مثال: /analyze 35.0 51.0 50\n"
            "/help - این راهنما"
        )

    # 7. Set bot commands
    await bot.set_my_commands([
        BotCommand(command="start", description="شروع"),
        BotCommand(command="analyze", description="تحلیل زمین"),
        BotCommand(command="help", description="راهنما"),
    ])

    # 8. Test connection
    logger.info("🔍 Testing Telegram API connection...")
    try:
        me = await bot.get_me()
        logger.info(f"✅ Connected! Bot: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("")
        logger.error("💡 Solutions:")
        logger.error("   1. Make sure VPN is running (v2rayN, Clash, etc.)")
        logger.error("   2. Check proxy port is open")
        logger.error("   3. Try setting TELEGRAM_PROXY in .env")
        await bot.session.close()
        return

    # 9. Start polling
    logger.info("🚀 Bot started! Press Ctrl+C to stop")
    logger.info(f"📱 Find your bot on Telegram: @{me.username}")
    logger.info("")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
