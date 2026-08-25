# 📊 گزارش تحلیل ماژول‌های Skeleton - فاز ۳

**تاریخ:** 2026-08-25 19:17:01

**اصل:** Chesterton's Fence - قبل از اقدام، باید بدانیم چرا هر ماژول ناقص است.

---

## 🎯 خلاصه اجرایی

| اقدام پیشنهادی | تعداد | اولویت‌های بالا |
|---|---|---|
| 🚨 تکمیل فوری | 4 | 4 |
| ✅ تکمیل | 0 | 0 |
| 🔧 بهبود | 1 | 0 |
| 👁️ بررسی | 17 | 2 |
| 🔍 بررسی Placeholder | 0 | 0 |
| 🗑️ کاندید حذف | 0 | 0 |

---

## 📊 ماتریس اولویت (Business Priority × Maturity)

| ماژول | Priority | Maturity | Effort | Files | Lines | اقدام پیشنهادی |
|---|---|---|---|---|---|---|
| **analytics** | 10/10 | 1/10 | Medium | 2 | 107 | 🚨 تکمیل فوری |
| **auth** | 9/10 | 1/10 | Medium | 4 | 32 | 🚨 تکمیل فوری |
| **admin** | 8/10 | 1/10 | Medium | 1 | 109 | 🚨 تکمیل فوری |
| **reporting** | 8/10 | 2/10 | Medium | 4 | 65 | 🚨 تکمیل فوری |
| **bots** | 7/10 | 3/10 | High | 20 | 1479 | 👁️ بررسی |
| **satellite** | 7/10 | 3/10 | High | 8 | 2548 | 👁️ بررسی |
| **map_engine** | 6/10 | 3/10 | High | 18 | 2782 | 👁️ بررسی |
| **telegram_bot** | 6/10 | 3/10 | High | 11 | 1589 | 👁️ بررسی |
| **carbon** | 5/10 | 1/10 | Medium | 3 | 152 | 🔧 بهبود |
| **design_engine** | 5/10 | 2/10 | Medium | 2 | 257 | 👁️ بررسی |
| **scientific_motors** | 5/10 | 3/10 | High | 18 | 6377 | 👁️ بررسی |
| **ledger** | 4/10 | 3/10 | Medium | 5 | 198 | 👁️ بررسی |
| **science** | 4/10 | 1/10 | High | 5 | 321 | 👁️ بررسی |
| **workflow** | 4/10 | 2/10 | Medium | 4 | 65 | 👁️ بررسی |
| **field_monitoring** | 3/10 | 2/10 | Medium | 1 | 144 | 👁️ بررسی |
| **mobile_monitoring** | 3/10 | 2/10 | Medium | 1 | 146 | 👁️ بررسی |
| **supabase** | 3/10 | 2/10 | Medium | 3 | 151 | 👁️ بررسی |
| **content** | 2/10 | 1/10 | Medium | 2 | 164 | 👁️ بررسی |
| **data_sources** | 2/10 | 1/10 | Medium | 2 | 232 | 👁️ بررسی |
| **api_gateway** | 1/10 | 3/10 | High | 40 | 9489 | 👁️ بررسی |
| **business_modules** | 1/10 | 2/10 | High | 17 | 1804 | 👁️ بررسی |
| **models** | 1/10 | 3/10 | High | 8 | 839 | 👁️ بررسی |

---

## 🚨 تکمیل فوری (4 ماژول)

### 📦 `analytics`

- **مسیر:** `services/analytics/`
- **Priority کسب‌وکاری:** 10/10
- **Maturity:** 1/10
- **تعداد فایل:** 2
- **تعداد خطوط:** 107
- **تعداد Classes:** 0
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**وابستگی‌های خارجی:** `__future__`

---

### 📦 `auth`

- **مسیر:** `services/auth/`
- **Priority کسب‌وکاری:** 9/10
- **Maturity:** 1/10
- **تعداد فایل:** 4
- **تعداد خطوط:** 32
- **تعداد Classes:** 1
- **Service Classes:** 1
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `AuthService` in `service.py` (2 methods)

**وابستگی‌های داخلی:** `database.models`

---

### 📦 `admin`

- **مسیر:** `services/admin/`
- **Priority کسب‌وکاری:** 8/10
- **Maturity:** 1/10
- **تعداد فایل:** 1
- **تعداد خطوط:** 109
- **تعداد Classes:** 3
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `ProjectStatus` in `nojin_admin.py` (0 methods)
- `MaterialInventory` in `nojin_admin.py` (0 methods)
- `SystemHealth` in `nojin_admin.py` (0 methods)

