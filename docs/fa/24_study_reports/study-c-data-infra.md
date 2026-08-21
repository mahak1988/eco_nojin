# گزارش مطالعه: داده، ML، تست و زیرساخت — پروژه Eco Nojin (D:\eco_nojin)

> تاریخ: 2026-08-17 | تهیهشده با بررسی مستقیم فایلسیستم (PowerShell + Python) و اجرای pytest
> شعبه git فعلی: `feature/phase-b-alembic` | آخرین commit: `68b2608` (2026-08-17 03:31، پیام: 371 pytest + 18 vitest + lint green)

---

## 1) تستها — `D:\eco_nojin\tests\`

### ساختار و فهرست فایلها

| مسیر | تعداد فایل | نقش |
|---|---|---|
| `tests\unit\` | 18 فایل `test_*.py` + `__init__.py` | تست واحد (واحدهای دامنه/مهندسی) |
| `tests\integration\` | 14 فایل `test_*.py` + `__init__.py` | تست یکپارچه (API + DB) |
| `tests\benchmarks\` | `test_numba_performance.py` | بنچمارک Numba (۲ تست) |
| `tests\e2e\` | فقط `__init__.py` | خالی — هیچ تست E2E وجود ندارد |
| ریشه `tests\` | ۱۳ فایل | داده (CDS/Copernicus/ERA5/NASA POWER)، PINN، C++ bridge، bot، alert |

### تعداد کل تستها (اجرای زنده)

اجرا شد: `python -m pytest --collect-only -q` در `D:\eco_nojin` با `.venv` → **371 تست جمعآوری شد** در 16.28 ثانیه (خروجی کد 0). تفکیک دقیق از node-id ها:

- `tests/unit/` → **191 تست** (blockchain 21، marketplace 21، ecowallet 20، ussd 21، voice 20، scenarios 17، numba_correctness 14، satellite 9، settings 9، ai 7، carbon 7، watershed 7، auth 6، security 5، models 2، climate 2، compost 2، placeholder 1)
- `tests/` ریشه → **101 تست** (bot_phase2 14، bot_phase1 13، cds 10، nasa_power 10، copernicus 9، copernicus_phase4 9، era5 7، scl_masking 7، phase4_extras 6، cpp_bridge 5، alert_loop 4، alert_runner 4، pinn 3)
- `tests/integration/` → **77 تست** (models_phase7 16، content_phase6 7، phase6_remainder 7، phase8_final 7، sync 6، carbon_phase8 5، admin_modules 5، auth_refresh 4، api_satellite 4، admin_finalize 4، admin_api 3، admin_models 3، api 3، api_ai 3)
- `tests/benchmarks/` → **2 تست**

جمع: **371 تست** = 191 واحد + 77 یکپارچه + 101 داده/ML + 2 بنچمارک.

### پوشش (Coverage)

- فایل `D:\eco_nojin\.coverage` (53,248 بایت) یک دیتابیس SQLite است؛ پرسوجو از آن نشان داد **جدول `file` خالی است (0 فایل)** — یعنی آخرین اجرای coverage دیتایی ثبت نکرده (احتمالاً در حالت خطادار یا ناقص اجرا شده). هیچ `htmlcov/` یا `coverage.xml` هم وجود ندارد.
- `pytest-cov 7.1.0` و `coverage 7.15.4` در `.venv` نصباند ولی عدد پوشش واقعی **در دسترس نیست**. «درصد پوشش» در هیچ گزارش موجودی ذکر نشده.

### تستهای فرانت (Vitest)

- `frontend\vitest.config.mts` — jsdom، globals، `setupFiles: vitest.setup.ts`، `include: __tests__/**/*.test.{ts,tsx}`، alias `@` → ریشه frontend
- `frontend\vitest.setup.ts` — jest-dom + استاب ResizeObserver/scrollIntoView
- `frontend\__tests__\` — 6 فایل: `charts.test.tsx` (5)، `data-table.test.tsx` (6)، `form.test.tsx` (3)، `command-palette.test.tsx` (2)، `sheet.test.tsx` (2) → **جمعاً 18 تست vitest** (با شمارش `it(`/`test(` تأیید شد). در `package.json` اسکریپت `test` برای vitest **تعریف نشده** (فقط dev/build/start/lint).

### نکات مهم

- `tests\unit\test_placeholder.py` یک تست نشانه (assert True) است.
- در `engine\hydroma\` زیرپوشههای `*_fast.py` همراه `tests\test_{module_name}.py` (placeholder) و یک تست واقعی `soil\tests\test_soil.py` وجود دارد، اما چون `pyproject.toml` مقدار `testpaths = ["tests"]` دارد، اینها در اجرای پیشفرض pytest **جمعآوری نمیشوند**.
- فایلهای تاریخی نتایج (ریشه پروژه): `final_test_results.txt` (۷KB) نشان میدهد ۱۲ فایل تست با `NameError: name 'model_validator' is not defined` در collection شکست خورده بودند؛ `full_test_results.txt` (۳۷KB) خطای `SyntaxError: invalid syntax` در `engine\hydroma\config\settings.py` خط ۱۹۰ (چسبیدن دو خط به هم) را نشان میدهد. هر دو مربوط به حالت قبلیاند — اجرای زنده امروز ۳۷۱ تست را سالم جمع میکند و آخرین commit ادعای سبز بودن کامل دارد. (پس از این دو گزارش، فایل `settings.py` تعمیر شده: ایمپورت `model_validator` در خط ۶ و استفاده در خط ۲۵۸ موجود است.)

---

## 2) ML — `D:\eco_nojin\ml\` و ماژولهای ML واقعی

### پوشه `ml\` — فقط اسکلت

`ml\features\.gitkeep`، `ml\models\.gitkeep`، `ml\notebooks\.gitkeep`، `ml\registry\.gitkeep` — **هیچ مدل، دیتاست یا نوتبوکی وجود ندارد**؛ پوشه صرفاً placeholder است.

### کد ML واقعی (در `services\models\` و `engine\hydroma\`)

- **`services\models\registry.py`** (23,910 بایت) — رجیستری **۲۲ مدل علمی** با برچسب وفاداری (`fidelity`: official 9 / simplified 11 / experimental 2)، هر مدل یک تابع واقعی پیادهشده را wrap میکند (بدون stub). مدلها: ET0 هارگریوز، رواناب، طراحی سازههای آبخیز، عملکرد محصول (AquaCrop-style)، پروژکشن اقلیمی، زیستتوده IPCC، **RothC 5-pool**، **فتوسنتز Farquhar**، راندمان کوانتومی، ترسیب کربن (VM0042-aligned)، شاخص سلامت خاک، pedotransfer (Saxton & Rawls)، شوری FAO، **van Genuchten**، AWC، **RUSLE**. API عمومی: `GET /api/v1/models`، `GET /api/v1/models/{slug}`، `POST /api/v1/models/{slug}/run` (اعتبارسنجی پارامتر، خطاهای صریح — هرگز fallback بیصدا).
- **مدل کارتها**: دیکشنری `MODEL_CARDS` در همان فایل (خط ۳۶۷+) — برای هر ۲۲ مدل فیلدهای `validity` (دامنه اعتبار) و `limitations` (محدودیتها) به فارسی، از طریق `model_card(slug)` در پاسخ API و کاتالوگ فرانت `/models` نمایش داده میشود. متن فارسی با UTF-8 سالم ذخیره شده (بررسی شد: `'تبخیر و تعرق مرجع (هارگریوز)'` بدون کاراکتر خراب).
- **`services\models\pinn_surrogate.py`** (3,336 بایت) — اسکلفولد PINN: MLP (لایههای `[32,32]` پیشفرض + Tanh)، متد `fit` با Adam + MSELoss، `predict`، تابع `status()` صادقانه. **وضعیت اجرا: در `.venv` نسخه `torch 2.13.0` نصب است** → `TORCH_AVAILABLE=True` و تستهای PINN واقعاً اجرا میشوند (نه skip). سند داخل ماژول صریح میگوید: «scaffold + toy training loop؛ آموزش surrogate تولیدی کار بعدی است» — یعنی هنوز مدل آموزشدیده/وزن ذخیرهشده وجود ندارد.
- **`services\models\cpp_bridge.py`** (4,045 بایت) — bridge با ctypes به `hydroma_core.dll` (ET0 هارگریوز، تابش فرازمینی، van Genuchten)؛ قوانین کشف DLL: متغیر env `HYDROMA_CORE_DLL` → `engine\cpp_core\hydroma_core.dll` → ماژول/CWD. خطای صریح `CppBridgeUnavailable`، هرگز fallback بیصدا.
- **`engine\hydroma\ml\models.py`** — کلاسهای Pydantic placeholder خالی (`MLCreate/MLRead/MLUpdate`) — عملاً بیاستفاده.
- **کرنلهای Numba**: `engine\hydroma\cpp_bridge\soil_physics_fast.py` (van Genuchten θ/K)، `hydrology_fast.py` (Muskingum–Cunge، Saint-Venant 1D، CFL)، `indices_fast.py` (NDVI/EVI/SAVI/NBR) — همه با `@njit(cache=True)` و fallback گریدار اگر numba نصب نباشد.

---

## 3) داده — کلاینتها و ساختار

### پوشه `data\`

`data\raw\`، `data\processed\`، `data\external\`، `data\metadata\` — همه فقط `.gitkeep` (خالی). `data\econojin.db` (196KB، **صفر ردیف داده**) + فایلهای WAL/SHM و `econojin.db.bak_20260815_041559`. **یافته مهم:** در ریشه پروژه یک دیتابیس دوم `D:\eco_nojin\econojin.db` (274KB + WAL 4.1MB) وجود دارد با **۲۲ جدول و داده واقعی (۱ مزرعه، ۲ کاربر، جدولهای audit_logs/content_items/error_logs/settings)** که در `data\econojin.db` نیستند — یعنی **دو دیتابیس SQLite موازی با اسکیمای متفاوت** (ریسک واگرایی داده). `database\config.py` مسیر را `sqlite:///./data/econojin.db` (نسبی به ریشه) resolve میکند، پس دیتابیس فعالِ پیکربندیشده همان خالی است؛ دیتابیس ریشه احتمالاً از کانفیگ قدیمی باقی مانده و مرجع داده جاری است.

### کلاینتهای داده (همه در `services\satellite\`)

- **`services\satellite\cds.py`** (10,133 بایت) — کلاینت یکپارچه **CDS / EWDS / ADS** (هر سه job-based REST مشترک): `DataStoreClient(store="cds|ewds|ads")` با submit → poll → download؛ پشتیبانی auth دوگانه (Bearer برای CDS جدید 2025+ با token «key:...»، و basic «uid:api_key» برای legacy) از طریق `CDS_AUTH`؛ `configured` فقط وقتی کلید ست باشد؛ بدون کلید → `DataStoreNotConfigured` (هرگز داده جعل نمیشود). کلیدها در env: `CDS_UID/CDS_API_KEY`، `EWDS_UID/EWDS_API_KEY`، `ADS_UID/ADS_API_KEY`. وضعیت واقعی: در `.env` مقدار `CDS_API_KEY` **پر است** (بقیه خالی). نکته: `CDS_API_KEY` در git-tracked شده؟ خیر — `.env` در .gitignore است.
- **`services\satellite\copernicus.py`** (20,833 بایت) — کلاینت **CDSE (Copernicus Data Space)**: OAuth2 (client_credentials یا password با `cdse-public`)، جستجوی STAC `sentinel-2-l2a`، دانلود COG باندهای B04/B08/B02 + **SCL** با rasterio و نمونهگیری پیکسل → **NDVI/EVI/SAVI واقعی**؛ توابع ریاضی خالص قابل تست (`ndvi_from_bands` و…)؛ `Scene.is_usable` با آستانه ابر ۲۰٪؛ ماسک ابر SCL (کلاسهای 4/5/6) و `clear_ratio_from_scl`؛ بدون credential → `CopernicusNotConfigured`.
- **`services\satellite\era5_fetch.py`** (5,936 بایت) — سری روزانه ERA5 از CDS (متغیرهای t2m/tp)، parse واقعی NetCDF با xarray؛ خطاهای شبکه صریح.
- **`services\satellite\nasa_power.py`** (8,758 بایت) — NASA POWER (بدون کلید) + محاسبه ET0 هارگریوز؛ باگ قبلی fill-value=-999 تعمیر شده (در commit ها).
- **`services\satellite\open_meteo.py`** (4,720 بایت) — ERA5-Land آرشیو Open-Meteo با `et0_fao_evapotranspiration` (بدون کلید).

### earth_search — توجه: داده شبیهسازیشده

`engine\hydroma\satellite\providers\earth_search.py` — کلاینت **STAC عمومی Element 84** (`https://earth-search.aws.element84.com/v1`، بدون کلید). متد `search()` واقعاً به API عمومی درخواست میدهد، اما **متد `fetch_tile()` داده مصنوعی برمیگرداند**: `np.random.uniform(...)` باندهای ۶۴×۶۴ با `np.random.seed(hash(item_id))` و **برچسب صریح `data_source="simulated"`** — داکاسترینگ خود فایل میگوید «simplified mock that returns synthetic data for demo». یعنی: جستجوی صحنه واقعی است، پیکسلها جعلیاند و بهدرستی برچسب خوردهاند (honesty contract در `base.py`: فیلد `data_source` در dataclass `SatelliteTile` با مقدار پیشفرض `"real"` و الزام مصرفکننده به نمایش برچسب). کلاینت واقعی جایگزین، `copernicus.py` است که با CDSE فقط وقتی scene واقعی نمونهگیری شود `data_source="copernicus"` میدهد (در `routers\satellite.py` نیز همین قرارداد).

### ساختار داده پایدار

جدولها (SQLite، ۱۶–۲۲ جدول): `users`، `farms`، `soil_profiles`، `soil_analyses`، `satellite_analyses` (با ستونهای provenance — migration `b7c9d2e4f1a3_satellite_provenance_columns.py`)، `carbon_projects`، `eco_wallets`، `eco_transactions`، `products`، `materials`، `plants`، `scenario_runs`، `recommendation_cache`، `password_reset_tokens`، `ai_conversations` + (فقط در DB ریشه) `audit_logs`، `content_items`، `content_versions`، `content_translations`، `error_logs`، `settings`.

### DVC

`dvc.yaml` (۹۵۳ بایت) — ۳ stage: `stac_fetch` (خروجی `data/raw/scenes.jsonl`)، `band_sample` (خروجی `data/processed/indices.parquet`)، `load_db` — با کامنت صریح «honest: no stage fabricates data». **اما:** دستورها `python -m services.satellite.cli fetch-scenes` و… به ماژولی اشاره میکنند که **وجود ندارد** (`services\satellite\` فایل `cli.py` ندارد و هیچ رجیستری از `fetch-scenes` در کد پیدا نشد) و **خود DVC هم نصب نیست** (`importlib.util.find_spec('dvc') → None`). پس پایپلاین DVC در وضعیت «اسکلت غیرقابلاجرا» است. `.dvcignore`: `.venv/`، `frontend/`، `*.db` و واریانتهای WAL/SHM.

---

## 4) Supabase

- **`supabase\migrations\00001_auth_roles_rls.sql`** (2,222 بایت) — تنها فایل: توابع `public.current_role()` (از `auth.jwt() -> app_metadata.role` با fallback `farmer`) و `public.is_admin()`؛ ویو `public.user_profiles` روی `auth.users`؛ **فعالسازی RLS فقط روی جدول `public.farms`** با سه policy (select: مالک یا admin؛ insert: مالک؛ update: مالک یا admin)؛ ساخت bucket استوریج `media` (public). کامنت فایل تصریح میکند که جداول اصلی توسط backend (FastAPI/SQLAlchemy) مدیریت میشوند و این policy ها «الگو» هستند — یعنی **RLS فقط روی یک جدول نمونه پیاده شده** و بقیه جداول (users, satellite_analyses, eco_wallets و…) در Supabase بدون policyاند (اگر قرار باشد از Supabase بخوانند محافظت ندارند).
- `supabase\config.toml` وجود ندارد؛ بدون کلاینت/CI برای Supabase.

---

## 5) اسکریپتها — `D:\eco_nojin\scripts\`

- **`scripts\bootstrap_admin.py`** (3,502 بایت) — ساخت اولین ادمین: `--create --password` برای ثبت کاربر جدید با نقش admin، `--set-password` برای ریست رمز کاربر موجود (حداقل ۶ کاراکتر)، idempotent؛ از `services.api_gateway.auth.hash_password` و `database.config.SessionLocal` استفاده میکند؛ بدون `--create` اگر کاربر نباشد فقط پیام خطا میدهد (خروجی 1).
- **`scripts\backup.py`** (3,027 بایت) — پشتیبانگیری pure-stdlib: کپی سازگار SQLite با **sqlite3 online backup API**، کپی `.env` و lockfile ها و `alembic.ini`، کپی درخت `alembic/`، **git bundle** کامل (تاریخچه همه branch ها)، حذف پشتیبانهای قدیمیتر از `--retain` (پیشفرض ۱۰). آخرین بکاپ موجود: `backups\20260816_033634`.
- **`database\create_test_data.py`** (4,354 بایت) — ساخت داده تست (کاربر demo با رمز هاردکد؛ در گزارش امنیتی بهعنوان HIGH flagged شده).

---

## 6) Deploy، Docker، CI/CD

- **`deploy\`** — کاملاً خالی (`ci\.gitkeep`، `docker\.gitkeep`، `k8s\.gitkeep`). هیچ مانيفست Kubernetes یا اسکریپت دپلوی واقعی وجود ندارد.
- **`docker-compose.yml`** (۳۰۶ بایت) — دو سرویس: `postgis/postgis:16-3.4` (پورت 5432، کاربر/رمز/دیتابیس از `.env`) و `redis:7-alpine` (پورت 6379). **نقص:** در `requirements*.txt` هیچ درایور Postgres (`psycopg`) یا کلاینت Redis و هیچ `geoalchemy2` وجود ندارد → اپلیکیشن عملاً نمیتواند به این سرویسها وصل شود؛ compose صرفاً زیرساخت آماده است.
- **`.github\workflows\ci.yml`** (2,527 بایت) — سه job:
  1. `lint`: Python 3.11 + uv؛ `ruff check .` + `ruff format --check .`؛ سپس `mypy engine/ database/ services/` با **`continue-on-error: true`** (مایپای غیربلوکهکننده — ریسک: خطای تایپ وارد CI میشود).
  2. `test` (needs lint): نصب فقط `requirements.lock.txt` و اجرای `pytest --tb=short -q`.
  3. `frontend`: Node 22 + pnpm؛ `pnpm install --frozen-lockfile` + `pnpm build` — **vitest اجرا نمیشود** در CI.
  - **هیچ job دپلوی/انتشار** (docker build/push، Supabase db push) وجود ندارد. کنکورنسی `cancel-in-progress` دارد. شکاف مهم: تستهایی که `xarray`/`rasterio`/`netcdf4`/`h5netcdf`/`duckdb` ایمپورت میکنند (test_era5، test_copernicus_phase4 و…) در CI که فقط lock-file نصب میکند **در کالکشن میترکند** چون این پکیجها در lock نیستند (در `.venv` محلی بهصورت ad-hoc نصب شدهاند).

---

## 7) DVC، بنچمارکها (Numba چند برابر؟)

- `dvc.yaml` و `.dvcignore` — بخش ۳ بالا؛ اسکلت غیرقابلاجرا.
- **`benchmarks\benchmark.py`** (4,460 بایت) + **`benchmarks\benchmark_report.md`** (2,377 بایت) — گزارش W5 مورخ 2026-08-14 (Python 3.11.15، numba 0.67، numpy 2.4.6، MSVC 2019 /O2):
  - **van Genuchten K(h)، N=200,000:** pure Python 0.234s → NumPy 0.036s (**6.4x**) → Numba 0.038s (**6.1x**) — یعنی ادعای «۸ برابر» درست نیست؛ ~۶ برابر است. هر سه پیادهسازی با rtol 1e-10 همخواناند.
  - **LHS vs Monte Carlo** (E[x+y]): SE از 0.03966 به 0.00042 → **کاهش واریانس 95.5x** (Python) و 108x در C++ (`hydroma_advanced_tests.exe`) — LHS سامپلر پیشفرض سناریوها (`yield_ensemble_lhs`).
  - **Muskingum (N=5000):** Numba 0.00006s در برابر loop خالص 0.00318s → **50.4x**.
  - **هسته C++**: 70/70 تست سبز (35+35)؛ کرنلهای جدید: Richards 1D (Picard اصلاحشده، بستهشدن جرم <1cm)، Saint-Venant 1D (Rusanov، خطای جرم <2%)، FAO-56 dual-Kc (بسته ~0mm)، RUSLE+SDR+Brune، MC/LHS. **لنگر رگرسیون بینزبانی:** K(h)/θ(h) سیپلاسپلاس با مرجع Numba تا 1e-6 تطبیق دارد (رفع باگ براکت مفقود Mualem–van Genuchten).
  - Caveat خود گزارش: pybind11 ماژول فعلاً ساخته نشده بود ولی طبق README اخیر `engine\cpp_core\build2\Release\hydroma_core.cp311-win_amd64.pyd` ساخته شده و در `engine\hydroma\cpp_bridge\` کپی شده (verification 2026-08-14).
- **`tests\benchmarks\test_numba_performance.py`** (2,574 بایت) — ۲ تست NDVI performance (آرایه بزرگ/کوچک).
- پشتیبانی API: `services\api_gateway\routers\benchmark.py` → `POST /api/v1/benchmark/ndvi` (مقایسه NumPy vs Numba، warmup برای JIT).

---

## 8) وابستگیها و ابزار کیفیت

- **`requirements.txt`** (837 بایت) — محدودههای pinned: fastapi>=0.141,<1.0؛ uvicorn؛ pydantic>=2.13,<3؛ sqlalchemy>=2,<3؛ **numpy>=2.4,<3؛ numba>=0.67,<1؛ pandas>=3,<4؛ scipy>=1.17؛ scikit-learn>=1.5**؛ requests/httpx؛ pytest>=9؛ pytest-timeout؛ aiogram>=3.30؛ **aiohttp==3.14.3 پینشده** (کامنت: python-bale-bot آن را downgrade میکند و aiogram را میشکند).
- **`requirements.lock.txt`** (3,053 بایت) — خروجی `uv pip compile`: fastapi 0.141.1، numpy 2.4.6، numba 0.67.0، pandas 3.0.5، scikit-learn 1.9.0، scipy 1.17.1، sqlalchemy 2.0.52، pytest 9.1.1، pydantic 2.13.4، starlette 1.6.0 و… (توجه: `.venv` محلی sklearn 1.5.2 دارد — با lock ناهماهنگ).
- **`requirements-optional.txt`** — همهچیز کامنتشده (torch، celery، redis، mlflow، xgboost، lightgbm، geopandas، rasterio، xarray، netcdf4، zarr، psycopg، geoalchemy2، duckdb) با اشاره به نصب شرطی. **شکاف:** برخی از اینها در واقع الزامیاند چون تستها و کد از آنها استفاده میکنند (rasterio در copernicus.py؛ xarray/netcdf4 در era5؛ duckdb در analytics).
- **`requirements-research.txt`** — محیط research (xarray، rasterio، geopandas، duckdb، diskcache، jinja2، numba>=0.58).
- **`pyproject.toml`** (1,568 بایت) — setuptools؛ `requires-python >=3.11`؛ extras: `dev` (pytest، pytest-cov، ruff، mypy) و `ml` (scikit-learn)؛ **ruff:** line-length 100، target py311، select `E,W,F,I,B,C4,UP,SIM`، ignore `E501,B008,C901,PLR0913,PLR0912`، per-file-ignore برای `__init__.py` و `tests/*`؛ **mypy:** python 3.11، `warn_return_any`، `check_untyped_defs`، `namespace_packages`، overrides ignore_missing_imports برای numpy/scipy/pandas/sqlalchemy/sklearn؛ **pytest:** `testpaths=["tests"]`، `python_files=["test_*.py"]`.
- وضعیت ابزارها در `.venv`: ruff 0.16.3، mypy 2.3.0، pytest 9.1.1، pytest-cov 7.1.0، torch 2.13.0، numba 0.67.0، coverage 7.15.4؛ **غایب**: dvc، mlflow، celery، redis client، psycopg.

---

## 9) فایلهای ریشهای — خلاصه وضعیت

- **`diagnosis.txt`** (80,646 بایت) — دامپ متنی ترکیبی از سورس و تستها (شامل `test_ecowallet.py` و `routers\ecowallet.py`)؛ یک آرتیفکت تشخیصی خام، بدون ساختار نتیجه.
- **`final_test_results.txt`** (7,334 بایت) — خروجی pytest قدیمی: **۱۲ خطای collection** (`NameError: model_validator`) + هشدار deprecation؛ `Interrupted: 12 errors` — وضعیت شکسته قبلی (اکنون رفع شده).
- **`full_test_results.txt`** (37,178 بایت) — خروجی pytest قدیمیتر: **SyntaxError** در `engine\hydroma\config\settings.py:190` (ادغام دو خط: `return env in (...)    model_config = ...`) — همان خطایی که با فایلهای `settings.py.backup` / `.env-backup` / `.safe-backup` در پوشه config ردیابی میشود؛ الان فایل سالم است.
- **`security_report.json.security-backup`** (2,573 بایت) — اسکن ۲۷۰ فایل، **۴ یافته HIGH** (همه «hardcoded password»): (۱) `database\create_test_data.py:36` مقدار واقعی `password="demo123"` (واقعی)، (۲-۴) سه مورد در `frontend\app\profile\page.tsx` — پیامهای اعتبارسنجی «Min 6 chars»/«Passwords mismatch»/«Password changed» که **false positive**اند. وضعیت env: `.env` وجود دارد، `.env.example` دارد، در gitignore هست، ۵۱ secret. پوشش gitignore **85%**؛ الگوهای ازقلمافتاده: `!.env.example`، `*.p12`، `*.pfx`.
- **یافتههای تکمیلی از `git ls-files` (مهم):** فایلهای زیر **در git کامیت شدهاند** با وجود .gitignore: `.env.backup` (فایل محیطی حاوی مقادیر)، `engine\hydroma\config\settings.py.env-backup`، `econojin.db-shm`، `econojin.db-wal` (WAL 4MB که مدام تغییر میکند و در git status دیده میشود)، `data\econojin.db-wal`/`-shm`/`bak_20260815_041559`، `hydroma_research.db.bak_20260815_041559`. `.env` اصلی و `econojin.db` ریشه در git نیستند (خوب) اما `.env.backup` حاوی ۳۴ مقدار غیر-placeholder است (ریسک افشای secret در تاریخچه git).
- وضعیت فعلی تست (تأیید زنده): ۳۷۱ تست جمعآوری میشود؛ آخرین commit (همین امروز 03:31) پیام «371 pytest + 18 vitest + lint green» دارد. دیتابیسها: دیتابیس ریشه داده واقعی دارد (۱ مزرعه، ۲ کاربر).

---

## نقاط قوت

1. **انضباط «صداقت داده» (honesty contract) در سطح کد**: برچسب `data_source="simulated"|"real"` در `SatelliteTile` و پاسخهای API، ارورهای صریح (`DataStoreNotConfigured`، `CopernicusNotConfigured`، `CppBridgeUnavailable`) و ممنوعیت صریح fabricate/fallback — رویکردی کمیاب و حرفهای که در `cds.py`، `copernicus.py`، `earth_search.py`، `registry.py` و `pinn_surrogate.py` یکدست رعایت شده.
2. **پوشش تستی نسبتاً قوی و روبهرشد**: ۳۷۱ تست پایتون (۱۹۱ واحد، ۷۷ یکپارچه، ۱۰۱ داده/ML) + ۱۸ تست vitest؛ تستهای داده آفلاین و mock-based با دیتای مصنوعی واقعگرایانه (NetCDF و COG سنتزیشده)؛ رجیستری ۲۲ مدل با ۸ تست conformance عددی و تستهای پاریتی C++/Python با تولرانس 1e-9/1e-6.
3. **لایه علمی واقعی**: کرنلهای C++20 (Richards، Saint-Venant، FAO-56 dual-Kc، RUSLE) با ۷۰ تست سبز، لنگر رگرسیون بینزبانی، بنچمارک مستند (LHS 95-108x کاهش واریانس، Muskingum Numba 50x) و مدل کارتهای فارسی با validity/limitations.
4. **زیرساخت پشتیبانگیری و bootstrap خوب**: `backup.py` با sqlite online-backup API + git bundle + retention؛ `bootstrap_admin.py` idempotent؛ اسکیمای واحد SQLAlchemy/Alembic با ۶ migration و head سالم.
5. **قراردادهای کیفیت کد**: pyproject کامل (ruff/mypy/pytest)، lock-file با uv، CI سه مرحلهای، مستندات فنی انگلیسی/فارسی (docs/en 0-23 + docs/fa)، CVE ثبتشده برای Next.js.

## نقاط ضعف / ریسک

1. **افشای secret در git**: `.env.backup`، `settings.py.env-backup` و فایلهای DB/WAL در تاریخچه git کامیت شدهاند — ریسک امنیتی جدی (rotating همه کلیدها + پاکسازی تاریخچه git لازم است).
2. **دو دیتابیس SQLite موازی با اسکیمای متفاوت** (`econojin.db` ریشه با داده واقعی در برابر `data\econojin.db` خالی) — ریسک واگرایی و ازدسترفتن داده؛ مشخص نیست کدام مرجع است.
3. **CI در عمل شکسته خواهد بود**: نصب فقط `requirements.lock.txt` در CI بدون xarray/rasterio/netcdf4/h5netcdf/duckdb → تستهای ERA5/Copernicus در CI خطای ImportError میدهند؛ mypy با `continue-on-error: true` بلوکه نمیشود؛ vitest اصلاً در CI اجرا نمیشود؛ هیچ job دپلوی وجود ندارد.
4. **DVC غیرقابلاجرا**: `services.satellite.cli` وجود ندارد، dvc نصب نیست؛ `dvc.yaml` اسکلت نمایشی است و هیچ stage ای واقعاً قابل اجرا نیست.
5. **earth_search داده شبیهسازیشده دارد** (با برچسب صادقانه) — اگر UI برچسب را در همهجا نشان ندهد، داده مصنوعی ممکن است بهعنوان واقعی دیده شود؛ مسیر تولیدی واقعی (CDSE) به credential وابسته است.
6. **پوشش (coverage) ناموجود عملاً**: `.coverage` خالی است؛ هیچ عدد پوشش قابل استنادی در پروژه نیست.
7. **عدم تطابق وابستگیها**: sklearn در venv (1.5.2) با lock (1.9.0)؛ پکیجهای «optional» که الزامیاند؛ بدون psycopg/redis با وجود docker-compose postgis/redis.
8. **پوشه `ml/` خالی** (فقط gitkeep) — انتظار دایرکتوری داده/مدل/رجیستری واقعی؛ PINN فقط scaffold با toy-loop (هیچ وزنی ذخیره نشده).
9. **Supabase ناقص**: فقط ۱ migration با RLS نمونه روی `farms`؛ بقیه جداول بدون policy؛ بدون config.toml و بدون پایپلاین db push در CI.
10. **placeholder در کد**: `engine/hydroma/*/tests/test_{module_name}.py` (placeholders)؛ سرویسهای auth/ledger/notification/reporting/workflow هرکدام ~۱۱۳ خط placeholder؛ `tests/unit/test_placeholder.py`؛ تست E2E صفر.

## پیشنهادها

1. **فوری/امنیتی**: چرخش (rotate) همه کلیدهای `.env`؛ حذف `.env.backup`، `settings.py.env-backup` و `*.db-wal/*.db-shm/*.db.bak` از git (git filter-repo + تاریخچه)؛ افزودن `!.env.backup`/`*.p12`/`*.pfx` به .gitignore و قفل کردن مسیرهای حساس با هشدار در CI.
2. **یکسانسازی دیتابیس**: انتخاب یک مسیر واحد (پیشنهاد: `data/econojin.db` طبق config فعلی)، migrate دادههای دیتابیس ریشه، حذف DB ریشه، و افزودن تست سلامت که فقط یک SQLite در ریشه repo وجود دارد.
3. **تعمیر CI**: افزودن پکیجهای علمی لازم به `requirements.txt`/lock (یا نصب `requirements-research.txt` در job تست)؛ mypy را بلوکهکننده کنید؛ اسکریپت `test` برای vitest در package.json + اجرای آن در job فرانت؛ افزودن job دپلوی (docker build یا Supabase db push).
4. **DVC واقعی**: یا `services/satellite/cli.py` را با دستورهای fetch-scenes/sample-bands/load-db بسازید و dvc را نصب کنید، یا `dvc.yaml` را حذف/علامتگذاری کنید تا «pipeline نمایشی» گمراهکننده نباشد.
5. **ML**: آموزش و ذخیره واقعی surrogate PINN (با ثبت loss/metric و تست مقایسه سرعت با solver مرجع)؛ پر کردن `ml/` (دیتاست، وزن، کارت مدل نسخهدار)؛ اضافه کردن tracking (MLflow یا حداقل JSON ثبت).
6. **پوشش**: اجرای `pytest --cov=engine --cov=services --cov-report=term-missing` بعد از سبز شدن و ثبت عدد پوشش بهعنوان gate در CI (هدف اولیه ≥70% برای لایه سرویس).
7. **Supabase**: تکرار الگوی RLS برای همه جداول حساس (satellite_analyses، eco_wallets و…)؛ افزودن `config.toml` و اجرای `supabase db push` در CI.
8. **کیفیت تست**: حذف placeholders (`test_placeholder.py`، `test_{module_name}.py`)، پر کردن `tests/e2e`، و اضافه کردن تستهای جدولهای audit/content در دیتابیس فعال.

---

*گزارش بر اساس بازرسی زنده فایلها و اجرای pytest --collect-only تهیه شد؛ هیچ مقدار secret (`.env`) در این گزارش درج نشده و فقط نام کلیدها ارجاع داده شده است.*
