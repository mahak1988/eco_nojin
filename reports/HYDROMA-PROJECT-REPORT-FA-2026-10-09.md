# گزارش جامع پروژه HyDroMA (اکو نوژین / Eco Nojin)

**تاریخ بررسی:** ۲۰۲۶-۱۰-۰۹ · **HEAD:** `d6fac05` (ECO-02 Track C2) · **روش:** بازرسی مستقیم فایل‌ها + اجرای زنده تست، lint، mypy و import-guard

---

## ۱. مشخصات کلی

| مورد | مقدار |
|---|---|
| نام بسته (`pyproject.toml`) | `hydroma` v0.1.0 — «Scientific water-energy-agriculture modeling engine» |
| مجوز / Python | MIT / ≥3.11 ( interpreter فعال: 3.12.10 در `D:\eco_nojin\.venv`) |
| وابستگی‌های هسته | numpy≥1.26, scipy≥1.11, pandas≥2.0, duckdb≥0.10, supabase≥2.0, requests, httpx, pydantic≥2, loguru |
| اختیاری | cpp: pybind11/ninja/cmake · ml: torch/transformers/sentence-transformers/qdrant-client |
| نصب تست | pytest, pytest-cov, pytest-asyncio, hypothesis, mypy, ruff |

**آمار کد (شمارش مستقیم، بدون venv/cache):**

| بخش | فایل .py | خط |
|---|---|---|
| `engine/` | 306 | 67,758 |
| `services/` | 648 | 93,571 |
| `adapters/` | 3 | 268 |
| `database/` | 5 | 268 |
| `alembic/` | 4 | 254 |
| `tools/` | 5 | 1,773 |
| **جمع مخزن** | **971** | — |

تاریخچه git: ۴ کامیت؛ ۱۰ فایل تغییرنیافته (uncommitted) شامل `database/*` و `engine/hydroma/biofertilizer/*`.

---

## ۲. معماری و قواعد ساختاری

زنجیره معماری (طبق `HYDROMA-MASTER.md` §۶): منابع داده → Data Integration → Validation → **Knowledge Engine** → **Model Registry** → **Scientific Engine** → **Evidence Engine** → **Decision Engine** → **API/Gateway** ← دانشیار/تصمیم‌یار → زنجیره شواهد → آداپتورهای ثبت خارجی.

**قواعد بایگانی (invariants) — قابل اجرا با `tools/detect_imports.py`:**
- INV-001: `engine` → `services` ممنوع
- INV-002: `engine` → `database` ممنوع (استثنای مجاز: `database.config`، `database.base`)
- INV-003: `services` → `engine.hydroma`/`engine.cpp_core`/`engine.ports` ممنوع؛ دسترسی فقط از طریق `EngineGateway` یا `services/_gateway_facade.py`
- AI-isolation: `services.ai` → engine ممنوع

**نتیجه اجرای زنده محافظ معماری: PASS — ۰ تخلف در ۹۶۹ فایل، ۲۴۰ دایرکتوری، ۸ قانون.**

---

## ۳. موتور علمی `engine/`

### ۳.۱ `engine/hydroma/` — هسته محاسباتی (۲۸ زیربسته)

مدل‌ها و معادلات پیاده‌سازی‌شده با مراجع علمی:

| حوزه | مدل/معادله | فایل |
|---|---|---|
| اقلیم | FAO-56 Penman-Monteith (eq.39)، Hargreaves (eq.52، توان ۰.۴۸)، تابش خارج‌زمینی (eq.21)، فشار بخار (eq.11)، سایکرومتریک (eq.8) | `climate/et_calculator.py` |
| خاک | van Genuchten θ(h) و Mualem K(h)، Brooks-Corey، Campbell، Durner dual-pores، Schaap-van Genuchten؛ جدول ۱۲ بافت USDA از CSV؛ تاکسونومی، CEC/ESP/SAR، شوری، pedotransfer | `soil/physics.py`, `soil/water_retention.py` |
| آب زیرزمینی | Theis (1935): `s = Q/(4πT)·W(u)` با `W(u) = −Ei(−u)` از `scipy.special.expi`؛ مخزن خطی ماهانه | `groundwater/models.py` |
| رواناب | SCS-CN (`S=25400/CN−254`, `Ia=0.2S`, `Q=(P−Ia)²/(P+0.8S)`)، روش گویا، SCS-CN مکانی با rioxarray | `models/runoff_model.py` |
| فرسایش | RUSLE `A=R·K·LS·C·P` با ضریب LS مک‌کول (1987)، R-factor FAO، کارایی تله برون (1953) | `core/core.py`, `land/erosion_risk.py` |
| حوضه | Strahler (Kahn O(V+E))، نسبت‌های هورتون، Kirpich `Tc=0.0195·L^0.77·S^−0.385`، مسیریابی Muskingum با پنجره پایداری `2Kx ≤ dt ≤ 2K(1−x)`؛ طراحی ۵ سازه (سد چک، سنگلیز، نیم‌ماه، تراس، آبگیر) | `watershed/calculator.py` |
| کربن | حسابرسی IPCC 2019 Refinement با ضریب ۰.۸۵ | `carbon/calculator.py` |
| شبیه‌سازی | RothC (`temp_factor = 47.9/(1+exp(106.06/(T+18.27)))`)، runnerهای SWAT/AquaCrop، orchestrator | `simulation/` |
| اقتصاد | NPV، payback، ROI، هزینه/درآمد کشاورزی، ریسک قیمت و محصول | `economics/` |
| سایر | زمان‌بندی آبیاری، آسانسور داده (GBIF + Copernicus CGLS)، ماهواره (NASA POWER, Earth Search)، بیوفورتیلایزر، PINN+GP surrogate، plant_neuro، MRV، scenarios/Monte-Carlo | زیربسته‌های مربوطه |

