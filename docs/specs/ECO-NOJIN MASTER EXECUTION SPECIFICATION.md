# ECO-NOJIN MASTER EXECUTION SPECIFICATION
# سند مادر اجرای یکپارچه اکو نوژین

**شناسه سند:** ECO-MASTER-v2.0-ZED-UNIFIED
**وضعیت:** نهایی و اجرایی
**تاریخ:** ۲۰۲۵
**نسخه:** ۲.۰.۰ - یکپارچه با پیمان ZED و معماری داخلی
**مخاطب:** Kilo Code Agent و ایجنت‌های تخصصی مجاز
**پروژه:** Eco Nojin / اکو نوژین
**هسته علمی:** Hydroma Engine / موتور هیدروما
**سامانه دانش:** Daneshyar / دانشیار
**سامانه تصمیم:** Tasmimyar / تصمیم‌یار

---

> **Implementation status (verified 2026-10-11)** — وضعیت فازهای ECO-01..17 این سند مادر.
> فهرست فازها و حیطهٔ هر یک دست‌نخورده است؛ اینجا فقط نتیجهٔ اجرا ثبت می‌شود.
>
> | فاز | خواستهٔ سند | وضعیت ۲۰۲۶-۱۰-۱۱ | شواهد |
> |---|---|---|---|
> | ECO-01 | ممیزی بنیادی و پایدارسازی | ✅ انجام‌شده (تاریخچهٔ پروژه) | `docs/specs/ECO-01.md` |
> | ECO-02 | آشتی معماری و قراردادها | ✅ انجام‌شده + بدهی Track C2 باز | `docs/adr/014-import-guard-policy.md` |
> | ECO-03 | زیرساخت محیط و تست | ✅ انجام‌شده | `AGENTS.md` |
> | ECO-04 | الزام معماری (guard در CI) | ⚠️ گیت نصب است اما **FAIL — ۱۶ bypass سرویس→Gateway** | `python tools/detect_imports.py --root .` |
> | ECO-05 | Engine Gateway | ✅ ماژول ساخته و در CI گیت می‌شود؛ مسیر کامل تمام نشده | `engine/gateway/__init__.py` |
> | ECO-06 | رجیستری مدل علمی | ✅ ۷۰ مدل ثبت‌شده، ۲۲ کارت | `engine/models/registry.py` |
> | ECO-07 | قرارداد داده و persistence | ✅ Port + آداپتر SQLite؛ اسکیمای لایهٔ ۱ در سند §۴.۴ مستقیماً پیاده نشده | `engine/ports/persistence_port.py`؛ `adapters/persistence/` |
> | ECO-08 | شواهد و منشأ | ✅ ماژول Evidence؛ سیم‌کشی تولید پروvاننس باز | `engine/evidence/__init__.py` |
> | ECO-09 | دانش و لایهٔ معرفتی (Daneshyar) | ✅ ماژول Knowledge؛ تفکیک درخواستی نشده | `engine/knowledge/__init__.py` |
> | ECO-10..17 | اقتصاد/خدمات/اشتغال/رهگیری/پایلوت | ⚠️ بخش کسب‌وکار در `services/` پیاده شد (بازار، هاب روستایی، گردشگری، مالکیت زمین، دفتر کل، موجودی) | `services/marketplace/`, `services/land/`, `services/finance/`, `services/inventory/` |
>
> **نتیجهٔ سنجش امروز:** `pytest engine/strict_tests/` ۱۳۲۳ پاس/۰ شکست ·
> `pytest engine/` **۷ شکست/۲۶۹۹ پاس** (یکی اثر انتقال اسناد از ریشه به `docs/`،
> بقیه drift گراف/مرز سرویس/biofertilizer) · `pytest services/` **۱ شکست/۱۴۴۳ پاس**
> (جمع‌آوری به‌دلیل فایل ردیابی‌نشدهٔ همزمان متوقف؛ بدون آن ۱۴۵۳ تست) ·
> `mypy engine` ۰ خطا · `ruff check .` ۸۱۵ یافته · import guard ۱۶ تخلف.
> **بدهی باز:** `data/mirror/` و لایهٔ دادهٔ خام (G-Z4)، stub `Quantity`/pint (G-Z5)،
> `engine/data_connector.py` + DuckDB قدیمی (G-Z3)، ده شاخص نوین، مهاجرت کامل سرویس→Gateway.
>
> **نکتهٔ مسیر:** این فایل در ۲۰۲۶-۱۰-۱۱ از ریشه به `docs/specs/` منتقل شد؛ بازخورد
> `engine/tests/test_architecture_rules.py:34` هنوز مسیر قدیمی ریشه را می‌خواند (تخلف باز برای
> دارندهٔ `engine/**`).
---

## فهرست مطالب

1. مقدمه و اصول حاکم
2. پیمان صفر وابستگی به بیرون (ZED)
3. معماری غیرقابل‌مذاکره
4. معماری داده و پایگاه داده داخلی
5. زنجیره اجرای یکپارچه
6. مراحل اجرایی (ECO-01 تا ECO-17)
7. ترمزهای ایمنی ایجنت
8. کاتالوگ شاخص‌های علمی
9. استانداردهای گزارش‌دهی
10. دستور نهایی به ایجنت

---

# بخش یک: مقدمه

## ۱.۱. مأموریت اصلی

مأموریت تو، رساندن پروژه اکو نوژین به یک سامانهٔ علمی-نرم‌افزاری یکپارچه است که بتواند:

1. داده‌های اقلیمی، هواشناسی، ماهواره‌ای، آب، خاک، کشاورزی، اقتصادی و اجتماعی را دریافت کند.
2. کیفیت، واحد، مقیاس مکانی و زمانی، منشأ و محدودیت داده‌ها را بررسی کند.
3. شاخص‌های علمی را با روش‌های مستند و آزمون‌پذیر محاسبه کند.
4. مدل‌های تخصصی را با قراردادهای مشخص ثبت، اعتبارسنجی و اجرا کند.
5. خروجی مدل‌ها را بدون از بین بردن معنا، واحد، منشأ و عدم‌قطعیت به مدل‌های بعدی منتقل کند.
6. دانش، شواهد، ادعاها، تعارض‌ها و وضعیت معرفتی را در دانشیار مدیریت کند.
7. سناریوهای اقلیمی، زیست‌فیزیکی، اقتصادی و مدیریتی را تعریف و اجرا کند.
8. گزینه‌های تصمیم‌گیری را با اهداف، قیود، ریسک‌ها، عدم‌قطعیت و پیامدهای اجتماعی مقایسه کند.
9. دلایل هر توصیه را به داده، شواهد، مدل‌ها، مفروضات و نسخه‌های اجرایی متصل کند.
10. پس از اجرای واقعی تصمیم‌ها، نتایج را پایش کند و امکان ارزیابی عملکرد تصمیم را فراهم سازد.

## .۲. اصول حاکم

**اصل ۱: صفر وابستگی به بیرون (ZED)**
هیچ ابزار پولی، API ابری، سرویس Freemium یا دیتابیس سروری در هسته اولیه مجاز نیست.

