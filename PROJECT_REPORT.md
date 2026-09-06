# 📊 گزارش جامع پروژه — eco_nojin

- **تاریخ تولید:** 2026-09-06 04:23:03
- **مسیر:** `D:\eco_nojin`
- **محیط:** Python 3.12.10 | Windows 10
- **مدت اسکن:** 9.3 ثانیه
- **⭐ امتیاز سلامت:** **96/100** (گرید A 🟢)

## ۱) خلاصه اجرایی

| مورد | مقدار |
|---|---|
| کل فایل‌ها | 2,362 |
| حجم کل | 224.4 MB |
| خطوط کد واقعی | 97,979 |
| اندپوینت‌های API | 304 |
| کامپوننت‌های React (tsx) | 159 |
| کلاس‌های Model (تقریبی) | 318 |
| تست بک‌اند / فرانت‌اند | 83 / 1 فایل |
| یافته‌های امنیتی (بالا/متوسط) | 0 / 1 |

**استک:** FastAPI · Node.js · Pydantic · Pytest · Python · React · SQLAlchemy · Starlette · TypeScript · aiohttp

**ابزارها:** Dockerfile · Alembic (مهاجرت DB) · README.md · نمونه .env · Hardhat (قرارداد هوشمند) · GitHub Actions (1 workflow)

## ۲) وضعیت Git

- ریپازیتوری Git یافت نشد.

## ۳) ساختار پوشه‌ها (تا عمق 3)

