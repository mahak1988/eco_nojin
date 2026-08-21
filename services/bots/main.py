"""Eco Nojin bot — multi-platform entry point (Phase 2).

Usage:
    python -m services.bots.main

Platforms: telegram (always), eitaa (EITAA_ENABLED=true + EITAA_TOKEN),
bale (BALE_ENABLED=true + BALE_TOKEN), rubika (RUBIKA_ENABLED=true +
RUBIKA_TOKEN). Telegram/Eitaa run concurrently on the same dispatcher.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from .adapters.bale import BaleGateway
from .adapters.rubika import RubikaGateway
from .adapters.telegram import create_bot
from .config import BotConfig
from .factory import build_dispatcher
from .platforms import enabled_platforms, token_for

logger = logging.getLogger(__name__)


def runner_plan(config: BotConfig) -> list[str]:
    """Keys of platforms that would start with this config (no side effects).

    Telegram/Eitaa run via aiogram polling; Bale/Rubika are reported here
    but cannot start yet (they raise a clear error if forced).
    """
    return [spec.key for spec in enabled_platforms(config)]


async def _run(config: BotConfig) -> None:
    plan = enabled_platforms(config)
    if not plan:
        print(
            "No platform configured. Set BOT_TOKEN in .env (Telegram), or\n"
            "enable Eitaa/Bale/Rubika per docs/en/15_multiplatform_bots.md.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    tasks = []
    for spec in plan:
        token = token_for(spec, config)
        if spec.kind == "aiogram":
            bot = create_bot(token, api_base=spec.api_base)
            dp = build_dispatcher(config)
            logger.info("Starting %s (%s)", spec.label, spec.key)
            tasks.append(dp.start_polling(bot))
        elif spec.kind == "bale":
            gateway = BaleGateway(token)
            if not gateway.available():
                logger.warning("Bale skipped: python-bale-bot not installed")
            else:
                # blocking loop -> worker thread
                tasks.append(asyncio.to_thread(gateway.start))
        elif spec.kind == "rubika":
            gateway = RubikaGateway(token)
            logger.warning("Rubika skipped: integration not implemented yet")
        else:  # pragma: no cover
            logger.error("Unknown platform kind %s", spec.kind)

    if not tasks:
        print("No runnable platform (see warnings above).", file=sys.stderr)
        raise SystemExit(2)

    await asyncio.gather(*tasks)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    config = BotConfig.from_env()
    if not config.has_token and not enabled_platforms(config):
        print(
            "BOT_TOKEN is missing. Set it in .env (get one from @BotFather).\n"
            "See docs/en/14_telegram_bot.md for the quick start.",
            file=sys.stderr,
        )
        return 2
    try:
        asyncio.run(_run(config))
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
