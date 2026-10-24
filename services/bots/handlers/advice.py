"""Advice flow: RAG retrieval + optional local-LLM synthesis with citations."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .. import i18n
from .start import get_lang

router = Router(name="advice")

_ADVICE_LABELS = {ui["advice_btn"] for ui in i18n.UI.values()}


@router.message(F.text.in_(_ADVICE_LABELS))
async def advice_prompt(message: Message, state: FSMContext) -> None:
    lang = await get_lang(state, message)
    await message.answer(i18n.t(lang, "ask_prompt"))


@router.message(F.text)
async def advice_answer(message: Message, state: FSMContext, data: dict) -> None:
    """Answer any free text as an advisory question (outside other flows)."""
    if message.text.startswith("/"):
        return  # let command handlers deal with it

    lang = await get_lang(state, message)
    service = data["advice"]
    result = await service.advise(message.text, lang)
    await message.answer(result["answer"])