```text
eco_nojin/  (55 فایل در ریشه)
├── .benchmarks/ (0 فایل)
├── .github/ (1 فایل)
│   └── workflows/ (1 فایل)
├── .turbo/ (0 فایل)
│   └── cache/ (0 فایل)
├── adapters/ (2 فایل)
├── alembic/ (18 فایل)
│   └── versions/ (15 فایل)
│       └── _archived/ (12 فایل)
├── analysis.json/ (1 فایل)
├── backups/ (1 فایل)
│   └── 20260901_061756/ (1 فایل)
├── benchmarks/ (2 فایل)
├── blockchain/ (3 فایل)
│   ├── config/ (1 فایل)
│   ├── contracts/ (1 فایل)
│   └── scripts/ (1 فایل)
├── contracts/ (11 فایل)
│   ├── scripts/ (1 فایل)
│   └── src/ (2 فایل)
├── data/ (208 فایل)
│   ├── _archived_excel_data/ (15 فایل)
│   ├── analyses/ (0 فایل)
│   │   └── topography/ (0 فایل)
│   │       └── test_site/ (0 فایل)
│   ├── analysis_results/ (3 فایل)
│   ├── calibration/ (0 فایل)
│   ├── copernicus/ (0 فایل)
│   │   ├── agera5/ (0 فایل)
│   │   ├── cams/ (0 فایل)
│   │   ├── era5_land/ (0 فایل)
│   │   └── seasonal/ (0 فایل)
│   ├── copernicus_cache/ (1 فایل)
│   ├── designs/ (0 فایل)
│   │   ├── irrigation/ (0 فایل)
│   │   └── structures/ (0 فایل)
│   ├── external/ (1 فایل)
│   ├── lab/ (1 فایل)
│   ├── lms/ (1 فایل)
│   ├── manual/ (4 فایل)
│   │   └── elevation_cache/ (3 فایل)
│   ├── maps/ (103 فایل)
│   │   ├── cache/ (17 فایل)
│   │   │   ├── dem/ (1 فایل)
│   │   │   ├── landcover/ (1 فایل)
│   │   │   ├── rainfall/ (1 فایل)
│   │   │   ├── runoff/ (1 فایل)
│   │   │   ├── soil/ (1 فایل)
│   │   │   └── vegetation/ (3 فایل)
│   │   ├── M-ERS_58cf8263/ (2 فایل)
│   │   ├── M-ERS_9e8a4043/ (2 فایل)
│   │   ├── M-ERS_edc5eb71/ (2 فایل)
│   │   ├── M-RUN_161021d8/ (2 فایل)
│   │   ├── M-RUN_97ea3b75/ (2 فایل)
│   │   ├── M-RUN_b9379f20/ (2 فایل)
│   │   ├── M-SLP_23f7f9b1/ (2 فایل)
│   │   ├── M-SLP_90dff977/ (2 فایل)
│   │   ├── M-SLP_ba108539/ (2 فایل)
│   │   ├── M-TOP_0b25d85f/ (3 فایل)
│   │   ├── M-TOP_1fbdec2f/ (3 فایل)
│   │   ├── M-TOP_3d6aeb1b/ (3 فایل)
│   │   ├── M-VEG_2c76b1f2_summer/ (2 فایل)
│   │   ├── M-VEG_523ff3d2_autumn/ (2 فایل)
│   │   ├── M-VEG_9baa06aa_spring/ (2 فایل)
│   │   ├── M-VEG_a9e27938_autumn/ (2 فایل)
│   │   ├── M-VEG_b3bdf24a_summer/ (2 فایل)
│   │   └── M-VEG_b614c448_spring/ (2 فایل)
│   ├── metadata/ (1 فایل)
│   ├── motors/ (8 فایل)
│   │   └── cache/ (8 فایل)
│   ├── mrv/ (3 فایل)
│   ├── processed/ (1 فایل)
│   ├── raw/ (1 فایل)
│   ├── reports/ (42 فایل)
│   ├── security/ (1 فایل)
│   └── swat_projects/ (17 فایل)
├── database/ (22 فایل)
│   ├── hub/ (10 فایل)
│   └── models/ (1 فایل)
├── DELIVERY/ (1 فایل)
├── deploy/ (3 فایل)
│   ├── ci/ (1 فایل)
│   ├── docker/ (1 فایل)
│   └── k8s/ (1 فایل)
├── docs/ (201 فایل)
│   ├── architecture/ (9 فایل)
│   │   └── local_first/ (9 فایل)
│   ├── backlog/ (1 فایل)
│   ├── en/ (37 فایل)
│   ├── fa/ (63 فایل)
│   │   ├── 22_research_reports/ (4 فایل)
│   │   └── 24_study_reports/ (4 فایل)
│   ├── hydroma/ (75 فایل)
│   │   ├── benchmark/ (10 فایل)
│   │   ├── benchmark_strict/ (1 فایل)
│   │   ├── benchmark_v10/ (0 فایل)
│   │   ├── benchmark_v11/ (0 فایل)
│   │   ├── benchmark_v13/ (1 فایل)
│   │   ├── benchmark_v14/ (1 فایل)
│   │   ├── benchmark_v9/ (1 فایل)
│   │   ├── bio_materials/ (11 فایل)
│   │   ├── figures/ (6 فایل)
│   │   ├── forecasts/ (13 فایل)
│   │   ├── integration/ (4 فایل)
│   │   └── regional_data/ (2 فایل)
│   └── security/ (1 فایل)
├── engine/ (392 فایل)
│   ├── cpp_core/ (168 فایل)
│   │   ├── bindings/ (2 فایل)
│   │   ├── build2/ (111 فایل)
│   │   │   ├── ALL_BUILD.dir/ (0 فایل)
│   │   │   ├── CMakeFiles/ (27 فایل)
│   │   │   ├── hydroma_advanced_tests.dir/ (11 فایل)
│   │   │   ├── hydroma_core.dir/ (11 فایل)
│   │   │   ├── hydroma_core_py.dir/ (16 فایل)
│   │   │   ├── hydroma_tests.dir/ (11 فایل)
│   │   │   ├── Release/ (5 فایل)
│   │   │   ├── RUN_TESTS.dir/ (0 فایل)
│   │   │   ├── Testing/ (1 فایل)
│   │   │   ├── x64/ (10 فایل)
│   │   │   └── ZERO_CHECK.dir/ (0 فایل)
│   │   ├── include/ (10 فایل)
│   │   │   └── hydroma/ (10 فایل)
│   │   ├── src/ (10 فایل)
│   │   └── tests/ (24 فایل)
│   ├── data/ (1 فایل)
│   ├── hydroma/ (173 فایل)
│   │   ├── ai_assistant/ (4 فایل)
│   │   ├── analyses/ (1 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── biofertilizer/ (14 فایل)
│   │   │   ├── api/ (0 فایل)
│   │   │   ├── data/ (3 فایل)
│   │   │   ├── models/ (0 فایل)
│   │   │   ├── repositories/ (0 فایل)
│   │   │   ├── services/ (0 فایل)
│   │   │   └── tests/ (3 فایل)
│   │   ├── calculation/ (3 فایل)
│   │   ├── calculations/ (1 فایل)
│   │   ├── calibration/ (4 فایل)
│   │   ├── carbon/ (2 فایل)
│   │   ├── climate/ (2 فایل)
│   │   ├── climate_adaptation/ (9 فایل)
│   │   ├── config/ (2 فایل)
│   │   ├── core/ (4 فایل)
│   │   ├── cpp_bridge/ (9 فایل)
│   │   ├── data/ (2 فایل)
│   │   ├── decision_support/ (1 فایل)
│   │   ├── economics/ (8 فایل)
│   │   ├── examples/ (1 فایل)
│   │   ├── groundwater/ (5 فایل)
│   │   │   └── tests/ (2 فایل)
│   │   ├── infrastructure/ (6 فایل)
│   │   ├── irrigation/ (2 فایل)
│   │   ├── materials/ (2 فایل)
│   │   ├── models/ (21 فایل)
│   │   │   ├── global_watchdog/ (6 فایل)
│   │   │   └── validation/ (2 فایل)
│   │   ├── mrv/ (12 فایل)
│   │   │   └── tests/ (1 فایل)
│   │   ├── optimization/ (1 فایل)
│   │   ├── performance/ (2 فایل)
│   │   ├── satellite/ (8 فایل)
│   │   │   ├── processors/ (2 فایل)
│   │   │   └── providers/ (4 فایل)
│   │   ├── scenario/ (1 فایل)
│   │   ├── scenarios/ (6 فایل)
│   │   ├── simulation/ (13 فایل)
│   │   │   └── runners/ (5 فایل)
│   │   ├── soil/ (16 فایل)
│   │   │   └── tests/ (2 فایل)
│   │   ├── utils/ (1 فایل)
│   │   ├── visualization/ (1 فایل)
│   │   └── watershed/ (4 فایل)
│   │       └── tests/ (1 فایل)
│   └── land/ (32 فایل)
│       ├── integration/ (14 فایل)
│       │   └── tests/ (6 فایل)
│       ├── reference/ (3 فایل)
│       └── tests/ (6 فایل)
├── frontend/ (801 فایل)
│   ├── .turbo/ (180 فایل)
│   │   └── cache/ (180 فایل)
│   ├── apps/ (91 فایل)
│   │   ├── dashboard/ (61 فایل)
│   │   │   ├── .turbo/ (2 فایل)
│   │   │   ├── public/ (1 فایل)
│   │   │   └── src/ (50 فایل)
│   │   └── web/ (30 فایل)
│   │       ├── .turbo/ (2 فایل)
│   │       ├── public/ (1 فایل)
│   │       └── src/ (19 فایل)
│   ├── packages/ (508 فایل)
│   │   ├── api/ (314 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (308 فایل)
│   │   ├── auth/ (10 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (6 فایل)
│   │   ├── charts/ (12 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (8 فایل)
│   │   ├── config/ (8 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (4 فایل)
│   │   ├── geo/ (12 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (8 فایل)
│   │   ├── i18n/ (15 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (11 فایل)
│   │   ├── models/ (14 فایل)
│   │   │   ├── .turbo/ (1 فایل)
│   │   │   └── src/ (10 فایل)
│   │   ├── ui/ (103 فایل)
│   │   │   └── src/ (101 فایل)
│   │   └── utils/ (20 فایل)
│   │       ├── .turbo/ (1 فایل)
│   │       ├── src/ (14 فایل)
│   │       └── tests/ (1 فایل)
│   └── tooling/ (11 فایل)
│       ├── biome/ (2 فایل)
│       ├── tailwind/ (4 فایل)
│       └── typescript/ (5 فایل)
├── interfaces/ (3 فایل)
├── migrations/ (3 فایل)
│   └── versions/ (0 فایل)
├── ml/ (4 فایل)
│   ├── features/ (1 فایل)
│   ├── models/ (1 فایل)
│   ├── notebooks/ (1 فایل)
│   └── registry/ (1 فایل)
├── reports/ (2 فایل)
├── requirements_proposal/ (6 فایل)
├── scripts/ (8 فایل)
│   ├── setup/ (3 فایل)
│   └── utils/ (4 فایل)
├── services/ (478 فایل)
│   ├── admin/ (12 فایل)
│   │   ├── api/ (2 فایل)
│   │   └── tests/ (3 فایل)
│   ├── ai/ (24 فایل)
│   │   └── prompts/ (10 فایل)
│   │       ├── admin/ (5 فایل)
│   │       └── support/ (5 فایل)
│   ├── analytics/ (12 فایل)
│   │   ├── api/ (2 فایل)
│   │   └── tests/ (3 فایل)
│   ├── api_gateway/ (76 فایل)
│   │   └── routers/ (65 فایل)
│   ├── audit/ (2 فایل)
│   ├── auth/ (12 فایل)
│   │   ├── api/ (2 فایل)
│   │   └── tests/ (3 فایل)
│   ├── bots/ (27 فایل)
│   │   ├── adapters/ (5 فایل)
│   │   ├── api/ (2 فایل)
│   │   ├── core/ (5 فایل)
│   │   ├── handlers/ (6 فایل)
│   │   └── tests/ (2 فایل)
│   ├── business_modules/ (17 فایل)
│   │   ├── blockchain/ (6 فایل)
│   │   ├── insurance/ (2 فایل)
│   │   ├── ussd/ (3 فایل)
│   │   └── voice/ (5 فایل)
│   ├── carbon/ (5 فایل)
│   ├── content/ (4 فایل)
│   ├── data/ (28 فایل)
│   │   ├── maps/ (15 فایل)
│   │   ├── motors/ (0 فایل)
│   │   │   └── cache/ (0 فایل)
│   │   └── reports/ (13 فایل)
│   ├── data_manual/ (3 فایل)
│   ├── data_sources/ (2 فایل)
│   ├── design_engine/ (2 فایل)
│   ├── ecowallet/ (7 فایل)
│   ├── field_monitoring/ (2 فایل)
│   ├── land/ (7 فایل)
│   │   └── tests/ (3 فایل)
│   ├── landscape/ (13 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (1 فایل)
│   │   ├── models/ (2 فایل)
│   │   ├── repositories/ (1 فایل)
│   │   ├── schemas/ (1 فایل)
│   │   ├── services/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── ledger/ (6 فایل)
│   │   └── tests/ (1 فایل)
│   ├── livestock/ (15 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── economics/ (1 فایل)
│   │   ├── nutrition/ (2 فایل)
│   │   ├── simulators/ (6 فایل)
│   │   └── tests/ (2 فایل)
│   ├── map_engine/ (23 فایل)
│   │   ├── api/ (2 فایل)
│   │   ├── fetchers/ (7 فایل)
│   │   ├── pipelines/ (6 فایل)
│   │   ├── processors/ (1 فایل)
│   │   └── tests/ (2 فایل)
│   ├── marketplace/ (16 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (1 فایل)
│   │   ├── models/ (2 فایل)
│   │   ├── repositories/ (1 فایل)
│   │   ├── schemas/ (1 فایل)
│   │   ├── services/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── mobile_monitoring/ (2 فایل)
│   ├── models/ (8 فایل)
│   ├── mrv/ (4 فایل)
│   ├── notification/ (5 فایل)
│   │   └── tests/ (1 فایل)
│   ├── ogc/ (2 فایل)
│   ├── quality/ (0 فایل)
│   │   ├── standards/ (0 فایل)
│   │   └── tests/ (0 فایل)
│   ├── reporting/ (12 فایل)
│   │   ├── api/ (2 فایل)
│   │   └── tests/ (3 فایل)
│   ├── satellite/ (15 فایل)
│   │   ├── api/ (2 فایل)
│   │   └── tests/ (2 فایل)
│   ├── science/ (5 فایل)
│   ├── scientific_motors/ (34 فایل)
│   ├── security/ (13 فایل)
│   │   └── tests/ (1 فایل)
│   ├── simulation/ (18 فایل)
│   │   ├── adapters/ (8 فایل)
│   │   ├── api/ (2 فایل)
│   │   ├── engine/ (2 فایل)
│   │   └── tests/ (2 فایل)
│   ├── supabase/ (5 فایل)
│   │   └── migrations/ (2 فایل)
│   ├── telegram_bot/ (17 فایل)
│   │   ├── api/ (2 فایل)
│   │   └── tests/ (2 فایل)
│   ├── tourism/ (13 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (1 فایل)
│   │   ├── models/ (2 فایل)
│   │   ├── repositories/ (1 فایل)
│   │   ├── schemas/ (1 فایل)
│   │   ├── services/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   └── workflow/ (5 فایل)
│       └── tests/ (1 فایل)
├── supabase/ (9 فایل)
│   └── migrations/ (9 فایل)
│       └── legacy/ (1 فایل)
├── testing_lab/ (5 فایل)
│   ├── benchmarks/ (1 فایل)
│   ├── fixtures/ (0 فایل)
│   │   ├── climate_data/ (0 فایل)
│   │   └── soil_profiles/ (0 فایل)
│   ├── integration_tests/ (1 فایل)
│   ├── reports/ (0 فایل)
│   └── scientific_tests/ (1 فایل)
└── tests/ (122 فایل)
    ├── benchmarks/ (3 فایل)
    ├── e2e/ (1 فایل)
    ├── fixtures/ (1 فایل)
    ├── integration/ (31 فایل)
    │   └── land/ (2 فایل)
    └── unit/ (39 فایل)
        └── land/ (2 فایل)
… و 17 زیرپوشه در عمق بیشتر
```

