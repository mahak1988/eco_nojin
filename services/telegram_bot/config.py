"""Bot configuration from environment variables."""
import structlog

logger = structlog.get_logger()
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class BotConfig:
    """Telegram bot configuration."""

    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_BASE_URL: str = os.getenv("BOT_API_BASE_URL", "http://os.environ.get('HOST', '127.0.0.1'):8000")

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = int(os.getenv("BOT_RATE_LIMIT", "10"))

    # Timeouts
    REQUEST_TIMEOUT: float = float(os.getenv("BOT_REQUEST_TIMEOUT", "60.0"))

    # Logging
    LOG_LEVEL: str = os.getenv("BOT_LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            logger.error("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
            logger.info("Get one from @BotFather on Telegram")
            return False
        return True


config = BotConfig()
