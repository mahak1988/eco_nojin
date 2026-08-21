# گزارش تحلیل عمیق پروژه Eco Nojin
**تاریخ تحلیل:** 2026-08-21T23:22:34.371415
**مسیر پروژه:** D:\eco_nojin

## ⚠️ تخلفات معماری شناسایی‌شده (Architecture Violations)
- 🔴 **DOMAIN_COUPLING** در `engine/hydroma/blockchain`: ماژول کسب‌وکار در لایه موتور علمی قرار دارد. (Severity: HIGH)
- 🔴 **DOMAIN_COUPLING** در `engine/hydroma/ecowallet`: ماژول کسب‌وکار در لایه موتور علمی قرار دارد. (Severity: HIGH)
- 🔴 **DOMAIN_COUPLING** در `engine/hydroma/insurance`: ماژول کسب‌وکار در لایه موتور علمی قرار دارد. (Severity: HIGH)
- 🔴 **DOMAIN_COUPLING** در `engine/hydroma/marketplace`: ماژول کسب‌وکار در لایه موتور علمی قرار دارد. (Severity: HIGH)
- 🔴 **DOMAIN_COUPLING** در `engine/hydroma/ussd`: ماژول کسب‌وکار در لایه موتور علمی قرار دارد. (Severity: HIGH)
- 🔴 **DOMAIN_COUPLING** در `engine/hydroma/voice`: ماژول کسب‌وکار در لایه موتور علمی قرار دارد. (Severity: HIGH)

