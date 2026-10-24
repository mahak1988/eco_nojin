"""
Eco Nojin Telegram Bot - Main Entry Point.

Run with:
    python -m services.telegram_bot.main

``python-telegram-bot`` is an optional dependency (pyproject
``[project.optional-dependencies].telegram``). When it is not installed,
importing this module raises the typed
:class:`services.telegram_bot.handlers.TelegramDependencyMissing` with an
actionable message instead of a bare ``ModuleNotFoundError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:  # python-telegram-bot is an optional dependency (see below)
    from telegram.ext import Application

logger = structlog.get_logger()

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .config import config

# Imported through .handlers so the missing-dependency guard below is shared:
# handlers raises TelegramDependencyMissing when python-telegram-bot is absent.
from .handlers import (
    TelegramDependencyMissing,
    analyze_command,
    error_handler,
    health_command,
    help_command,
    landscapes_command,
    start_command,
    stats_command,
)

__all__ = [
    "TelegramDependencyMissing",
    "analyze_command",
    "error_handler",
    "health_command",
    "help_command",
    "landscapes_command",
    "main",
    "post_init",
    "setup_logging",
    "start_command",
    "stats_command",
]


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        level=getattr(logging, config.LOG_LEVEL),
        handlers=[
            logging.StreamHandler(),
        ],
    )
    # Suppress httpx logs (too verbose)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


async def post_init(application: Application) -> None:
    """Post-initialization hook."""
    logger = logging.getLogger("econojin.bot")
    logger.info("=" * 70)
    logger.info("ECO NOJIN TELEGRAM BOT STARTED")
    logger.info("=" * 70)
    logger.info(f"Bot username: @{application.bot.username}")
    logger.info(f"API Base URL: {config.API_BASE_URL}")
    logger.info(f"Rate limit: {config.MAX_REQUESTS_PER_MINUTE}/min")
    logger.info("=" * 70)
    logger.info("Ready to receive commands!")
    logger.info("")


def main():
    """Main entry point."""
    # Imported lazily: python-telegram-bot is an optional dependency and the
    # module-level import in this package fails with TelegramDependencyMissing
    # when it is absent.
    from telegram import Update
    from telegram.ext import Application, CommandHandler

    logger = logging.getLogger("econojin.bot")

    # Validate configuration
    if not config.validate():
        logger.info("\nPlease set TELEGRAM_BOT_TOKEN in your .env file.")
        logger.info("Get one from @BotFather on Telegram.")
        sys.exit(1)

    # Setup logging
    setup_logging()

    # Build application
    logger.info("Building Telegram bot application...")
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("health", health_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("landscapes", landscapes_command))
    application.add_handler(CommandHandler("analyze", analyze_command))

    # Register error handler
    application.add_error_handler(error_handler)

    # Start polling
    logger.info("Starting polling...")
    logger.info("\n" + "=" * 70)
    logger.info("BOT IS RUNNING - Press Ctrl+C to stop")
    logger.info("=" * 70 + "\n")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