## ۴) آمار فایل‌ها بر اساس نوع

| پسوند | تعداد | حجم |
|---|---:|---:|
| `.py` | 731 | 3.7 MB |
| `.ts` | 371 | 350.5 KB |
| `.json` | 341 | 5.2 MB |
| `.tsx` | 159 | 368.0 KB |
| `.md` | 156 | 1.1 MB |
| `.bak` | 123 | 850.4 KB |
| `.tif` | 88 | 53.3 MB |
| `.zst` | 60 | 27.1 MB |
| `.tlog` | 50 | 310.3 KB |
| `.cpp` | 39 | 188.4 KB |
| `(بدون پسوند)` | 36 | 390.8 KB |
| `.txt` | 29 | 78.1 KB |
| `.sql` | 13 | 42.4 KB |
| `.log` | 12 | 3.8 KB |
| `.csv` | 11 | 4.9 MB |
| `.hpp` | 10 | 28.7 KB |
| `.tsbuildinfo` | 10 | 354.7 KB |
| `.vcxproj` | 9 | 226.7 KB |
| `.recipe` | 9 | 3.8 KB |
| `.yaml` | 8 | 824.9 KB |
| `.lastbuildstate` | 8 | 1.3 KB |
| `.png` | 7 | 440.4 KB |
| `.xlsx` | 7 | 15.9 MB |
| `.filters` | 7 | 4.7 KB |
| `.cmake` | 5 | 12.2 KB |