**اصل ۲: معماری واقعی در کد**
وجود فایل به معنای وجود قابلیت نیست. وجود کلاس به معنای تکمیل معماری نیست. موفقیت import به معنای صحت علمی نیست.

**اصل ۳: اعتبارسنجی علمی مستقل**
هر مدل باید با داده مرجع مستقل، آزمون قابل تکرار و منبع علمی معتبر اثبات شود.

**اصل ۴: ردیابی کامل (Provenance)**
هر خروجی باید تا داده خام، نسخه مدل، پارامترها و شواهد قابل ردیابی باشد.

**اصل ۵: صداقت در محدودیت**
اگر قابلیتی پیاده‌سازی نشده، ناقص است یا مسدود است، باید صریحاً گزارش شود.

---

# بخش دو: پیمان ZED (Zero-External-Dependency)

## ۲.۱. تعریف ZED

ZED یعنی: **صفر وابستگی به منابع خارج از مخزن و محیط استاندارد Python.**

## ۲.۲. قواعد غیرقابل‌مذاکره ZED

### الف) ابزارهای ممنوع

| دسته | ممنوع | دلیل |
|------|-------|------|
| زبان/Runtime | MATLAB, Mathematica, R (اجباری), Julia (اجباری) | وابستگی خارجی |
| GIS تجاری | ArcGIS, ArcPy, ERDAS, ENVI | لایسانس |
| دیتابیس سروری | PostgreSQL (اجباری), MongoDB, Redis, Oracle | نیاز نصب جداگانه |
| APIهای ابری | OpenAI API, Claude API, Google Earth Engine (اجباری), AWS S3 (اجباری) | نیاز کلید و اینترنت |
| نرم‌افزار تجاری | MS Excel (as engine), Tableau, PowerBI | لایسانس |
| کامپایلر تجاری | Intel Compiler, MSVC Enterprise | لایسانس |
| سرویس‌های SaaS | AnyDesk, Dropbox, Google Drive (as dependency) | وابستگی شبکه |

### ب) وابستگی‌های مجاز (Approved FOSS Stack)

| لایه | ابزار | مجوز | نحوه استفاده |
|------|-------|------|-------------|
| زبان | Python 3.11+ | PSF | اجباری |
| محاسبات | NumPy, SciPy, pandas | BSD | اجباری |
| GIS | rasterio, geopandas, shapely, pyproj | BSD | اختیاری (fallback pure Python) |
| داده | sqlite3 (stdlib) | - | اجباری |
| ORM/DB | SQLAlchemy 2.x | MIT | اختیاری |
| GIS DB | SpatiaLite (SQLite ext) | LGPL | اختیاری |
| تست | pytest, hypothesis | MIT | توسعه |
| C++ Build | GCC/Clang, CMake, pybind11 | GPL/BSD | اختیاری |
| ML | scikit-learn | BSD | اختیاری |
| سرعت | numba | BSD | اختیاری |
| گزارش | Matplotlib | PSF-based | اختیاری |
| واحد | pint | BSD | اختیاری (توصیه‌شده) |

### ج) قواعد داده

1. **هیچ دانلود لحظه‌ای در هسته علمی.** داده باید از قبل در data/raw/ موجود باشد.
2. **Mirror محلی اجبار.** هر داده خارجی باید نسخه محلی با checksum داشته باشد.
3. **Ingestion جدا از Engine.** ماژول ingestion می‌تواند دانلود کند، اما فقط با flag --allow-download و خارج از هسته.
4. **همه داده‌ها باید قابل بازتولید offline باشند.**

### د) قواعد وابستگی Python

هر pip install جدید باید:
1. مجوز OSI-Approved داشته باشد
2. بدون API Key کار کند
3. بدون اینترنت پس از نصب کار کند
4. در pyproject.toml ثبت شود
5. در LICENSES/ مستند شود

---

# بخش سه: معماری غیرقابل‌مذاکره

## ۳.۱. زنجیره کلان معماری

```
User / Product / Application
         |
         v
  Application Services  <--- AI Interpreter (فقط تفسیر، محدود)
         |
         v
   Decision Engine (Tasmimyar)
         |
         v
Knowledge & Evidence (Daneshyar)
         |
         v
   Scenario Engine
         |
         v
   Engine Gateway
         |
         v
Model Registry + Scientific Model Cards
         |
         v
   Hydroma Engine
         |
         v
Numerical & Scientific Kernels
         |
         v
Persistence Port <--- SQLite/GeoPackage (داخلی)
```

## ۳.۲. قواعد وابستگی (Architecture Rules)

| Rule ID | قاعده | جریمه نقض |
|---------|-------|-----------|
| AR-01 | engine نباید به services وابسته باشد | FAIL CI |
| AR-02 | engine نباید مستقیماً به DB implementation وابسته باشد | FAIL CI |
| AR-03 | هسته علمی نباید به HTTP framework وابسته باشد | FAIL CI |
| AR-04 | هسته علمی نباید به auth/payment/blockchain وابسته باشد | FAIL CI |
| AR-05 | سرویس‌ها نباید مل علمی را خارج از Gateway فراخوانی کنند | FAIL CI |
| AR-06 | همه مسیرهای مدل باید از Gateway عبور کنند | FAIL CI |
| AR-07 | AI نباید معادلات یا پارامترهای علمی را تغییر دهد | FAIL CI + Audit |
| AR-08 | Daneshyar نباید تعارض علمی را پنهان کند | FAIL CI + Audit |
| AR-09 | Tasmimyar نباید بدون اهداف و قیود توصیه قطعی بدهد | FAIL CI |
| AR-10 | هیچ سرویس نباید نتیجه یک مدل را به عنوان مدل دیگر معرفی کند | FAIL CI |

## ۳.۳. Enforcement معماری

ابزار enforcement باید:
- در CI یا مسیر آزمون رسمی اجرا شود
- کد خروجی غیرصفر در صورت نقض تولید کند
- آزمون منفی برای هر قانون داشته باشد
- آزمون مثبت برای مسیرهای مجاز داشته باشد
- قوانین جدید بدون تغییر کد ابزار قابل تعریف باشند

اگر CI وجود ندارد، یک مسیر CI مناسب ایجاد کن (GitHub Actions یا معادل).

---

# بخش چهار: معماری داده و پایگاه داده داخلی

## ۴.۱. اصل بنیادی

داده خام، داده پردازش‌شده، شاخص محاسبه‌ده، خروجی مدل، ادعا و تصمیم، انواع متفاوتی از اطلاعات هستند. آن‌ها را در یک موجودیت عمومی ادغام نکن.

## ۴.۲. لایه‌های داده

### لایه A: داده خام (Raw Data)

```
data/raw/
  climate/           ← CHIRPS, ERA5-Land, ایستگاهی
  satellite/       ← MODIS, Sentinel, WaPOR
  soil/            ← SoilGrids, HWSD, آزمایشگاهی
  topography/      ← SRTM, FABDEM
  socioeconomic/   ← جمعیت، قیمت، هزینه
  surveys/         ← داده میدانی، پرسشنامه
```

