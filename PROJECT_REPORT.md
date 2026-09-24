# 📊 گزارش جامع پروژه — eco_nojin

- **تاریخ تولید:** 2026-09-24 02:33:23
- **مسیر:** `D:\eco_nojin`
- **محیط:** Python 3.12.10 | Windows 10
- **مدت اسکن:** 31.2 ثانیه
- **⭐ امتیاز سلامت:** **52/100** (گرید D 🟠)

## ۱) خلاصه اجرایی

| مورد | مقدار |
|---|---|
| کل فایل‌ها | 4,356 |
| حجم کل | 705.7 MB |
| خطوط کد واقعی | 209,865 |
| اندپوینت‌های API | 712 |
| کامپوننت‌های React (tsx) | 163 |
| کلاس‌های Model (تقریبی) | 598 |
| تست بک‌اند / فرانت‌اند | 105 / 0 فایل |
| یافته‌های امنیتی (بالا/متوسط) | 10 / 20 |

**استک:** FastAPI · Node.js · Pydantic · Pytest · Python · SQLAlchemy · TypeScript · aiohttp

**ابزارها:** Dockerfile · Alembic (مهاجرت DB) · README.md · نمونه .env · Hardhat (قرارداد هوشمند) · GitHub Actions (7 workflow)

## ۲) وضعیت Git

- ریپازیتوری Git یافت نشد.

## ۳) ساختار پوشه‌ها (تا عمق 3)

