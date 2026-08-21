"""Phase 1 tests: Eco Nojin Telegram bot (no network, no token required).

Handlers are exercised directly with lightweight fakes; the AI service uses
a fake Ollama client so tests stay deterministic and offline.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from services.bots import i18n
from services.bots.config import BotConfig
from services.bots.core.ai import AdviceService
from services.bots.handlers import advice as advice_mod
from services.bots.handlers import farm as farm_mod
from services.bots.handlers import start as start_mod


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------
def make_user(user_id: int = 42, lang: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        language_code=lang,
        full_name="Test Farmer",
        first_name="Test",
        is_bot=False,
    )


def make_message(text: str | None = None, lang: str | None = None,
                 location: SimpleNamespace | None = None,
                 user: SimpleNamespace | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        from_user=user or make_user(lang=lang),
        location=location,
        chat=SimpleNamespace(id=1, type="private"),
    )


def make_callback(data: str, message=None) -> SimpleNamespace:
    answers: list[str] = []

    async def _answer(**kw):
        answers.append("ok")

    cb = SimpleNamespace(data=data, message=message, answers=answers)
    cb.answer = _answer
    return cb


class FakeOllama:
    """Deterministic stand-in; offline by default."""

    def __init__(self, available: bool = False) -> None:
        self._available = available

    async def available(self) -> bool:
        return self._available

    async def chat(self, system: str, user: str, temperature: float = 0.2) -> str | None:
        return "پاسخ تستی با استناد [1]"


class FakeAnswerMessage:
    """Message fake that records .answer() calls (async, like aiogram)."""

    def __init__(self, base: SimpleNamespace) -> None:
        self.base = base
        self.sent: list[str] = []

    async def answer(self, text: str, **kwargs) -> None:
        self.sent.append(text)

    def __getattr__(self, item):
        return getattr(self.base, item)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def run(coro):
    return asyncio.run(coro)


async def make_state(user_id: int = 42, chat_id: int = 1) -> FSMContext:
    storage = MemoryStorage()
    key = StorageKey(bot_id=1, chat_id=chat_id, user_id=user_id, thread_id=None)
    return FSMContext(storage=storage, key=key)


def make_advice_service(ollama_available: bool = False) -> AdviceService:
    cfg = BotConfig(bot_token = "test_token_placeholder")
    return AdviceService(cfg, ollama=FakeOllama(ollama_available))


# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------
def test_languages_are_14():
    assert len(i18n.LANGUAGES) == 14
    assert i18n.LANGUAGE_NAMES.keys() == set(i18n.LANGUAGES)
    for lang in i18n.LANGUAGES:
        for key in ("greeting", "advice_btn", "farm_btn", "about_btn", "lang_btn"):
            assert i18n.t(lang, key), f"{lang}/{key} empty"


def test_detect_language_bcp47():
    assert i18n.detect_language("fa-IR") == "fa"
    assert i18n.detect_language("en-US") == "en"
    assert i18n.detect_language("zh_CN") == "zh"
    assert i18n.detect_language(None) == i18n.DEFAULT_LANGUAGE


def test_detect_language_script_heuristics():
    assert i18n.detect_language(None, "کمپوست و کود") == "fa"
    assert i18n.detect_language(None, "مرحبا بك") == "ar"
    assert i18n.detect_language(None, "खेत और मिट्टी") == "hi"
    assert i18n.detect_language(None, "こんにちは") == "zh"
    assert i18n.detect_language(None, "Здравствуйте") == "ru"


# ---------------------------------------------------------------------------
# /start flow
# ---------------------------------------------------------------------------
def test_start_greeting_in_persian_by_default():
    async def scenario():
        state = await make_state()
        msg = FakeAnswerMessage(make_message("/start", lang=None))
        await start_mod.cmd_start(msg, state)
        return msg.sent

    sent = run(scenario())
    assert sent and "اکو نوژین" in sent[0]


def test_language_callback_switches_to_english():
    async def scenario():
        state = await make_state()
        msg = FakeAnswerMessage(make_message("/start", lang=None))
        await start_mod.cmd_start(msg, state)
        cb_msg = FakeAnswerMessage(make_message(None))
        cb = make_callback("set_lang:en", message=cb_msg)
        await start_mod.set_language(cb, state)
        data = await state.get_data()
        return data.get("language"), cb_msg.sent

    lang, sent = run(scenario())
    assert lang == "en"
    assert sent and "Main menu" in sent[0]


def test_invalid_language_callback_falls_back():
    async def scenario():
        state = await make_state()
        cb_msg = FakeAnswerMessage(make_message(None))
        cb = make_callback("set_lang:xx", message=cb_msg)
        await start_mod.set_language(cb, state)
        data = await state.get_data()
        return data.get("language")

    assert run(scenario()) == i18n.DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# Advice flow
# ---------------------------------------------------------------------------
def test_advice_offline_falls_back_to_rag_with_note():
    async def scenario():
        state = await make_state()
        service = make_advice_service(ollama_available=False)
        msg = FakeAnswerMessage(make_message("What is the compost C/N ratio?"))
        await advice_mod.advice_answer(msg, state, {"advice": service})
        return msg.sent

    sent = run(scenario())
    assert sent
    assert "FAO" in sent[0] or "Compost" in sent[0]  # evidence grounded
    assert "Ollama" in sent[0]  # honest offline note


def test_advice_with_ollama_translates_and_cites():
    async def scenario():
        state = await make_state()
        service = make_advice_service(ollama_available=True)
        msg = FakeAnswerMessage(make_message("What is the compost C/N ratio?"))
        await advice_mod.advice_answer(msg, state, {"advice": service})
        return msg.sent

    sent = run(scenario())
    assert sent and "پاسخ تستی" in sent[0]


def test_advice_no_match_returns_honest_answer():
    async def scenario():
        state = await make_state()
        service = make_advice_service(ollama_available=False)
        msg = FakeAnswerMessage(make_message("zxqwv invalid query 12345"))
        await advice_mod.advice_answer(msg, state, {"advice": service})
        return msg.sent

    sent = run(scenario())
    assert sent and ("یافت نشد" in sent[0] or "⚠️" in sent[0])


# ---------------------------------------------------------------------------
# Farm registration FSM (persists to a temp SQLite DB)
# ---------------------------------------------------------------------------
@pytest.fixture
def temp_farm_db(tmp_path):
    """Point the farm handler at a temp SQLite DB and create the schema."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import database.models  # noqa: F401  (register all tables on Base)
    from database.models import Base

    db_path = tmp_path / "bot_farm_test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    original = farm_mod._session
    farm_mod._session = session_factory
    yield session_factory, str(db_path)
    farm_mod._session = original


