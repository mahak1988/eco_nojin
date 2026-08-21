"""Telegram adapter — the only place that knows about the Telegram Bot API.

Eitaa and Rubika expose Telegram-compatible Bot APIs; pointing this factory
at a custom ``api_base`` (e.g. https://eitaayar.ir/api) lets the exact same
dispatcher and handlers serve those platforms. Bale uses a different client
library (see adapters/bale.py).
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode


def create_bot(token: str, api_base: str | None = None) -> Bot:
    """Create an aiogram Bot for the given token.

    ``api_base`` overrides the Bot API server — used for Telegram-compatible
    platforms (Eitaa: https://eitaayar.ir/api). ``None`` means the official
    Telegram API.
    """
    kwargs: dict = {}
    if api_base:
        kwargs["session"] = AiohttpSession(
            api=TelegramAPIServer.from_base(api_base.rstrip("/") + "/")
        )
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        **kwargs,
    )
