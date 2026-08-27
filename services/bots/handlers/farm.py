"""Farm registration wizard (FSM) — writes into the unified SQLite schema.

Flow: name -> area (ha) -> location ("lat, lon" or Telegram location) ->
soil type (optional). On completion the farm is persisted via the project's
``database.config.SessionLocal`` (same tables as the API).
"""

from __future__ import annotations

import asyncio
import re
import secrets
from dataclasses import dataclass

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from .. import i18n
from .start import get_lang

router = Router(name="farm")

_FARM_LABELS = {ui["farm_btn"] for ui in i18n.UI.values()}

_LOCATION_RE = re.compile(
    r"^\s*(-?\d{1,3}(?:\.\d+)?)\s*[,،]\s*(-?\d{1,3}(?:\.\d+)?)\s*$"
)


class FarmRegister(StatesGroup):
    name = State()
    area = State()
    location = State()
    soil = State()


@dataclass
class FarmDraft:
    """In-memory wizard state before persistence."""

    name: str = ""
    area: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    soil_type: str | None = None


def _session():
    """Session factory seam — tests monkeypatch this to use a temp DB."""
    from database.config import SessionLocal

    return SessionLocal()


@router.message(F.text.in_(_FARM_LABELS))
async def farm_start(message: Message, state: FSMContext) -> None:
    lang = await get_lang(state, message)
    await state.set_state(FarmRegister.name)
    await state.update_data(draft=FarmDraft(), lang=lang)
    await message.answer(i18n.t(lang, "farm_name_q"))


@router.message(F.text, FarmRegister.name)
async def farm_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", i18n.DEFAULT_LANGUAGE)
    draft: FarmDraft = data["draft"]
    draft.name = message.text.strip()
    await state.update_data(draft=draft)
    await state.set_state(FarmRegister.area)
    await message.answer(i18n.t(lang, "farm_area_q"))


@router.message(F.text, FarmRegister.area)
async def farm_area(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", i18n.DEFAULT_LANGUAGE)
    try:
        area = float(message.text.strip().replace(",", "."))
        if area <= 0 or area > 100000:
            raise ValueError
    except ValueError:
        await message.answer(i18n.t(lang, "farm_area_q") + " ⚠️")
        return
    draft: FarmDraft = data["draft"]
    draft.area = area
    await state.update_data(draft=draft)
    await state.set_state(FarmRegister.location)
    await message.answer(i18n.t(lang, "farm_loc_q"))


@router.message(F.location, FarmRegister.location)
async def farm_location_share(message: Message, state: FSMContext) -> None:
    loc = message.location
    data = await state.get_data()
    lang = data.get("lang", i18n.DEFAULT_LANGUAGE)
    draft: FarmDraft = data["draft"]
    draft.latitude = loc.latitude
    draft.longitude = loc.longitude
    await state.update_data(draft=draft)
    await state.set_state(FarmRegister.soil)
    await message.answer(i18n.t(lang, "farm_soil_q"))


@router.message(F.text, FarmRegister.location)
async def farm_location_text(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", i18n.DEFAULT_LANGUAGE)
    match = _LOCATION_RE.match(message.text.strip())
    if not match:
        await message.answer(i18n.t(lang, "farm_loc_q") + " ⚠️")
        return
    draft: FarmDraft = data["draft"]
    draft.latitude = float(match.group(1))
    draft.longitude = float(match.group(2))
    await state.update_data(draft=draft)
    await state.set_state(FarmRegister.soil)
    await message.answer(i18n.t(lang, "farm_soil_q"))


@router.message(F.text, FarmRegister.soil)
async def farm_soil(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", i18n.DEFAULT_LANGUAGE)
    draft: FarmDraft = data["draft"]
    soil = message.text.strip()
    draft.soil_type = None if soil in ("-", "–", "—") else soil
    await state.update_data(draft=draft)

    # Persist (blocking sync DB in a worker thread — fine for Phase 1).
    saved = await asyncio.to_thread(_save_farm, draft, message.from_user.id, message.from_user.full_name)
    await state.clear()
    if saved:
        await message.answer(i18n.t(lang, "farm_saved").format(name=draft.name))
    else:
        await message.answer(i18n.t(lang, "no_answer"))


def _save_farm(draft: FarmDraft, tg_user_id: int, tg_name: str) -> bool:
    """Create-or-reuse a user (keyed by tg id) and insert the farm row."""
    from database.models import Farm, User

    session = _session()
    try:
        phone_key = f"tg:{tg_user_id}"
        user = session.query(User).filter(User.phone == phone_key).first()
        if user is None:
            user = User(
                email=f"tg_{tg_user_id}@eco-nojin.local",
                full_name=tg_name or f"Telegram {tg_user_id}",
                # Telegram-bound accounts have no password; store an
                # unguessable placeholder (they authenticate via Telegram).
                hashed_password=secrets.token_urlsafe(48),
                phone=phone_key,
                role="farmer",
                language="fa",
                is_active=True,
            )
            session.add(user)
            session.flush()

        farm = Farm(
            name=draft.name,
            owner_id=user.id,
            latitude=draft.latitude,
            longitude=draft.longitude,
            area_hectares=draft.area,
            soil_type=draft.soil_type,
        )
        session.add(farm)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()