---

### 📦 `reporting`

- **مسیر:** `services/reporting/`
- **Priority کسب‌وکاری:** 8/10
- **Maturity:** 2/10
- **تعداد فایل:** 4
- **تعداد خطوط:** 65
- **تعداد Classes:** 5
- **Service Classes:** 1
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `BaseReporting` in `models.py` (0 methods)
- `ReportingCreate` in `models.py` (0 methods)
- `ReportingRead` in `models.py` (0 methods)
- `ReportingUpdate` in `models.py` (0 methods)
- `ReportingService` in `service.py` (2 methods)

---

## 🔧 بهبود (1 ماژول)

### 📦 `carbon`

- **مسیر:** `services/carbon/`
- **Priority کسب‌وکاری:** 5/10
- **Maturity:** 1/10
- **تعداد فایل:** 3
- **تعداد خطوط:** 152
- **تعداد Classes:** 0
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**وابستگی‌های خارجی:** `__future__`, `database`

---

## 👁️ بررسی (17 ماژول)

### 📦 `bots`

- **مسیر:** `services/bots/`
- **Priority کسب‌وکاری:** 7/10
- **Maturity:** 3/10
- **تعداد فایل:** 20
- **تعداد خطوط:** 1479
- **تعداد Classes:** 10
- **Service Classes:** 1
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `BotConfig` in `config.py` (3 methods)
- `PlatformSpec` in `platforms.py` (0 methods)
- `BaleGateway` in `adapters\bale.py` (4 methods)
- `RubikaGateway` in `adapters\rubika.py` (3 methods)
- `WhatsAppAdapter` in `adapters\whatsapp.py` (5 methods)
- `OllamaClient` in `core\ai.py` (3 methods)
- `AdviceService` in `core\ai.py` (2 methods)
- `AlertRule` in `core\alerts.py` (0 methods)
- `FarmRegister` in `handlers\farm.py` (0 methods)
- `FarmDraft` in `handlers\farm.py` (0 methods)

**وابستگی‌های داخلی:** `database.config`, `database.models`, `engine.hydroma.ai_assistant.rag_engine`, `services.bots.core.alerts`, `services.bots.core.dispatcher`

**وابستگی‌های خارجی:** `__future__`, `adapters`, `aiogram`, `config`, `core`, `database`, `dataclasses`, `factory`, `handlers`, `platforms`

---

### 📦 `satellite`

- **مسیر:** `services/satellite/`
- **Priority کسب‌وکاری:** 7/10
- **Maturity:** 3/10
- **تعداد فایل:** 8
- **تعداد خطوط:** 2548
- **تعداد Classes:** 22
- **Service Classes:** 4
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `DataStoreError` in `cds.py` (0 methods)
- `DataStoreNotConfigured` in `cds.py` (0 methods)
- `DataStoreRequestError` in `cds.py` (0 methods)
- `DataStoreClient` in `cds.py` (7 methods)
- `CdsClient` in `cds.py` (1 methods)
- `CopernicusError` in `copernicus.py` (0 methods)
- `CopernicusNotConfigured` in `copernicus.py` (0 methods)
- `CopernicusFetchError` in `copernicus.py` (0 methods)
- `CopernicusBandError` in `copernicus.py` (0 methods)
- `Scene` in `copernicus.py` (1 methods)
- ... و 12 مورد دیگر

**وابستگی‌های داخلی:** `database.config`, `database.models`, `engine.hydroma.crop.ndvi_analysis`, `engine.hydroma.soil.moisture`, `engine.hydroma.water.surface_area`, `services.satellite.cds`

**وابستگی‌های خارجی:** `__future__`, `dataclasses`, `enum`, `pathlib`, `rasterio`

---

### 📦 `map_engine`

- **مسیر:** `services/map_engine/`
- **Priority کسب‌وکاری:** 6/10
- **Maturity:** 3/10
- **تعداد فایل:** 18
- **تعداد خطوط:** 2782
- **تعداد Classes:** 18
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `MapType` in `base.py` (0 methods)
- `MapRequest` in `base.py` (0 methods)
- `MapResult` in `base.py` (1 methods)
- `MapPipeline` in `base.py` (5 methods)
- `MapFetcher` in `base.py` (2 methods)
- `MapOrchestrator` in `orchestrator.py` (13 methods)
- `SmartMapGenerator` in `smart_mapper.py` (5 methods)
- `DEMFetcher` in `fetchers\dem_fetcher.py` (7 methods)
- `LandCoverFetcher` in `fetchers\landcover_fetcher.py` (5 methods)
- `RainfallFetcher` in `fetchers\rainfall_fetcher.py` (5 methods)
- ... و 8 مورد دیگر