def _full_farm_wizard(session_factory):
    """Drive the whole wizard; returns the sent messages."""
    async def scenario():
        state = await make_state()
        sent = []

        msg = FakeAnswerMessage(make_message("🌾 ثبت مزرعه", lang="fa"))
        await farm_mod.farm_start(msg, state)
        sent += msg.sent

        msg = FakeAnswerMessage(make_message("مزرعه نمونه"))
        await farm_mod.farm_name(msg, state)
        sent += msg.sent

        msg = FakeAnswerMessage(make_message("5.5"))
        await farm_mod.farm_area(msg, state)
        sent += msg.sent

        msg = FakeAnswerMessage(make_message("35.6892, 51.3890"))
        await farm_mod.farm_location_text(msg, state)
        sent += msg.sent

        msg = FakeAnswerMessage(make_message("لومی"))
        await farm_mod.farm_soil(msg, state)
        sent += msg.sent

        return sent

    return run(scenario())


def test_farm_wizard_persists_farm(temp_farm_db):
    session_factory, db_path = temp_farm_db
    sent = _full_farm_wizard(session_factory)

    assert sent and "ثبت شد" in sent[-1]

    from database.models import Farm, User

    session = session_factory()
    try:
        farms = session.query(Farm).all()
        users = session.query(User).all()
    finally:
        session.close()

    assert len(farms) == 1
    assert farms[0].name == "مزرعه نمونه"
    assert farms[0].area_hectares == 5.5
    assert farms[0].latitude == 35.6892
    assert farms[0].longitude == 51.3890
    assert farms[0].soil_type == "لومی"
    assert len(users) == 1
    assert users[0].phone == "tg:42"


def test_farm_wizard_reauthores_same_user(temp_farm_db):
    session_factory, _ = temp_farm_db
    _full_farm_wizard(session_factory)
    _full_farm_wizard(session_factory)  # same tg user registers twice

    from database.models import Farm, User

    session = session_factory()
    try:
        n_farms = session.query(Farm).count()
        n_users = session.query(User).count()
    finally:
        session.close()

    assert n_farms == 2
    assert n_users == 1  # user reused, not duplicated


def test_farm_wizard_rejects_bad_area(temp_farm_db):
    session_factory, _ = temp_farm_db

    async def scenario():
        state = await make_state()
        msg = FakeAnswerMessage(make_message("🌾 ثبت مزرعه", lang="fa"))
        await farm_mod.farm_start(msg, state)
        msg = FakeAnswerMessage(make_message("مزرعه نمونه"))
        await farm_mod.farm_name(msg, state)
        msg = FakeAnswerMessage(make_message("abc"))
        await farm_mod.farm_area(msg, state)
        data = await state.get_data()
        current = await state.get_state()
        return msg.sent, current, data

    sent, current_state, data = run(scenario())
    assert sent and "⚠️" in sent[-1]  # re-prompt
    assert current_state == farm_mod.FarmRegister.area  # stays in state
    assert data["draft"].area == 0.0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def test_main_requires_token(capsys):
    import services.bots.main as main_mod

    code = main_mod.main()  # no BOT_TOKEN in env -> exit 2
    captured = capsys.readouterr()
    assert code == 2
    assert "BOT_TOKEN" in captured.err