## ۵) بزرگ‌ترین فایل‌ها

| حجم | فایل |
|---:|---|
| 34.5 MB | `data/eco_nojin_master.duckdb` ⚠️ |
| 11.2 MB | `engine/cpp_core/build2/hydroma_core_py.dir/Release/hydroma_core.cp311-win_amd64.iobj` ⚠️ |
| 11.2 MB | `engine/cpp_core/build2/hydroma_core_py.dir/Release/hydroma_core.cp312-win_amd64.iobj` ⚠️ |
| 10.3 MB | `data/maps/M-TOP_3d6aeb1b/contours.gpkg` ⚠️ |
| 10.3 MB | `data/maps/M-TOP_0b25d85f/contours.gpkg` ⚠️ |
| 10.2 MB | `data/maps/M-TOP_1fbdec2f/contours.gpkg` ⚠️ |
| 8.4 MB | `data/manual/eco_manual_v1.sqlite` ⚠️ |
| 6.5 MB | `data/eco_nojin.duckdb` ⚠️ |
| 6.4 MB | `data/maps/M-VEG_523ff3d2_autumn/vegetation.tif` ⚠️ |
| 6.4 MB | `data/maps/M-VEG_a9e27938_autumn/vegetation.tif` ⚠️ |
| 6.4 MB | `data/maps/M-VEG_2c76b1f2_summer/vegetation.tif` ⚠️ |
| 6.4 MB | `data/maps/M-VEG_b3bdf24a_summer/vegetation.tif` ⚠️ |
| 6.4 MB | `data/maps/M-VEG_b614c448_spring/vegetation.tif` ⚠️ |
| 6.4 MB | `data/maps/M-VEG_9baa06aa_spring/vegetation.tif` ⚠️ |
| 5.6 MB | `data/_archived_excel_data/01-03_climate_history_2000_2024.xlsx` ⚠️ |

## ۶) وابستگی‌ها

### فرانت‌اند — package.json

| پکیج | نسخه | نوع |
|---|---|---|
| @biomejs/biome | ^1.9.4 | dev |
| @changesets/cli | ^2.27.1 | dev |
| @types/node | ^20.16.5 | dev |
| orval | ^8.28.1 | dev |
| turbo | ^2.3.3 | dev |
| typescript | ^5.9.3 | dev |

### اسکریپت‌های npm

| دستور | اسکریپت |
|---|---|
| `dev` | `turbo run dev` |
| `build` | `turbo run build` |
| `lint` | `turbo run lint` |
| `type-check` | `turbo run type-check` |
| `test` | `turbo run test` |
| `format` | `biome format --write .` |
| `format:check` | `biome format .` |
| `lint:fix` | `biome lint --write .` |
| `clean` | `turbo run clean && rm -rf node_modules .turbo` |
| `changeset` | `changeset` |
| `version-packages` | `changeset version` |

### بک‌اند — requirements.txt