**وابستگی‌های خارجی:** `__future__`, `abc`, `base`, `dataclasses`, `enum`, `fetchers`, `pathlib`, `pipelines`, `shapely`, `uuid`

---

### 📦 `telegram_bot`

- **مسیر:** `services/telegram_bot/`
- **Priority کسب‌وکاری:** 6/10
- **Maturity:** 3/10
- **تعداد فایل:** 11
- **تعداد خطوط:** 1589
- **تعداد Classes:** 4
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `PlatformAPIClient` in `api_client.py` (5 methods)
- `HydromaTelegramBot` in `bot.py` (5 methods)
- `BotConfig` in `config.py` (1 methods)
- `HydromaBotIntegration` in `integration.py` (3 methods)

**وابستگی‌های داخلی:** `services.scientific_motors.base`, `services.scientific_motors.crop_advisor`, `services.scientific_motors.erosion_rusle`, `services.scientific_motors.irrigation_scheduler`, `services.scientific_motors.mrv_system`, `services.scientific_motors.planting_calendar`, `services.scientific_motors.satellite_integration`

**وابستگی‌های خارجی:** `__future__`, `aiogram`, `aiohttp_socks`, `api_client`, `config`, `dotenv`, `formatters`, `handlers`, `i18n`, `integration`

---

### 📦 `design_engine`

- **مسیر:** `services/design_engine/`
- **Priority کسب‌وکاری:** 5/10
- **Maturity:** 2/10
- **تعداد فایل:** 2
- **تعداد خطوط:** 257
- **تعداد Classes:** 7
- **Service Classes:** 7
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `IrrigationScheduleItem` in `irrigation_design_service.py` (0 methods)
- `IrrigationDesignInput` in `irrigation_design_service.py` (0 methods)
- `IrrigationDesignOutput` in `irrigation_design_service.py` (0 methods)
- `IrrigationDesigner` in `irrigation_design_service.py` (3 methods)
- `StructureDesignInput` in `water_structure_design_service.py` (0 methods)
- `StructureDesignOutput` in `water_structure_design_service.py` (0 methods)
- `StructureDesigner` in `water_structure_design_service.py` (4 methods)

**وابستگی‌های خارجی:** `__future__`, `pathlib`, `shapely`, `uuid`

---

### 📦 `scientific_motors`

- **مسیر:** `services/scientific_motors/`
- **Priority کسب‌وکاری:** 5/10
- **Maturity:** 3/10
- **تعداد فایل:** 18
- **تعداد خطوط:** 6377
- **تعداد Classes:** 51
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `AquaCropMotor` in `aquacrop.py` (9 methods)
- `MotorType` in `base.py` (0 methods)
- `MotorStatus` in `base.py` (0 methods)
- `MotorInput` in `base.py` (0 methods)
- `MotorOutput` in `base.py` (0 methods)
- `MotorParameters` in `base.py` (0 methods)
- `MotorResult` in `base.py` (1 methods)
- `AbstractScientificMotor` in `base.py` (7 methods)
- `BiofertilizerType` in `biofertilizer.py` (0 methods)
- `BiofertilizerRecommendation` in `biofertilizer.py` (0 methods)
- ... و 41 مورد دیگر

**وابستگی‌های داخلی:** `engine.hydroma.carbon.calculator`, `engine.hydroma.cpp_bridge`, `engine.hydroma.mrv.metrics`, `engine.hydroma.simulation.runners.rothc_runner`

**وابستگی‌های خارجی:** `__future__`, `abc`, `base`, `crop_database`, `dataclasses`, `enum`, `hydroma`, `pathlib`, `satellite`, `satellite_integration`

---

### 📦 `ledger`

- **مسیر:** `services/ledger/`
- **Priority کسب‌وکاری:** 4/10
- **Maturity:** 3/10
- **تعداد فایل:** 5
- **تعداد خطوط:** 198
- **تعداد Classes:** 6
- **Service Classes:** 1
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `BaseLedger` in `models.py` (0 methods)
- `LedgerCreate` in `models.py` (0 methods)
- `LedgerRead` in `models.py` (0 methods)
- `LedgerUpdate` in `models.py` (0 methods)
- `PQUnavailableError` in `pqc.py` (0 methods)
- `LedgerService` in `service.py` (2 methods)

**وابستگی‌های خارجی:** `__future__`, `cryptography`

---

### 📦 `science`