```text
eco_nojin/  (59 فایل در ریشه)
├── .benchmarks/ (0 فایل)
├── .git-hooks/ (1 فایل)
├── .github/ (11 فایل)
│   └── workflows/ (10 فایل)
│       └── scripts/ (3 فایل)
├── .hypothesis/ (491 فایل)
│   ├── constants/ (465 فایل)
│   └── examples/ (25 فایل)
│       ├── 04e6b3400353b141/ (11 فایل)
│       ├── 25db8945d5b6f2a9/ (1 فایل)
│       ├── 2b51f26f2150d363/ (2 فایل)
│       ├── 2d9919cbaa5f64a6/ (1 فایل)
│       ├── 41fa364a7f910fe6/ (1 فایل)
│       ├── 4a5ad394c75b8967/ (1 فایل)
│       ├── 643b1c89b58af69f/ (1 فایل)
│       ├── 66d75e32d1d3abc1/ (2 فایل)
│       ├── d1c9a67d0b5a8f0e/ (1 فایل)
│       ├── e9cfe77132020e9e/ (2 فایل)
│       ├── f49eacb6dca0e8c1/ (1 فایل)
│       └── f99b49ec9f49e6d6/ (1 فایل)
├── .openclaw/ (2 فایل)
├── .snapshots/ (3 فایل)
├── .tmp/ (54 فایل)
│   ├── pytest-of-hp/ (54 فایل)
│   │   ├── pytest-0/ (20 فایل)
│   │   │   ├── test_access_logging0/ (1 فایل)
│   │   │   ├── test_alembic_upgrade_head0/ (1 فایل)
│   │   │   ├── test_commitment_verification0/ (1 فایل)
│   │   │   ├── test_connection_pooling_under_0/ (1 فایل)
│   │   │   ├── test_end_to_end0/ (0 فایل)
│   │   │   ├── test_farm_wizard_persists_farm0/ (0 فایل)
│   │   │   ├── test_farm_wizard_reauthores_sa0/ (0 فایل)
│   │   │   ├── test_farm_wizard_rejects_bad_a0/ (0 فایل)
│   │   │   ├── test_foreign_key_constraints0/ (1 فایل)
│   │   │   ├── test_migration_creates_core_ta0/ (1 فایل)
│   │   │   ├── test_missing_columns_raises0/ (1 فایل)
│   │   │   ├── test_missing_executable_raises0/ (0 فایل)
│   │   │   ├── test_missing_header_raises0/ (1 فایل)
│   │   │   ├── test_missing_project_raises0/ (0 فایل)
│   │   │   ├── test_nodata_pixels_masked0/ (2 فایل)
│   │   │   ├── test_nonzero_exit_raises0/ (1 فایل)
│   │   │   ├── test_parses_and_aggregates0/ (1 فایل)
│   │   │   ├── test_rollback_on_error0/ (1 فایل)
│   │   │   ├── test_selective_disclosure0/ (1 فایل)
│   │   │   ├── test_store_and_retrieve0/ (1 فایل)
│   │   │   ├── test_success_with_mocked_subpr0/ (2 فایل)
│   │   │   ├── test_uniform_scene0/ (2 فایل)
│   │   │   └── test_unique_constraints0/ (1 فایل)
│   │   ├── pytest-1/ (20 فایل)
│   │   │   ├── test_access_logging0/ (1 فایل)
│   │   │   ├── test_alembic_upgrade_head0/ (1 فایل)
│   │   │   ├── test_commitment_verification0/ (1 فایل)
│   │   │   ├── test_connection_pooling_under_0/ (1 فایل)
│   │   │   ├── test_end_to_end0/ (0 فایل)
│   │   │   ├── test_farm_wizard_persists_farm0/ (0 فایل)
│   │   │   ├── test_farm_wizard_reauthores_sa0/ (0 فایل)
│   │   │   ├── test_farm_wizard_rejects_bad_a0/ (0 فایل)
│   │   │   ├── test_foreign_key_constraints0/ (1 فایل)
│   │   │   ├── test_migration_creates_core_ta0/ (1 فایل)
│   │   │   ├── test_missing_columns_raises0/ (1 فایل)
│   │   │   ├── test_missing_executable_raises0/ (0 فایل)
│   │   │   ├── test_missing_header_raises0/ (1 فایل)
│   │   │   ├── test_missing_project_raises0/ (0 فایل)
│   │   │   ├── test_nodata_pixels_masked0/ (2 فایل)
│   │   │   ├── test_nonzero_exit_raises0/ (1 فایل)
│   │   │   ├── test_parses_and_aggregates0/ (1 فایل)
│   │   │   ├── test_rollback_on_error0/ (1 فایل)
│   │   │   ├── test_selective_disclosure0/ (1 فایل)
│   │   │   ├── test_store_and_retrieve0/ (1 فایل)
│   │   │   ├── test_success_with_mocked_subpr0/ (2 فایل)
│   │   │   ├── test_uniform_scene0/ (2 فایل)
│   │   │   └── test_unique_constraints0/ (1 فایل)
│   │   └── pytest-2/ (14 فایل)
│   │       ├── test_access_logging0/ (1 فایل)
│   │       ├── test_commitment_verification0/ (1 فایل)
│   │       ├── test_end_to_end0/ (0 فایل)
│   │       ├── test_farm_wizard_persists_farm0/ (0 فایل)
│   │       ├── test_farm_wizard_reauthores_sa0/ (0 فایل)
│   │       ├── test_farm_wizard_rejects_bad_a0/ (0 فایل)
│   │       ├── test_missing_columns_raises0/ (1 فایل)
│   │       ├── test_missing_executable_raises0/ (0 فایل)
│   │       ├── test_missing_header_raises0/ (1 فایل)
│   │       ├── test_missing_project_raises0/ (0 فایل)
│   │       ├── test_nodata_pixels_masked0/ (2 فایل)
│   │       ├── test_nonzero_exit_raises0/ (1 فایل)
│   │       ├── test_parses_and_aggregates0/ (1 فایل)
│   │       ├── test_selective_disclosure0/ (1 فایل)
│   │       ├── test_store_and_retrieve0/ (1 فایل)
│   │       ├── test_success_with_mocked_subpr0/ (2 فایل)
│   │       └── test_uniform_scene0/ (2 فایل)
│   └── torchinductor_hp/ (0 فایل)
├── .turbo/ (0 فایل)
│   └── cache/ (0 فایل)
├── _quarantine_bak_2026-09-21/ (114 فایل)
│   ├── contracts/ (1 فایل)
│   │   └── src/ (1 فایل)
│   ├── database/ (11 فایل)
│   │   └── hub/ (7 فایل)
│   ├── engine/ (13 فایل)
│   │   └── hydroma/ (3 فایل)
│   │       └── mrv/ (3 فایل)
│   ├── scripts/ (2 فایل)
│   │   ├── setup/ (1 فایل)
│   │   └── utils/ (1 فایل)
│   ├── services/ (59 فایل)
│   │   ├── admin/ (2 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── ai/ (9 فایل)
│   │   ├── analytics/ (2 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── api_gateway/ (23 فایل)
│   │   │   └── routers/ (18 فایل)
│   │   ├── auth/ (2 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── bots/ (3 فایل)
│   │   │   ├── api/ (1 فایل)
│   │   │   ├── core/ (1 فایل)
│   │   │   └── handlers/ (1 فایل)
│   │   ├── carbon/ (1 فایل)
│   │   ├── content/ (2 فایل)
│   │   ├── field_monitoring/ (1 فایل)
│   │   ├── landscape/ (1 فایل)
│   │   │   └── models/ (1 فایل)
│   │   ├── map_engine/ (1 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── marketplace/ (1 فایل)
│   │   │   └── models/ (1 فایل)
│   │   ├── mobile_monitoring/ (1 فایل)
│   │   ├── reporting/ (2 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── satellite/ (1 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── scientific_motors/ (1 فایل)
│   │   ├── simulation/ (1 فایل)
│   │   │   └── api/ (1 فایل)
│   │   ├── telegram_bot/ (2 فایل)
│   │   │   └── api/ (1 فایل)
│   │   └── tourism/ (1 فایل)
│   │       └── models/ (1 فایل)
│   └── tests/ (27 فایل)
│       ├── integration/ (10 فایل)
│       └── unit/ (1 فایل)
├── adapters/ (2 فایل)
├── alembic/ (37 فایل)
│   └── versions/ (34 فایل)
│       └── _archived/ (12 فایل)
├── analysis.json/ (1 فایل)
├── apps/ (501 فایل)
│   └── web/ (501 فایل)
│       ├── .next-phase1check/ (181 فایل)
│       │   ├── cache/ (9 فایل)
│       │   ├── diagnostics/ (2 فایل)
│       │   ├── server/ (99 فایل)
│       │   ├── static/ (35 فایل)
│       │   └── types/ (22 فایل)
│       ├── messages/ (14 فایل)
│       ├── playwright-report/ (45 فایل)
│       │   └── data/ (44 فایل)
│       ├── public/ (34 فایل)
│       │   ├── brand/ (11 فایل)
│       │   └── fonts/ (22 فایل)
│       ├── scripts/ (1 فایل)
│       ├── src/ (164 فایل)
│       │   ├── app/ (122 فایل)
│       │   ├── components/ (25 فایل)
│       │   ├── content/ (1 فایل)
│       │   ├── i18n/ (4 فایل)
│       │   ├── lib/ (8 فایل)
│       │   └── types/ (3 فایل)
│       ├── test-results/ (45 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--0e3b1-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--106d3-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--14fa1-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--37a32-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--5ffce--elements-have-focus-styles-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--718a0-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--97569-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--ac4fd-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--d2593-igation-works-on-cover-page-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2--ef43f-no-critical-a11y-violations-chromium/ (1 فایل)
│       │   ├── a11y-Accessibility-WCAG-2-1-AA-Skip-link-works-chromium/ (1 فایل)
│       │   ├── cover-Cover-Page---Navigat-3f3bd-حات-عمومی-navigates-to-home-chromium/ (1 فایل)
│       │   ├── cover-Cover-Page---Navigat-642ac-ازارگاه-navigates-to-market-chromium/ (1 فایل)
│       │   ├── cover-Cover-Page-T01-Arabic-locale-loads-with-RTL-chromium/ (1 فایل)
│       │   ├── cover-Cover-Page-T01-Chinese-locale-loads-chromium/ (1 فایل)
│       │   ├── cover-Cover-Page-T01-English-locale-loads-correctly-chromium/ (1 فایل)
│       │   ├── cover-Cover-Page-T01-loads-2d311-e-slogan-quote-and-two-CTAs-chromium/ (1 فایل)
│       │   ├── home-Home-Page---RTL-LTR-en-and-de-are-LTR-chromium/ (1 فایل)
│       │   ├── home-Home-Page---RTL-LTR-fa-and-ar-are-RTL-chromium/ (1 فایل)
│       │   ├── home-Home-Page-English-locale-shows-real-data-chromium/ (1 فایل)
│       │   ├── home-Home-Page-loads-and-d-4c8b3--land-profiles-and-products-chromium/ (1 فایل)
│       │   ├── home-Home-Page-navigates-to-hydroma-from-CTA-chromium/ (1 فایل)
│       │   ├── home-Home-Page-navigates-to-market-from-CTA-chromium/ (1 فایل)
│       │   ├── hydroma-Hydroma---Navigation-navigates-from-cover-page-chromium/ (1 فایل)
│       │   ├── hydroma-Hydroma---Navigation-navigates-from-home-page-chromium/ (1 فایل)
│       │   ├── hydroma-Hydroma-Science-Pa-2a974-splays-C-status-models-list-chromium/ (1 فایل)
│       │   ├── hydroma-Hydroma-Science-Page-English-locale-shows-C-status-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-070c3-itcher-shows-all-14-locales-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-21173-have-correct-text-direction-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-adb55-have-correct-text-direction-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-Arabic-ar-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-bc2bf-de-falls-back-to-en-then-fa-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-Chinese-zh-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-English-en-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-French-fr-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-German-de-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-Locale-change-persists-via-URL-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-Persian-fa-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-Spanish-es-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── i18n-i18n---All-14-locales-Urdu-ur-loads-with-correct-dir-chromium/ (1 فایل)
│       │   ├── market-Market-Page---Navigation-navigates-from-cover-page-chromium/ (1 فایل)
│       │   ├── market-Market-Page-English-locale-shows-products-chromium/ (1 فایل)
│       │   ├── market-Market-Page-loads-a-dbd21-ats-products-with-real-data-chromium/ (1 فایل)
│       │   └── market-Market-Page-product-cards-show-price-stock-producer-chromium/ (1 فایل)
│       ├── tests/ (6 فایل)
│       └── tokens/ (2 فایل)
├── backups/ (1 فایل)
│   └── 20260901_061756/ (1 فایل)
├── benchmarks/ (2 فایل)
├── blockchain/ (3 فایل)
│   ├── config/ (1 فایل)
│   ├── contracts/ (1 فایل)
│   └── scripts/ (1 فایل)
├── brand-assets/ (4 فایل)
│   └── source/ (4 فایل)
├── config/ (1 فایل)
├── contracts/ (33 فایل)
│   ├── cache/ (1 فایل)
│   ├── scripts/ (1 فایل)
│   ├── src/ (15 فایل)
│   └── test/ (5 فایل)
├── data/ (318 فایل)
│   ├── _archived_excel_data/ (15 فایل)
│   ├── analyses/ (0 فایل)
│   │   └── topography/ (0 فایل)
│   │       └── test_site/ (0 فایل)
│   ├── analysis_results/ (3 فایل)
│   ├── cache/ (12 فایل)
│   │   ├── cgls/ (0 فایل)
│   │   ├── chirps/ (0 فایل)
│   │   ├── esa_worldcover/ (1 فایل)
│   │   ├── gbif/ (6 فایل)
│   │   ├── hydrosheds/ (0 فایل)
│   │   ├── nasa_power/ (0 فایل)
│   │   ├── ncep_reanalysis/ (0 فایل)
│   │   ├── open_meteo/ (0 فایل)
│   │   ├── open_meteo_seasonal/ (0 فایل)
│   │   ├── soilgrids/ (0 فایل)
│   │   ├── stac/ (0 فایل)
│   │   ├── test_gbif/ (5 فایل)
│   │   └── worldclim/ (0 فایل)
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
│   ├── maps/ (149 فایل)
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
│   ├── motors/ (9 فایل)
│   │   └── cache/ (9 فایل)
│   ├── mrv/ (3 فایل)
│   ├── processed/ (1 فایل)
│   ├── raw/ (1 فایل)
│   ├── reports/ (88 فایل)
│   ├── security/ (1 فایل)
│   └── swat_projects/ (18 فایل)
├── database/ (13 فایل)
│   ├── alembic/ (1 فایل)
│   │   └── versions/ (1 فایل)
│   ├── hub/ (3 فایل)
│   └── models/ (1 فایل)
├── DELIVERY/ (3 فایل)
├── deploy/ (8 فایل)
│   ├── ci/ (1 فایل)
│   ├── docker/ (1 فایل)
│   ├── k8s/ (1 فایل)
│   └── n8n/ (4 فایل)
├── docs/ (218 فایل)
│   ├── adr/ (2 فایل)
│   ├── architecture/ (9 فایل)
│   │   └── local_first/ (9 فایل)
│   ├── backlog/ (1 فایل)
│   ├── content/ (1 فایل)
│   ├── en/ (37 فایل)
│   ├── fa/ (72 فایل)
│   │   ├── 22_research_reports/ (4 فایل)
│   │   └── 24_study_reports/ (4 فایل)
│   ├── frontend/ (3 فایل)
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
│   ├── ops/ (1 فایل)
│   ├── report/ (1 فایل)
│   └── security/ (1 فایل)
├── engine/ (449 فایل)
│   ├── cpp_core/ (169 فایل)
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
│   │   └── tests/ (25 فایل)
│   ├── data/ (1 فایل)
│   ├── hydroma/ (238 فایل)
│   │   ├── ai_assistant/ (3 فایل)
│   │   ├── analyses/ (1 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── biofertilizer/ (15 فایل)
│   │   │   ├── api/ (0 فایل)
│   │   │   ├── data/ (3 فایل)
│   │   │   ├── models/ (0 فایل)
│   │   │   ├── repositories/ (0 فایل)
│   │   │   ├── services/ (0 فایل)
│   │   │   └── tests/ (4 فایل)
│   │   ├── calculation/ (3 فایل)
│   │   ├── calculations/ (1 فایل)
│   │   ├── calibration/ (4 فایل)
│   │   ├── carbon/ (2 فایل)
│   │   ├── climate/ (2 فایل)
│   │   ├── climate_adaptation/ (9 فایل)
│   │   ├── config/ (2 فایل)
│   │   ├── core/ (5 فایل)
│   │   ├── cpp_bridge/ (11 فایل)
│   │   │   └── tests/ (2 فایل)
│   │   ├── crop/ (2 فایل)
│   │   ├── data/ (2 فایل)
│   │   ├── data_assimilation/ (2 فایل)
│   │   ├── data_pipeline/ (4 فایل)
│   │   │   └── tests/ (1 فایل)
│   │   ├── decision_support/ (1 فایل)
│   │   ├── distributed_ml/ (2 فایل)
│   │   ├── economics/ (8 فایل)
│   │   ├── examples/ (1 فایل)
│   │   ├── generative_ai/ (1 فایل)
│   │   ├── groundwater/ (5 فایل)
│   │   │   └── tests/ (2 فایل)
│   │   ├── hybrid_ml/ (3 فایل)
│   │   ├── infrastructure/ (6 فایل)
│   │   ├── irrigation/ (2 فایل)
│   │   ├── materials/ (2 فایل)
│   │   ├── models/ (55 فایل)
│   │   │   ├── expansion/ (4 فایل)
│   │   │   ├── global_watchdog/ (6 فایل)
│   │   │   └── validation/ (31 فایل)
│   │   ├── mrv/ (9 فایل)
│   │   │   └── tests/ (1 فایل)
│   │   ├── optimization/ (1 فایل)
│   │   ├── performance/ (2 فایل)
│   │   ├── plant_neuro/ (5 فایل)
│   │   │   └── tests/ (1 فایل)
│   │   ├── production/ (2 فایل)
│   │   ├── satellite/ (8 فایل)
│   │   │   ├── processors/ (2 فایل)
│   │   │   └── providers/ (4 فایل)
│   │   ├── scenario/ (1 فایل)
│   │   ├── scenarios/ (6 فایل)
│   │   ├── simulation/ (13 فایل)
│   │   │   └── runners/ (5 فایل)
│   │   ├── simulation_env/ (7 فایل)
│   │   ├── soil/ (16 فایل)
│   │   │   └── tests/ (2 فایل)
│   │   ├── utils/ (1 فایل)
│   │   ├── visualization/ (1 فایل)
│   │   ├── water/ (2 فایل)
│   │   └── watershed/ (4 فایل)
│   │       └── tests/ (1 فایل)
│   └── land/ (33 فایل)
│       ├── integration/ (14 فایل)
│       │   └── tests/ (6 فایل)
│       ├── reference/ (3 فایل)
│       └── tests/ (7 فایل)
├── foundry/ (5 فایل)
├── helm/ (16 فایل)
│   └── eco-nojin/ (16 فایل)
│       └── templates/ (14 فایل)
├── interfaces/ (3 فایل)
├── k8s/ (16 فایل)
│   ├── base/ (10 فایل)
│   ├── istio/ (0 فایل)
│   └── overlays/ (6 فایل)
│       ├── dr/ (2 فایل)
│       ├── production/ (2 فایل)
│       └── staging/ (2 فایل)
├── lib/ (1046 فایل)
│   ├── forge-std/ (69 فایل)
│   │   ├── .github/ (4 فایل)
│   │   │   └── workflows/ (2 فایل)
│   │   ├── scripts/ (1 فایل)
│   │   ├── src/ (31 فایل)
│   │   │   └── interfaces/ (9 فایل)
│   │   └── test/ (23 فایل)
│   │       ├── compilation/ (4 فایل)
│   │       └── fixtures/ (4 فایل)
│   └── openzeppelin-contracts/ (977 فایل)
│       ├── .changeset/ (1 فایل)
│       ├── .claude/ (4 فایل)
│       │   └── skills/ (4 فایل)
│       ├── .github/ (16 فایل)
│       │   ├── actions/ (3 فایل)
│       │   ├── ISSUE_TEMPLATE/ (3 فایل)
│       │   └── workflows/ (8 فایل)
│       ├── .husky/ (1 فایل)
│       ├── audits/ (14 فایل)
│       ├── contracts/ (385 فایل)
│       │   ├── access/ (15 فایل)
│       │   ├── account/ (13 فایل)
│       │   ├── crosschain/ (11 فایل)
│       │   ├── finance/ (3 فایل)
│       │   ├── governance/ (24 فایل)
│       │   ├── interfaces/ (45 فایل)
│       │   ├── metatx/ (3 فایل)
│       │   ├── mocks/ (120 فایل)
│       │   ├── proxy/ (13 فایل)
│       │   ├── token/ (57 فایل)
│       │   ├── utils/ (78 فایل)
│       │   └── vendor/ (2 فایل)
│       ├── docs/ (43 فایل)
│       │   ├── modules/ (36 فایل)
│       │   └── templates/ (4 فایل)
│       ├── fv/ (81 فایل)
│       │   ├── diff/ (3 فایل)
│       │   ├── harnesses/ (20 فایل)
│       │   ├── reports/ (3 فایل)
│       │   └── specs/ (51 فایل)
│       ├── hardhat/ (6 فایل)
│       ├── lib/ (79 فایل)
│       │   ├── erc4626-tests/ (5 فایل)
│       │   ├── forge-std/ (69 فایل)
│       │   └── halmos-cheatcodes/ (5 فایل)
│       ├── scripts/ (68 فایل)
│       │   ├── checks/ (7 فایل)
│       │   ├── generate/ (25 فایل)
│       │   ├── release/ (14 فایل)
│       │   ├── solhint-custom/ (2 فایل)
│       │   └── upgradeable/ (8 فایل)
│       └── test/ (248 فایل)
│           ├── access/ (11 فایل)
│           ├── account/ (25 فایل)
│           ├── crosschain/ (8 فایل)
│           ├── finance/ (3 فایل)
│           ├── governance/ (24 فایل)
│           ├── helpers/ (23 فایل)
│           ├── metatx/ (3 فایل)
│           ├── proxy/ (14 فایل)
│           ├── token/ (47 فایل)
│           └── utils/ (88 فایل)
├── logs/ (32 فایل)
├── messages/ (14 فایل)
├── ml/ (4 فایل)
│   ├── features/ (1 فایل)
│   ├── models/ (1 فایل)
│   ├── notebooks/ (1 فایل)
│   └── registry/ (1 فایل)
├── mobile/ (10 فایل)
│   └── src/ (7 فایل)
│       ├── context/ (1 فایل)
│       ├── hooks/ (1 فایل)
│       ├── screens/ (4 فایل)
│       └── services/ (1 فایل)
├── monitoring/ (4 فایل)
│   ├── loki/ (1 فایل)
│   ├── tempo/ (0 فایل)
│   └── velero/ (0 فایل)
├── packages/ (37 فایل)
│   ├── api-client/ (7 فایل)
│   │   └── src/ (5 فایل)
│   │       └── types/ (1 فایل)
│   ├── config/ (2 فایل)
│   │   ├── biome/ (0 فایل)
│   │   └── tsconfig/ (1 فایل)
│   ├── types/ (6 فایل)
│   │   └── src/ (4 فایل)
│   └── ui/ (22 فایل)
│       └── src/ (20 فایل)
├── reports/ (40 فایل)
│   └── browser-test-2026-09-15/ (19 فایل)
├── requirements_proposal/ (6 فایل)
├── scripts/ (50 فایل)
│   ├── setup/ (2 فایل)
│   └── utils/ (4 فایل)
├── services/ (611 فایل)
│   ├── admin/ (10 فایل)
│   │   ├── api/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── ai/ (17 فایل)
│   │   └── prompts/ (10 فایل)
│   │       ├── admin/ (5 فایل)
│   │       └── support/ (5 فایل)
│   ├── alerting/ (5 فایل)
│   ├── analysis/ (3 فایل)
│   ├── analytics/ (10 فایل)
│   │   ├── api/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── api_gateway/ (106 فایل)
│   │   ├── cache/ (3 فایل)
│   │   ├── eventbus/ (5 فایل)
│   │   │   └── tests/ (1 فایل)
│   │   ├── middleware/ (5 فایل)
│   │   ├── observability/ (3 فایل)
│   │   ├── resilience/ (4 فایل)
│   │   ├── routers/ (77 فایل)
│   │   ├── security/ (0 فایل)
│   │   └── tests/ (0 فایل)
│   ├── audit/ (2 فایل)
│   ├── auth/ (11 فایل)
│   │   ├── api/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── backup/ (5 فایل)
│   ├── bots/ (24 فایل)
│   │   ├── adapters/ (5 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (4 فایل)
│   │   ├── handlers/ (5 فایل)
│   │   └── tests/ (2 فایل)
│   ├── business_modules/ (24 فایل)
│   │   ├── blockchain/ (6 فایل)
│   │   ├── carbon/ (3 فایل)
│   │   ├── insurance/ (2 فایل)
│   │   ├── iot/ (2 فایل)
│   │   ├── ussd/ (3 فایل)
│   │   └── voice/ (7 فایل)
│   ├── carbon/ (16 فایل)
│   │   ├── compliance/ (4 فایل)
│   │   ├── integration/ (2 فایل)
│   │   └── tests/ (3 فایل)
│   ├── commerce/ (8 فایل)
│   │   ├── routers/ (2 فایل)
│   │   └── tests/ (4 فایل)
│   ├── content/ (2 فایل)
│   ├── contracts/ (5 فایل)
│   ├── data/ (28 فایل)
│   │   ├── maps/ (15 فایل)
│   │   ├── motors/ (0 فایل)
│   │   │   └── cache/ (0 فایل)
│   │   └── reports/ (13 فایل)
│   ├── data_manual/ (3 فایل)
│   ├── data_sources/ (2 فایل)
│   ├── design_engine/ (2 فایل)
│   ├── dispute_resolution/ (5 فایل)
│   │   └── routers/ (2 فایل)
│   ├── ecosystem/ (3 فایل)
│   ├── ecowallet/ (7 فایل)
│   ├── event_bus/ (6 فایل)
│   ├── field_monitoring/ (1 فایل)
│   ├── finance/ (12 فایل)
│   │   ├── routers/ (2 فایل)
│   │   └── tests/ (5 فایل)
│   ├── integration/ (3 فایل)
│   ├── inventory/ (7 فایل)
│   │   ├── routers/ (2 فایل)
│   │   └── tests/ (3 فایل)
│   ├── jobs/ (5 فایل)
│   ├── land/ (8 فایل)
│   │   └── tests/ (4 فایل)
│   ├── landscape/ (12 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (1 فایل)
│   │   ├── models/ (1 فایل)
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
│   ├── logistics/ (5 فایل)
│   │   └── routers/ (2 فایل)
│   ├── map_engine/ (22 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── fetchers/ (7 فایل)
│   │   ├── pipelines/ (6 فایل)
│   │   ├── processors/ (1 فایل)
│   │   └── tests/ (2 فایل)
│   ├── marketplace/ (27 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (1 فایل)
│   │   ├── models/ (4 فایل)
│   │   ├── repositories/ (2 فایل)
│   │   ├── schemas/ (2 فایل)
│   │   ├── services/ (1 فایل)
│   │   └── tests/ (7 فایل)
│   ├── mobile_monitoring/ (1 فایل)
│   ├── models/ (8 فایل)
│   ├── mrv/ (4 فایل)
│   ├── notification/ (7 فایل)
│   │   └── tests/ (1 فایل)
│   ├── observability/ (2 فایل)
│   ├── ogc/ (2 فایل)
│   ├── oracle/ (2 فایل)
│   ├── privacy/ (2 فایل)
│   ├── provenance/ (6 فایل)
│   ├── quality/ (0 فایل)
│   │   ├── standards/ (0 فایل)
│   │   └── tests/ (0 فایل)
│   ├── quality_assurance/ (5 فایل)
│   │   └── routers/ (2 فایل)
│   ├── reliability/ (2 فایل)
│   ├── reporting/ (10 فایل)
│   │   ├── api/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── satellite/ (16 فایل)
│   │   ├── api/ (1 فایل)
│   │   └── tests/ (2 فایل)
│   ├── science/ (5 فایل)
│   ├── scientific_motors/ (33 فایل)
│   ├── security/ (17 فایل)
│   │   └── tests/ (1 فایل)
│   ├── simulation/ (17 فایل)
│   │   ├── adapters/ (8 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── engine/ (2 فایل)
│   │   └── tests/ (2 فایل)
│   ├── supabase/ (3 فایل)
│   ├── telegram_bot/ (15 فایل)
│   │   ├── api/ (1 فایل)
│   │   └── tests/ (2 فایل)
│   ├── tourism/ (12 فایل)
│   │   ├── api/ (1 فایل)
│   │   ├── core/ (1 فایل)
│   │   ├── models/ (1 فایل)
│   │   ├── repositories/ (1 فایل)
│   │   ├── schemas/ (1 فایل)
│   │   ├── services/ (1 فایل)
│   │   └── tests/ (3 فایل)
│   ├── validation/ (3 فایل)
│   ├── workers/ (2 فایل)
│   └── workflow/ (5 فایل)
│       └── tests/ (1 فایل)
├── supabase/ (10 فایل)
│   └── migrations/ (10 فایل)
│       └── legacy/ (1 فایل)
├── testing_lab/ (5 فایل)
│   ├── benchmarks/ (1 فایل)
│   ├── fixtures/ (0 فایل)
│   │   ├── climate_data/ (0 فایل)
│   │   └── soil_profiles/ (0 فایل)
│   ├── integration_tests/ (1 فایل)
│   ├── reports/ (0 فایل)
│   └── scientific_tests/ (1 فایل)
└── tests/ (118 فایل)
    ├── benchmarks/ (3 فایل)
    ├── e2e/ (1 فایل)
    ├── fixtures/ (1 فایل)
    ├── integration/ (24 فایل)
    │   └── land/ (2 فایل)
    ├── load/ (1 فایل)
    └── unit/ (51 فایل)
        └── land/ (2 فایل)
… و 48 زیرپوشه در عمق بیشتر
```