- ﻿# ============================================================
- about-time==4.2.1
- aenum==3.1.17
- affine==3.0.0
- aiofiles==25.1.0
- aiogram==3.30.0
- aiohappyeyeballs==2.7.1
- aiohttp==3.14.3
- aiosignal==1.4.0
- aiosqlite==0.22.1
- alembic==1.19.1
- alive-progress==3.3.0
- annotated-doc==0.0.5
- annotated-types==0.8.0
- anyio==4.14.2
- aquacrop==3.1.0
- arabic-reshaper==3.0.1
- astroid==4.0.4
- attrs==26.1.0
- autoflake==2.4.0
- autograd==1.9.1
- bandit==1.8.0
- bcrypt==4.0.1
- bitarray==3.10.1
- black==26.5.1
- blosc2==4.11.0
- bmipy==2.0.1
- boolean.py==5.0
- CacheControl==0.14.4
- cdsapi==0.7.7
- certifi==2026.7.22
- cffi==2.1.1
- cfgv==3.5.0
- cftime==1.6.5
- charset-normalizer==3.5.1
- ckzg==2.1.8
- clarabel==0.11.1
- click==8.5.0
- click-plugins==1.1.1.2
- cligj==0.7.2
- cma==4.4.4
- colorama==0.4.6
- contourpy==1.3.3
- coverage==7.15.4
- cryptography==50.0.0
- cvxpy==1.9.2
- cycler==0.12.1
- cyclonedx-python-lib==7.6.2
- cyclopts==4.23.2
- cytoolz==1.1.0
- dacite==1.9.2
- dataclasses-json==0.6.7
- defusedxml==0.7.1
- Deprecated==1.3.1
- deprecation==2.1.0
- dill==0.4.1
- distlib==0.4.3
- dnspython==2.8.0
- docstring_parser==0.18.0
- duckdb==1.5.5
- duckdb_engine==0.17.0
- earthengine-api==1.7.41
- ecdsa==0.19.2
- ecmwf-datastores-client==0.5.3
- email-validator==2.3.0
- eradicate==3.0.1
- et_xmlfile==2.0.0
- eth-account==0.14.0
- eth-hash==0.8.0
- eth-keyfile==0.10.0
- eth-keys==0.8.0
- eth-rlp==3.0.0
- eth-tester==0.14.0b1
- eth-typing==6.0.0
- eth-utils==6.0.0
- eth_abi==6.0.0
- Faker==40.37.0
- fastapi==0.141.1
- filelock==3.32.4
- filetype==1.2.0
- fiona==1.10.1
- fonttools==4.63.0
- fpdf2==2.8.8
- freetype-py==2.5.1
- frozenlist==1.8.0
- fsspec==2026.7.0
- GeoAlchemy2==0.20.0
- geojson==3.3.0
- geopandas==1.1.4
- glcontext==3.0.0
- google-api-core==2.34.0
- google-api-python-client==2.199.0
- google-auth==2.57.0
- google-auth-httplib2==0.4.2
- google-cloud-core==2.7.0
- google-cloud-storage==3.13.1
- google-crc32c==1.8.0
- google-resumable-media==2.10.2
- googleapis-common-protos==1.75.2
- graphemeu==0.7.2
- greenlet==3.5.5
- h11==0.16.0
- h2==4.4.1
- HBV==1.5.2
- hexbytes==2.0.0
- hf-xet==1.6.0
- highspy==1.15.1
- hpack==4.2.0
- hsluv==5.0.4
- html5lib==1.1
- httpcore==1.0.9
- httplib2==0.32.0
- httpx==0.28.1
- huggingface_hub==1.28.0
- hyperframe==6.1.0
- hypothesis==6.122.0
- identify==2.6.19
- idna==3.19
- ImageHash==4.3.2
- ImageIO==2.37.4
- importlib_metadata==9.0.0
- iniconfig==2.3.0
- isort==5.13.2
- jellyfish==1.2.1
- Jinja2==3.1.6
- joblib==1.5.3
- jsonschema==4.26.0
- jsonschema-specifications==2025.9.1
- keybert==0.9.0
- kiwisolver==1.5.0
- landlab==2.11.0
- langdetect==1.0.9
- lazy-loader==0.5
- libcst==1.9.0
- license-expression==30.4.4
- llvmlite==0.45.1
- looseversion==1.3.0
- magic-filter==1.0.12
- Mako==1.4.1
- markdown-it-py==4.2.0
- MarkupSafe==3.0.3
- marshmallow==3.26.2
- matplotlib==3.10.0
- mccabe==0.7.0
- mdurl==0.1.2
- minify_html==0.18.1
- moderngl==5.12.0
- moocore==0.3.2
- more-itertools==11.1.0
- mpmath==1.3.0
- msgpack==1.2.1
- multidict==6.7.1
- multimethod==1.12
- multiprocess==0.70.19
- multiurl==0.3.9
- mypy==1.13.0
- mypy_extensions==1.1.0
- narwhals==2.25.0
- ndindex==1.10.1
- netCDF4==1.7.4
- networkx==3.6.1
- nodeenv==1.10.0
- numba==0.62.1
- numexpr==2.14.2
- numpy==2.3.5
- oauthlib==3.3.1
- openet-core==0.8.1
- openpyxl==3.1.5
- osmnx==2.1.1
- osqp==1.1.3
- packageurl-python==0.17.6
- packaging==26.3
- paho-mqtt==2.1.0
- pandas==2.3.3
- parsimonious==0.10.0
- passlib==1.7.4
- pathspec==1.1.1
- patsy==1.0.2
- phik==0.12.5
- pillow==12.3.0
- pip-api==0.0.34
- pip-requirements-parser==32.0.1
- pip_audit==2.7.3
- planetary-computer==1.0.0
- platformdirs==4.11.4
- pluggy==1.6.0
- polars==1.44.1
- polars-runtime-32==1.44.1
- pooch==1.9.0
- postgrest==2.31.0
- pre_commit==4.0.1
- propcache==0.5.2
- proto-plus==1.28.4
- protobuf==7.36.0
- psycopg==3.3.4
- psycopg-binary==3.3.4
- PuLP==3.3.2
- puremagic==2.2.0
- py-cpuinfo==9.0.0
- py-ecc==8.0.0
- py-richdem==2.2.0rc2
- py-serializable==1.1.2
- pyasn1==0.6.4
- pyasn1_modules==0.4.2
- pycln==2.6.0
- pycparser==3.0
- pycryptodome==3.23.0
- pydantic==2.13.4
- pydantic-settings==2.15.0
- pydantic_core==2.46.4
- pydocstyle==6.3.0
- pyfao56==1.4.3
- pyflakes==3.4.0
- pyglet==2.1.16
- Pygments==2.21.0
- PyJWT==2.13.0
- pylint==4.0.7
- pymoo==0.6.2
- pymupdf==1.28.2
- pyogrio==0.13.0
- pyomo==6.10.1
- pyparsing==3.3.2
- pypdf==6.16.2
- pyproj==3.7.2
- pyRothC==0.0.4
- pysheds==0.5
- pyshp==3.1.6
- pystac==1.15.2
- pystac-client==0.9.0
- pystac-core==1.15.2
- pystac-ext-classification==2.0.1
- pystac-ext-datacube==2.2.1
- pystac-ext-eo==1.1.1
- pystac-ext-file==2.1.1
- pystac-ext-grid==1.1.1
- pystac-ext-item-assets==1.0.1
- pystac-ext-label==1.0.2
- pystac-ext-mgrs==1.0.1
- pystac-ext-mlm==1.4.1
- pystac-ext-pointcloud==1.0.1
- pystac-ext-projection==2.0.1
- pystac-ext-raster==1.1.1
- pystac-ext-render==2.0.0
- pystac-ext-sar==1.0.1
- pystac-ext-sat==1.0.1
- pystac-ext-scientific==1.0.1
- pystac-ext-storage==2.0.1
- pystac-ext-table==1.2.1
- pystac-ext-timestamps==1.1.1
- pystac-ext-version==1.2.1
- pystac-ext-view==1.0.1
- pystac-ext-xarray-assets==1.0.1
- pySWATPlus==1.3.0
- pytest==9.1.1
- pytest-asyncio==1.4.0
- pytest-cov==6.0.0
- python-bidi==0.6.11
- python-dateutil==2.9.0.post0
- python-discovery==1.5.3
- python-dotenv==1.2.3
- python-jose==3.5.0
- python-multipart==0.0.32
- pytokens==0.4.1
- pytz==2026.3.post1
- pyunormalize==17.0.0
- pyupgrade==3.19.0
- pyvista==0.48.4
- pyvistaqt==0.12.0
- PyWavelets==1.9.0
- pywin32==312
- pywr==1.31.1
- PyYAML==6.0.3
- qdldl==0.1.9.post1
- QtPy==2.4.3
- rasterio==1.5.1
- realtime==2.31.0
- referencing==0.37.0
- regex==2026.7.19
- reportlab==5.0.1
- requests==2.34.2
- requests-oauthlib==2.0.0
- requireit==0.11.0
- rfactor==0.1.5
- rich==15.0.0
- rich-click==1.9.8
- rich-rst==2.1.0
- rioxarray==0.23.0
- rlp==5.0.0
- rpds-py==2026.6.3
- rsa==4.9.1
- ruff==0.11.2
- safetensors==0.8.0
- SALib==1.5.2
- scikit-image==0.26.0
- scikit-learn==1.9.0
- scikit-surprise==1.1.5
- scipy==1.16.3
- scooby==0.11.2
- scs==3.2.11
- seaborn==0.13.2
- segtok==1.5.11
- semantic-version==2.10.0
- sentence-transformers==6.0.0
- sentinelhub==3.11.5
- setuptools==84.0.0
- shapely==2.1.2
- shellingham==1.5.4
- six==1.17.0
- snowballstemmer==3.1.1
- sortedcontainers==2.4.0
- sparsediffpy==0.3.0
- SQLAlchemy==2.0.52
- starlette==1.6.0
- statsmodels==0.14.6
- stevedore==5.9.1
- storage3==2.31.0
- StrEnum==0.4.15
- structlog==26.1.0
- supabase==2.31.0
- supabase-auth==2.31.0
- supabase-functions==2.31.0
- sympy==1.14.0
- tables==3.11.1
- tabulate==0.10.0
- threadpoolctl==3.6.0
- tifffile==2026.8.23
- tokenize_rt==6.2.0
- tokenizers==0.23.1
- toml==0.10.2
- tomli==2.4.1
- tomli_w==1.2.0
- tomlkit==0.15.1
- toolz==1.1.0
- torch==2.13.0
- tqdm==4.70.0
- trame==3.13.2
- trame-client==3.13.6
- trame-common==1.2.7
- trame-server==3.14.0
- transformers==5.16.1
- typeguard==4.6.0
- typer==0.27.1
- types-requests==2.33.0.20260712
- typing-inspect==0.9.0
- typing-inspection==0.4.4
- typing_extensions==4.16.0
- tzdata==2026.3
- uritemplate==4.2.0
- urllib3==2.7.0
- utm==0.9.0
- uvicorn==0.52.4
- virtualenv==21.7.5
- visions==0.8.1
- vispy==0.16.2
- vtk==9.6.2
- vulture==2.11
- web3==7.16.0
- webencodings==0.6.1
- websockets==15.0.1
- wordcloud==1.9.6
- wrapt==2.3.0
- wslink==2.5.7
- xarray==2026.7.0
- yake==0.7.3
- yarl==1.24.5
- ydata-profiling==4.18.4
- zipp==4.1.0
- pyproject.toml: ✅ موجود
- lockfile فرانت‌اند: ✅ pnpm-lock.yaml

