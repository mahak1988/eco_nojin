"""Bot factory — builds a fully wired Dispatcher (no token needed, testable)."""

from __future__ import annotations

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .config import BotConfig
from .core.ai import AdviceService
from .handlers import advice, farm, start


def build_dispatcher(config: BotConfig | None = None, advice_service: AdviceService | None = None) -> Dispatcher:
    """Assemble the dispatcher with all routers and shared services."""
    config = config or BotConfig.from_env()
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config
    dp["advice"] = advice_service or AdviceService(config)
    dp.include_router(start.router)
    dp.include_router(advice.router)
    dp.include_router(farm.router)
    return dp
