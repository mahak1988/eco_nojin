# 14. Telegram Bot (Phase 1) — «اکو نوژین» Quick Start

**Status:** Phase 1 — implemented & tested | **Version:** 1.0.0 | **Date:** 2026-08-16

## What is included

- `services/bots/` — one bot core, platform adapters:
  - `config.py` — env-driven settings
  - `i18n.py` — **14 languages** (ar, bn, de, en, es, fa, fr, hi, it, ms, pt,
    ru, ur, zh) + automatic language detection (BCP-47 code first, then
    script heuristics; default `fa`)
  - `handlers/start.py` — `/start`, language selection, main menu
  - `handlers/advice.py` — advisory flow
  - `handlers/farm.py` — farm registration wizard (FSM) persisted into the
    unified SQLite schema (users + farms tables)
  - `core/ai.py` — `OllamaClient` (local, offline-safe) + `AdviceService`
    (citation-grounded answers from the existing RAG engine)
  - `adapters/telegram.py` — the only Telegram-aware file (Eitaa / Rubika /
    Bale reuse everything else)
- `tests/test_bot_phase1.py` — 13 offline tests (no token, no network)

## How the advisory flow works

1. User asks a question in any of the 14 languages.
2. The RAG engine (`engine/hydroma/ai_assistant`) retrieves the top-3 most
   relevant documents from the FAO-aligned knowledge base.
3. If a local Ollama server is running, the model synthesizes an answer in
   the user's language **with inline citations** `[1], [2], …` and a source
   list. Nothing is invented: the model is instructed to answer only from
   the retrieved context.
4. If Ollama is offline, the raw evidence is returned in English with an
   honest note — never fabricated content.

Recommended local models (better quality than `llama3.1:8b`, still free):

```bash
ollama pull glm4:9b          # Chinese, strong multilingual (recommended)
ollama pull qwen2.5:7b       # strong multilingual
ollama pull dolphin-mistral  # lightweight alternative
```

Set `OLLAMA_MODEL=glm4:9b` in `.env` after pulling.

## Running the bot

```bash
# 1. Get a token from @BotFather and put it in .env:
#    BOT_TOKEN=123456:ABC...
# 2. (optional but recommended) start Ollama with a multilingual model
# 3. Run:
python -m services.bots.main
```

Without `BOT_TOKEN` the bot refuses to start with a clear message — it never
runs half-configured.

## Bot features (menu)

- 💬 **مشاوره / Advice** — ask agricultural questions, answers with sources
- 🌾 **ثبت مزرعه / Register farm** — step-by-step wizard:
  name → area (ha) → location (shared pin or `lat, lon`) → soil type
  (optional). Saved into the same database as the web API.
- ℹ️ **درباره / About** — platform info
- 🌐 **زبان / Language** — 14 languages, auto-detected on first contact

## Telegram → other platforms (Phase 2 preview)

- **Eitaa & Rubika** expose Telegram-compatible bot APIs → the same
  dispatcher/handlers run with a new token (new adapter).
- **Bale** uses its own client library (`python-bale-bot` / `telegram-bale-bot`)
  → an adapter that maps aiogram-style handlers onto it.
- **WhatsApp / Instagram** come via Meta's official APIs (second tier).

## Tests

```bash
python -m pytest tests/test_bot_phase1.py -q     # 13 tests, offline
python -m pytest -q                              # full suite
```