## ۷) بک‌اند (API)

- تعداد اندپوینت‌ها: **304** — DELETE×4 · GET×173 · POST×123 · PUT×4
- WebSocket: 1 اندپوینت — `/ws/chat`

| متد | مسیر | فایل |
|---|---|---|
| GET | `/dashboard/overview` | `services/admin/nojin_admin.py` |
| GET | `/projects` | `services/admin/nojin_admin.py` |
| GET | `/inventory` | `services/admin/nojin_admin.py` |
| POST | `/projects/{project_id}/verify` | `services/admin/nojin_admin.py` |
| POST | `/credits/issue` | `services/admin/nojin_admin.py` |
| GET | `/reports/monthly/{year}/{month}` | `services/admin/nojin_admin.py` |
| GET | `/health` | `services/admin/api/__init__.py` |
| GET | `/status` | `services/admin/api/__init__.py` |
| GET | `/stats` | `services/admin/api/__init__.py` |
| GET | `/audit-logs` | `services/admin/api/__init__.py` |
| GET | `/dashboard` | `services/analytics/api/__init__.py` |
| GET | `/sales-summary` | `services/analytics/api/__init__.py` |
| GET | `/tourism-metrics` | `services/analytics/api/__init__.py` |
| GET | `/landscape-metrics` | `services/analytics/api/__init__.py` |
| GET | `/` | `services/api_gateway/main.py` |
| GET | `/health` | `services/api_gateway/main.py` |
| GET | `/ready` | `services/api_gateway/main.py` |
| GET | `/debug/routes` | `services/api_gateway/main.py` |
| GET | `/health` | `services/api_gateway/main.py` |
| GET | `/health` | `services/api_gateway/routers/admin.py` |
| GET | `/users` | `services/api_gateway/routers/admin.py` |
| POST | `/users/{user_id}/block` | `services/api_gateway/routers/admin.py` |
| POST | `/users/{user_id}/unblock` | `services/api_gateway/routers/admin.py` |
| GET | `/audit` | `services/api_gateway/routers/admin.py` |
| GET | `/content` | `services/api_gateway/routers/admin.py` |
| POST | `/content` | `services/api_gateway/routers/admin.py` |
| PUT | `/content/{item_id}` | `services/api_gateway/routers/admin.py` |
| POST | `/content/{item_id}/publish` | `services/api_gateway/routers/admin.py` |
| DELETE | `/content/{item_id}` | `services/api_gateway/routers/admin.py` |
| GET | `/content/{item_id}/versions` | `services/api_gateway/routers/admin.py` |
| GET | `/content/{item_id}/translations` | `services/api_gateway/routers/admin.py` |
| POST | `/content/{item_id}/translate` | `services/api_gateway/routers/admin.py` |
| POST | `/content/generate-draft` | `services/api_gateway/routers/admin.py` |
| POST | `/content/{item_id}/schedule` | `services/api_gateway/routers/admin.py` |
| POST | `/content/{item_id}/cancel-schedule` | `services/api_gateway/routers/admin.py` |
| GET | `/bots` | `services/api_gateway/routers/admin.py` |
| POST | `/bots/{key}/toggle` | `services/api_gateway/routers/admin.py` |
| GET | `/errors` | `services/api_gateway/routers/admin.py` |
| POST | `/errors/{error_id}/ack` | `services/api_gateway/routers/admin.py` |
| GET | `/settings` | `services/api_gateway/routers/admin.py` |
| … | … | و 264 مورد دیگر |