## ۴) آمار فایل‌ها بر اساس نوع

| پسوند | تعداد | حجم |
|---|---:|---:|
| `.py` | 1,046 | 6.4 MB |
| `(بدون پسوند)` | 558 | 2.3 MB |
| `.sol` | 542 | 4.1 MB |
| `.js` | 372 | 4.1 MB |
| `.json` | 354 | 7.5 MB |
| `.md` | 302 | 2.0 MB |
| `.tsx` | 163 | 712.2 KB |
| `.tif` | 148 | 75.0 MB |
| `.bak` | 113 | 805.1 KB |
| `.ts` | 67 | 2.7 MB |
| `.tlog` | 50 | 310.3 KB |
| `.yaml` | 49 | 1.1 MB |
| `.png` | 48 | 16.4 MB |
| `.txt` | 47 | 215.9 KB |
| `.cpp` | 40 | 193.1 KB |
| `.adoc` | 37 | 249.3 KB |
| `.spec` | 33 | 300.7 KB |
| `.yml` | 32 | 96.4 KB |
| `.log` | 23 | 7.8 MB |
| `.woff2` | 22 | 352.5 KB |
| `.sh` | 21 | 15.9 KB |
| `.npy` | 18 | 2.5 KB |
| `.conf` | 18 | 4.2 KB |
| `.pdf` | 16 | 4.7 MB |
| `.db` | 15 | 4.8 MB |