`engine/hydroma/formulas/catalog.py`: رجیستری ~۱۲۰۰ خط از فرمول‌ها با فیلدهای `canonical`، `literature_ref`، `units`، `status` (`verified`/`divergent`/`stub`) و `stub_reason`.

### ۳.۲ `engine/land/` — هوش زمین

`DEMProcessor` (GeoTIFF)، شیب/جهت Horn ۳×۳، انحنا (Wilson 1986)، TWI (Beven-Kirkby 1975)، TPI، جهت‌یابی جریان D8، تعریف ظرفیت زمین USDA، ارزیابی ریسک فرسایش؛ مدل‌های Pydantic V2 در `land/models.py`؛ مرحله یکپارچه‌سازی ۴ فازی در `land/integration/` (soil/climate/comprehensive/motors_hub).

### ۳.۳ `engine/gateway/__init__.py` (۱۰۸۸ خط) — درگاه واحد دسترسی

`EngineGateway.execute()`: خط لوله ۸ مرحله‌ای (اعتبارسنجی → انتخاب مدل → نرمال‌سازی واحد → اجرا → ثبت شواهد). جداول داده‌ای: `GatewayRequest`/`GatewayResult` با `UnitSpec`، `ProvenanceSpec`، `UncertaintySpec` (پیش‌فرض صادقانه `NOT_ESTIMATED`)، `ExecutionMetadata` (trace_id). **~۷۵ مسیر dispatch واقعی**: CANON-001/002/011→ET₀، CANON-004/008→runoff، CANON-005→Theis، CANON-006/007/009→soil، SOIL_*/ECON_*/WATERSHED_*/MRV_* و … — همه به پیاده‌سازی‌های واقعی وصل‌اند (فقط CANON-016/017 به پل C++ و CANON-003 Thornthwaite `NotImplementedError`).

### ۳.۴ موتورهای شواهد/دانش/تصمیم

- `engine/evidence/__init__.py` (۴۷۵ خط): `Evidence`، `EvidenceEngine` با `validate()`، `to_fact()`، `trace()`، `export_chain()`، `validate_chain_integrity()`.
- `engine/knowledge/__init__.py` (۳۹۷ خط): `Fact`/`Rule`/`Claim`، forward-chaining `derive()` با `confidence = min(premise)·(1+boost)`، `evaluate_claim()`.
- `engine/tasmimyar/__init__.py` (۴۳۰ خط): `DecisionEngine` با معیارهای پیش‌فرض وزن‌دار (evidence_count ۰.۳، evidence_quality ۰.۴، confidence ۰.۳) و نتایج RECOMMEND≥۰.۷ / CAUTION≥۰.۴ / REJECT / INSUFFICIENT_EVIDENCE.
- `engine/models/registry.py` (۷۲۲ خط): `ModelRegistry` با ۲۲ مدل CANON + ~۵۰ مدل فاساد + ۱۶ کارت مدل در `models/cards/`.

### ۳.۵ `engine/ports/` — بندرگاه‌های وابستگی

Protocolهای `SessionPort`، `QueryPort`، `UnitOfWork`، `PersistencePort`، `Clock`/`FixedClock`، `EvidenceAdapter`/`ComputationRecord`، `ReadingSink`/`NullReadingSink`؛ پیاده‌سازی‌های `InMemoryPersistence`/`FileBackedPersistence`. واردات `engine.ports` از database/services/sqlalchemy کاملاً پاک است.

