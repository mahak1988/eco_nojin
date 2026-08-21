"""/start, language selection and the main menu."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from .. import i18n

router = Router(name="start")

_ABOUT_LABELS = {ui["about_btn"] for ui in i18n.UI.values()}
_LANG_LABELS = {ui["lang_btn"] for ui in i18n.UI.values()}


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=name, callback_data=f"set_lang:{code}")
        for code, name in i18n.LANGUAGE_NAMES.items()
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.t(lang, "advice_btn")),
                KeyboardButton(text=i18n.t(lang, "farm_btn")),
            ],
            [
                KeyboardButton(text=i18n.t(lang, "about_btn")),
                KeyboardButton(text=i18n.t(lang, "lang_btn")),
            ],
        ],
        resize_keyboard=True,
    )


async def get_lang(state: FSMContext, message: Message | None = None) -> str:
    """Current language: FSM data first, then detection, then default."""
    data = await state.get_data()
    if data.get("language"):
        return data["language"]
    detected = i18n.detect_language(message.from_user.language_code if message and message.from_user else None)
    await state.update_data(language=detected)
    return detected


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    lang = await get_lang(state, message)
    await message.answer(i18n.t(lang, "greeting"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language(callback: CallbackQuery, state: FSMContext) -> None:
    lang = callback.data.split(":", 1)[1]
    if lang not in i18n.LANGUAGES:
        lang = i18n.DEFAULT_LANGUAGE
    await state.update_data(language=lang)
    if callback.message:
        await callback.message.answer(
            i18n.t(lang, "main_menu"),
            reply_markup=main_menu_keyboard(lang),
        )
    await callback.answer()


@router.message(F.text.in_(_LANG_LABELS))
async def language_request(message: Message, state: FSMContext) -> None:
    lang = await get_lang(state, message)
    await message.answer(i18n.t(lang, "greeting"), reply_markup=language_keyboard())


@router.message(F.text.in_(_ABOUT_LABELS))
async def about(message: Message, state: FSMContext) -> None:
    lang = await get_lang(state, message)
    await message.answer(i18n.t(lang, "about"))
