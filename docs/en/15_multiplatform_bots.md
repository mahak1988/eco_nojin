# 15. Multi-Platform Bots (Phase 2) — Eitaa, Bale, Rubika

**Status:** Phase 2 — adapters + registry + alert engine implemented; live
verification pending tokens | **Version:** 1.0.0 | **Date:** 2026-08-16

## Architecture: one core, many adapters

```
services/bots/
├── core/          # AI, alerts, i18n — platform-agnostic
├── handlers/      # Telegram-shaped handlers (start/advice/farm) — reusable
├── adapters/
│   ├── telegram.py   # aiogram Bot factory (custom api_base support) ✅ verified
│   ├── bale.py       # python-bale-bot bridge (lazy import)       ⏳ needs live token
│   └── rubika.py     # guarded stub — integration study needed    ⛔ not implemented
└── platforms.py      # registry: token envs, enable flags, kinds
```

## Platform matrix (honest status)

| Platform | Kind | API base | Token from | Status |
|---|---|---|---|---|
| Telegram | aiogram | api.telegram.org (default) | @BotFather | ✅ verified |
| Eitaa | aiogram | `https://eitaayar.ir/api` | Eitaayar | ⏳ needs live getMe check |
| Bale | bale | python-bale-bot | @Bot_Father (Bale) | ⏳ library conflict on Windows; needs isolated env |
| Rubika | rubika | proprietary protocol | — | ⛔ integration study required |

**Eitaa** — its Bot API is Telegram-compatible (documented at
developer.eitaa.com; base `https://eitaayar.ir/api`), so the *same*
dispatcher/handlers run unchanged: only the API base changes
(`create_bot(token, api_base=EITAA_API_BASE)`). Verified=False until a live
`getMe` succeeds with a real Eitaayar token.

**Bale** — `python-bale-bot` (v2.5.0) is the community client. ⚠️ It pulls
an old aiohttp and a shadow `asyncio` package that break the main
environment — that is why it is **not** installed here and `aiohttp==3.14.3`
is pinned. On a separate host (e.g. the Linux deploy VM):

```bash
python -m venv bale-venv && bale-venv/bin/pip install python-bale-bot
# run with BALE_ENABLED=true + BALE_TOKEN=<token>
```

**Rubika** — its bot protocol is *not* Telegram-compatible (phone-session
auth, different message model). Requires a dedicated integration study
before any code. Until then the adapter refuses to start with a clear
message — no unverified glue ships.

## Enabling a platform

```dotenv
# .env
BOT_TOKEN=123:your-telegram-token      # always on
EITAA_TOKEN=your-eitaayar-token
EITAA_ENABLED=true
BALE_TOKEN=your-bale-token
BALE_ENABLED=true
RUBIKA_TOKEN=unused-for-now
RUBIKA_ENABLED=false
```

Run: `python -m services.bots.main` — Telegram and Eitaa poll concurrently
on the same dispatcher (FSM state, language, farm registration all shared).

## Smart alerts (⭐5)

`core/alerts.py` — rule engine over farm data rows:

- Rules: `metric`, `op` (`< <= > >= ==`), `threshold`, `severity`,
  Persian label.
- Missing metrics never fire — no fabricated alerts.
- `format_alert()` renders a Persian message with the observed value and
  threshold (ℹ️/⚠️/🚨).

Example rule: `AlertRule("soil_moisture_pct", "<", 25.0, "critical",
"رطوبت خاک پایین است")`. Wiring alerts to real satellite/soil data arrives
with Phase 4 (real Copernicus data replaces the simulated source, W-001).

## Tests

```bash
python -m pytest tests/test_bot_phase2.py -q   # 14 tests, offline
```

Covers: registry completeness + honest verified flags, Eitaa enable-flag
logic, Eitaa API-base URL construction, Bale/Rubika loud failures, alert
thresholds/missing-metric/formatting.