### ۳.۶ `engine/baseline/` — خط مبنای اجرایی

۱۴ حالت مرجع قطعی (soil_retention، climate_et0، runoff، groundwater، watershed…) در `cases.py` با CLI `capture.py --show/--diff/--regenerate` و خروجی ثبت‌شده `R18.json`.

### ۳.۷ `engine/cpp_core/` + `cpp_bridge/`

۱۱ واحد C++ (soil, sediment, sampling, saint_venant, richards, nojin_calculator, indices, hydrology, erosion, crop_water, climate) + bindings pybind11، CMake/setup.py. **باینری‌های کامپایل‌شده `.pyd` برای cp311/cp312-win_amd64 موجودند** (در `engine/hydroma/cpp_bridge/` و `build2/Release/`) و ۱۱ exe تست. اما `engine/README.md` این بخش را *Orphaned* می‌نامد و روی مسیر اجرا اصلی حساب نمی‌شود؛ `cpp_bridge` الگوی fast/fallback با fallback خالص-Python دارد. **هیچ کامپایلر MSVC/Clang و cmake روی PATH نیست** — بازسازی باینری‌ها غیرممکن است.

### ۳.۸ ماژول‌های سطح engine

`data_connector.py` (DuckDB master ۱۳۲ جدول + SQLite تراکنشی ۶۲ جدول + ۱۸ جدول مرجع دستی، با اعتبارسنج white-list شناسه SQL)، `resilience.py` (circuit breaker CLOSED/OPEN/HALF_OPEN، retry، timeout)، `resource_manager.py`، `safe_math.py`، `memory_monitor.py`.

### ۳.۹ تست‌های سخت‌گیرانه `engine/strict_tests/`

۱۵ ماژول S00–S15: S02 ET₀ (فرضیه‌محور با hypothesis)، S03 SCS-CN در برابر مثال حل‌شده NRCS، S04 Theis و توازن جرم، S05 van Genuchten در برابر Saxton-Rawls 2006، S09 همسانی ابعادی، S10 حدود فیزیکی/تکرارپذیری، S11 tripwire هم‌سویی Python↔C++، S12–S14 جداول خاک، S15 provenance. ثابت‌های مرجع در `conftest.py`: `FAO56_REFERENCE_DAY`، `NRCS_SCS_CN_WORKED_EXAMPLE`، `THEIS_REFERENCE`، `SAXTON_RAWLS_2006_AWC_MM_PER_M`، `PHYSICAL_BOUNDS`.

---

## ۴. لایه سرویس‌ها `services/` (۷۹ زیربسته)

**خوشه‌بندی:**

| خوشه | سرویس‌ها |
|---|---|
| آب/زمین/کشاورزی | land، landscape، rangeland، livestock، satellite، field_monitoring، carbon، watershed، ecosystem، restoration، territory |
| مالی/تجاری | finance (Ledger/Wallet/PaymentProvider: Stripe, COD, BankTransfer)، ecowallet، wallet، commerce (بازارچه روستایی)، marketplace، ledger، blockchain (EcoCoin Ledger: تعادل، گواهی اثر، phase-gate، oracle، treasury)، insurance |
| حکمرانی/حقوقی | legal، compliance (KYC/AML)، dispute_resolution، governance، audit |
| دانش/تصمیم | knowledge (Daneshyar)، tasmimyar (از `EngineGateway` استفاده می‌کند)، ai، science، validation |
| پایش | satellite (Sentinel-2/Landsat/MODIS)، mobile_monitoring، alerting، notification |
| یکپارچه‌سازی | integration (Outbox)، ogc (OGC API Features + WaterML 2.0 برای SPI/SPEI)، supabase، data_manual (FAOSTAT، تقویم محصول…)، oracle |
| امنیت | auth (JWT)، security (Spider Firewall ۱۱ لایه: WAF، rate-limit، CSP، PQC، honeypot، ZT-RBAC)، privacy (رمزنگاری سطح فیلد) |
| پلتفرم | api_gateway (FastAPI با ۱۰۱ router)، workers، jobs، observability (OTel+Prometheus)، reliability، backup، map_engine، analytics، reporting |
| سایر | simulation (آکواکراپ/راث‌سی/سوات+)، provenance، mrv (KoboToolbox، مقایسه آزمایشگاه، PDF فارسی)، business_modules (Voice/USSD)، telegram_bot، bots (Bale/Rubika)، tourism، sponsors، admin، inventory، logistics… |

