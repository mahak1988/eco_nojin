# Eco Nojin (اکو نوژین) / HyDroMa (هیدروما)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![C++20](https://img.shields.io/badge/C++-20-00599C.svg)](https://isocpp.org/)
[![Services: 38](https://img.shields.io/badge/microservices-38-blueviolet.svg)](services/)
[![i18n: 14 locales](https://img.shields.io/badge/i18n-14%20locales-green.svg)](apps/web/messages/)

## English

Eco Nojin is an international, standards-based platform for ecosystem restoration,
smart agriculture, water and soil management, rural prosperity, pastoralist support,
carbon incentives, marketplace, and ecotourism.

HyDroMa is the scientific and computational engine of Eco Nojin — combining
deterministic physical models (Richards, Saint-Venant, FAO-56, RUSLE, SWAT, RothC),
satellite-based MRV, and an economics/finance layer to deliver decision-grade
simulations for land, water, and carbon.

### Architecture

```
┌──────────────────────────┐    ┌──────────────────────────┐
│  Frontend (Next.js/React 19)│◄──►│  API Gateway (FastAPI)   │
│  deck.gl · MapLibre · 3D │    │  Auth · Rate · Routing   │
└──────────────────────────┘    └────────────┬─────────────┘
                                              │
                ┌─────────────────────────────┼─────────────────────────┐
                ▼                             ▼                         ▼
        ┌───────────────┐            ┌────────────────┐         ┌────────────────┐
│   HyDroMa     │            │   Microservices │         │   Supabase     │
│   (Python)    │◄──────────►│   (38 services) │◄───────►│   (Postgres+RLS)│
        └───────┬───────┘            └────────┬───────┘         └────────────────┘
                │                             │
                ▼                             ▼
        ┌───────────────┐            ┌────────────────┐
        │  C++20 Core   │            │  External data │
        │  pybind11     │            │  Sentinel · ERA5│
        └───────────────┘            └────────────────┘
```

### Prerequisites

- Python 3.12+
- Node.js 20+ and pnpm 9+
- A C++20 compiler (MSVC 2022 / GCC 12+ / Clang 15+) — only required to rebuild `cpp_core`
- SQLite for local development (default), or PostgreSQL 15+ / Supabase for integrations and production
- Optional: Podman Desktop for a local PostgreSQL/Redis/n8n stack
- (Optional) Copernicus CDSE credentials for real Sentinel-2/1 tiles

### Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | Local SQLite or production PostgreSQL connection | Yes |
| `SUPABASE_URL` / `SUPABASE_KEY` | Managed database + auth | Production integrations |
| `REDIS_URL` | Optional managed Redis for rate limiting/cache | Production |
| `NATS_URL` | Optional managed NATS when the event bus is enabled | Event-bus mode |
| `CDSE_CLIENT_ID` / `CDSE_CLIENT_SECRET` | Real Sentinel access | For Phase 1 |
| `OPEN_METEO_URL` | ERA5 climate (free, no key) | Recommended |
| `JWT_SECRET` | Auth token signing | Yes (prod) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot service | Optional |

### Deployment tooling

- Local development uses a native Python environment and SQLite; Docker is not required.
- Optional local infrastructure: Podman Desktop with `podman compose -f deploy/docker-compose.yml up -d`.
- `requirements-local-api.txt` — scientific packages imported by the API routers.
- `Dockerfile` — optional container image for the API gateway + engine in staging/production.
- `render.yaml` — Render.com service manifests.
- `railway.toml` — Railway.app deployment config.
- `alembic.ini` + `alembic/`, `migrations/` — schema migration runner.
- `dvc.yaml` — DVC pipeline for data/model versioning.
- `pyproject.toml` — Python package config (`econojin.egg-info`).
- `.pre-commit-config.yaml` — pre-commit hooks (lint, format, secret scan).
- `pnpm-workspace.yaml` — pnpm monorepo workspace.

### Quick start

Docker is not required for the default local profile. SQLite, an in-process/optional
service fallback, and native Python are enough for development.

```bash
# Python 3.12+ virtual environment (uv is optional)
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-local-api.txt
# Optional integrations: python -m pip install -r requirements-optional.txt

# Windows PowerShell: Copy-Item .env.example .env
# Linux/macOS: cp .env.example .env

# API gateway (SQLite is configured in .env.example)
python -m uvicorn services.api_gateway.main:app --reload --port 8000

# Frontend
pnpm -C apps/web install
pnpm -C apps/web dev

# Tests
python -m pytest -q
```

For integration testing, set `DATABASE_URL`, `REDIS_URL`, and (when needed) `NATS_URL`
to managed services. `requirements-local-api.txt` supplies the scientific packages
imported by the API routers; `requirements-optional.txt` is only for additional
integrations. If all dependencies must run locally, install Podman Desktop and
run `podman compose -f deploy/docker-compose.yml up -d`; this is an optional path.

### Layout

| Path | Purpose |
|---|---|
| `engine/hydroma/` | Scientific engine — 30+ submodules (soil, climate, climate_adaptation, hydrology/watershed, erosion, carbon, mrv, satellite, scenarios, biofertilizer, economics, irrigation, groundwater, materials, tourism, land, infrastructure, decision_support, optimization, simulation, calibration, models, ai_assistant, performance, visualization, api, calculation, analyses, examples, utils, core, data, config, cpp_bridge) |
| `engine/cpp_core/` | C++20 numerical core (Richards, Saint-Venant, FAO-56, RUSLE, sampling) with pybind11 bindings |
| `engine/data/`, `engine/land/` | Auxiliary engine data + land-profile utilities |
| `services/` | 38 microservices: admin, ai, analytics, api_gateway, audit, auth, bots, business_modules, carbon, content, data, data_manual, data_sources, design_engine, ecowallet, field_monitoring, land, landscape, ledger, livestock, map_engine, marketplace, mobile_monitoring, models, mrv, notification, ogc, quality, reporting, satellite, science, scientific_motors, security, simulation, supabase, telegram_bot, tourism, workflow |
| `apps/web/` | Next.js 15 + React 19 + TypeScript App Router. UI: Tailwind 4 + `@eco/ui`; data: TanStack Query; i18n: next-intl with 14 locales; PWA target: Serwist + IndexedDB. |

| `adapters/` | External-system adapters (third-party API integrations) |
| `ml/` | Machine-learning models and training pipelines |
| `blockchain/`, `contracts/` | On-chain components and smart-contract sources |
| `supabase/` | Supabase project assets (RLS policies, edge functions, seeds) |
| `database/`, `alembic/`, `migrations/` | DB schema, Alembic migration history |
| `interfaces/` | Cross-cutting interfaces and shared contracts |
| `scripts/` | Operational scripts (bootstrap, ops, one-shot fixes) |
| `deploy/`, `demo/` | Deployment manifests and demo artifacts |
| `testing_lab/`, `benchmarks/`, `data/` | Experimental harnesses, perf benchmarks, raw data |
| `backups/` | Backup snapshots (kept under gitignore or quarantine) |
| `docs/` | Canonical project and frontend architecture documentation; legacy documentation is not the source of truth |
| `tests/` | Test suites — subfolders: `unit/`, `integration/`, `e2e/`, `fixtures/`, `benchmarks/`; plus top-level `test_*.py` and `challenge_*.py` scripts (e.g. `challenge_25_scientists.py`, `strict_challenge_v2.py`) |
| `apps/web/src/` | Next App Router source — `app/`, `components/`, `lib/`, `i18n/`, `messages/` |

### Honesty note on satellite data

- The legacy `earth_search` provider has been removed from active code paths.
  Any remaining `data_source="simulated"` blocks are explicitly labelled and
  never returned as real observations.
- **Phase 1 (real path):** `POST /api/v1/satellite/real-land` aggregates
  REAL free data — Copernicus CDSE Sentinel-2/1 + Landsat LST, Open-Meteo
  ERA5 climate, ISRIC SoilGrids profile — and **never fabricates** values;
  without CDSE credentials the satellite block returns an honest
  `credentials_required` status (climate + soil still return real values).
- Tracked as **W-001** (no-fabrication rule) in
  `docs/11_weaknesses_and_fixes.md`.

### Frontend routes (Phase 0)

All pages are reachable from the router (no orphan pages):

| Path | Page |
|---|---|
| `/` | HomePage |
| `/about` `/mission` `/features` `/pricing` `/blog` `/contact` `/docs` `/terms` `/privacy` | Public pages |
| `/hydroma-about` `/help` `/support` | Public info pages |
| `/login` `/register` `/forgot-password` | Auth |
| `/hydroma` | HydromaDashboard (protected) |
| `/virtual-lab` | VirtualLandLabPage (protected) — the simulator hub |
| `/simulator` `/simulators` | SimulatorDashboard / VisualSimulatorsPage (protected) |
| `/terrain` `/visualization-3d` | TerrainAnalysis / Visualization3D (protected) |
| `/models` `/models/rothc` `/models/swat` `/models/watershed` | ModelsLibrary + model pages (protected) |
| `/land-profiles` `/capability` | LandProfiles / CapabilityAssessment (protected) |
| `/monitoring` `/reports` `/data` `/api-docs` `/settings` `/profile` | Platform pages (protected) |

### Documentation

- `docs/en/00_master_plan.md`, `docs/fa/00_master_plan.md` – master plan
- `docs/10_quality_standards.md` – internal quality standards STD-001–015
- `docs/11_weaknesses_and_fixes.md` – known weaknesses W-001–021 with evidence
- `docs/12_30_year_strategy.md` – 30-year maintenance strategy (until 2055)

### Standards & governance

- **STD-001–015**: internal quality standards (calibration traceability,
  unit discipline, no fabricated values, bilingual parity, RLS-by-default).
- **W-001–021**: tracked weaknesses with evidence and fix status.
- **MRV**: all measurements, models, and satellite sources carry provenance
  metadata — `data_source`, `model_version`, `calibration_set_id`.
- **No fabrication rule**: if real data is unavailable, the API returns
  `credentials_required` or `simulated` (clearly labelled). Never invented.

### Contributing

1. Fork & create a feature branch (`feat/<scope>-<short-name>`).
2. Run `pytest` and `pnpm test` before opening a PR (frontend also has
   `pnpm test:e2e` for Playwright, `pnpm quality` for type-check + lint + format).
3. New scientific code must include: unit tests, a calibration reference,
   and a `provenance.json` for the dataset(s) used.
4. Translations: edit `apps/web/messages/<locale>.json`; all 14 official locales use the same key contract and explicit RTL metadata in `apps/web/src/i18n/routing.ts`.
5. Read `docs/11_weaknesses_and_fixes.md` to avoid repeating known issues.

### Project status

- **Phase 0**: UI scaffold + routing — ✅ complete
- **Phase 1**: real satellite path (Sentinel/ERA5/SoilGrids) — 🚧 in progress
- **Phase 2**: SWAT + RothC integration — ⏳ planned
- **Phase 3**: carbon marketplace MVP — ⏳ planned

See `docs/12_30_year_strategy.md` for the long-horizon roadmap (2025 → 2055).

---

## فارسی

اکو نوژین یک پلتفرم بین‌المللی و مبتنی بر استاندارد برای ترمیم اکوسیستم،
کشاورزی هوشمند، مدیریت آب و خاک، رفاه روستایی، حمایت از دامداران و عشایر،
انگیزه‌های کربن، بازارگاه و اکوتوریسم است.

هایدروما (HyDroMa) موتور علمی و محاسباتی اکو نوژین است — ترکیبی از مدل‌های
فیزیکی معین (ریچاردز، سن‌ونان، FAO-56، RUSLE، SWAT، RothC)، MRV مبتنی بر
ماهواره، و لایه اقتصاد/مالی برای ارائه شبیه‌سازی‌های تصمیم‌پایه در حوزه‌های
زمین، آب و کربن.

### معماری

```
┌──────────────────────────┐    ┌──────────────────────────┐
│  فرانت‌اند (Next.js/React19)│◄──►│  دروازه API (FastAPI)    │
│  deck.gl · MapLibre · 3D │    │  احراز هویت · نرخ · مسیریابی│
└──────────────────────────┘    └────────────┬─────────────┘
                                              │
        ┌─────────────────────────────────────┼─────────────────────────┐
        ▼                                     ▼                         ▼
  ┌───────────────┐                  ┌────────────────┐         ┌────────────────┐
│   HyDroMa     │                  │  میکروسرویس‌ها │         │   Supabase     │
│   (پایتون)    │◄────────────────►│  (۳۸ سرویس)    │◄───────►│ (پستگرس+RLS) │
  └───────┬───────┘                  └────────┬───────┘         └────────────────┘
          │                                   │
          ▼                                   ▼
  ┌───────────────┐                  ┌────────────────┐
  │  هسته C++20   │                  │  داده‌های خارجی│
  │  pybind11     │                  │  Sentinel · ERA5│
  └───────────────┘                  └────────────────┘
```

### پیش‌نیازها

- پایتون ۳.۱۲ به بالا
- Node.js ۲۰ به بالا و pnpm ۹ به بالا
- کامپایلر C++20 (MSVC 2022 / GCC 12+ / Clang 15+) — فقط برای بازسازی `cpp_core`
- SQLite برای توسعه محلی (پیش‌فرض)، یا PostgreSQL 15+ / Supabase برای یکپارچگی و تولید
- اختیاری: Podman Desktop برای اجرای محلی PostgreSQL/Redis/n8n
- (اختیاری) اعتبارنامه‌های Copernicus CDSE برای تایل‌های واقعی Sentinel-2/1

### متغیرهای محیطی

فایل `.env.example` را به `.env` کپی کنید و فقط سرویس‌های موردنیاز را مقداردهی کنید:

| متغیر | کاربرد | الزامی |
|---|---|---|
| `DATABASE_URL` | اتصال SQLite محلی یا PostgreSQL تولید | بله |
| `SUPABASE_URL` / `SUPABASE_KEY` | پایگاه‌داده و احراز هویت مدیریت‌شده | یکپارچگی تولید |
| `REDIS_URL` | Redis مدیریت‌شده برای rate limiting/cache | تولید |
| `NATS_URL` | NATS مدیریت‌شده در صورت فعال‌بودن event bus | حالت event bus |
| `CDSE_CLIENT_ID` / `CDSE_CLIENT_SECRET` | دسترسی واقعی Sentinel | فاز ۱ |
| `OPEN_METEO_URL` | اقلیم ERA5 (رایگان، بدون کلید) | توصیه‌شده |
| `JWT_SECRET` | امضای توکن احراز هویت | بله (تولید) |
| `TELEGRAM_BOT_TOKEN` | سرویس ربات تلگرام | اختیاری |

### ابزارهای استقرار

- توسعه محلی با محیط پایتون-native و SQLite انجام می‌شود؛ Docker لازم نیست.
- زیرساخت محلی اختیاری: Podman Desktop با `podman compose -f deploy/docker-compose.yml up -d`.
- `requirements-local-api.txt` — بسته‌های علمی موردنیاز routerهای API.
- `Dockerfile` — ایمیج کانتینر اختیاری برای دروازه API + موتور در staging/production.
- `render.yaml` — مانیفست‌های سرویس Render.com.
- `railway.toml` — پیکربندی استقرار Railway.app.
- `alembic.ini` + `alembic/`، `migrations/` — اجراکننده مهاجرت طرحواره.
- `dvc.yaml` — خط لوله DVC برای نسخه‌بندی داده/مدل.
- `pyproject.toml` — پیکربندی بسته پایتون (`econojin.egg-info`).
- `.pre-commit-config.yaml` — هوک‌های pre-commit (لینت، قالب‌بندی، اسکن اسرار).
- `pnpm-workspace.yaml` — فضای کاری monorepo با pnpm.

### شروع سریع

برای پروفایل محلی پیش‌فرض، Docker لازم نیست. SQLite و محیط پایتون-native
برای توسعه کافی است.

```bash
# محیط مجازی پایتون 3.12+ (uv اختیاری است)
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-local-api.txt
# یکپارچگی اختیاری: python -m pip install -r requirements-optional.txt

# Windows PowerShell: Copy-Item .env.example .env
# Linux/macOS: cp .env.example .env

# دروازه API (SQLite در .env.example تنظیم شده است)
python -m uvicorn services.api_gateway.main:app --reload --port 8000

# فرانت‌اند
pnpm -C apps/web install
pnpm -C apps/web dev

# تست‌ها
python -m pytest -q
```

برای تست یکپارچگی، `DATABASE_URL`، `REDIS_URL` و در صورت نیاز `NATS_URL` را
به سرویس‌های مدیریت‌شده متصل کنید. `requirements-local-api.txt` بسته‌های علمی
موردنیاز routerهای API را نصب می‌کند؛ `requirements-optional.txt` فقط برای
یکپارچگی‌های اضافی است. اگر همه وابستگی‌ها باید محلی اجرا شوند،
Podman Desktop را نصب کنید و دستور اختیاری
`podman compose -f deploy/docker-compose.yml up -d` را اجرا کنید.

### ساختار

| مسیر | کاربرد |
|---|---|
| `engine/hydroma/` | موتور علمی — ۳۰+ زیرماژول (خاک، اقلیم، سازگاری اقلیمی، هیدرولوژی/حوضه، فرسایش، کربن، MRV، ماهواره، سناریو، بیوفرتیلایزر، اقتصاد، آبیاری، آب زیرزمینی، مواد، گردشگری، زمین، زیرساخت، پشتیبانی تصمیم، بهینه‌سازی، شبیه‌سازی، کالیبراسیون، مدل‌ها، دستیار هوش مصنوعی، کارایی، ویژوال‌سازی، api، محاسبه، تحلیل‌ها، نمونه‌ها، ابزارها، هسته، داده، پیکربندی، پل C++) |
| `engine/cpp_core/` | هسته عددی C++20 (ریچاردز، سن‌ونان، FAO-56، RUSLE، نمونه‌برداری) با اتصال pybind11 |
| `engine/data/`، `engine/land/` | داده‌های کمکی موتور + ابزارهای پروفایل زمین |
| `services/` | ۳۸ میکروسرویس: admin، ai، analytics، api_gateway، audit، auth، bots، business_modules، carbon، content، data، data_manual، data_sources، design_engine، ecowallet، field_monitoring، land، landscape، ledger، livestock، map_engine، marketplace، mobile_monitoring، models، mrv، notification، ogc، quality، reporting، satellite، science، scientific_motors، security، simulation، supabase، telegram_bot، tourism، workflow |
| `frontend/` | SPA با Vite 8 + React 19 + TypeScript. کیت UI: antd 6 + tailwind-merge. ویژوال‌سازی: deck.gl 9، MapLibre GL، Three.js + drei + postprocessing، echarts، recharts. حالت: zustand، TanStack Query. فرم‌ها: react-hook-form + zod. انیمیشن: framer-motion. بومی‌سازی: react-i18next 17 (محلی‌ها: `en`، `fa`). تست: vitest 4 + Testing Library + Playwright + MSW. |
| `adapters/` | آداپتورهای سیستم‌های خارجی (اتصال به APIهای شخص ثالث) |
| `ml/` | مدل‌های یادگیری ماشین و خط لوله آموزش |
| `blockchain/`، `contracts/` | مؤلفه‌های زنجیره‌بلوکی و منابع قرارداد هوشمند |
| `supabase/` | دارایی‌های پروژه Supabase (سیاست‌های RLS، Edge Functions، داده‌های اولیه) |
| `database/`، `alembic/`، `migrations/` | طرحواره پایگاه‌داده و تاریخچه مهاجرت Alembic |
| `interfaces/` | رابط‌های فراگیر و قراردادهای مشترک |
| `scripts/` | اسکریپت‌های عملیاتی (بوت‌استرپ، عملیات، اصلاح یک‌بار) |
| `deploy/`، `demo/` | مانیفست‌های استقرار و نمونه‌های دمو |
| `testing_lab/`، `benchmarks/`، `data/` | ابزارهای آزمایشی، بنچمارک‌های کارایی، داده خام |
| `backups/` | عکس‌های پشتیبان |
| `docs/en`، `docs/fa` | مستندات دوزبانه (۰۰–۱۲) |
| `tests/` | مجموعه تست‌ها — زیرپوشه‌ها: `unit/`، `integration/`، `e2e/`، `fixtures/`، `benchmarks/`؛ به‌علاوه فایل‌های `test_*.py` و `challenge_*.py` در سطح بالا (مانند `challenge_25_scientists.py`، `strict_challenge_v2.py`) |
| `frontend/src/` | منبع SPA — روتر `App.tsx`، `features/`، `components/`، `lib/`، `i18n/`، `app/` |

### نکته صداقت درباره داده ماهواره

- ارائه‌دهنده قدیمی `earth_search` از مسیرهای فعال کد حذف شده است. هر بلاک
  باقی‌مانده با برچسب `data_source="simulated"` به‌صراحت علامت‌گذاری شده و
  هرگز به‌عنوان مشاهده واقعی ارائه نمی‌شود.
- **فاز ۱ (مسیر واقعی):** اندپوینت `POST /api/v1/satellite/real-land`
  داده‌های واقعی رایگان را تجمیع می‌کند — Copernicus CDSE Sentinel-2/1 +
  Landsat LST، اقلیم Open-Meteo ERA5، پروفایل ISRIC SoilGrids — و **هرگز**
  مقداری جعل نمی‌کند. در صورت نبود اعتبارنامه‌های CDSE، بلاک ماهواره مقدار
  صریح `credentials_required` برمی‌گرداند (اقلیم و خاک همچنان مقدار واقعی
  دارند).
- این موضوع با شناسه **W-001** (قانون عدم جعل) در
  `docs/11_weaknesses_and_fixes.md` پیگیری می‌شود.

### مستندات

- `docs/en/00_master_plan.md`، `docs/fa/00_master_plan.md` – نقشه جامع
- `docs/10_quality_standards.md` – استانداردهای کیفیت داخلی STD-001–015
- `docs/11_weaknesses_and_fixes.md` – نقاط ضعف شناخته‌شده W-001–021 همراه با شواهد
- `docs/12_30_year_strategy.md` – استراتژی نگهداری ۳۰ ساله (تا ۲۰۵۵)

### استانداردها و حاکمیت

- **STD-001–015**: استانداردهای کیفیت داخلی (ردیابی کالیبراسیون، انضباط
  واحدی، عدم جعل مقادیر، تقارن دوزبانه، RLS پیش‌فرض).
- **W-001–021**: نقاط ضعف ردگیری‌شده همراه با شواهد و وضعیت رفع.
- **MRV**: تمام اندازه‌گیری‌ها، مدل‌ها و منابع ماهواره‌ای حاوی فراداده
  Provenance هستند — `data_source`، `model_version`، `calibration_set_id`.
- **قانون عدم جعل**: در صورت عدم دسترسی به داده واقعی، API مقدار
  `credentials_required` یا `simulated` (با برچسب صریح) برمی‌گرداند. هرگز
  مقدار ساختگی.

### مشارکت

1. Fork کنید و یک شاخه ویژگی بسازید (`feat/<scope>-<short-name>`).
2. پیش از ارسال PR، `pytest` و `pnpm test` را اجرا کنید (فرانت‌اند همچنین
   `pnpm test:e2e` برای Playwright و `pnpm quality` برای type-check + lint +
   format دارد).
3. کد علمی جدید باید شامل: تست واحد، مرجع کالیبراسیون، و `provenance.json`
   برای داده‌های مصرفی باشد.
4. ترجمه‌ها: `apps/web/messages/<locale>.json` را ویرایش کنید؛ هر ۱۴ locale رسمی از قرارداد کلید مشترک و فرادادهٔ RTL صریح در `apps/web/src/i18n/routing.ts` استفاده می‌کنند.
5. برای جلوگیری از تکرار نقاط ضعف شناخته‌شده، `docs/` و Decision Freeze را مطالعه کنید.

### وضعیت پروژه

- **فاز ۰**: اسکفولد UI + مسیریابی — ✅ تکمیل
- **فاز ۱**: مسیر ماهواره واقعی (Sentinel/ERA5/SoilGrids) — 🚧 در حال انجام
- **فاز ۲**: یکپارچه‌سازی SWAT + RothC — ⏳ برنامه‌ریزی‌شده
- **فاز ۳**: MVP بازارگاه کربن — ⏳ برنامه‌ریزی‌شده

برای نقشه راه بلندمدت (۲۰۲۵ → ۲۰۵۵) به `docs/12_30_year_strategy.md` مراجعه کنید.

## Installation

```bash
git clone https://github.com/mahak1988/eco_nojin.git
cd eco_nojin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-local-api.txt
cp .env.example .env
uvicorn services.api_gateway.main:app --reload
```

## Usage

```bash
curl -X POST http://127.0.0.1:8000/api/v1/platform/analyze \
  -H "Content-Type: application/json" \
  -d '{"name": "Farm", "latitude": 35.6892, "longitude": 51.3890, "area_ha": 50.0}'
```

## API Documentation

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Windows Deployment (No Docker Required)

For Windows environments where Docker is not available, Eco Nojin can run as a
native Windows Service using **NSSM** (Non-Sucking Service Manager).

### Prerequisites

- Python 3.12+ installed
- Project venv activated: `.\.venv\Scripts\Activate.ps1`
- Dependencies installed: `pip install -r requirements.txt -r requirements-local-api.txt`

### Quick Setup

```powershell
# 1. Activate venv
.\.venv\Scripts\Activate.ps1

# 2. Install the service (one-time setup)
.\scripts\install-service.ps1

# 3. Start the service
.\scripts\start-service.ps1

# 4. Check status
.\scripts\service-status.ps1

# 5. View logs
.\scripts\service-logs.ps1
```

### Manual Run (Development)

```powershell
.\.venv\Scripts\Activate.ps1
.\scripts\start.ps1
```

### Install py-evm (Optional, for Blockchain tests)

```powershell
.\scripts\install-py-evm.ps1
```

### Service Management

| Command | Action |
|---------|--------|
| `.\scripts\start-service.ps1` | Start API Gateway |
| `.\scripts\stop-service.ps1` | Stop API Gateway |
| `.\scripts\service-status.ps1` | Check service status |
| `.\scripts\service-logs.ps1` | Tail live logs |

The service starts automatically on Windows boot. Logs are written to `logs/api-gateway.log`.

## License

MIT License