## ۸) فرانت‌اند

- کامپوننت‌های TSX: 159
- lazy(): 0 | Suspense: 0 | Route: 0
- کیفیت TS: `any`×0 | ts-ignore×0 | eslint-disable×1 | inline-style×24
- هوک‌ها: useEffect×21 | useState×123
- فایل‌های تست فرانت‌اند: 1

## ۹) امنیت

| شدت | قانون | فایل:خط |
|---|---|---|
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `frontend/packages/ui/src/primitives/rich-text-editor.tsx:65` |
| کم | ذخیرهٔ احتمالی توکن در localStorage | `frontend/packages/auth/src/store.ts:28` |
| اطلاع | کلیدهای حساس در فایل env: ACCESS_TOKEN_EXPIRE_MINUTES, ADS_API_KEY, AI_LLM_KEY, ALCHEMY_API_KEY, ALLOW_CREDENTIALS, BALE_TOKEN, BOT_TOKEN, CDSE_CLIENT_SECRET | `.env` |
| اطلاع | کلیدهای حساس در فایل env: AI_LLM_KEY, COPERNICUS_ADS_API_KEY, COPERNICUS_CDS_API_KEY, JWT_SECRET_KEY, SUPABASE_ACCESS_TOKEN, SUPABASE_ANON_KEY, SUPABASE_KEY, TELEGRAM_BOT_TOKEN | `.env.example` |
| اطلاع | کلیدهای حساس در فایل env: ANTHROPIC_API_KEY, APP_SECRET_KEY, BLOCKCHAIN_PRIVATE_KEY, CORS_ALLOW_CREDENTIALS, ECO_TOKEN_CONTRACT_ADDRESS, JWT_SECRET, OPENAI_API_KEY, OPENWEATHERMAP_API_KEY | `.env.template` |
| اطلاع | کلیدهای حساس در فایل env: POLYGONSCAN_API_KEY, PRIVATE_KEY | `contracts/.env` |
| اطلاع | کلیدهای حساس در فایل env: POLYGONSCAN_API_KEY, PRIVATE_KEY | `contracts/.env.example` |

> 🔐 مقادیر محرمانه به متغیر محیطی منتقل و از تاریخچهٔ گیت پاک‌سازی شوند. این اسکن جایگزین ابزارهای تخصصی (`gitleaks`, `bandit`, `trufflehog`) نیست.

## ۱۰) کیفیت کد پایتون (AST)

- فایل‌های تحلیل‌شده: 715 | توابع: 4216 | کلاس‌ها: 1094
- ❌ خطای سینتکس در 1 فایل:
  - `services/ai/admin_assistant.py:370 — unexpected indent`
- پوشش docstring: **61٪** (3264/5310)
- توابع دارای return annotation: **49٪**
- بیشترین آرگومان تابع: 14 → `services/tourism/service.py:89 → create_tour()`
- طولانی‌ترین تابع: 330 خط → `engine/hydroma/biofertilizer/advanced_calculator.py:369 → analyze()`

### پیچیدگی شناختی برتر (تقریبی)

| پیچیدگی | فایل |
|---:|---|
| 210 | `eco_chaos_test_v2.py` |
| 205 | `tests/strict_challenge_v2.py` |
| 164 | `engine/hydroma/biofertilizer/advanced_calculator.py` |
| 133 | `services/conftest.py` |
| 120 | `services/satellite/sentinel2_provider.py` |
| 113 | `services/api_gateway/routers/admin.py` |
| 104 | `services/api_gateway/routers/nojin.py` |
| 102 | `style_design_diagnostic.py` |
| 96 | `services/satellite/copernicus.py` |
| 95 | `engine/land/integration/soil_integrator.py` |

### پرتکرارترین ماژول‌های importشده (شامل ماژول‌های داخلی)

`services`×457, `engine`×371, `typing`×215, `database`×210, `sqlalchemy`×156, `__future__`×148, `datetime`×135, `numpy`×109, `fastapi`×104, `pytest`×92, `logging`×88, `dataclasses`×81, `pathlib`×77, `pydantic`×70, `structlog`×68

## ۱۱) پایگاه‌داده و ORM