**الگوی دسترسی به engine:** `services/_gateway_facade.py` تنها مسیر مجاز — ۸۰+ تابع wrapper با fallback به gateway. در مجموع ۴۲ فایل `from engine` دارند که عمدتاً `get_settings()` پیکربندی است؛ ۶ استثنا در `tools/import_guard_policy.json` (v1.0.0) ثبت شده، از جمله `engine.hydroma.carbon.calculator` که خودش به‌عنوان **POLICY GAP** علامت‌گذاری شده.

**قراردادهای سرویس:** `services/_contracts/` شامل `formula.py` (S-SCI: محل واحد هر فرمول با اجبار ارجاع)، `money.py` (S-MONEY: Decimal، ISO 4217)، `status.py` (S-HONEST: پاکت `Tainted[T]` با وضعیت‌های OK/DEGRADED/STALE/UNAVAILABLE/NOT_IMPLEMENTED و `assert_honest()`). `services/contracts/` رجیستری نسخه‌بندی قرارداد با diff سازگاری OpenAPI.

---

## ۵. پایگاه داده و مهاجرت

- `database/base.py`: `Base` واحد مشترک (یک MetaData برای create_all و Alembic).
- `database/config.py`: موتور SQLite حافظه‌ای با `StaticPool`.
- `database/models.py`: ۸ مدل ORM نتایج موتور (LandProfile، RunoffCalculationResult، GroundwaterModelResult، CropWaterReqResult، StructureDesignResult، IrrigationDesignResult، CalibrationResult، NojinCalibrationRecordDB) + واردات پویای مدل‌های `services/*/models.py`.
- `database/hub.py`: stub `Hub`؛ دسترسی‌های DuckDB `NotImplementedError` می‌دهند (هنوز پیکربندی نشده).
- `alembic/`: ۳ مهاجرت خطی — `20260924_000000` (land_profiles + escrow_items)، `20260926_020000` (no-op placeholder)، `20260927_010000` (۶ جدول نتایج engine با FK به land_profiles).

---

## ۶. ابزارها، آداپتورها، داده‌ها و API

- `tools/detect_imports.py`: اسکنر AST با ۸ قانون معماری؛ سیاست خارجی‌شده در `import_guard_policy.json`.
- `tools/check_security.py`: ۷ بررسی امنیتی (راز سخت‌کدگی، bypass gateway، نشت جزئیات خطا، فیلد provenance…).
- `tools/migrate_services_to_gateway.py`: بازنویسی خودکر واردات مستقیم به فاساد (IMPORT_MAP ۵۰+ مورد).
- `tools/eco04_comprehensive_scan.py`: اسکنر invariantهای INV-001…INV-009 (بدون وابستگی numpy/pytest).
- `adapters/engine_adapter.py`: تحلیل terrain/drainage/capability. `adapters/hydroma_adapter.py`: شوری خاک، ET₀ هارگریوز، طراحی سد چک، Theis.
- `data/`: `model_registry.json` (۹ مدل: MODFLOW6، SWAT+، EnKF، 4D-Var، Particle Filter، PINN‌ها)، `security/audit.jsonl` (۱۷۹۴ رویداد antibot/breaker/honeypot)، cacheهای تست GBIF.
- `openapi.json`: OpenAPI 3.1.0، «HyDroMA Climate API»، ۳ مسیر زیر `/api/v1/hydroma/climate` (لیست ابزارها، جزئیات، اجرا)؛ بدون security scheme.

---

## ۷. نتایج اجرای زنده (شواهد، نه ادعا)

| چک | فرمان | نتیجه |
|---|---|---|
| تست engine | `pytest engine/` | **1578 passed, 0 failed, 0 errors, 29 skipped, 39 xfailed** (101.65s) |
| تست services | `pytest services/` | **271 passed, 44 failed, 9 skipped, 41 errors** — ۵ خطای collection به‌خاطر `User`، `CarbonCredit`، `FinIdempotencyKey`، `FinAccount` که در `database.models` نیستند (در `services/*/schemas.py` به‌صورت Pydantic تعریف شده‌اند) |
| import-guard | `tools/detect_imports.py` | **PASS، ۰ تخلف** |
| ruff | `ruff check .` | **۲۳۳۲ خطا** (B008: ۷۵۰، E501: ۴۶۳، E402: ۳۸۵، F401: ۳۲۳، I001: ۱۸۰، UP045: ۱۲۱، F821: ۱۸، ۱۵ invalid-syntax) |
| mypy engine | `mypy engine` | **۱۰۱۴ خطا در ۱۲۸ فایل** (عمدتاً union-attr روی `ExecutionMetadata | None`) |