**قرارداد:** هر فایل خام باید همراه با *.meta.json باشد:

```json
{
  "dataset_id": "CHIRPSv3_daily_2024",
  "source": "UCSB Climate Hazards Center",
  "url": "https://chc.ucsb.edu/data/chirps",
  "license": "Public Domain",
  "retrieved_at": "2025-01-15",
  "spatial_resolution": "0.05 deg",
  "temporal_resolution": "daily",
  "checksum_sha256": "abc123...",
  "local_path": "data/raw/climate/chirps_v3_daily_2024.tif"
}
```

### لایه B: داده استانداردشده (Standardized)

```
data/processed/
  climate/           ← واحد یکسان، CRS یکسان، زمان یکسان
  soil/              ← بافت، SOC، pH استاندارد
  landcover/         ← طبقه‌بندی UNCCD-LCD
```

**عملیات:**
- یکسان‌سازی نام متغیرها
- تبدیل واحد به استاندارد
- ثبت زمان و منطقه زمانی
- تعریف CRS
- پرچم‌گذاری داده گمشده
- ثبت تبدیل‌ها

### لایه C: شاخص‌ها (Indicators)

```
data/indices/
  climate/           ← ET0, SPI, SPEI, AI
  agriculture/       ← WP, Kc, NPP
  water/             ← Water Balance, Groundwater
  soil/              ← SOC Stock, Erosion
  degradation/       ← SDG 15.3.1 sub-indicators
```

### لایه D: ورودی/خروجی مدل (Model I/O)

```
data/model_runs/
  {run_id}/
    inputs.json
    parameters.json
    outputs.nc or .csv
    metadata.json
    provenance.json
```

### لایه E: شواهد و ادعاها (Evidence & Claims)

```
data/evidence/
  evidence_registry.db      ← SQLite
  claim_registry.db         ← SQLite
  provenance_logs/          ← JSON Lines
```

### لایه F: سناریو و تصمیم (Scenarios & Decisions)

```
data/scenarios/
  {scenario_id}/
    definition.yaml
    assumptions.yaml
    results.json

data/decisions/
  {decision_id}/
    problem_definition.yaml
    objectives.yaml
    constraints.yaml
    options_evaluated.json
    recommendation.yaml
```

## ۴.۳. پایگاه داده داخلی (SQLite + GeoPackage)

### چرا SQLite؟

- در stdlib Python است (بدون pip install)
- فایل‌محور (serverless)
- ACID compliant
- قابل حمل (یک فایل)
- با GeoPackage سازگار (برای GIS)

### چرا GeoPackage؟

- استاندارد OGC
- همان SQLite با پسوند .gpkg
- پشتیبانی از geometry, raster tiles
- قابل باز شدن در QGIS (رایگان)

## ۴.۴. اسکیمای اصلی SQLite

### جدول datasets

```sql
CREATE TABLE datasets (
    dataset_id TEXT PRIMARY KEY,
    dataset_version TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_uri TEXT,
    provider TEXT,
    license TEXT,
    retrieved_at TEXT,
    valid_from TEXT,
    valid_to TEXT,
    variable TEXT NOT NULL,
    unit TEXT NOT NULL,
    spatial_ref TEXT,
    temporal_resolution TEXT,
    spatial_resolution TEXT,
    quality_flag TEXT,
    uncertainty REAL,
    processing_history TEXT,
    content_hash TEXT UNIQUE,
    local_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول model_runs

```sql
CREATE TABLE model_runs (
    run_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parameters_json TEXT,
    inputs_hash TEXT,
    outputs_hash TEXT,
    status TEXT CHECK(status IN ("PENDING", "RUNNING", "SUCCESS", "FAILED", "BLOCKED")),
    error_message TEXT,
    execution_time_ms INTEGER,
    environment_json TEXT,
    FOREIGN KEY (model_id) REFERENCES models(model_id)
);
```

### جدول models (Registry)

```sql
CREATE TABLE models (
    model_id TEXT PRIMARY KEY,
    model_version TEXT NOT NULL,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    purpose TEXT,
    inputs_schema TEXT,
    outputs_schema TEXT,
    assumptions TEXT,
    equations TEXT,
    applicability_domain TEXT,
    limitations TEXT,
    scientific_references TEXT,
    calibration_status TEXT,
    validation_status TEXT,
    uncertainty_method TEXT,
    maturity_level TEXT CHECK(maturity_level IN ("S0","S1","S2","S3","S4","S5","S6")),
    UNIQUE(model_id, model_version)
);
```

### جدول evidence

```sql
CREATE TABLE evidence (
    evidence_id TEXT PRIMARY KEY,
    evidence_type TEXT CHECK(evidence_type IN ("MEASUREMENT", "OBSERVATION", "SIMULATION", "EXPERT_OPINION", "SCIENTIFIC_EVIDENCE", "MODEL_OUTPUT")),
    source_dataset_id TEXT,
    source_model_run_id TEXT,
    location TEXT,
    valid_time TEXT,
    value REAL,
    unit TEXT,
    quality_score REAL,
    uncertainty REAL,
    provenance_chain TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_dataset_id) REFERENCES datasets(dataset_id),
    FOREIGN KEY (source_model_run_id) REFERENCES model_runs(run_id)
);
```

### جدول claims

```sql
CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    claim_text TEXT NOT NULL,
    claim_type TEXT,
    epistemic_status TEXT CHECK(epistemic_status IN ("OBSERVATION", "MEASUREMENT", "LOCAL_KNOWLEDGE", "TRADITIONAL_KNOWLEDGE", "EXPERT_OPINION", "SCIENTIFIC_EVIDENCE", "MODEL_OUTPUT", "INFERENCE", "HYPOTHESIS", "EXPERIMENTAL_RESULT")),
    confidence_basis TEXT,
    known_limitations TEXT,
    review_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول claim_evidence (many-to-many)

```sql
CREATE TABLE claim_evidence (
    claim_id TEXT REFERENCES claims(claim_id),
    evidence_id TEXT REFERENCES evidence(evidence_id),
    relationship TEXT CHECK(relationship IN ("SUPPORTS", "CONTRADICTS", "NEUTRAL")),
    weight REAL DEFAULT 1.0,
    PRIMARY KEY (claim_id, evidence_id)
);
```

### جدول scenarios