## ۵) بزرگ‌ترین فایل‌ها

| حجم | فایل |
|---:|---|
| 105.1 MB | `foundry.zip` ⚠️ |
| 83.2 MB | `foundry/forge.exe` ⚠️ |
| 60.4 MB | `foundry/cast.exe` ⚠️ |
| 41.9 MB | `foundry/chisel.exe` ⚠️ |
| 41.4 MB | `apps/web/.next-phase1check/cache/webpack/server-production/0.pack` ⚠️ |
| 41.2 MB | `foundry/anvil.exe` ⚠️ |
| 34.5 MB | `data/eco_nojin_master.duckdb` ⚠️ |
| 24.6 MB | `apps/web/.next-phase1check/cache/webpack/client-production/0.pack` ⚠️ |
| 17.7 MB | `data/cache/esa_worldcover/esa_worldcover_N24E042_f1837263.tif` ⚠️ |
| 11.2 MB | `engine/cpp_core/build2/hydroma_core_py.dir/Release/hydroma_core.cp311-win_amd64.iobj` ⚠️ |
| 11.2 MB | `engine/cpp_core/build2/hydroma_core_py.dir/Release/hydroma_core.cp312-win_amd64.iobj` ⚠️ |
| 11.2 MB | `apps/web/.next-phase1check/cache/webpack/edge-server-production/0.pack` ⚠️ |
| 10.3 MB | `data/maps/M-TOP_3d6aeb1b/contours.gpkg` ⚠️ |
| 10.3 MB | `data/maps/M-TOP_0b25d85f/contours.gpkg` ⚠️ |
| 10.2 MB | `data/maps/M-TOP_1fbdec2f/contours.gpkg` ⚠️ |