---

## ۸. وضعیت علمی: پیاده‌سازی‌شده در برابر اسکلت

**واقعی و اعتبارسنجی‌شده با مرجع:** ET₀ (PM/Hargreaves)، van Genuchten/Mualem و ۴ رابط نگهداشت دیگر، Theis، SCS-CN، RUSLE، Strahler/Horton/Kirpich/Muskingum، RothC، حساب کربن IPCC، طراحی ۵ سازه حوضه، طبقه‌بندی خاک/شوری/تاکسونومی.

**استکلت یا ناقص (صداقتاً علامت‌گذاری شده):** CANON-003 (Thornthwaite)، CANON-016/017 (وابسته به `.pyd`)، MODFLOW (`models/groundwater_model.py:78`)، HEC-RAS (`simulation/hecras.py:103`)، runner پایه (`simulation/runners/base.py`)، ~۱۵ رکورد `status="stub"` در کاتالوگ فرمول‌ها، و **دو مسیر dispatch خراب: `RECOMMEND` → `decision_support.recommender` و `MRV_VALIDATE` → `mrv.validators` که ماژول‌شان وجود ندارد.**

---

## ۹. بدهی‌ها و مسائل شناسه‌شده

1. **انحراف تست سرویس‌ها:** تست‌ها از `database.models` کلاس‌هایی می‌خواهند که آنجا نیستند (۴۱ خطا).
2. **معامله دو-رجیستری latent:** shim `engine/hydroma/core/database.py` در حالت uncommitted ممکن است `get_base()` روی `declarative_base()` جدید برگرداند و مدل‌های core را از `create_all()` جدا کند (هیچ تستی این را نمی‌گیرد — توصیه: `get_base()` باید `database.base.Base` را برگرداند).
3. **Track C2:** ۶ واردات فاساد هنوز در allowlist محافظ هستند (یکی POLICY GAP).
4. **cpp_core orphaned** و باینری‌ها ویندوز-اختصاصی و غیرقابل بازسازی در این محیط.
5. **بدهی lint/type:** ۲۳۳۲ ruff و ۱۰۱۴ mypy (پیش‌از‌حال شناخته‌شده؛ AGENTS.md سه مورد E501/E402/F401 را ثبت کرده).
6. **تناقض مستندات:** گزارش‌های ECO-04 یکدیگر را متناقض کرده‌اند (گزارش ۱۹ «READY» در برابر گزارش ۳۵ «FAIL/0 tests»). `reports/eco-04/99-GAP-ANALYSIS-ECO00-TO-04.1.md` این تناقض‌ها را رفع می‌کند و وضعیت واقعی را تأیید می‌کند: سه کلاس نقص P0 (مسیر contracts، `Base=None`، shim persistence) **اصلاح و تأیید شده‌اند** — تاریخچه تست strict: ۸۶۶ → ۹۹۴ → ۱۵۷۸ پاس.

---

## ۱۰. اکوسیستم مستندات

`HYDROMA-MASTER.md` (دستور مادر ۷۰۰+ خط با قواعد صداقت علمی: «وجود فایل معادل تکمیل قابلیت نیست»)، ECO-00 (ممیزی forensیک)، ECO-01 (استخراج دانش)، ECO-02 (معماری канонیک + ADRs)، ECO-03/03.1 (بازتایید موانع)، ECO-04/04.1 (پیاده‌سازی کنترل‌شده) و ~۱۰۰ گزارش زیر `reports/{hydroma, engine-services, eco-02, eco-04}` شامل ماتریس تأیید، معیارهای پذیرش، بازبینی امنیتی، کاتالوگ مدل‌ها و گزارش یکپارچه‌سازی.

---

## ۱۱. جمع‌بندی

HyDroMA یک موتور علمی واقعی و قابل اجرا است: هسته محاسباتی غنی با مراجع علمی صریح، خط لوله شواهد/دانش/تصمیم کامل، محافظ معماری فعال با صفر تخلف، و ۱۵۷۸ تست موتور همگرا. نقاط ضعف اصلی در لایه سرویس‌ها (۴۱ خطای تست از انحراف مدل ORM)، دو مسیر dispatch خراب (RECOMMEND/MRV_VALIDATE)، وابستگی به باینری‌های C++ غیرقابل بازسازی، و بدهی lint/type قابل‌توجه هستند. معماری برای اتصال آینده به دانشیار، تصمیم‌یار و زنجیره ثبت شواهد (بلاکچین/EcoCoin) آماده است اما — طبق دستور مادر — هیچ اتصال واقعی به بلاکچین ادعا نمی‌شود.