- **مسیر:** `services/science/`
- **Priority کسب‌وکاری:** 4/10
- **Maturity:** 1/10
- **تعداد فایل:** 5
- **تعداد خطوط:** 321
- **تعداد Classes:** 2
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `ZenodoClient` in `zenodo.py` (6 methods)
- `ZenodoError` in `zenodo.py` (0 methods)

**وابستگی‌های داخلی:** `services.models.registry`

**وابستگی‌های خارجی:** `__future__`

---

### 📦 `workflow`

- **مسیر:** `services/workflow/`
- **Priority کسب‌وکاری:** 4/10
- **Maturity:** 2/10
- **تعداد فایل:** 4
- **تعداد خطوط:** 65
- **تعداد Classes:** 5
- **Service Classes:** 1
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `BaseWorkflow` in `models.py` (0 methods)
- `WorkflowCreate` in `models.py` (0 methods)
- `WorkflowRead` in `models.py` (0 methods)
- `WorkflowUpdate` in `models.py` (0 methods)
- `WorkflowService` in `service.py` (2 methods)

---

### 📦 `field_monitoring`

- **مسیر:** `services/field_monitoring/`
- **Priority کسب‌وکاری:** 3/10
- **Maturity:** 2/10
- **تعداد فایل:** 1
- **تعداد خطوط:** 144
- **تعداد Classes:** 3
- **Service Classes:** 3
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `FieldDataType` in `service.py` (0 methods)
- `FieldMonitoringReport` in `service.py` (0 methods)
- `FieldMonitoringService` in `service.py` (5 methods)

**وابستگی‌های داخلی:** `database.config`, `database.models`, `engine.hydroma.soil.health`, `engine.hydroma.soil.moisture`, `engine.hydroma.water.quality`

**وابستگی‌های خارجی:** `dataclasses`, `enum`

---

### 📦 `mobile_monitoring`

- **مسیر:** `services/mobile_monitoring/`
- **Priority کسب‌وکاری:** 3/10
- **Maturity:** 2/10
- **تعداد فایل:** 1
- **تعداد خطوط:** 146
- **تعداد Classes:** 3
- **Service Classes:** 3
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `MobileReportType` in `service.py` (0 methods)
- `MobileMonitoringReport` in `service.py` (0 methods)
- `MobileMonitoringService` in `service.py` (5 methods)

**وابستگی‌های داخلی:** `database.config`, `database.models`, `engine.hydroma.soil.health`, `engine.hydroma.soil.moisture`, `engine.hydroma.water.quality`

**وابستگی‌های خارجی:** `dataclasses`, `enum`

---

### 📦 `supabase`

- **مسیر:** `services/supabase/`
- **Priority کسب‌وکاری:** 3/10
- **Maturity:** 2/10
- **تعداد فایل:** 3
- **تعداد خطوط:** 151
- **تعداد Classes:** 4
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `PlatformLandscape` in `models.py` (0 methods)
- `PlatformProfile` in `models.py` (0 methods)
- `PlatformCarbonProject` in `models.py` (0 methods)
- `PlatformCarbonCredit` in `models.py` (0 methods)

**وابستگی‌های خارجی:** `dataclasses`, `dotenv`, `pathlib`, `supabase`, `uuid`

---

### 📦 `content`

- **مسیر:** `services/content/`
- **Priority کسب‌وکاری:** 2/10
- **Maturity:** 1/10
- **تعداد فایل:** 2
- **تعداد خطوط:** 164
- **تعداد Classes:** 0
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**وابستگی‌های خارجی:** `__future__`, `database`

---

### 📦 `data_sources`

- **مسیر:** `services/data_sources/`
- **Priority کسب‌وکاری:** 2/10
- **Maturity:** 1/10
- **تعداد فایل:** 2
- **تعداد خطوط:** 232
- **تعداد Classes:** 1
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `CopernicusCDSClient` in `copernicus_cds.py` (7 methods)

**وابستگی‌های خارجی:** `__future__`, `pathlib`

---

### 📦 `api_gateway`

- **مسیر:** `services/api_gateway/`
- **Priority کسب‌وکاری:** 1/10
- **Maturity:** 3/10
- **تعداد فایل:** 40
- **تعداد خطوط:** 9489
- **تعداد Classes:** 100
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `RateLimitMiddleware` in `security.py` (2 methods)
- `SecurityHeadersMiddleware` in `security.py` (1 methods)
- `RequestIDMiddleware` in `security.py` (1 methods)
- `ChannelStatus` in `routers\admin.py` (0 methods)
- `HealthResponse` in `routers\admin.py` (0 methods)
- `AdminUserOut` in `routers\admin.py` (0 methods)
- `AuditOut` in `routers\admin.py` (0 methods)
- `ActionResponse` in `routers\admin.py` (0 methods)
- `ContentCreate` in `routers\admin.py` (0 methods)
- `ContentUpdate` in `routers\admin.py` (0 methods)
- ... و 90 مورد دیگر

