# Eco Nojin (اکو نوژین) / HyDroMa (هیدروما)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![C++20](https://img.shields.io/badge/C++-20-00599C.svg)](https://isocpp.org/)
[![Services: 38](https://img.shields.io/badge/microservices-38-blueviolet.svg)](services/)
[![i18n: en, fa](https://img.shields.io/badge/i18n-en%20%C2%B7%20fa-green.svg)](frontend/src/i18n/locales/)

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
│  Frontend (Vite/React 19)│◄──►│  API Gateway (FastAPI)   │
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

- Python 3.11+
- Node.js 20+ and pnpm 9+
- A C++20 compiler (MSVC 2022 / GCC 12+ / Clang 15+) — only required to rebuild `cpp_core`
- PostgreSQL 15+ (or Supabase project) for persistence
- (Optional) Copernicus CDSE credentials for real Sentinel-2/1 tiles

### Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Purpose | Required |
|---|---|---|
| `SUPABASE_URL` / `SUPABASE_KEY` | Database + auth | Yes (prod) |
| `CDSE_CLIENT_ID` / `CDSE_CLIENT_SECRET` | Real Sentinel access | For Phase 1 |
| `OPEN_METEO_URL` | ERA5 climate (free, no key) | Recommended |
| `JWT_SECRET` | Auth token signing | Yes (prod) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot service | Optional |

### Deployment tooling

- `Dockerfile` — container image for the API gateway + engine.
- `render.yaml` — Render.com service manifests.
- `railway.toml` — Railway.app deployment config.
- `alembic.ini` + `alembic/`, `migrations/` — schema migration runner.
- `dvc.yaml` — DVC pipeline for data/model versioning.
- `pyproject.toml` — Python package config (`econojin.egg-info`).
- `.pre-commit-config.yaml` — pre-commit hooks (lint, format, secret scan).
- `pnpm-workspace.yaml` — pnpm monorepo workspace.

### Quick start

```bash
# Python 3.11+ virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# API gateway
uvicorn services.api_gateway.main:app --reload --port 8000

# Frontend (Vite + React 19 + TypeScript)
cd frontend
pnpm install
pnpm run dev

# Tests
pytest
```

### Layout

| Path | Purpose |
|---|---|
| `engine/hydroma/` | Scientific engine — 30+ submodules (soil, climate, climate_adaptation, hydrology/watershed, erosion, carbon, mrv, satellite, scenarios, biofertilizer, economics, irrigation, groundwater, materials, tourism, land, infrastructure, decision_support, optimization, simulation, calibration, models, ai_assistant, performance, visualization, api, calculation, analyses, examples, utils, core, data, config, cpp_bridge) |
| `engine/cpp_core/` | C++20 numerical core (Richards, Saint-Venant, FAO-56, RUSLE, sampling) with pybind11 bindings |
| `engine/data/`, `engine/land/` | Auxiliary engine data + land-profile utilities |
| `services/` | 38 microservices: admin, ai, analytics, api_gateway, audit, auth, bots, business_modules, carbon, content, data, data_manual, data_sources, design_engine, ecowallet, field_monitoring, land, landscape, ledger, livestock, map_engine, marketplace, mobile_monitoring, models, mrv, notification, ogc, quality, reporting, satellite, science, scientific_motors, security, simulation, supabase, telegram_bot, tourism, workflow |
| `frontend/` | Vite 8 + React 19 + TypeScript SPA. UI kit: antd 6 + tailwind-merge. Visualization: deck.gl 9, MapLibre GL, Three.js + drei + postprocessing, echarts, recharts. State: zustand, TanStack Query. Forms: react-hook-form + zod. Animation: framer-motion. i18n: react-i18next 17 (locales: `en`, `fa`). Testing: vitest 4 + Testing Library + Playwright + MSW. |
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
| `docs/en`, `docs/fa` | Bilingual documentation (00–12) |
| `tests/` | Test suites — subfolders: `unit/`, `integration/`, `e2e/`, `fixtures/`, `benchmarks/`; plus top-level `test_*.py` and `challenge_*.py` scripts (e.g. `challenge_25_scientists.py`, `strict_challenge_v2.py`) |
| `frontend/src/` | SPA source — `App.tsx` router, `features/`, `components/`, `lib/`, `i18n/`, `app/` |

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
4. Translations: edit `frontend/src/i18n/locales/<lang>.json` — currently
   `en` and `fa` are shipped. Additional locales (ar, ur, etc.) are tracked
   in `docs/`; new translations must include RTL metadata in the
   corresponding LanguageContext entry.
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
│  فرانت‌اند (Vite/React19)│◄──►│  دروازه API (FastAPI)    │
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

- پایتون ۳.۱۱ به بالا
- Node.js ۲۰ به بالا و pnpm ۹ به بالا
- کامپایلر C++20 (MSVC 2022 / GCC 12+ / Clang 15+) — فقط برای بازسازی `cpp_core`
- PostgreSQL ۱۵ به بالا (یا پروژه Supabase) برای ذخیره‌سازی
- (اختیاری) اعتبارنامه‌های Copernicus CDSE برای تایل‌های واقعی Sentinel-2/1

### متغیرهای محیطی

فایل `.env.example` را به `.env` کپی کنید و مقداردهی نمایید:

| متغیر | کاربرد | الزامی |
|---|---|---|
| `SUPABASE_URL` / `SUPABASE_KEY` | پایگاه‌داده + احراز هویت | بله (تولید) |
| `CDSE_CLIENT_ID` / `CDSE_CLIENT_SECRET` | دسترسی واقعی Sentinel | فاز ۱ |
| `OPEN_METEO_URL` | اقلیم ERA5 (رایگان، بدون کلید) | توصیه‌شده |
| `JWT_SECRET` | امضای توکن احراز هویت | بله (تولید) |
| `TELEGRAM_BOT_TOKEN` | سرویس ربات تلگرام | اختیاری |

### ابزارهای استقرار

- `Dockerfile` — ایمیج کانتینر برای دروازه API + موتور.
- `render.yaml` — مانیفست‌های سرویس Render.com.
- `railway.toml` — پیکربندی استقرار Railway.app.
- `alembic.ini` + `alembic/`، `migrations/` — اجراکننده مهاجرت طرحواره.
- `dvc.yaml` — خط لوله DVC برای نسخه‌بندی داده/مدل.
- `pyproject.toml` — پیکربندی بسته پایتون (`econojin.egg-info`).
- `.pre-commit-config.yaml` — هوک‌های pre-commit (لینت، قالب‌بندی، اسکن اسرار).
- `pnpm-workspace.yaml` — فضای کاری monorepo با pnpm.

### شروع سریع

```bash
# محیط مجازی پایتون 3.11+
python -m venv .venv
.venv\Scripts\activate          # ویندوز
pip install -r requirements.txt

# دروازه API
uvicorn services.api_gateway.main:app --reload --port 8000

# فرانت‌اند (Vite + React 19 + TypeScript)
cd frontend
pnpm install
pnpm run dev

# تست‌ها
pytest
```

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
4. ترجمه‌ها: `frontend/src/i18n/locales/<lang>.json` را ویرایش کنید — در
   حال حاضر `en` و `fa` ارائه شده‌اند. زبان‌های بیشتر (ar، ur و غیره) در
   `docs/` ردگیری می‌شوند؛ ترجمه‌های جدید باید فراداده RTL را در ورودی
   متناظر LanguageContext داشته باشند.
5. برای جلوگیری از تکرار نقاط ضعف شناخته‌شده، `docs/11_weaknesses_and_fixes.md`
   را مطالعه کنید.

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
pip install -r requirements.txt
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

## License

MIT License