## ۶) وابستگی‌ها

### فرانت‌اند — package.json

| پکیج | نسخه | نوع |
|---|---|---|
| clsx | ^2.1.1 | runtime |
| geotiff | ^3.0.5 | runtime |
| tailwind-merge | ^3.6.0 | runtime |
| @biomejs/biome | ^2.5.14 | dev |
| @next/bundle-analyzer | 15.5.25 | dev |
| @types/node | ^22.15.0 | dev |
| @types/react | 19.0.0 | dev |
| @types/react-dom | 19.0.0 | dev |
| orval | ^8.35.0 | dev |
| turbo | ^2.5.4 | dev |
| typescript | ^5.9.3 | dev |

### اسکریپت‌های npm

| دستور | اسکریپت |
|---|---|
| `dev` | `pnpm -C apps/web dev` |
| `build` | `pnpm -C apps/web build` |
| `start` | `pnpm -C apps/web start` |
| `lint` | `pnpm -C apps/web lint` |
| `format` | `pnpm -C apps/web format` |
| `test` | `pnpm -C apps/web test` |
| `test:e2e` | `pnpm -C apps/web test:e2e` |
| `type-check` | `pnpm -C apps/web type-check` |
| `generate:api` | `pnpm -C apps/web generate:api` |
| `backend:test` | `python -m pytest -q` |
| `test:all` | `pnpm test && pnpm backend:test` |