**وابستگی‌های داخلی:** `database.config`, `database.models`, `engine.hydroma`, `engine.hydroma.ai_assistant.rag_engine`, `engine.hydroma.analyses.topography_analysis`, `engine.hydroma.biofertilizer.advanced_calculator`, `engine.hydroma.biofertilizer.data`, `engine.hydroma.biofertilizer.models`, `engine.hydroma.biofertilizer.repositories`, `engine.hydroma.calculations.crop_water_req_calc`

**وابستگی‌های خارجی:** `__future__`, `auth`, `collections`, `contextlib`, `database`, `dependencies`, `jose`, `models`, `passlib`, `routers`

---

### 📦 `business_modules`

- **مسیر:** `services/business_modules/`
- **Priority کسب‌وکاری:** 1/10
- **Maturity:** 2/10
- **تعداد فایل:** 17
- **تعداد خطوط:** 1804
- **تعداد Classes:** 29
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `ProjectStatus` in `blockchain\carbon_registry.py` (0 methods)
- `CarbonProject` in `blockchain\carbon_registry.py` (0 methods)
- `CarbonCredit` in `blockchain\carbon_registry.py` (0 methods)
- `CarbonRegistry` in `blockchain\carbon_registry.py` (12 methods)
- `BlockchainLedger` in `blockchain\ledger.py` (5 methods)
- `TraceEvent` in `blockchain\supply_chain.py` (0 methods)
- `TracedProduct` in `blockchain\supply_chain.py` (0 methods)
- `SupplyChainRegistry` in `blockchain\supply_chain.py` (9 methods)
- `Web3Provider` in `blockchain\web3_provider.py` (4 methods)
- `IndexInsuranceResult` in `insurance\index_insurance.py` (0 methods)
- ... و 19 مورد دیگر

**وابستگی‌های داخلی:** `engine.hydroma.ai_assistant.rag_engine`

**وابستگی‌های خارجی:** `__future__`, `dataclasses`, `engine`, `enum`, `eth_tester`, `stt_provider`, `tts_provider`, `web3`, `web3_provider`

---

### 📦 `models`

- **مسیر:** `services/models/`
- **Priority کسب‌وکاری:** 1/10
- **Maturity:** 3/10
- **تعداد فایل:** 8
- **تعداد خطوط:** 839
- **تعداد Classes:** 7
- **Service Classes:** 0
- **README:** ❌
- **Commits:** 0
- **آخرین تغییر:** N/A

**Classes:**
- `CppBridgeUnavailable` in `cpp_bridge.py` (0 methods)
- `LandProfileDB` in `land_models.py` (0 methods)
- `TerrainAnalysisDB` in `land_models.py` (0 methods)
- `LandCapabilityAssessmentDB` in `land_models.py` (0 methods)
- `PINNSurrogate` in `pinn_surrogate.py` (3 methods)
- `ParamSpec` in `registry.py` (0 methods)
- `ModelSpec` in `registry.py` (1 methods)

**وابستگی‌های داخلی:** `engine.hydroma.carbon.calculator`, `engine.hydroma.climate.et_calculator`, `engine.hydroma.scenarios.climate_scenarios`, `engine.hydroma.scenarios.crop_scenarios`, `engine.hydroma.soil.health`, `engine.hydroma.soil.pedotransfer`, `engine.hydroma.soil.physics`, `engine.hydroma.soil.salinity`, `engine.hydroma.watershed.calculator`, `engine.hydroma.wrapper`

**وابستگی‌های خارجی:** `__future__`, `base`, `dataclasses`

---

## 🗺️ نقشه راه پیشنهادی فاز ۳

### موج ۱: تکمیل فوری (۱-۲ هفته)

- **analytics** (Priority 10)
- **auth** (Priority 9)
- **admin** (Priority 8)
- **reporting** (Priority 8)

### موج ۲: تکمیل (۲-۳ هفته)


### موج ۳: بهبود (تدریجی)

- **carbon** (Priority 5)

### کاندید حذف (پس از بررسی)


---

*این گزارش فقط تحلیلی است و هیچ تغییری اعمال نکرده است.*
*گام بعدی: اسکریپت `phase3_complete_priority_modules.py` برای تکمیل ماژول‌های موج ۱*