```sql
CREATE TABLE scenarios (
    scenario_id TEXT PRIMARY KEY,
    scenario_version TEXT NOT NULL,
    baseline_id TEXT,
    spatial_scope TEXT,
    time_horizon TEXT,
    climate_assumptions TEXT,
    land_management TEXT,
    crop_plan TEXT,
    water_allocation TEXT,
    soil_interventions TEXT,
    economic_assumptions TEXT,
    social_constraints TEXT,
    model_versions TEXT,
    dataset_versions TEXT,
    parameter_set_versions TEXT,
    uncertainty_settings TEXT,
    execution_status TEXT,
    validation_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### جدول decisions

```sql
CREATE TABLE decisions (
    decision_id TEXT PRIMARY KEY,
    problem_definition TEXT,
    objectives TEXT,
    constraints TEXT,
    options_evaluated TEXT,
    scenarios_used TEXT,
    evidence_considered TEXT,
    model_outputs_used TEXT,
    risks TEXT,
    uncertainty_handling TEXT,
    trade_offs TEXT,
    recommendation TEXT,
    recommendation_basis TEXT,
    monitoring_plan TEXT,
    limitations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## ۴.۵. Persistence Port (قرارداد انتزاعی)

```python
# engine/ports/persistence_port.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class PersistencePort(ABC):
    @abstractmethod
    def save_dataset(self, dataset: Dict[str, Any]) -> str:
        """returns dataset_id"""
        pass

    @abstractmethod
    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_model_run(self, model_run: Dict[str, Any]) -> str:
        """returns run_id"""
        pass

    @abstractmethod
    def get_model_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_evidence(self, evidence: Dict[str, Any]) -> str:
        """returns evidence_id"""
        pass

    @abstractmethod
    def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_claim(self, claim: Dict[str, Any]) -> str:
        """returns claim_id"""
        pass

    @abstractmethod
    def link_evidence_to_claim(self, claim_id: str, evidence_id: str, relationship: str, weight: float = 1.0) -> None:
        pass

    @abstractmethod
    def get_claim_evidence(self, claim_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_scenario(self, scenario: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def save_decision(self, decision: Dict[str, Any]) -> str:
        pass
```

### پیاده‌سازی SQLite

```python
# adapters/persistence/sqlite_persistence.py
import sqlite3
import json
from engine.ports.persistence_port import PersistencePort

class SQLitePersistence(PersistencePort):
    def __init__(self, db_path: str = "data/eco-nojin.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        # Execute CREATE TABLE statements from schema above
        pass
```

## ۴.۶. قرارداد داده (Data Contract)

هر مجموعه داده باید شامل این فیلدها باشد:

```python
REQUIRED_DATASET_FIELDS = [
    "dataset_id",
    "dataset_version",
    "source_id",
    "variable",
    "unit",
    "content_hash"
]

RECOMMENDED_DATASET_FIELDS = [
    "source_uri_or_reference",
    "provider",
    "license",
    "retrieved_at",
    "valid_time",
    "processing_time",
    "spatial_reference",
    "geometry_or_location",
    "temporal_resolution",
    "spatial_resolution",
    "quality_flag",
    "uncertainty",
    "processing_history"
]
```

---

# بخش پنج: زنجیره اجرای یکپارچه

## ۵.۱. زنجیره مرجع (Reference Chain)

```
Raw Data
   |
   v
[Data Ingestion & Validation]
   |-- Quality Control
   |-- Unit Validation
   |-- CRS Harmonization
   |-- Missing Data Flagging
   v
[Standardized Data Layer]
   |-- SQLite/GeoPackage
   v
[Indicator Calculation Engine]
   |-- ET0 (FAO-56)
   |-- SPI/SPEI
   |-- Water Balance
   |-- SOC Stock
   |-- WP
   v
[Scientific Model Execution]
   |-- Model Registry lookup
   |-- Gateway dispatch
   |-- Version control
   |-- Provenance logging
   v
[Evidence & Provenance Engine]
   |-- Evidence generation
   |-- Claim registration
   |-- Conflict detection
   |-- Uncertainty propagation
   v
[Daneshyar / Knowledge Engine]
   |-- Epistemic status management
   |-- Inference tracking
   |-- Knowledge graph (optional)
   v
[Scenario Engine]
   |-- Baseline definition
   |-- Scenario versioning
   |-- What-if analysis
   v
[Tasmimyar / Decision Engine]
   |-- Problem formulation
   |-- Multi-criteria analysis
   |-- Sensitivity analysis
   |-- Recommendation generation
   v
[Monitoring & Feedback]
   |-- Implementation record
   |-- Outcome tracking
   |-- Model update trigger
```

## ۵.۲. قرارداد Provenance (منشأ)

برای هر خروجی نهایی باید بتوان این را استخراج کرد:

```json
{
  "output_id": "decision_2025_001",
  "output_type": "DECISION",
  "provenance": {
    "raw_datasets": ["chirps_v3_2024", "era5land_2024", "soilgrids_v2"],
    "indicators_calculated": ["ET0_FAO56_001", "SPI_12_001", "WB_001"],
    "models_executed": [
      {
        "model_id": "hydroma_et0_fao56",
        "version": "1.2.0",
        "run_id": "run_et0_20250115_001"
      }
    ],
    "evidence_ids": ["ev_001", "ev_002", "ev_003"],
    "claim_ids": ["claim_001", "claim_002"],
    "scenario_id": "scenario_baseline_2025",
    "parameter_sets": ["params_kc_wheat_v2"],
    "transformations": [
      {"from": "mm/day", "to": "mm/month", "method": "temporal_aggregation"}
    ],
    "uncertainty_status": "PARTIALLY_ESTIMATED",
    "generated_at": "2025-01-15T10:30:00Z",
    "generator_version": "eco-nojin-2.0.0"
  }
}
```

## ۵.۳. قرارداد خطای ساختاریافته

```python
class HydromaError(Exception):
    def __init__(self, error_code, message, context=None):
        self.error_code = error_code
        self.context = context or {}
        super().__init__(message)

ERROR_CODES = {
    "INPUT_INVALID": "ورودی نامعتبر",
    "UNIT_INCOMPATIBLE": "واحد ناسازگار",
    "MODEL_UNKNOWN": "مدل ناشناخته",
    "MODEL_VERSION_INVALID": "نسخه نامعتبر",
    "OUT_OF_DOMAIN": "خارج از دامنه کاربرد",
    "DATA_INSUFFICIENT": "داده ناکافی",
    "NUMERICAL_ERROR": "خطای عددی",
    "EXECUTION_FAILED": "خطای اجرای مدل",
    "PERSISTENCE_ERROR": "خطای ذخیره‌سازی",
    "UNCERTAINTY_NOT_ESTIMATED": "عدم‌قطعیت محاسبه‌نشده",
    "VALIDATION_FAILED": "اعتبارسنجی ناموفق",
    "NOT_IMPLEMENTED": "پیاده‌سازی نده",
    "ARCHITECTURE_VIOLATION": "نقض معماری"
}
```

---

# بخش شش: مراحل اجرایی (ECO-01 تا ECO-17)

## ۶.۱. ECO-01: Baseline and Forensic Audit

### هدف
شناخت دقیق وضعیت واقعی مخزن قبل از هر تغییر.

### خروجی‌های اجباری
- reports/eco-nojin/ECO-01-FORENSIC-AUDIT.md
- reports/eco-nojin/ECO-01-git-state.txt
- reports/eco-nojin/ECO-01-python-files.txt
- reports/eco-nojin/ECO-01-freeze.txt
- reports/eco-nojin/ECO-01-collect.txt

### Definition of Done
- [ ] git status, git log --oneline -20, git diff --stat ثبت شده
- [ ] ساختار دایرکتوری با tree -L 4 مستند شده
- [ ] تمام فایل‌های Python شمارش شده
- [ ] وابستگی‌ها استخراج و مجوزها بررسی شده
- [ ] گزارش‌های قبلی (ECO-00 تا ECO-04) راستی‌آزمایی شده

---

## ۶.۲. ECO-02: Architecture and Contract Reconciliation

### هدف
تثبیت معماری مرجع و قراردادهای داده.

### خروجی‌های اجباری
- architecture/eco-nojin-architecture.yaml
- architecture/rules.yaml
- architecture/dependency_graph.md
- tools/architecture_enforcement.py

### Definition of Done
- [ ] فایل architecture.yaml وجود دارد
- [ ] قواعد AR-01 تا AR-10 تعریف شده
- [ ] ابزار enforcement اجرا می‌شود
- [ ] حداقل ۳ آزمون منفی برای هر قانون معماری

---

## ۶.۳. ECO-03: Environment and Test Infrastructure

### هدف
آماده‌سازی محیط اجرای کاملاً محلی.

### خروجی‌های اجباری
- pyproject.toml (یا setup.py به‌روز)
- requirements.txt + requirements-dev.txt
- pytest.ini
- reports/eco-nojin/ECO-03-environment.md

### Definition of Done
- [ ] محیط مجازی مستقل ساخته شده
- [ ] وابستگی‌ها نصب شده
- [ ] pytest --collect-only اجرا شده
- [ ] مجوز همه پکیج‌ها بررسی شده
- [ ] داده مرجع آزمون در tests/reference_data/ قرار دارد

---

## ۶.۴. ECO-04: Architecture Enforcement

### هدف
اجرای قواعد معماری و رع نقض‌ها.

### Definition of Done
- [ ] ابزار enforcement در CI متصل شده
- [ ] همه آزمون‌های مثبت و منفی pass شده
- [ ] هیچ import غیرمجاز باقی نمانده
- [ ] گزارش نقض‌ها و اصلاحات ثبت شده

---

## ۶.۵. ECO-05: Engine Gateway

### هدف
تکمیل Gateway برای dispatch واقعی مدل‌ها.

### خروجی‌های اجباری
- engine/gateway/engine_gateway.py
- engine/gateway/model_dispatcher.py
- engine/gateway/input_validator.py
- engine/gateway/unit_converter.py
- tests/integration/test_gateway_dispatch.py

### Definition of Done
- [ ] Registry واقعاً dispatch می‌کند
- [ ] ورودی با Pydantic/dataclass validate می‌شود
- [ ] واحدها با pint/UnitRegistry چک می‌شوند
- [ ] خطاهای ساختاریافته پیاده‌سازی شده
- [ ] حداقل ۸۰٪ coverage مسیرهای اصلی

---

## ۶.۶. ECO-06: Scientific Model Registry

### هدف
ثبت تمام مدل‌های علمی با متادیتای کامل.

### خروجی‌های اجباری
- engine/registry/model_registry.py
- engine/registry/model_card.py
- models/scientific/*.yaml (Model Cards)
- tests/unit/test_registry.py

### Definition of Done
- [ ] حداقل ۱ مدل با maturity S3+ ثبت شده
- [ ] معادلات، ورودی، خروجی، واحد مستند شده
- [ ] منابع علمی ثبت شده
- [ ] آزمون CRUD Registry pass شده

---

## ۶.۷. ECO-07: Persistence and Data Contracts

### هدف
تکمیل لایه Persistence با SQLite داخی.

### خروجی‌های اجباری
- engine/ports/persistence_port.py
- adapters/persistence/sqlite_persistence.py
- data/eco-nojin.db (اسکیمای اولیه)
- tests/integration/test_persistence.py

### Definition of Done
- [ ] Persistence Port تعریف شده
- [ ] SQLite adapter پیاده‌سازی شده
- [ ] هیچ import مستقیم sqlite3 در engine/services
- [ ] آزمون بازتولید pass شده

---

## ۶.۸. ECO-08: Evidence and Provenance

### هدف
تکمیل زنجیره شواهد و منشأ.

### خروجی‌های اجباری
- engine/evidence/evidence_engine.py
- engine/evidence/provenance_tracker.py
- tests/integration/test_evidence_provenance.py

### Definition of Done
- [ ] Evidence Registry کار می‌کند
- [ ] Provenance از داده تا خروجی قابل ردیابی است
- [ ] آزمون conflict detection pass شده

---

## ۶.۹. ECO-09: Knowledge and Epistemic Layer (Daneshyar)

### هدف
تکمیل دانشیار با مدیریت ادعاها و وضعیت معرفتی.

### خروجی‌های اجباری
- knowledge/daneshyar/claim_registry.py
- knowledge/daneshyar/epistemic_manager.py
- knowledge/daneshyar/conflict_resolver.py
- tests/unit/test_knowledge_layer.py

### Definition of Done
- [ ] Claim Registry کار می‌کند
- [ ] Epistemic Status مدیریت می‌شود
- [ ] Conflict Resolution پیاده‌سازی شده
- [ ] حداقل ۱ آزمون end-to-end: داده → شاهد → ادعا

---

## ۶.۱۰. ECO-10: Scientific Indicators

### هدف
پیاده‌سازی شاخص‌های علمی اولویت‌دار.

### خروجی‌های اجباری
- engine/hydroma/et0_fao56.py
- engine/hydroma/spi_calculator.py
- engine/hydroma/water_balance.py
- engine/hydroma/water_productivity.py
- indicators/*.yaml
- tests/scientific/test_et0_fao56.py
- tests/scientific/test_spi.py
- tests/scientific/test_water_balance.py

### Definition of Done
- [ ] ET0 با آزمون مرجع FAO-56 Example 18 pass شده
- [ ] SPI با داده مرجع pass شده
- [ ] Water Balance با موازنه جرم pass شده
- [ ] WP با واحد صحیح pass شده
- [ ] هر شاخص YAML Model Card درد

---

## ۶.۱۱. ECO-11: Uncertainty

### هدف
مدیریت عدم‌قطعیت در زنجیره.

### خروجی‌های اجباری
- engine/hydroma/uncertainty/uncertainty_engine.py
- engine/hydroma/uncertainty/propagation.py
- tests/scientific/test_uncertainty.py

### Definition of Done
- [ ] عدم‌قطعیت measurement error ثبت می‌شود
- [ ] عدم‌قطعیت parameter uncertainty ثبت می‌شود
- [ ] NOT_ESTIMATED صادقانه گزارش می‌شود
- [ ] آزمون propagation برای حداقل ۱ مدل pass شده

---

## ۶.۱۲. ECO-12: Scenario Engine

### هدف
تعریف و اجرای سناریوهای قابل‌بازتولید.

### خروجی‌های اجباری
- scenario/engine/scenario_engine.py
- scenario/engine/baseline_manager.py
- scenario/definitions/*.yaml
- tests/integration/test_scenario_engine.py

### Definition of Done
- [ ] سناریو نسخه‌بندی می‌شود
- [ ] فرض‌ها مستند می‌شوند
- [ ] مقایسه با baseline امکان‌پذیر است
- [ ] حداقل ۱ سناریو end-to-end اجرا شده

---

## ۶.۱۳. ECO-13: Decision Engine (Tasmimyar)

### هدف
تصمیم‌یار با ردیابی کامل دلایل.

### خروجی‌های اجباری
- decision/tasmimyar/problem_formulator.py
- decision/tasmimyar/mca_engine.py
- decision/tasmimyar/sensitivity_analyzer.py
- decision/weights.yaml
- tests/integration/test_decision_engine.py

### Definition of Done
- [ ] اهداف و قیود ثبت می‌شوند
- [ ] گزینه‌ها ارزیابی می‌شوند
- [ ] دلیل توصیه قابل بازسازی است
- [ ] Fail Closed پیاده‌سازی شده
- [ ] آزمون sensitivity analysis pass شده

---

## ۶.۱۴. ECO-14: Service Integration

### هدف
یکپارچه‌سازی سرویس‌ها با هسته.

### Definition of Done
- [ ] موجودی تمام فراخوانی‌ها استخراج شده
- [ ] مسیرهای غیرمجاز حذف یا Adapter شده
- [ ] آزمون سازگاری pass شده

---

## ۶.۱۵. ECO-15: C++/Python and Numerical Verification

### هدف
تطبیق نسخه‌های C++ و Python.

### Definition of Done
- [ ] Bridge بررسی شده
- [ ] Build مستند شده
- [ ] آزمون تطبیق اجرا شده
- [ ] اگر blocked، صریحاً گزارش شده

---

## ۶.۱۶. ECO-16: End-to-End Integration

### هدف
اجرای کامل زنجیره با داده واقعی.

### زنجیره اجباری
```
Raw Data (CHIRPS + ERA5-Land + SoilGrids)
   → Quality Control
   → ET0 Calculation (FAO-56)
   → SPI Calculation
   → Water Balance
   → Water Productivity
   → Evidence Generation
   → Daneshyar (Claims)
   → Scenario (Baseline vs. Drier Climate)
   → Tasmimyar (Recommendation)
   → Monitoring Plan
```

### Definition of Done
- [ ] زنجیره با داده واقعی (نه synthetic) اجرا شده
- [ ] Provenance کامل ثبت شده
- [ ] گزارش ECO-16 در reports/eco-nojin/ECO-16-E2E-REPORT.md
- [ ] خروجی‌ها در outputs/eco-nojin/e2e-demo/ ذخیره شده

---

## ۶.۱۷. ECO-17: Final Independent Verification

### هدف
راستی‌آزمایی نهایی و تولید گزارش واحد.

### خروی اجباری
reports/eco-nojin/FINAL-IMPLEMENTATION-AND-SCIENTIFIC-VERIFICATION-REPORT.md

### Definition of Done
- [ ] آزمون‌ها دوباره اجرا شده
- [ ] قواعد معماری بررسی شده
- [ ] گزارش‌ها با کد تطبیق داده شده
- [ ] وضعیت نهایی تعیین شده

---

# بخش هفت: ترمزهای ایمنی ایجنت (Safety Brakes)

ایجنت در حالت خودگردان پیش می‌رود، اما در این شرایط **باید فوراً متوقف شود** و منتظر دستور صریح بماند:

## ترمز ۱: تغییر معماری
اگر یک تغییر بیش از ۵ فایل اصلی (engine, gateway, registry, services, persistence) را لمس می‌کند، متوقف شو.

## ترمز ۲: تغییر API عمومی
اگر امضای یک تابع یا کلاس public تغییر می‌کند (نام، ورودی، خروجی، استثنا)، متوقف شو.

## ترمز ۳: اصلاح مدل علمی
اگر می‌خواهی معادله، پارامتر، ضریب یا فرمول FAO-56, SPI, RUSLE, SOC یا هر مدل دیگر را تغییر دهی، متوقف شو.

## ترمز ۴: افزودن وابستگی جدید
هر pip install جدید خارج از پشته ZED باید متوقف و دلیل، مجوز و جایگزین محلی ارائه شود.

## ترمز ۵: حذف کد قدیمی
اگر بیش از ۱۰۰ خط کد موجود حذف می‌شود، یا فایلی که در ۶ ماه گذشته ویرایش شده، متوقف شو.

## ترمز ۶: داده مصنوعی برای اعتبارسنجی علمی
اگر داده مرجع موجود نیست و می‌خواهی داده بسازی، فقط در tests/fixtures/synthetic/ و با برچسب SYNTHETIC_TEST_DATA مجاز است. برای ادعای scientific validation باید متوقف شوی.

## ترمز ۷: تغییر قرارداد واحدها
اگر واحد ورودی یا خروجی یک مدل تغییر می‌کند (مثلاً mm/day به mm/month)، متوقف شو.

## ترمز ۸: تغییر در Decision Weights
اگر وزن‌های Tasmimyar تغییر می‌کند، متوقف شو.

## ترمز ۹: افزودن ماژول AI به هسته
اگر می‌خواهی ماژولی که به API خارجی متصل می‌شود را به engine اضافه کنی، متوقف شو.

## ترمز ۱۰: تغییر Database Schema عمومی
اگر جدول‌های اصلی SQLite تغییر می‌کند (ستون اضافه/حذف)، متوقف شو.

---

# بخش هشت: کاتالوگ شاخص‌های علمی

## ۸.۱. اولویت‌بندی پیاده‌سازی

### مرحله ۱: هسته اولیه (ECO-10 Priority 1) - اجباری

| شاخص | شناسه | منبع | آزمون مرجع | وضعیت هدف |
|------|-------|------|-----------|-----------|
| ET0 FAO-56 | ENO_ET0_FAO56_001 | Allen et al. 1998 | Example 18: 5.08 mm/day | S3+ |
| ETc Kc-based | ENO_ETC_KC_001 | FAO-56 Chapter 6 | داده مرجع محصول | S3+ |
| Water Productivity | ENO_WP_001 | FAO WaPOR | kg/m³ مرجع | S3+ |
| SPI 1/3/6/12 | ENO_SPI_001 | McKee et al. 1993 | WMO No. 1090 | S3+ |
| Water Balance | ENO_WB_001 | Water Balance Eq | موازنه جرم | S3+ |

### مرحله ۲: تکمیل علمی (ECO-10 Priority 2)

| شاخص | شناسه | منبع | آزمون مرجع |
|------|-------|------|-----------|
| SPEI 1/3/6/12 | ENO_SPEI_001 | Vicente-Serrano 2010 | داده مرجع |
| RUSLE | ENO_RUSLE_001 | Renard et al. 1997 | USDA Handbook 703 |
| SOC Stock | ENO_SOC_001 | FAO 2019 | Poeplau et al. 2017 |
| Groundwater dV | ENO_GW_001 | Alley et al. 1999 | Konikow 2014 |
| Aridity Index | ENO_AI_001 | UNEP 1992 | AI = P/PET |

### مرحله ۳: نوین و یکپارچه (ECO-10 Priority 3)

| شاخص | شناسه | منبع | کاربرد |
|------|-------|------|--------|
| Flash Drought Index (FDII) | ENO_FDII_001 | Christian 2024 | خشکسالی سریع |
| Compound Drought-Heat (CDHE) | ENO_CDHE_001 | Zscheischler 2020 | رویداد ترکیبی |
| Crop Multi-Stress (CMSI) | ENO_CMSI_001 | Webber 2020 | تنش چندگانه محصول |
| Water-Soil Nexus (WSNI) | ENO_WSNI_001 | اکو نوژین | یکپارچگی آب-خاک |
| Restoration Readiness (RRI) | ENO_RRI_001 | اکو نوژین | آمادگی احیا |

## ۸.۲. قرارداد YAML شاخص

```yaml
indicator_id: "ENO_ET0_FAO56_001"
name:
  en: "Reference Evapotranspiration FAO-56"
  fa: "تبخیر و تعرق مرجع FAO-56"
domain: "climate"
formula: "ET0 = [0.408*Delta*(Rn-G) + gamma*(900/(T+273))*u2*(es-ea)] / [Delta + gamma*(1+0.34*u2)]"
unit: "mm day-1"
input_variables:
  - name: "T_mean"
    unit: "degC"
    required: true
  - name: "Rn"
    unit: "MJ m-2 day-1"
    required: true
  - name: "u2"
    unit: "m s-1"
    required: true
  - name: "es_minus_ea"
    unit: "kPa"
    required: true
  - name: "G"
    unit: "MJ m-2 day-1"
    required: false
    default: 0
reference:
  source: "Allen et al. 1998, FAO Paper 56"
  url: "https://www.fao.org/4/X0490E/x0490e06.htm"
validation_status: "REFERENCE_DATA_REQUIRED"
version: "1.0.0"
zed_compliant: true
maturity_target: "S3"
```

## ۸.۳. داده‌های مرجع آزمون

### FAO-56 Example 18
- **مکان:** Rome, Italy
- **تاریخ:** 6 July
- **عرض جغرافیایی:** 41.8°
- **T_max:** 34.8°C
- **T_min:** 24.6°C
- **RH_max:** 52%
- **RH_min:** 28%
- **u2:** 2.0 m/s
- **Rs:** 22.3 MJ/m²/day
- **Elevation:** 142 m
- **مقدار مرجع:** ET0 ≈ 5.08 mm/day
- **تلورانس:** ±0.05 mm/day

### SPI Reference Data
- **منبع:** WMO No. 1090, Appendix
- **محتوا:** سری‌های بارش و SPI محاسبه‌شده
- **مسیر:** tests/reference_data/spi_reference.csv

## ۸.۴. پایگاه داده مرجع علمی

| شاخص | منبع اصلی | آزمون مرجع | وضعیت |
|------|----------|-----------|-------|
| ET0 | FAO Paper 56, Annex 2 | Example 18 | موجود |
| SPI | WMO No. 1090 | Appendix | موجود |
| SPEI | Vicente-Serrano 2010 | داده مرجع | نیازمند تهیه |
| RUSLE | USDA Handbook 703 | داده مرجع | نیازمند تهیه |
| SOC | FAO 2019 | Poeplau 2017 | نیازمند تهیه |

---

# بخش نه: استانداردهای گزارش‌دهی

## ۹.۱. گزارش نهایی اجباری

مسیر: reports/eco-nojin/FINAL-IMPLEMENTATION-AND-SCIENTIFIC-VERIFICATION-REPORT.md

### ساختار گزارش نهایی

```markdown
# گزارش نهایی اجرا و اعتبارسنجی علمی اکو نوژین

## ۱. خلاصه مدیریتی
## ۲. مشخصا مخزن و محیط
## ۳. موجودی قابلیت‌ها (Capability Inventory)
## ۴. ماتریس معماری
## ۵. موجودی مدل‌های علمی
## ۶. موجودی شاخص‌ها
## ۷. وضعیت دانشیار (Daneshyar)
## ۸. وضعیت تصمیم‌یار (Tasmimyar)
## ۹. وضعیت سناریو
## ۱۰. تغییرات کد
## ۱۱. نتایج آزمون
## ۱۲. موانع و محدودیت‌ها
## ۱۳. موارد باقی‌مانده (P0-P3)
## ۱۴. قابلیت بازتولید
## ۱۵. پیوست ZED (وابستگی‌ها و مجوزها)
## ۱۶. پیوست Decision Log
```

## ۹.۲. وضعیت‌های نهایی مجاز

| وضعیت | شرط |
|-------|-----|
| **PASS_INTEGRATION_READY** | همه شرایط بخش ۲۳ سند مادر + هیچ P0 باقی‌مانده |
| **PARTIAL_NOT_READY** | بخشی پیاده‌سازی شده، اما شرایط ضروری ناقص |
| **BLOCKED_ENVIRONMENT** | محیط مانع اجرای ضروری‌ها شده و قابل‌رفع نبوده |
| **BLOCKED_ARCHITECTURE** | نقض معماری مهم باقی مانده |
| **SCIENTIFIC_REVIEW_REQUIRED** | پیاده‌سازی نرم‌افزاری موجود، اعتبار علمی اثبات نشده |

## ۹.۳. اولویت‌بندی موارد باقی‌مانده

| اولویت | تعریف | نمونه |
|--------|-------|-------|
| **P0** | مانع جدی صحت علمی، امنیت یا معماری | نقض AR-01، خطای ET0، عدم Provenance |
| **P1** | مانع یکپارچه‌سازی یا قابلیت ضروری | Gateway بدون dispatch، Registry بدون Model |
| **P2** | بهبود مهم ولی غیرمسدودکننده | Coverage پایین، Lint errors |
| **P3** | بهبود اختیاری | مستندات اضافی، بهینه‌سازی |

---

# بخش ده: دستور نهایی به ایجنت

> مأموریت تو، رساندن اکو نوژین به یک سامانهٔ علمی-نرم‌افزاری یکپارچه، **کاملاً رایگان، کاملاً محلی و کاملاً قابل بازتولید** است.
>
> ## قواعد غیرقابل‌مذاکره:
> ۱. هیچ ابزار پولی، API ابری یا سرویس Freemium در هسته مجاز نیست.
> ۲. هیچ داده‌ای در زمان اجرا از اینترنت گرفته نمی‌شود؛ همه چیز local mirror است.
> ۳. هیچ معادلهٔ علمی، پارامتر، API عمومی یا وابستگی جدید بدون مجوز صریح من اضافه نمی‌شود.
> ۴. هیچ ادعای scientific validation بدون داده مرجع مستقل و آزمون قابل تکرار پذیرفته نیست.
> ۵. هیچ آزمون اجرا‌نشه‌ای PASS نیست.
> ۶. هیچ تغییر بالای ۵ فایل اصلی بدون توقف و مجوز انجام نمی‌شود.
> ۷. هیچ داده مصنوعی برای ادعای علمی استفاده نمی‌شود.
>
> ## مراحل اجرا:
> ۱. ECO-01: ۵ دستور ۱۰ دقیقه‌ای را اجرا و گزارش بده.
> ۲. ECO-02: معماری ZED-compliant را تثبیت کن.
> ۳. ECO-03 تا ECO-05: Gateway و Registry را با آزمون واقعی بساز.
> ۴. ECO-07: SQLite Persistence Port را پیاده‌سازی کن.
> ۵. ECO-10: شاخص‌های هسته (ET0, SPI, WP, Water Balance) را با داده مرجع اجرا کن.
> ۶. ECO-08 تا ECO-09: Evidence و Daneshyar را بساز.
> ۷. ECO-12 تا ECO-13: Scenario و Tasmimyar را بساز.
> ۸. ECO-16: زنجیره end-to-end با داده واقعی اجرا و provenance کامل ثبت کن.
> ۹. ECO-17: گزارش نهایی واحد بنویس.
>
> ## اگر به ترمز ایمنی رسیدی:
> - توقف کن
> - دلیل را در reports/eco-nojin/BLOCKED-{timestamp}.md ثبت کن
> - ادامه نده تا مجوز صریح دریافت کنی
>
> ## اگر به مانع برخوردی:
> - BLOCKED را با دلیل فنی ثبت کن
> - سایر مراحل مستقل را ادامه بده
>
> ## اگر شک داری:
> - FAIL CLOSED کن
> - صادقانه گزارش بده
> - از حدس زدن خودداری کن
>
> **مهم‌ترین معیار:** معماری باید در کد واقعی برقرار باشد، در آزمون‌ها قابل‌بررسی باشد، در اجرای مدل‌ها قابل‌مشاهده باشد و در گزارش نهایی با شواهد اثبات شود.

---

# پیوست: ساختار فایل‌های اجباری مخزن

```
eco-nojin/
├── engine/
│   ├── hydroma/                    # هسته علمی
│   │   ├── et0_fao56.py
│   │   ├── spi_calculator.py
│   │   ├── water_balance.py
│   │   ├── water_productivity.py
│   │   ├── uncertainty/
│   │   │   ├── uncertainty_engine.py
│   │   │   └── propagation.py
│   │   └── tests/
│   │       ├── unit/
│   │       ├── scientific/
│   │       └── reference_data/
│   ├── gateway/
│   │   ├── engine_gateway.py
│   │   ├── model_dispatcher.py
│   │   ├── input_validator.py
│   │   └── unit_converter.py
│   ├── registry/
│   │   ├── model_registry.py
│   │   └── model_card.py
│   ── ports/
│   │   └── persistence_port.py
│   └── evidence/
│       ├── evidence_engine.py
│       └── provenance_tracker.py
├── knowledge/
│   └── daneshyar/
│       ├── claim_registry.py
│       ├── epistemic_manager.py
│       └── conflict_resolver.py
├── decision/
│   └── tasmimyar/
│       ├── problem_formulator.py
│       ├── mca_engine.py
│       └── sensitivity_analyzer.py
│   └── weights.yaml
├── scenario/
│   └── engine/
│       ├── scenario_engine.py
│       └── baseline_manager.py
│   └── definitions/
├── services/
│   └── domain/
│       └── (سرویس‌های دامنه)
├── adapters/
│   └── persistence/
│       └── sqlite_persistence.py
├── indicators/
│   ├── ENO_ET0_FAO56_001.yaml
│   ├── ENO_SPI_001.yaml
│   ├── ENO_WP_001.yaml
│   ├── ENO_WB_001.yaml
│   └── ...
├── models/
│   └── scientific/
│       ├─ et0_fao56_card.yaml
│       ├── spi_card.yaml
│       └── ...
├── data/
│   ├── raw/
│   │   ├── climate/
│   │   ├── satellite/
│   │   ├── soil/
│   │   ├── topography/
│   │   └── socioeconomic/
│   ├── processed/
│   ├── reference/
│   │   └── fao56_examples.csv
│   ├── indices/
│   ├── model_runs/
│   ├── evidence/
│   ├── scenarios/
│   ├── decisions/
│   └── eco-nojin.db              # SQLite master database
├── tests/
│   ├── unit/
│   ├── scientific/
│   │   ├── test_et0_fao56.py
│   │   ├── test_spi.py
│   │   └── test_water_balance.py
│   ├── integration/
│   │   ├── test_gateway_dispatch.py
│   │   ├── test_persistence.py
│   │   ├── test_evidence_provenance.py
│   │   └── test_scenario_engine.py
│   ├── architecture/
│   ├── e2e/
│   └── fixtures/
│       ├── synthetic/
│       └── reference_data/
│           ├── fao56_examples.csv
│           └── spi_reference.csv
├── architecture/
│   ├── eco-nojin-architecture.yaml
│   └── rules.yaml
├── reports/
│   └── eco-nojin/
│       ├── ECO-01-FORENSIC-AUDIT.md
│       ├── ECO-02-ARCHITECTURE.md
│       ├── ...
│       └── FINAL-IMPLEMENTATION-AND-SCIENTIFIC-VERIFICATION-REPORT.md
├── docs/
│   └── scientific_references/
│       └── REFERENCES.md
├── tools/
│   └── architecture_enforcement.py
├── pyproject.toml
├── pytest.ini
├── README-ZED.md                 # راهنمای نصب و اجرای کاملاً محلی
└── LICENSES/                     # مجوز هر وابستگی
```

---

# پیوست: Quick Start (۵ دستور ۱۰ دقیقه‌ای)

ایجنت باید ابتدا این ۵ دستور را اجرا و گزارش کند:

```bash
# ۱. وضعیت Git
git status && git log --oneline -10 > reports/eco-nojin/ECO-01-git-state.txt 2>&1

# ۲. ساختار مخزن
find . -type f -name "*.py" | head -100 > reports/eco-nojin/ECO-01-python-files.txt

# ۳. وابستگی‌ها
python -m pip freeze > reports/eco-nojin/ECO-01-freeze.txt 2>/dev/null || echo "NO_PIP_FREEZE" >> reports/eco-nojin/ECO-01-freeze.txt

# ۴. آزمون Collection
python -m pytest --collect-only > reports/eco-nojin/ECO-01-collect.txt 2>&1 || echo "COLLECTION_FAILED" >> reports/eco-nojin/ECO-01-collect.txt

# ۵. اسکن وابستگی‌ها
python -c "import ast, os; [print(f) for f in os.popen('find . -name *.py').read().splitlines()[:50]]" > reports/eco-nojin/ECO-01-imports.txt
```

---

*این سند نسخه ۲.۰.۰ یکپارچه اکو نوژین است. شامل پیمان ZED، معماری داخلی، پایگاه داده SQLite، زنجیره اجرای یکپارچه، ۱۷ مرحله اجرایی، ۱۰ ترمز ایمنی، کاتالوگ شاخص‌ها و دستور نهایی به ایجنت.*
*شناسه: ECO-MASTER-v2.0-ZED-UNIFIED*
*پیوست علمی: ZED-Scientific-001*
*تاریخ تدوین: ۲۰۲۵*