### بک‌اند — requirements.txt

- fastapi==0.115.0
- uvicorn[standard]==0.32.0
- python-dotenv==1.0.1
- python-multipart==0.0.20
- httpx==0.27.2
- pydantic==2.10.0
- pydantic-settings==2.7.0
- openai==1.58.0
- qdrant-client==1.12.0
- numpy==2.1.0
- pandas==2.2.3
- xarray==2024.10.0
- xclim==0.52.0
- scipy==1.14.0
- langdetect==1.0.9
- tenacity==9.0.0
- structlog==24.4.0
- sqlalchemy==2.0.36
- psycopg[binary]==3.2.5
- alembic==1.14.0
- python-jose[cryptography]==3.4.0
- passlib[bcrypt]==1.7.4
- nats-py==2.10.0
- pytest==8.3.3
- pytest-asyncio==0.24.0
- pytest-cov==5.0.0
- pyproject.toml: ✅ موجود
- lockfile فرانت‌اند: ✅ pnpm-lock.yaml

## ۷) بک‌اند (API)

- تعداد اندپوینت‌ها: **712** — DELETE×17 · GET×368 · PATCH×8 · POST×303 · PUT×16
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
| POST | `/rules` | `services/alerting/router.py` |
| GET | `/rules` | `services/alerting/router.py` |
| GET | `/rules/{rule_id}` | `services/alerting/router.py` |
| PATCH | `/rules/{rule_id}` | `services/alerting/router.py` |
| DELETE | `/rules/{rule_id}` | `services/alerting/router.py` |
| GET | `/` | `services/alerting/router.py` |
| GET | `/{alert_id}` | `services/alerting/router.py` |
| POST | `/{alert_id}/acknowledge` | `services/alerting/router.py` |
| POST | `/{alert_id}/resolve` | `services/alerting/router.py` |
| POST | `/{alert_id}/suppress` | `services/alerting/router.py` |
| GET | `/summary` | `services/alerting/router.py` |
| GET | `/dashboard` | `services/analytics/api/__init__.py` |
| GET | `/sales-summary` | `services/analytics/api/__init__.py` |
| GET | `/tourism-metrics` | `services/analytics/api/__init__.py` |
| GET | `/landscape-metrics` | `services/analytics/api/__init__.py` |
| GET | `/` | `services/api_gateway/main.py` |
| GET | `/health` | `services/api_gateway/main.py` |
| GET | `/health/live` | `services/api_gateway/main.py` |
| GET | `/health/ready` | `services/api_gateway/main.py` |
| GET | `/api/v1/health` | `services/api_gateway/main.py` |
| GET | `/ready` | `services/api_gateway/main.py` |
| GET | `/debug/routes` | `services/api_gateway/main.py` |
| GET | `/health` | `services/api_gateway/routers/admin.py` |
| GET | `/users` | `services/api_gateway/routers/admin.py` |
| POST | `/users/bulk-action` | `services/api_gateway/routers/admin.py` |
| POST | `/users/{user_id}/block` | `services/api_gateway/routers/admin.py` |
| POST | `/users/{user_id}/unblock` | `services/api_gateway/routers/admin.py` |
| GET | `/audit` | `services/api_gateway/routers/admin.py` |
| GET | `/content` | `services/api_gateway/routers/admin.py` |
| POST | `/content/bulk-action` | `services/api_gateway/routers/admin.py` |
| … | … | و 672 مورد دیگر |