## 📊 وضعیت دامنه‌های موتور علمی (HyDroMa Domains)
| دامنه (Domain) | وضعیت کلی | تعداد فایل‌های اصلی | جزئیات |
|---|---|---|---|
| **ai_assistant** | `EXISTS/PARTIAL` | 4 | engine\hydroma\ai_assistant\knowledge_base.py (PARTIAL/EXISTS), engine\hydroma\ai_assistant\rag_engine.py (PARTIAL/EXISTS), engine\hydroma\ai_assistant\rag_service.py (STUB/MOCK) |
| **api** | `MISSING/EMPTY` | 1 |  |
| **blockchain** | `PARTIAL (Heavy Stubbing)` | 6 | engine\hydroma\blockchain\carbon_registry.py (STUB/MOCK), engine\hydroma\blockchain\ledger.py (PARTIAL/EXISTS), engine\hydroma\blockchain\supply_chain.py (STUB/MOCK) ... |
| **carbon** | `EXISTS/PARTIAL` | 2 | engine\hydroma\carbon\calculator.py (PARTIAL/EXISTS) |
| **climate** | `STUB/MOCK` | 2 | engine\hydroma\climate\et_calculator.py (STUB/MOCK) |
| **config** | `STUB/MOCK` | 2 | engine\hydroma\config\settings.py (STUB/MOCK) |
| **core** | `PARTIAL (Heavy Stubbing)` | 4 | engine\hydroma\core\database.py (STUB/MOCK), engine\hydroma\core\models.py (PARTIAL/EXISTS), engine\hydroma\core\schemas.py (STUB/MOCK) |
| **cpp_bridge** | `PARTIAL (Heavy Stubbing)` | 4 | engine\hydroma\cpp_bridge\hydrology_fast.py (STUB/MOCK), engine\hydroma\cpp_bridge\indices_fast.py (STUB/MOCK), engine\hydroma\cpp_bridge\soil_physics_fast.py (PARTIAL/EXISTS) |
| **crop** | `STUB/MOCK` | 4 | engine\hydroma\crop\models.py (STUB/MOCK) |
| **data_ingestion** | `STUB/MOCK` | 4 | engine\hydroma\data_ingestion\models.py (STUB/MOCK) |
| **ecotourism** | `STUB/MOCK` | 4 | engine\hydroma\ecotourism\models.py (STUB/MOCK) |
| **ecowallet** | `EXISTS/PARTIAL` | 5 | engine\hydroma\ecowallet\earning_rules.py (PARTIAL/EXISTS), engine\hydroma\ecowallet\ledger.py (PARTIAL/EXISTS), engine\hydroma\ecowallet\messages.py (PARTIAL/EXISTS) ... |
| **erosion** | `STUB/MOCK` | 4 | engine\hydroma\erosion\models.py (STUB/MOCK) |
| **finance** | `STUB/MOCK` | 4 | engine\hydroma\finance\models.py (STUB/MOCK) |
| **geospatial** | `STUB/MOCK` | 4 | engine\hydroma\geospatial\models.py (STUB/MOCK) |
| **groundwater** | `STUB/MOCK` | 4 | engine\hydroma\groundwater\models.py (STUB/MOCK) |
| **hydrology** | `STUB/MOCK` | 4 | engine\hydroma\hydrology\models.py (STUB/MOCK) |
| **insurance** | `EXISTS/PARTIAL` | 2 | engine\hydroma\insurance\index_insurance.py (PARTIAL/EXISTS) |
| **marketplace** | `EXISTS/PARTIAL` | 5 | engine\hydroma\marketplace\models.py (PARTIAL/EXISTS), engine\hydroma\marketplace\order_management.py (PARTIAL/EXISTS), engine\hydroma\marketplace\product_catalog.py (PARTIAL/EXISTS) ... |
| **materials** | `EXISTS/PARTIAL` | 2 | engine\hydroma\materials\compost_formulator.py (PARTIAL/EXISTS) |
| **ml** | `STUB/MOCK` | 4 | engine\hydroma\ml\models.py (STUB/MOCK) |
| **mrv** | `PARTIAL (Heavy Stubbing)` | 9 | engine\hydroma\mrv\iot_ingest.py (STUB/MOCK), engine\hydroma\mrv\metrics.py (STUB/MOCK), engine\hydroma\mrv\models.py (STUB/MOCK) ... |
| **performance** | `EXISTS/PARTIAL` | 2 | engine\hydroma\performance\benchmarks.py (PARTIAL/EXISTS) |
| **plants** | `STUB/MOCK` | 4 | engine\hydroma\plants\models.py (STUB/MOCK) |
| **risk** | `STUB/MOCK` | 4 | engine\hydroma\risk\models.py (STUB/MOCK) |
| **satellite** | `EXISTS/PARTIAL` | 8 | engine\hydroma\satellite\analyzer.py (PARTIAL/EXISTS), engine\hydroma\satellite\processors\indices.py (PARTIAL/EXISTS), engine\hydroma\satellite\providers\base.py (STUB/MOCK) ... |
| **scenario** | `MISSING/EMPTY` | 1 |  |
| **scenarios** | `EXISTS/PARTIAL` | 5 | engine\hydroma\scenarios\climate_scenarios.py (PARTIAL/EXISTS), engine\hydroma\scenarios\crop_scenarios.py (PARTIAL/EXISTS), engine\hydroma\scenarios\monte_carlo.py (PARTIAL/EXISTS) ... |
| **simulation** | `PARTIAL (Heavy Stubbing)` | 11 | engine\hydroma\simulation\calibration.py (PARTIAL/EXISTS), engine\hydroma\simulation\contracts.py (STUB/MOCK), engine\hydroma\simulation\orchestrator.py (STUB/MOCK) ... |
| **soil** | `EXISTS/PARTIAL` | 13 | engine\hydroma\soil\chemistry.py (PARTIAL/EXISTS), engine\hydroma\soil\health.py (PARTIAL/EXISTS), engine\hydroma\soil\models.py (STUB/MOCK) ... |
| **standards** | `STUB/MOCK` | 4 | engine\hydroma\standards\models.py (STUB/MOCK) |
| **ussd** | `STUB/MOCK` | 3 | engine\hydroma\ussd\engine.py (STUB/MOCK), engine\hydroma\ussd\sms_parser.py (STUB/MOCK) |
| **voice** | `PARTIAL (Heavy Stubbing)` | 5 | engine\hydroma\voice\ivr_engine.py (STUB/MOCK), engine\hydroma\voice\stt_provider.py (STUB/MOCK), engine\hydroma\voice\tts_provider.py (STUB/MOCK) ... |
| **watershed** | `EXISTS/PARTIAL` | 2 | engine\hydroma\watershed\calculator.py (PARTIAL/EXISTS) |
| **web_search** | `STUB/MOCK` | 4 | engine\hydroma\web_search\models.py (STUB/MOCK) |
| **cpp_core** | EXISTS | 10 فایل hpp | هسته محاسباتی |

## 🔍 دامنه‌های مورد انتظار اما یافت‌نشده (Missing Domains)
- ❌ `irrigation`
- ❌ `infrastructure`
- ❌ `economics`

---
*این گزارش توسط Eco Nojin Auditor v1.0 تولید شده است.*