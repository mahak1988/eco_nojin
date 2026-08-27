"""
Eco Nojin Telegram Bot - Main Entry Point.

Run with:
    python -m services.telegram_bot.main
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from telegram.ext import Application, CommandHandler

from .config import config
from .handlers import (
    analyze_command,
    error_handler,
    health_command,
    help_command,
    landscapes_command,
    start_command,
    stats_command,
)


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
    # Validate configuration
    if not config.validate():
        print("\nPlease set TELEGRAM_BOT_TOKEN in your .env file.")
        print("Get one from @BotFather on Telegram.")
        sys.exit(1)

    # Setup logging
    setup_logging()
    logger = logging.getLogger("econojin.bot")

    # Build application
    logger.info("Building Telegram bot application...")
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

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
    print("\n" + "=" * 70)
    print("BOT IS RUNNING - Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    from telegram import Update
    main()