- سیستم‌های شناسایی‌شده: Alembic, PostgreSQL, Redis, SQLAlchemy, SQLite
- کلاس‌های Model (تقریبی): 318
- فایل‌های مهاجرت (migrations): 17

## ۱۲) تکرار کد (تقریبی)

- گروه‌های بلوک تکراری (≥۸ خط یکسان): **126**
  - `services/scientific_motors/aquacrop.py:109` · `services/scientific_motors/hecras.py:61` · `services/scientific_motors/land_capability.py:117` · `services/scientific_motors/rothc.py:81`
  - `tests/integration/test_admin_finalize.py:5` · `tests/integration/test_admin_models.py:5` · `tests/integration/test_content_phase6.py:5` · `tests/integration/test_phase6_remainder.py:5`
  - `services/livestock/simulators/goat.py:61` · `services/livestock/simulators/poultry.py:57` · `services/livestock/simulators/sheep.py:65`
  - `services/livestock/simulators/goat.py:65` · `services/livestock/simulators/poultry.py:61` · `services/livestock/simulators/sheep.py:69`
  - `services/scientific_motors/aquacrop.py:101` · `services/scientific_motors/hecras.py:53` · `services/scientific_motors/rothc.py:73`
  - `services/scientific_motors/aquacrop.py:105` · `services/scientific_motors/hecras.py:57` · `services/scientific_motors/rothc.py:77`
  - `tests/test_land_profile_challenging.py:5` · `tests/test_land_profile_comprehensive.py:5` · `tests/test_land_profile_service.py:1`
  - `engine/hydroma/biofertilizer/repositories.py:17` · `engine/hydroma/biofertilizer/repositories.py:85`

## ۱۳) مستندات و لایسنس

- README (`README.md`): 379 خط، 38 سرفصل، 6 بلوک کد
- بخش‌های یافت‌شده: نصب, اجرا, تست, مشارکت
- لایسنس: MIT
- پوشهٔ docs: ✅ 201 فایل
- CHANGELOG: — | CONTRIBUTING: —

## ۱۴) فعالیت و تازگی

- فایل‌های تغییر‌کرده در ۷ روز اخیر: 1,269
- فایل‌های تغییر‌کرده در ۳۰ روز اخیر: 1,091
- جدیدترین فایل: `frontend/apps/dashboard/tsconfig.tsbuildinfo`
- فایل‌های خالی: 30 | پوشه‌های خالی: 49

## ۱۵) معماری و نقاط ورود

- سبک شناسایی‌شده: **میکروسرویس**
- پوشه‌های سطح بالا: `.benchmarks`, `.github`, `.turbo`, `DELIVERY`, `adapters`, `alembic`, `analysis.json`, `backups`, `benchmarks`, `blockchain`, `contracts`, `data`, `database`, `deploy`, `docs`, `engine`, `frontend`, `interfaces`, `migrations`, `ml`, `reports`, `requirements_proposal`, `scripts`, `services`, `supabase`, `testing_lab`, `tests`
- نقاط ورود: —

## ۱۶) هشدارها و سلامت پروژه

- ✅ `.gitignore` کامل است.
- 📁 فایل‌های env (فقط نام کلیدها بررسی شد): `.env`, `.env.example`, `.env.template`, `contracts/.env`, `contracts/.env.example`, `frontend/apps/dashboard/.env`, `frontend/apps/dashboard/.env.example`, `frontend/apps/web/.env`, `frontend/apps/web/.env.example`
- 📝 TODO/FIXME: **3** مورد
  - `engine/land/integration/water_adapter.py:207` — TODO: Remove circular dependency - services.map_engine.pipelines.runoff
  - `services/api_gateway/routers/satellite.py:44` — TODO: Refactor to use service layer instead of direct database access
  - `services/scientific_motors/satellite_integration.py:181` — TODO: multi-temporal
- 🐍 print() در پایتون: 18 مورد (در پروداکشن از logging استفاده شود)
- 🔗 آدرس localhost هاردکد: 13 مورد — بیشترین: `engine/hydroma/config/settings.py` (3), `eco_beautify.py` (1), `start_dev_v4.py` (1), `contracts/hardhat.config.js` (1), `engine/hydroma/biofertilizer/tests/test_nojin_comprehensive.py` (1)
- 📦 فایل حجیم: `data/eco_nojin_master.duckdb` (34.5 MB)
- 📦 فایل حجیم: `engine/cpp_core/build2/hydroma_core_py.dir/Release/hydroma_core.cp311-win_amd64.iobj` (11.2 MB)
- 📦 فایل حجیم: `engine/cpp_core/build2/hydroma_core_py.dir/Release/hydroma_core.cp312-win_amd64.iobj` (11.2 MB)
- 📦 فایل حجیم: `data/maps/M-TOP_3d6aeb1b/contours.gpkg` (10.3 MB)
- 📦 فایل حجیم: `data/maps/M-TOP_0b25d85f/contours.gpkg` (10.3 MB)

## ۱۷) امتیازدهی تفصیلی

**امتیاز نهایی: 96/100 — گرید A 🟢**

| کسر | دلیل |
|---:|---|
| -2 | خطای parse پایتون (1 فایل) |
| -2 | 1 یافتهٔ امنیتی با شدت متوسط |
| -0 | print() (18 مورد) |
| -0 | TODO/FIXME (3 مورد) |

## ۱۸) اقدامات پیشنهادی

1. رسیدگی به یافته‌های امنیتی بخش ۹؛ انتقال کلیدها به متغیر محیطی و افزودن gitleaks به CI
2. Lazy loading مسیرها برای کاهش حجم باندل اولیه
3. افزودن type hint به توابع پایتون و افزودن mypy به CI
4. بازآرایی (refactor) بلوک‌های تکراری به توابع/ماژول مشترک
5. اجرای `npx depcheck` برای یافتن وابستگی‌های بلااستفاده
6. اجرای `npx vite-bundle-visualizer` برای تحلیل حجم باندل
