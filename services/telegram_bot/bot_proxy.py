"""
Hydroma Telegram Bot with Proxy Support

For regions where api.telegram.org is blocked,
uses SOCKS5/HTTP proxy to connect.

Usage:
    Set environment variables:
      TELEGRAM_BOT_TOKEN=your_token
      TELEGRAM_PROXY=socks5://user:pass@host:port
      # OR
      TELEGRAM_PROXY=http://user:pass@host:port
"""
import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hydroma_bot_proxy")


def create_proxy_aiohttp_session():
    """Create aiohttp session with proxy support."""
    import aiohttp
    
    proxy_url = os.getenv("TELEGRAM_PROXY")
    
    if not proxy_url:
        logger.info("No proxy configured, using direct connection")
        return aiohttp.ClientSession()
    
    logger.info(f"Using proxy: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
    
    # SOCKS5 proxy
    if proxy_url.startswith("socks"):
        try:
            from aiohttp_socks import ProxyConnector
            connector = ProxyConnector.from_url(proxy_url)
            return aiohttp.ClientSession(connector=connector)
        except ImportError:
            logger.error("aiohttp_socks not installed. Run: pip install aiohttp-socks")
            raise
    
    # HTTP/HTTPS proxy
    elif proxy_url.startswith("http"):
        return aiohttp.ClientSession()
    
    else:
        raise ValueError(f"Unknown proxy type: {proxy_url}")


async def test_connection_with_proxy():
    """Test Telegram API with proxy."""
    from aiogram import Bot
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return False
    
    if token == "your_token_here":
        print("❌ TOKEN is placeholder! Get real token from @BotFather")
        return False
    
    proxy_url = os.getenv("TELEGRAM_PROXY")
    
    print(f"🔍 Testing connection...")
    print(f"   Token: {token[:15]}...")
    print(f"   Proxy: {proxy_url or 'None (direct)'}")
    
    try:
        # Create session with proxy
        session = create_proxy_aiohttp_session()
        
        # Create bot with custom session
        bot = Bot(token=token, session=session)
        
        # Test getMe
        me = await bot.get_me()
        
        print(f"\n✅ SUCCESS! Bot info:")
        print(f"   ID: {me.id}")
        print(f"   Username: @{me.username}")
        print(f"   Name: {me.first_name}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}: {e}")
        print(f"\n💡 Solutions:")
        print(f"   1. Check if proxy is running and accessible")
        print(f"   2. Verify proxy credentials")
        print(f"   3. Try different proxy type (socks5 vs http)")
        print(f"   4. Use VPN instead of proxy")
        return False


if __name__ == "__main__":
    asyncio.run(test_connection_with_proxy())