## ۸) فرانت‌اند

- کامپوننت‌های TSX: 163
- lazy(): 2 | Suspense: 0 | Route: 5
- کیفیت TS: `any`×86 | ts-ignore×17 | eslint-disable×2 | inline-style×37
- هوک‌ها: useEffect×21 | useState×101
- فایل‌های تست فرانت‌اند: 0

## ۹) امنیت

| شدت | قانون | فایل:خط |
|---|---|---|
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `alembic/versions/e6f7a8b9c0d1_postgis_tribal_migration_route.py:84` |
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `engine/data_connector.py:412` |
| بالا | رمز عبور داخل Connection String | `helm/eco-nojin/templates/secret-api-gateway.yaml:15` |
| بالا | رمز عبور داخل Connection String | `k8s/base/secrets.yaml:12` |
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `scripts/db_maintenance.py:40` |
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `scripts/migrate_dev_sqlite.py:50` |
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `scripts/seed_pilot_data.py:356` |
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `services/api_gateway/eventbus/dlq.py:44` |
| بالا | کوئری SQL با f-string (خطر تزریق SQL) | `services/scientific_motors/data_repository.py:327` |
| بالا | رمز عبور داخل Connection String | `tests/unit/test_settings.py:61` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/server/chunks/49.js:3` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/server/chunks/740.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/server/chunks/907.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/server/pages/_error.js:8` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/702.804fd6ba7830988e.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/954-df7d1176549ad01b.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/c8dda10c-9f181afb237acb3a.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/framework-04117800bcccd73f.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/main-2490920485c4c465.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/app/_not-found/page-46932ebf429371d7.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/.next-phase1check/static/chunks/pages/_error-22eb0c58bbb42a4b.js:1` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/src/components/ui/Button.tsx:105` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/src/components/ui/CommandPalette.tsx:183` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/src/components/ui/Dialog.tsx:134` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/src/components/ui/Skeleton.tsx:87` |
| متوسط | dangerouslySetInnerHTML (ریسک XSS) | `apps/web/src/components/ui/Toast.tsx:107` |
| متوسط | استفاده از eval() | `engine/hydroma/distributed_ml/trainer.py:373` |
| متوسط | استفاده از eval() | `engine/hydroma/hybrid_ml/gp_surrogate.py:270` |
| متوسط | استفاده از eval() | `engine/hydroma/hybrid_ml/pinn.py:281` |
| متوسط | مقدار محرمانهٔ هاردکد | `k8s/base/secrets.yaml:10` |
| کم | هش ضعیف (md5/sha1) | `engine/hydroma/data_pipeline/pipeline.py:133` |
| کم | except خام (بلع خطا) | `scripts/validate_model.py:299` |
| کم | except خام (بلع خطا) | `services/privacy/vault.py:203` |
| اطلاع | کلیدهای حساس در فایل env: ACCESS_TOKEN_EXPIRE_MINUTES, ADS_API_KEY, AI_LLM_KEY, ALCHEMY_API_KEY, ALLOW_CREDENTIALS, BALE_TOKEN, BOT_TOKEN, CDSE_CLIENT_SECRET | `.env` |
| اطلاع | کلیدهای حساس در فایل env: ACCESS_TOKEN_EXPIRE_MINUTES, ADS_API_KEY, APP_SECRET_KEY, BOT_TOKEN, CDS_API_KEY, CLOUDFLARE_API_TOKEN, COHERE_API_KEY, DEEPSEEK_API_KEY | `.env.example` |
| اطلاع | کلیدهای حساس در فایل env: ACCESS_TOKEN_EXPIRE_MINUTES, ADS_API_KEY, AGENT_TOKEN, AI_LLM_KEY, ALCHEMY_API_KEY, ALLOW_CREDENTIALS, ANTHROPIC_API_KEY, API_KEY_HEADER | `.env.template` |
| اطلاع | کلیدهای حساس در فایل env: POLYGONSCAN_API_KEY, PRIVATE_KEY | `contracts/.env` |
| اطلاع | کلیدهای حساس در فایل env: POLYGONSCAN_API_KEY, PRIVATE_KEY | `contracts/.env.example` |

> 🔐 مقادیر محرمانه به متغیر محیطی منتقل و از تاریخچهٔ گیت پاک‌سازی شوند. این اسکن جایگزین ابزارهای تخصصی (`gitleaks`, `bandit`, `trufflehog`) نیست.

## ۱۰) کیفیت کد پایتون (AST)

- فایل‌های تحلیل‌شده: 1026 | توابع: 7313 | کلاس‌ها: 1930
- پوشش docstring: **58٪** (5343/9243)
- توابع دارای return annotation: **50٪**
- ⚠️ except خام: 3 مورد
- بیشترین آرگومان تابع: 16 → `services/marketplace/order_management.py:152 → register_vendor()`
- طولانی‌ترین تابع: 670 خط → `eco_chaos_test_v2.py:2656 → main()`

### پیچیدگی شناختی برتر (تقریبی)

| پیچیدگی | فایل |
|---:|---|
| 380 | `eco_chaos_test_v2.py` |
| 205 | `tests/strict_challenge_v2.py` |
| 186 | `engine/hydroma/data_pipeline/pipeline.py` |
| 167 | `services/api_gateway/routers/admin.py` |
| 164 | `engine/hydroma/biofertilizer/advanced_calculator.py` |
| 147 | `services/marketplace/hub_service.py` |
| 144 | `services/api_gateway/routers/village_hub.py` |
| 144 | `services/api_gateway/routers/auth.py` |
| 139 | `services/api_gateway/routers/marketplace.py` |
| 133 | `services/conftest.py` |

### پرتکرارترین ماژول‌های importشده (شامل ماژول‌های داخلی)

`services`×816, `engine`×577, `database`×382, `sqlalchemy`×363, `__future__`×305, `typing`×293, `datetime`×244, `fastapi`×177, `logging`×159, `numpy`×141, `dataclasses`×135, `pytest`×130, `pathlib`×111, `pydantic`×111, `json`×104

## ۱۱) پایگاه‌داده و ORM

- سیستم‌های شناسایی‌شده: Alembic, Redis, SQLAlchemy, SQLite
- کلاس‌های Model (تقریبی): 598
- فایل‌های مهاجرت (migrations): 36

## ۱۲) تکرار کد (تقریبی)

- گروه‌های بلوک تکراری (≥۸ خط یکسان): **473**
  - `apps/web/.next-phase1check/types/app/[locale]/layout.ts:5` · `apps/web/.next-phase1check/types/app/[locale]/page.ts:5` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:5` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:5`
  - `apps/web/.next-phase1check/types/app/[locale]/layout.ts:9` · `apps/web/.next-phase1check/types/app/[locale]/page.ts:9` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:9` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:9`
  - `apps/web/.next-phase1check/types/app/[locale]/layout.ts:29` · `apps/web/.next-phase1check/types/app/[locale]/page.ts:29` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:29` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:29`
  - `apps/web/.next-phase1check/types/app/[locale]/layout.ts:33` · `apps/web/.next-phase1check/types/app/[locale]/page.ts:33` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:33` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:33`
  - `apps/web/.next-phase1check/types/app/[locale]/layout.ts:37` · `apps/web/.next-phase1check/types/app/[locale]/page.ts:37` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:37` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:37`
  - `apps/web/.next-phase1check/types/app/[locale]/page.ts:13` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:13` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:13` · `apps/web/.next-phase1check/types/app/[locale]/ai/page.ts:13`
  - `apps/web/.next-phase1check/types/app/[locale]/page.ts:17` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:17` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:17` · `apps/web/.next-phase1check/types/app/[locale]/ai/page.ts:17`
  - `apps/web/.next-phase1check/types/app/[locale]/page.ts:21` · `apps/web/.next-phase1check/types/app/[locale]/about/page.ts:21` · `apps/web/.next-phase1check/types/app/[locale]/accessibility/page.ts:21` · `apps/web/.next-phase1check/types/app/[locale]/ai/page.ts:21`

## ۱۳) مستندات و لایسنس

- README (`README.md`): 433 خط، 49 سرفصل، 9 بلوک کد
- بخش‌های یافت‌شده: نصب, اجرا, تست, مشارکت
- لایسنس: MIT
- پوشهٔ docs: ✅ 218 فایل
- CHANGELOG: — | CONTRIBUTING: —

## ۱۴) فعالیت و تازگی

- فایل‌های تغییر‌کرده در ۷ روز اخیر: 3,262
- فایل‌های تغییر‌کرده در ۳۰ روز اخیر: 635
- جدیدترین فایل: `apps/web/tsconfig.tsbuildinfo`
- فایل‌های خالی: 45 | پوشه‌های خالی: 103

## ۱۵) معماری و نقاط ورود

- سبک شناسایی‌شده: **monorepo (apps/packages)**
- پوشه‌های سطح بالا: `.benchmarks`, `.git-hooks`, `.github`, `.hypothesis`, `.openclaw`, `.snapshots`, `.tmp`, `.turbo`, `DELIVERY`, `_quarantine_bak_2026-09-21`, `adapters`, `alembic`, `analysis.json`, `apps`, `backups`, `benchmarks`, `blockchain`, `brand-assets`, `config`, `contracts`, `data`, `database`, `deploy`, `docs`, `engine`, `foundry`, `helm`, `interfaces`, `k8s`, `lib`, `logs`, `messages`, `ml`, `mobile`, `monitoring`, `packages`, `reports`, `requirements_proposal`, `scripts`, `services`, `supabase`, `testing_lab`, `tests`
- نقاط ورود: —

## ۱۶) هشدارها و سلامت پروژه

- ✅ `.gitignore` کامل است.
- 📁 فایل‌های env (فقط نام کلیدها بررسی شد): `.env`, `.env.example`, `.env.template`, `contracts/.env`, `contracts/.env.example`
- 📝 TODO/FIXME: **13** مورد
  - `apps/web/src/app/[locale]/market/bazaars/actions.ts:26` — TODO: POST to /api/v1/bazaars/establish
  - `apps/web/src/app/[locale]/market/bazaars/actions.ts:55` — TODO: POST to /api/v1/bazaars/{bazaarId}/signatures
  - `apps/web/src/app/[locale]/market/bazaars/actions.ts:76` — TODO: POST to /api/v1/bazaars/{bazaarId}/verify
  - `lib/forge-std/scripts/vm.py:77` — TODO: Custom errors were introduced in 0.8.4
  - `lib/forge-std/scripts/vm.py:143` — HACK: A way to add group header comments without having to modify printer code
  - `lib/openzeppelin-contracts/hardhat.config.js:96` — XXX will be promoted to keyword in the future and will not be allowed as an identifier any
- 🖥️ console.log در فرانت: 9 مورد — بیشترین: `apps/web/.next-phase1check/server/chunks/233.js` (2), `apps/web/.next-phase1check/server/chunks/740.js` (2), `apps/web/.next-phase1check/static/chunks/954-df7d1176549ad01b.js` (2)
- 🐍 print() در پایتون: 61 مورد (در پروداکشن از logging استفاده شود)
- 🔗 آدرس localhost هاردکد: 44 مورد — بیشترین: `engine/hydroma/config/settings.py` (9), `tests/load/locustfile.py` (2), `tests/unit/test_phase1_cors.py` (2), `apps/web/next.config.ts` (1), `apps/web/playwright.config.ts` (1)
- ❌ تستی برای فرانت‌اند وجود ندارد (پیشنهاد: Vitest + Testing Library).
- 📦 فایل حجیم: `foundry.zip` (105.1 MB)
- 📦 فایل حجیم: `foundry/forge.exe` (83.2 MB)
- 📦 فایل حجیم: `foundry/cast.exe` (60.4 MB)
- 📦 فایل حجیم: `foundry/chisel.exe` (41.9 MB)
- 📦 فایل حجیم: `apps/web/.next-phase1check/cache/webpack/server-production/0.pack` (41.4 MB)

## ۱۷) امتیازدهی تفصیلی

**امتیاز نهایی: 52/100 — گرید D 🟠**

| کسر | دلیل |
|---:|---|
| -30 | 10 یافتهٔ امنیتی با شدت بالا |
| -10 | 20 یافتهٔ امنیتی با شدت متوسط |
| -6 | تست فرانت‌اند وجود ندارد |
| -2 | print() (61 مورد) |
| -0 | console.log (9 مورد) |
| -0 | TODO/FIXME (13 مورد) |

## ۱۸) اقدامات پیشنهادی

1. رسیدگی به یافته‌های امنیتی بخش ۹؛ انتقال کلیدها به متغیر محیطی و افزودن gitleaks به CI
2. افزودن Vitest و Testing Library برای تست فرانت‌اند
3. Lazy loading مسیرها برای کاهش حجم باندل اولیه
4. جایگزینی exceptهای خام با استثناهای مشخص + لاگ خطا
5. کاهش استفاده از `any` در TypeScript (فعال‌کردن strict mode)
6. بازآرایی (refactor) بلوک‌های تکراری به توابع/ماژول مشترک
7. اجرای `npx depcheck` برای یافتن وابستگی‌های بلااستفاده
8. اجرای `npx vite-bundle-visualizer` برای تحلیل حجم باندل
