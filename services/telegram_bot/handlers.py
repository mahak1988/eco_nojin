"""Telegram bot command handlers."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from services.api_gateway.errors import safe_error_detail

from .api_client import api_client
from .formatters import (
    format_analysis_response,
    format_error,
    format_help,
    format_landscapes_list,
    format_stats,
    format_welcome,
)

logger = logging.getLogger("econojin.bot.handlers")

_TELEGRAM_DEPENDENCY_MESSAGE = (
    "python-telegram-bot is not installed in this environment, so the "
    "services.telegram_bot handlers cannot be imported. Install the optional "
    "dependency with `pip install 'hydroma[telegram]'` (or "
    "`pip install python-telegram-bot`); the machine that produced this error "
    "has no network access to PyPI, so the bot stays disabled instead of "
    "failing with a bare ModuleNotFoundError."
)


class TelegramDependencyMissing(ImportError):
    """Raised when the optional ``python-telegram-bot`` dependency is absent."""


try:  # optional dependency — see pyproject.toml [project.optional-dependencies].telegram
    # Imported through importlib so the guard can live after the normal import
    # block; functionally identical to ``from telegram import Update`` and
    # ``from telegram.ext import ContextTypes``.
    _telegram = importlib.import_module("telegram")
    _telegram_ext = importlib.import_module("telegram.ext")
    Update: Any = _telegram.Update
    ContextTypes: Any = _telegram_ext.ContextTypes
except ImportError as exc:  # pragma: no cover - exercised only without the extra
    raise TelegramDependencyMissing(_TELEGRAM_DEPENDENCY_MESSAGE) from exc


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        format_welcome(),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        format_help(),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health command."""
    await update.message.reply_text("⏳ بررسی وضعیت API...")

    is_healthy = await api_client.health_check()

    if is_healthy:
        await update.message.reply_text(
            "✅ *API فعال و در دسترس است!*\n\n"
            "🚀 می‌توانید تحلیل زمین را شروع کنید:\n"
            "`/analyze 35.6892 51.389 50`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            format_error("API در دسترس نیست. لطفاً بعداً دوباره تلاش کنید."),
            parse_mode="Markdown",
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command."""
    await update.message.reply_text("⏳ دریافت آمار...")

    stats = await api_client.get_stats()

    if stats:
        await update.message.reply_text(
            format_stats(stats),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            format_error("دریافت آمار ناموفق بود."),
            parse_mode="Markdown",
        )


async def landscapes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /landscapes command."""
    await update.message.reply_text("⏳ دریافت لیست زمین‌ها...")

    landscapes = await api_client.list_landscapes()

    if landscapes is not None:
        await update.message.reply_text(
            format_landscapes_list(landscapes),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            format_error("دریافت لیست زمین‌ها ناموفق بود."),
            parse_mode="Markdown",
        )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /analyze command.

    Format: /analyze latitude longitude area_ha [name]
    Example: /analyze 35.6892 51.389 50 Tehran Farm
    """
    args = context.args

    if not args or len(args) < 3:
        await update.message.reply_text(
            "❌ *فرمت نادرست*\n\n"
            "📝 استفاده صحیح:\n"
            "`/analyze lat lon area [name]`\n\n"
            "🌟 مثال:\n"
            "`/analyze 35.6892 51.389 50 Tehran Farm`\n\n"
            "💡 راهنما: /help",
            parse_mode="Markdown",
        )
        return

    try:
        latitude = float(args[0])
        longitude = float(args[1])
        area_ha = float(args[2])
        name = " ".join(args[3:]) if len(args) > 3 else f"Farm-{int(latitude * 1000)}"

        # Validate ranges
        if not (-90 <= latitude <= 90):
            raise ValueError("عرض جغرافیایی باید بین -90 و 90 باشد")
        if not (-180 <= longitude <= 180):
            raise ValueError("طول جغرافیایی باید بین -180 و 180 باشد")
        if not (0 < area_ha <= 100000):
            raise ValueError("مساحت باید بین 0 و 100,000 هکتار باشد")

    except ValueError as e:
        await update.message.reply_text(
            format_error(safe_error_detail(e)),
            parse_mode="Markdown",
        )
        return

    # Send typing indicator
    await update.message.reply_text(
        f"🔍 *در حال تحلیل زمین {name}...*\n\n"
        f"📍 مختصات: `{latitude:.4f}, {longitude:.4f}`\n"
        f"📏 مساحت: {area_ha:.1f} هکتار\n\n"
        f"⏳ این فرآیند حدود ۳-۵ ثانیه طول می‌کشد...",
        parse_mode="Markdown",
    )

    # Call API
    result = await api_client.analyze_land(
        name=name,
        latitude=latitude,
        longitude=longitude,
        area_ha=area_ha,
    )

    if result:
        # Format and send response
        formatted = format_analysis_response(result)

        # Telegram has 4096 char limit, split if needed
        if len(formatted) > 4000:
            # Send in chunks
            chunks = [formatted[i : i + 4000] for i in range(0, len(formatted), 4000)]
            for chunk in chunks:
                await update.message.reply_text(
                    chunk,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
        else:
            await update.message.reply_text(
                formatted,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
    else:
        await update.message.reply_text(
            format_error(
                "تحلیل زمین ناموفق بود.\n\nلطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            ),
            parse_mode="Markdown",
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Exception: {context.error}")

    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            format_error("خطای غیرمنتظره. لطفاً دوباره تلاش کنید."),
            parse_mode="Markdown",
        )
