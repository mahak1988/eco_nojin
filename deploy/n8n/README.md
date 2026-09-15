# n8n Integration — Eco Nojin

Two importable workflows connect the platform's automation surface to n8n.

## 1. Import

In n8n: **Workflows → Import from File** and pick:

| File | Purpose |
|---|---|
| `econojin-daily-monitor.json` | هر روز ۶ صبح: اجرای سایکل ایجنت داخلی → اگر چکی شکست خورد، هشدار در مرکز داده |
| `econojin-chain-webhook.json` | Webhook برای اجرای زنجیرهٔ علمی (RUSLE → RothC → AquaCrop) با lat/lon |

## 2. Environment

Set on the n8n host (and on the backend host):

```bash
# backend (.env)
AGENT_TOKEN=<a long random string>     # protects /api/v1/automation/agent-run

# n8n
ECONOJIN_AGENT_TOKEN=<the same value>
```

Without `AGENT_TOKEN` the backend falls back to `dev-agent-token` (development only).

## 3. Endpoints n8n uses

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/automation/agent-run` | header `X-Agent-Token`; body `{"watch_farms":[],"store_digest":true}` |
| GET | `/api/v1/automation/health` | token status |
| POST | `/api/v1/motors/chain` | lat/lon scientific chain (long-running, ~20–120 s) |
| POST | `/api/v1/hub/runs` | store a run / alert in the central hub |
| GET | `/api/v1/hydroma/validation` | formula verification report |
| GET | `/api/v1/hydroma/db-stats` | database health |

## 4. AI Agent (best practice: native nodes + tools)

`econojin-ai-agent.json` — the platform assistant as a native n8n AI Agent:

- **Chat Trigger → AI Agent → (LLM + Memory + 6 HTTP tools)** — per the
  community best practice, the LLM only routes and summarizes; every number
  comes from a real platform tool call (`$fromAI` fills the parameters).
- Tools wired to the gateway: `get_formula_validation`, `get_db_stats`,
  `get_models`, `run_model` (slug+params via `$fromAI`), `get_hydroma_indices`,
  `run_agent_cycle` (uses `ECONOJIN_AGENT_TOKEN` from the n8n environment).
- Setup: create the OpenAI credential on the LLM node (or swap in an Ollama
  Chat Model for a fully local setup), set `ECONOJIN_AGENT_TOKEN`, then open
  the built-in chat and ask e.g. «راستیآزمایی فرمولها را اجرا کن».
- Production hardening (Hatchworks guide): run n8n in **queue mode with
  Postgres**, keep credentials in the n8n credential store (never in JSON),
  and set an Error Workflow for failed executions.

## 4. Cron alternative (no n8n)

```bash
# daily 06:00 — Windows Task Scheduler or cron
python scripts/agent_daily.py --base http://127.0.0.1:8000 --farms 1,2
python scripts/db_maintenance.py --backup
```

## 5. Notes

- The automation endpoint is **CSRF-exempt but token-protected** (it is called
  server-to-server and carries no cookies).
- Every agent cycle stores a digest (`model_id=agent-digest`) in the hub, so the
  automation history is auditable from the dashboard.
