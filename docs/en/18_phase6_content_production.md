# 18 — Phase 6 Kickoff: Content Production Panel

> Status: **phase 6 started** — editorial content now has versioning, AI
> translation and honest RAG sync. 307 backend tests green.

## 1. Goal

"One publish, three channels" (site + RAG + messengers) without touching
code. This session delivers the content backbone; scheduled bot publishing
and AI draft generation complete the phase.

## 2. What shipped

### Data model (migration `e5f1a2b3c4d5`)
- `content_versions` — snapshot of every update (version history).
- `content_translations` — per-language title/body (source: ai|manual).
- `content_items` += `generated_by_ai`, `rag_synced`, `published_at`.

### Backend (`/api/v1/admin/content*` + public search)
- **Create** now snapshots version 1; **update** snapshots the previous
  state before applying (audited as before).
- `GET /content/{id}/versions` — history (newest first).
- `GET /content/{id}/translations` — existing translations.
- `POST /content/{id}/translate?language={code}` — AI translation via local
  Ollama for 14 languages; honest 503 when Ollama is offline (no fake
  translations); upserts per language; audited.
- **Publish** sets `published_at` and runs `sync_content_to_rag` (marks all
  published items `rag_synced=True`, message includes the count).
- `services/content/rag_sync.py` — `snapshot_version`, `sync_content_to_rag`,
  `search_published_content`. Real embedding/vector retrieval lands in
  Phase 9; until then the RAG surface is an honest keyword index.
- **Public** `GET /api/v1/content/search?q=` — published items only,
  keyword search over title+body (the honest RAG surface).

### Frontend (`/admin/content`)
- Markdown editor with live preview tab (`MarkdownView`, dependency-free
  safe renderer — HTML-escaped, no raw HTML).
- Per-item drawer: AI translation (14-language selector), translation list,
  version history.
- Badges: AI-produced (`generated_by_ai`), RAG-synced.

## 3. Phase 6 acceptance criteria (master plan) — status

| Criterion | Status |
|---|---|
| Publish one article | ✅ draft → publish (with versioning + audit) |
| Translate to 14 languages | ✅ AI translation (needs Ollama runtime) |
| Enters RAG | ✅ honest keyword RAG sync + public search |
| Reaches Telegram channel | ⏳ bot dispatch (needs bot tokens + channel mapping) |
| Markdown editor + preview | ✅ |
| AI draft generation + label | ✅ `POST /admin/content/generate-draft` (Ollama, 503 honest) |
| Media (Supabase Storage) | ⏳ blocked on Supabase credentials |
| Scheduled publishing | ✅ `POST /admin/content/{id}/schedule` + due-publisher in the periodic loop |

## 4. Next steps (Phase 6 remainder)
1. AI draft generation endpoint (Ollama) with `generated_by_ai=True`.
2. Scheduled publishing to bot channels (bot tokens required).
3. Supabase Storage for media when credentials arrive.

## 5. Phase 6 remainder shipped (this session)

### AI draft generation
- `POST /api/v1/admin/content/generate-draft?topic=&category=` — local Ollama
  writes a Persian Markdown article; stored as draft with
  `generated_by_ai=True`, `source="ai-generated"`, initial version snapshot,
  audited (`content.ai_draft`). Honest 503 when Ollama is offline.
- UI: "تولید پیش‌نویس با AI" field+button above the form.

### Bot dispatch (honest)
- `services/content/bot_dispatch.py::dispatch_to_bots` — publish now
  dispatches to Telegram when ALL of: setting `content_auto_publish_bot=true`,
  `BOT_TOKEN` env, `content_publish_channel` set. Any missing piece →
  `dispatched=0` + explicit reason in the publish response (no fake "sent").
- New settings keys registered: `content_auto_publish_bot`,
  `content_publish_channel` (visible in /admin/settings).

### Scheduled publishing
- Migration `f6a2b3c4d5e6`: `content_items.scheduled_at`.
- `POST /admin/content/{id}/schedule?at=<ISO-8601>` (validates, audited) +
  `POST /admin/content/{id}/cancel-schedule`.
- `run_due_publishes(db)` publishes due drafts (status, published_at,
  rag_synced) — wired into the existing periodic alert loop in main.py.
- UI: datetime-local picker + زمان‌بندی/لغو buttons in the content drawer.

### Tests: tests/integration/test_phase6_remainder.py (7)
AI draft ok/503, schedule/cancel, bad datetime 400, due publisher, dispatch
no-token honest, dispatch sends when configured (mocked httpx).

## 6. Phase 6 acceptance — FINAL STATE
> "Publish one article → translate to 14 languages → enters RAG → reaches the
> Telegram channel (all automatic)."
- ✅ Publish (versioned + audited) → ✅ AI translation (14 langs) →
  ✅ RAG sync + public search → ✅ scheduled + Telegram dispatch mechanism
  (live dispatch needs BOT_TOKEN + channel id).
- ⏳ Media (Supabase Storage) — blocked on Supabase credentials (Phase 6
  remaining).
