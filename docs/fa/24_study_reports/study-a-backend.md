# گزارش مطالعه بکاند و موتور علمی پروژه اکو نوژین (Eco Nojin / HyDroMa)

**تاریخ مطالعه:** 2026-08-17
**مسیر پروژه:** `D:\eco_nojin`
**محدوده:** بکاند، موتور علمی، میکروسرویسها، دیتابیس، بلاکچین، امنیت
**روش:** خواندن مستقیم کد با PowerShell (Get-ChildItem / Get-Content)

---

## ۰) نمای کلی معماری

پروژه یک پلتفرم کشاورزی پایدار یکپارچه است: فرانتاند Next.js 15 (پوشه `frontend/`)، بکاند FastAPI متمرکز در `services/api_gateway/`، موتور علمی پایتونی `engine/hydroma/`، هسته عددی C++20 در `engine/cpp_core/`، لایه داده SQLAlchemy روی SQLite (فعلاً) با مهاجرت Alembic، شبیهسازی بلاکچین (EthereumTester + رجیستریهای in-memory)، و کانالهای دسترسی USSD/SMS/Voice. مستند معماری در `docs/ARCHITECTURE.md` است. نکته مهم: معماری «سرویسگرا» فقط در نام است؛ عملاً یک اپلیکیشن FastAPI واحد (api_gateway) همه روترها را لود میکند و سرویسهای `auth/ledger/notification/reporting/workflow` صرفاً placeholder هستند (فقط `main.py` چاپکننده + `models.py` خالی).

---

## ۱) `engine/hydroma/` — موتور علمی پایتونی

فهرست کامل ماژولها: `soil`, `climate`, `carbon`, `satellite`, `scenarios`, `watershed`, `ecowallet`, `marketplace`, `materials`, `ussd`, `voice`, `blockchain`, `ai_assistant`, `cpp_bridge`, `core`, `config`, `api`, `performance`, `wrapper.py`, `cpp_bindings.py`. ماژولهای **placeholder** (فقط Pydantic skeleton خالی + `tests/test_{module_name}.py` قالبی): `crop`, `data_ingestion`, `ecotourism`, `erosion`, `finance`, `geospatial`, `groundwater`, `hydrology`, `ml`, `mrv`, `plants`, `risk`, `standards`, `web_search`, `scenario` (فقط `__init__.py`).

### ۱.۱ soil — کاملترین ماژول
- `soil/physics.py` — معادلات: **van Genuchten (1980)** برای منحنی نگهداشت آب `θ(h) = θr + (θs−θr)/(1+|αh|ⁿ)^m`، **Mualem (1976)** برای هدایت هیدرولیکی `K(h) = Ks·Se^0.5·[1−(1−Se^(1/m))^m]²`، **Brooks & Corey (1964)**، **Campbell (1974)**؛ جدول پارامترهای **Carsel & Parrish (1988)** برای ۱۲ بافت USDA با Ks برحسب cm/day؛ توابع `available_water_capacity` (FC@-330cm منهای PWP@-15000cm)، `water_retention_curve`.
- `soil/chemistry.py` — CEC (تخمینی از clay/OM/pH با تفسیر)، **ESP** (آستانه ۱۵٪ سدیمی)، **SAR** = Na/√((Ca+Mg)/2)، نیاز آهک/گوگرد بر اساس pH (هدف ۶٫۵).
- `soil/health.py` — **Soil Health Index (SHI)**: میانگین وزنی ۹ شاخص (pH، ماده آلی، N، P، K، CEC، بافت، ساختمان، فعالیت بیولوژیک) با وزنهای ثابت، خروجی score 0-100 + عوامل محدودکننده + توصیه.
- `soil/salinity.py` — طبقهبندی شوری بر اساس EC بر مبنای **USDA Handbook 60 (1954)** (۵ کلاس: non_saline تا very_strongly_saline) + توصیه محصول و مدیریت + `calculate_leaching_requirement`.
- `soil/taxonomy.py` — کلاسهای ۱۲گانه بافت USDA با مرزهای مثلث بافت + سلسلهمراتب taxonomy (order تا series) + ۱۲ راسته خاک.
- `soil/texture.py` — طبقهبند مثلث بافت USDA (تابع `classify_texture`) + `texture_triangle_coords` برای رسم.
- `soil/pedotransfer.py` — **Saxton & Rawls (2006)**: تخمین θ_1500 (PWP)، θ_33 (FC)، θs، Ks از درصد شن/رس/ماده آلی با clamps فیزیکی.
- `soil/water_retention.py` — نسخه موازی vG (پارامترهای کمی متفاوت از physics.py — منبع ناسازگاری).
- `soil/recommendations.py` — تولید توصیههای کودی/اصلاحی.
- تست: `soil/tests/test_soil.py` حدود ۳۰KB (جامعترین تست ماژول).

ورودیها: مقادیر pH، ماده آلی، N/P/K، درصد رس/سیلت/شن؛ خروجیها: بافت، امتیاز سلامت، پارامترهای هیدرولیکی، توصیهها.

### ۱.۲ climate
- `climate/et_calculator.py` — فقط **Hargreaves-Samani**: `ET0 = 0.0023 × 0.408 × Ra × (Tmean + 17.8) × √(Tmax − Tmin)` با validation. نسخه کامل **FAO-56 Penman-Monteith** فقط در C++ هست (در Python پیادهسازی نشده).

### ۱.۳ carbon
- `carbon/calculator.py` — نرخ جذب کربن (tonnes CO₂/ha/yr) به تفکیک ۸ نوع پروژه (Afforestation 8.0، Reforestation 6.0، Soil Carbon Compost 1.2، Biochar 3.0 با permanence 500 سال و…) بر مبنای IPCC AR6؛ ضریب منطقهای (tropical 1.3 / arid 0.6)، discount عدمقطعیت ۱۵٪، قیمتگذاری voluntary market (Verra $12، Gold Standard $18)؛ رجیستری پروژه **in-memory** (`_projects: dict`) — دادهها با ریاستارت از بین میرود.

### ۱.۴ satellite
- `satellite/analyzer.py` — `SatelliteAnalyzer` (اورکستر): جستجوی تایل Sentinel-2، محاسبه شاخصها، تفسیر NDVI، تولید توصیه؛ singleton `get_analyzer()`؛ fallback صادقانه (data_quality="poor") وقتی داده نباشد.
- `satellite/processors/indices.py` — **NDVI، EVI، SAVI، NDWI، NBR** با فرمول استاندارد و clipping به [-1,1]؛ `interpret_ndvi`.
- `satellite/providers/earth_search.py` — کلاینت **STAC عمومی Element 84** (بدون API key، Sentinel-2 L2A، فیلتر ابر).
- `satellite/providers/nasa_power.py` — داده هواشناسی روزانه NASA POWER (T2M_MIN/MAX, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR).

### ۱.۵ scenarios
- `scenarios/climate_scenarios.py` — **سناریوهای CMIP6/IPCC AR6 سادهشده برای خاورمیانه/ایران**: SSP1-2.6، SSP2-4.5، SSP5-8.5 برای 2030/2050/2100 (مثلاً SSP5-8.5 در 2100: +5.2°C و −25٪ بارش)؛ تخمین ΔET0 ≈ 2.5٪ به ازای هر درجه.
- `scenarios/crop_scenarios.py` — مدل عملکرد محصول **سبک AquaCrop (Steduto et al. 2009)**: پایگاه ۱۳+ محصول (گندم، جو، ذرت، ارزن، سورگوم، نخود، گلرنگ، گیاهان دارویی…) با water productivity، Kc، دمای بهینه/حداکثر؛ `simulate_crop_yield` با فاکتورهای تنش دمایی، آبی، CO₂ fertilization (+5٪/100ppm).
- `scenarios/monte_carlo.py` — **Monte Carlo** برای عملکرد محصول و اقلیم (پارامتر seed برای تکرارپذیری، صدکهای ۵/۲۵/۵۰/۷۵/۹۵، احتمال شکست محصول <500 kg/ha).
- `scenarios/whatif_engine.py` — مقایسه سناریوها (رتبهبندی yield/revenue/water-productivity).

### ۱.۶ watershed
- `watershed/calculator.py` — روش **Rational** برای رواناب `Q = A×R×C`؛ طراحی **سنگچین (Check Dam)**، **ترانشه کانتور**، **Half-Moon** با ابعاد/هزینه بر مبنای FAO Watershed Management Field Manual.

### ۱.۷ سایر ماژولهای واقعی
- `materials/compost_formulator.py` — **محاسبه نسبت C/N کمپوست**: `Σ(mass×C%) / Σ(mass×N%)` (پاسخدهنده به «C/N کمپوست»).
- `ecowallet/` — دفتر کل متمرکز Phase 1 (`ledger.py`: EARN/REDEEM/TRANSFER/ADMIN با balance_after)، قوانین امتیازدهی (`earning_rules.py`: کاشت درخت ۵۰ ECO، احراز کربن ۸۰ ECO و…)؛ صریحاً «not a cryptocurrency».
- `marketplace/` — کاتالوگ محصول **in-memory با دیتای دمو** (تعاونیهای گلستان/قشقایی/خراسان)، مدیریت سفارش با رزرو موجودی، traceability.
- `ussd/` — موتور USSD (`engine.py`: منوی چندزبانه en/fa/ar، فرمت Africa's Talking CON/END) + پارسر SMS (`sms_parser.py`: دستورات SOIL/CROP/PRICE/WEATHER/ASK/LANG).
- `voice/` — IVR با DTMF، TTS/STT providers، `voice_assistant.py`.
- `ai_assistant/` — **RAG مبتنی بر TF-IDF + cosine similarity** روی دانشنامه FAO (`knowledge_base.py`)، آستانه شباهت ۰٫۰۵؛ پاسخ صادقانه «نمی دانم» در نبود نتیجه.
- `blockchain/` — به بخش ۵ مراجعه شود.
- `cpp_bridge/` — نسخههای **Numba-شتابدار**: `soil_physics_fast.py` (vG + K(h))، `hydrology_fast.py` (Muskingum-Cunge)، `indices_fast.py` (شاخصهای برداری موازی)؛ + `hydroma_core.cp311-win_amd64.pyd` (۳۹۴KB، کپی از build2).
- `core/` — `database.py` (delegation به `database.config`)؛ `models.py` (SoilProfile, Plant, Material با SQLAlchemy 2.0 `mapped_column`)؛ `schemas.py` (Pydantic برای SoilProfile/Plant/Material).
- `wrapper.py` / `cpp_bindings.py` — لایه پایتونیک روی C++ با fallback خودکار (جزئیات در بخش ۲).
- `config/settings.py` — pydantic-settings؛ شامل `secret_key="dev-secret-key"` و `jwt_secret="dev-jwt-secret"` بهعنوان **پیشفرض هاردکد** (ریسک امنیتی، بخش ۶).

---

## ۲) `engine/cpp_core/` — هسته C++20

### ۲.۱ ساختار و فایلهای کلیدی
- `CMakeLists.txt` — CMake ≥3.22، استاندارد **C++20**، کتابخانه استاتیک `hydroma_core` از ۱۰ فایل `src/*.cpp`، آپشن `HYDROMA_BUILD_PYTHON_BINDINGS` برای pybind11 (فقط در صورت پیدا شدن pybind11)، تستهای مستقل (بدون پایتون).
- هدرها در `include/hydroma/`، پیادهسازیها در `src/`، بایندینگها در `bindings/`، تستها در `tests/` (test_hydroma.cpp + test_advanced.cpp).
- فایلهای `build_*.bat` و ابجکتفایلهای قدیمی در ریشه (ساخته دستی با cl).

### ۲.۲ الگوریتمهای پیادهسازیشده
| ماژول | الگوریتم | نکته |
|---|---|---|
| `hydrology` | **Muskingum–Cunge** flood routing: `O(t+1)=C0·I(t+1)+C1·I(t)+C2·O(t)` | پارامترهای موج سینماتیک c=(5/3)v، `route_multi_reach`؛ همارز Numba |
| `soil` | van Genuchten θ(h) + Mualem K(h) | جدول پارامترها؛ باگ K فرمول 2026-08 رفع شده |
| `erosion` | **RUSLE**: `A = R·K·LS·C·P` | LS طبق McCool 1987 (دو رژیم شیب <9% و ≥9%)، R تخمینی Renard & Freimund 1994، K جدولی بافت |
| `climate` | **FAO-56 Penman–Monteith ET0** + Hargreaves-Samani + Ra (FAO-56 eq 21-25) + تشعشع خالص | کاملترین پیادهسازی ET0 در پروژه همین‌جاست |
| `indices` | NDVI/EVI/SAVI/NDWI/NBR (اسکالر و آرایه) | |
| `richards` | **معادله 1D ریچاردز (فرم مختلط)**، FV سلول-مرکز، backward Euler، **تکرار Picard اصلاحشده Celia et al. 1990** | `RichardsOptions/RichardsResult`؛ تشخیص سیستم ill-posed در BC تمام-شار؛ بقای جرم تا دقت عددی |
| `saint_venant` | **1D سنت-ونان** (آب کمعمق): فلاکس **Rusanov (LLF)** + اصطکاک Manning + سلول خشک | تست dam-break با بقای جرم <۲٪ |
| `crop_water` | **بیلان آب روزانه دو-ضریب FAO-56** (Kcb·Ks + Ke، TEW/REW، Ks تنش، آبیاری خودکار) | بستن بیلان ~۰mm |
| `sediment` | RUSLE گرید + **SDR (Boyce 1975): SDR = 0.41·A^-0.3** + **راندمان تله Brune (1953)** | TE = (C/I)/(C/I+k), k≈0.15 |
| `sampling` | **Monte Carlo + Latin Hypercube (McKay 1979)** + `yield_ensemble_lhs` | کاهش واریانس ~۱۰۸× در تستها |

### ۲.۳ اتصال به پایتون
- **pybind11** (مسیر اصلی): `bindings/bindings.cpp` با `PYBIND11_MODULE(hydroma_core, m)` تمام هستهها (شامل structهای خروجی) را در معرض پایتون میگذارد؛ خروجی `.pyd` با `OUTPUT_NAME hydroma_core` (آرشیو لینک جدا `hydroma_core_py` برای جلوگیری از تداخل با `.lib` استاتیک).
- **ctypes/C API** (مسیر ثانویه): `bindings/c_api.cpp` سه تابع `__declspec(dllexport)` — `et0_hargreaves`, `extraterrestrial_radiation`, `vg_theta` — برای `hydroma_core.dll` قدیمی. (توجه: c_api.cpp در CMakeLists نیست؛ با bat دستی کامپایل شده.)
- لودر پایتون: `engine/hydroma/cpp_bindings.py` جستجو در `build2/Release`, `build/Release` و... با تطبیق نسخه (cp311/cp312) و بارگذاری از طریق `importlib.util.spec_from_file_location`؛ سقوط امن به pure Python.

### ۲.۴ وضعیت باینری (DLL)
- `build2/Release/hydroma_core.cp311-win_amd64.pyd` (۳۹۴,۲۴۰ B) ✅ و `cp312` (۴۰۴,۴۸۰ B) ✅ — ساخته 2026-08-14 با CMake+pybind11 (Python 3.11 از `.venv`).
- کپی فعال: `engine/hydroma/cpp_bridge/hydroma_core.cp311-win_amd64.pyd` ✅ (همان سایز؛ import جواب میدهد).
- `engine/cpp_core/hydroma_core.dll` (۱۲۳,۳۹۲ B) — بیلد قدیمیتر (احتمالاً نسخه C API/ctypes، تاریخ قدیمیتر).
- تستها: ۷۰/۷۰ سبز (دو exe)؛ regression: C++ در برابر مرجع Numba تا 1e-6.

---

## ۳) `services/` — میکروسرویسها

### ۳.۱ واقعیت معماری
سرویسهای `auth/`, `ledger/`, `notification/`, `reporting/`, `workflow/` همگی **placeholder** هستند: `main.py` فقط چاپ میکند `"Eco Nojin service placeholder: X"` و `models.py` اسکلت Pydantic خالی (BaseXCreate/Read/Update با `pass`). منطق واقعی auth داخل خود `api_gateway` است. پس «میکروسرویس» بودن عملاً قراردادی/نامی است.

### ۳.۲ api_gateway (واقعی، مونولیت FastAPI)
- `services/api_gateway/main.py` — اپ FastAPI با `lifespan` (init_db + حلقه هشدار NDVI هر ۹۰۰ ثانیه در thread)، **GZip** و **CORS** (localhost)؛ ۲۳ فایل روتر با `include_router` داخل try/except جداگانه (خطای یک روتر بقیه را نمیکشد)؛ هندلر سراسری خطا (در development جزئیات را لو میدهد، در production "Internal error")؛ `/debug/routes` فقط در development.
- `auth.py` (گیتوی) — JWT + bcrypt + RBAC (بخش ۶).
- `security.py` — سه middleware (RateLimit، SecurityHeaders، RequestID) که **فقط در تستها ثبت شدهاند و در main.py رجیستر نشدهاند** (کد مرده — ریسک).

### ۳.۳ فهرست کامل APIها (استخراجشده از دکوریتورها؛ ۱۴۷ route در ۲۳ فایل، همه با پیشوند `/api/v1/...`)
- **auth** (۹): POST /auth/register, /login, /forgot-password, /reset-password, /change-password, /refresh, /seed-demo؛ GET /auth/me؛ PUT /auth/profile.
- **soil** (۵): POST /soil/analyze؛ GET /soil/history/{farm_id}, /soil/erosion؛ POST/GET /soil/ (CRUD SoilProfile).
- **satellite** (۱۰): POST /satellite/analyze, /era5/series؛ GET /satellite/history/{farm_id}, /weather, /stats/{farm_id}, /indices, /providers, /stores/status, /cds/status, /health.
- **carbon** (۱۲): POST /carbon/calculate, /register, /photosynthesis, /quantum, /soil-carbon, /projects/{project_id}/verify, /projects/{project_id}/issue؛ GET /carbon/projects, /standards, /species, /projects/{project_id}/oracle-report, /wallet.
- **blockchain** (۱۵): POST /blockchain/carbon/projects, /carbon/projects/{id}/verify, /carbon/projects/{id}/issue, /carbon/credits/transfer, /carbon/credits/{id}/retire, /supply-chain/products, /supply-chain/products/{id}/events؛ GET /carbon/projects/{id}, /carbon/credits/{id}, /carbon/stats, /supply-chain/products/{id}, /supply-chain/products/{id}/history, /supply-chain/stats, /health, /info.
- **ecowallet** (۹): POST /ecowallet/wallets, /earn, /redeem, /ussd, /distribute؛ GET /stats, /health, /earning-options, /redemption-options.
- **marketplace** (۹): GET /products, /products/search, /products/{id}, /products/{id}/trace, /producers, /orders, /stats؛ POST /orders, /orders/{id}/confirm.
- **admin** (۲۶): GET /admin/users, /audit, /content, /content/{id}/versions, /content/{id}/translations, /bots, /errors, /settings, /models, /overview, /security؛ POST /admin/users/{id}/block, /unblock, /content, /content/{id}/publish, /content/{id}/translate, /content/generate-draft, /content/{id}/schedule, /content/{id}/cancel-schedule, /bots/{key}/toggle, /errors/{id}/ack؛ PUT /admin/settings/{key}, /admin/content/{id}؛ DELETE /content/{id}.
- **analytics** (۷): GET /analytics/overview, /soil-trends, /ndvi-trends, /scenario-impact, /carbon-summary, /activity-timeline, /performance-metrics.
- **ai** (۶): POST /ai/chat (×۲ فایل), /ai/stream, /ai/voice/tts؛ GET /ai/history, /ai/health.
- **ussd** (۷): POST /ussd/ussd, /ussd/africastalking, /ussd/sms, /ussd/sms/webhook؛ GET /ussd/health (×۲), /menu/preview.
- **voice** (۹): POST /voice/ivr/start, /ivr/dtmf, /tts, /stt, /ask؛ GET /voice/health (×۲), /ivr/menu/{language}, /languages.
- **سایر**: scenarios (POST /apply؛ GET /compare/{farm_id})، watershed (GET /structure-types؛ POST /design)؛ farms (GET/POST /؛ GET/DELETE /{farm_id})؛ sync (POST /batch؛ GET /history/{device_id}, /stats)؛ models (GET /، /pinn-status، /cpp-status، /{slug}؛ POST /{slug}/run)؛ materials (POST /calculate-compost)؛ science (GET /citations، /citations/index، /datasets)؛ content (GET /search)؛ benchmark (POST /ndvi؛ GET /status).

### ۳.۴ منطق کلیدی سرویسهای دیگر
- `services/carbon/verification.py` — **بررسیهای سبک VM0042** (baseline, additionality, leakage, permanence با MIN ۲۰ سال)؛ رد صریح در صورت شکست هر چک.
- `services/carbon/oracle.py` — گزارش گواهی `ECO-ORACLE-{project_id}` از state واقعی ذخیرهشده.
- `services/analytics/duckdb_service.py` — جمعبندی آماری NDVI/EVI/SAVI با **DuckDB in-process** (SQL روی لیست dict؛ خروجی None بهجای عدد جعلی).
- `services/satellite/copernicus.py` — کلاینت **CDSE** (OAuth2 client-credentials/password، جستجوی STAC sentinel-2-l2a، نمونهگیری باند B04/B08/B02 با rasterio، **ماسک ابر SCL** و «قرارداد صداقت»: بدون اعتبارنامه `CopernicusNotConfigured`، هرگز داده جعلی).
- `services/satellite/cds.py` + `era5_fetch.py` — پایپلاین **ERA5** (submit→poll→download، پارس NetCDF با xarray/netcdf4 یا h5netcdf؛ t2m و tp روزانه).
- `services/models/registry.py` — **رجیستری ۲۲ مدل علمی** با برچسب وفاداری (official/simplified/experimental) و مراجع (FAO-56، RothC، Farquhar، vG، RUSLE، IPCC allometric، Chave 2014، Mokany 2006، FAO salinity…)؛ `run_model` خطای صریح، بدون fallback خاموش.
- `services/models/pinn_surrogate.py` — اسکلت **PINN** (MLP + Tanh؛ torch اختیاری؛ گزارش صادقانه `available=False`).
- `services/bots/` — آداپتورهای Telegram/Bale/Rubika، i18n (۲۵KB)، `alert_runner` (هشدارهای NDVI مزارع)، `core/ai.py` با **Ollama محلی** (در نبود مدل، مدرک خام RAG با توضیح — بدون ساخت محتوا).
- `services/ecowallet/service.py` — کیف پول **DB-backed** (جدول `eco_wallets`) با نرخهای earning و اعتبارسنجی موجودی.

---

## ۴) `database/` و `alembic/`

### ۴.۱ پیکربندی
- `database/config.py` — **یک** موتور SQLAlchemy واحد (رفع مشکل دیتابیس دوگانه Phase 0)؛ URL پیشفرض `sqlite:///./econojin.db` که بهصورت مسیر مطلق نسبت به ریشه پروژه resolve میشود؛ برای SQLite: `PRAGMA journal_mode=WAL`, `foreign_keys=ON`, `synchronous=NORMAL`؛ `init_db()` با `Base.metadata.create_all` (بوتاسترپ تحقیقاتی — در کنار alembic ریسک drift).
- `database/models.py` — **SQLAlchemy ORM**: ۲۰ مدل: User (با فیلدهای KYC، accept_tos)، PasswordResetToken (توکن ۶۴-کاراکتری، انقضای ۱ ساعت، یکبارمصرف)، Farm، SoilAnalysis، SatelliteAnalysis (با ستون `data_source` پیشفرض "simulated")، ScenarioRun، AIConversation، CarbonProject، EcoWallet، EcoTransaction (با balance_after)، Product، RecommendationCache، AuditLog، ContentVersion، ContentTranslation، Setting، ErrorLog، ContentItem. ستونهای JSON برای توصیهها؛ timestamps با `datetime.utcnow`.
- `engine/hydroma/core/models.py` — مدلهای موتور: SoilProfile، Plant، Material (سبک 2.0).
- `database/analytics.py` — گزارشهای تحلیلی.

### ۴.۲ Alembic — ۶ مایگریشن
ترتیب زنجیره: `ed7a1747d8db` (baseline unified schema) ← `c3d8e0f2a1b4` (audit_logs) ← `b7c9d2e4f1a3` (satellite provenance) ← `d4e9f0a3b2c5` (admin modules) ← `e5f1a2b3c4d5` (content versions/translations) ← `f6a2b3c4d5e6` (scheduled publishing). پوشه بکاپ `alembic.backup_20260816_032244` و `alembic.ini.backup_20260816_032245` وجود دارد.

### ۴.۳ نوع دیتابیس فعلی
**SQLite** (فایلهای `econojin.db` در ریشه ~۱؟ و `data/econojin.db` ۱۹۶KB با `-shm`/`-wal`). برای production، docker-compose شامل **PostGIS 16** (`postgis/postgis:16-3.4`) و Redis 7 آماده است؛ `DATABASE_URL` از `.env` میآید. Supabase: فقط یک مایگریشن `supabase/migrations/00001_auth_roles_rls.sql` (توابع `current_role()/is_admin()`، RLS روی `farms`).

---

## ۵) `blockchain/` — دفتر کل و رجیستری کربن

- `engine/hydroma/blockchain/web3_provider.py` — اتصال به **EthereumTester / PyEVMBackend** (بلاکچین آزمایشی in-memory، بدون وابستگی خارجی)؛ `get_accounts()[:10]`؛ برای production جایگزینی با Infura/Hyperledger پیشبینی شده.
- `engine/hydroma/blockchain/ledger.py` — `BlockchainLedger`: `deploy_contract` (ساخت قرارداد با ABI/bytecode دلخواه روی زنجیره تست)، `get_block_info`، `get_transaction`؛ singleton.
- `engine/hydroma/blockchain/carbon_registry.py` — `CarbonRegistry` (رجیستری کربن): dataclassهای `CarbonProject` و `CarbonCredit`؛ ماشین حالت `DRAFT → SUBMITTED → VERIFIED → ACTIVE → RETIRED` با اعتبارسنجی انتقال وضعیت (ValueError)؛ توابع register/verify/issue/transfer/retire/get_stats.
- `engine/hydroma/blockchain/supply_chain.py` — `SupplyChainRegistry`: محصول + رویدادهای TraceEvent (harvested/processed/…/delivered) و verify.
- **«غیرقابلتغییربودن» چگونه شبیهسازی شده:** (۱) `tx_hash` جعلی `0x{uuid4().hex[:64]}` در هر عملیات؛ (۲) قوانین انتقال وضعیت؛ (۳) نگهداری در dictهای in-memory. **هیچ زنجیره هش، امضا، Merkle یا persistence وجود ندارد** — آبجکتها در پایتون mutabl‌اند و با ریاستارت سرویس همهچیز پاک میشود. قرارداد هوشمند: فایل `.sol` در پروژه نیست؛ `BlockchainLedger.deploy_contract` صرفاً توانایی deploy را دارد (ABI/bytecode باید از خارج بیاید). `settings.blockchain_mode="simulation"` و `enable_blockchain=False`.
- مسیر API: روتر `services/api_gateway/routers/blockchain.py` این رجیستریهای in-memory را سرو میکند (۱۵ اندپوینت، بخش ۳). نکته: `services/ledger/` هیچ ارتباطی با این بلاکچین ندارد (placeholder).

---

## ۶) امنیت

### ۶.۱ احراز هویت (AuthN)
- **JWT (python-jose, HS256)**: `create_access_token` (ادعای sub + role، انقضا `access_token_expire_minutes`=۱۰۰۸۰ دقیقه = **۷ روز**) و `create_refresh_token` (ادعای `type=refresh`، ۳۰ روز) با **چرخش توکن** (rotation در هر refresh). `decode_token` با validation امضا/انقضا.
- رمز عبور: **bcrypt** از طریق `passlib.CryptContext(schemes=["bcrypt"])`.
- `get_current_user` (۴۰۱ سختگیرانه)، `get_current_user_optional`، `require_roles` (RBAC: farmer/advisor/admin)؛ روتر admin با `require_admin = require_roles("admin")` محافظت شده.
- Webhookهای مخابراتی (USSD/SMS/Voice) با `require_api_key` (X-API-Key مشترک)؛ در dev بدون کلید باز است، ولی در production اگر کلید تنظیم نشده باشد **۵۰۳ برمیگرداند** (رفتار درست).
- Tokenهای reset: ۶۴-کاراکتر `secrets`، انقضای ۱ ساعت، یکبارمصرف.

### ۶.۲ ریسکهای مشاهدهشده
1. **کلیدهای پیشفرض هاردکد**: `settings.py` دارای `secret_key="dev-secret-key"` و `jwt_secret="dev-jwt-secret"` است؛ اگر `.env` مقدار ندهد، امضای JWT با کلید عمومی شناختهشده انجام میشود (جعل کامل توکن). `.env.example` هم مقدار dev دارد. ارزش واقعی `.env` — نیازمند بررسی.
2. **Middlewareهای امنیتی ثبت نشدهاند**: `RateLimitMiddleware`/`SecurityHeadersMiddleware`/`RequestIDMiddleware` (فایل `security.py`) فقط در تستها استفاده میشوند؛ اپ واقعی فقط GZip + CORS دارد و `rate_limit_enabled=False` پیشفرض است.
3. **انقضای بلندمدت access token (۷ روز)** — در صورت نشت توکن، پنجره سوءاستفاده بزرگ است.
4. **حداقل طول رمز ۶ کاراکتر** در Register/Reset (ضعیف برای production).
5. `POST /auth/seed-demo` — ساخت کاربر دمو در هر environment (در production نباید در دسترس باشد).
6. `accept_tos`/`accept_privacy` وجود دارند ولی به نظر نمیرسد سمت سرور اجباری شوند (Boolean پیشفرض False).
7. **Stateهای in-memory** (بلاکچین، کربن، مارکتپلیس، کیف پول قدیمی) — از دست رفتن داده با ریاستارت؛ و در حالت چند-پردازهای ناسازگار.
8. **CORS** محدود به localhost (خوب) ولی `allow_credentials=True` با لیست صریح (خوب). `app_debug`/`/debug/routes` در production باید خاموش باشند.
9. چند فایل بکاپ در ریشه (main.py.bak، settings.py.backup و…) — ریسک آلودگی و افشای منطق/رمز قدیمی؛ `diagnosis.txt` و `security_report.json.security-backup` در ریشه.
10. SQLite + `check_same_thread=False` — مناسب توسعه، نه production (قفلنویسی).
11. نکات مثبت: کوئریهای پارامتری SQLAlchemy، `init_db` یکپارچه، هندلر خطای سراسری بدون لو دادن جزئیات در production، هدرهای CORS صریح، «قرارداد صداقت» در دادههای ماهوارهای (برچسب `simulated` در برابر `copernicus`)، عدم نگهداری secret در کد (بهجز پیشفرضها).

---

## ۷) نقاط قوت

1. **هسته علمی قوی و مستند**: C++20 با ۱۰ هسته عددی (Richards با Celia 1990، Saint-Venant با Rusanov، FAO-56 PM، RUSLE، dual-Kc، LHS) — نادر در پروژههای مشابه؛ ۷۰/۷۰ تست سبز + regression در برابر Numba تا 1e-6.
2. **لایهبندی درست محاسبات**: Python/Numba/C++ با fallback خودکار (`cpp_bindings.py` → wrapper)؛ بنچمارک مستند (LHS ۹۵٪ کاهش واریانس، Muskingum ۵۰×).
3. **صداقت داده (honesty contract)**: برچسب `data_source=simulated|copernicus`، عدم ساخت داده جعلی در Copernicus/ERA5، fallbackهای صریح.
4. **پوشش تست بالا**: ~۳۷۱ تست pytest + تستهای واحد برای تقریباً همه ماژولهای واقعی (soil ۳۰KB، blockchain ۱۰KB، ussd، voice، marketplace، ecowallet، scenarios).
5. **موتور خاک کامل**: ۷ فایل علمی با ارجاعات معتبر (vG/Mualem، Saxton-Rawls، Carsel-Parrish، USDA Handbook 60).
6. **رجیستری ۲۲ مدل با fidelity-label** و API یکنواخت؛ علم پایه کربن (Chave 2014، Farquhar، RothC-26.3) واقعی است.
7. **مهاجرت Alembic با زنجیره مشخص** و بکاپگیری منظم؛ طراحی مهاجرت به PostGIS.
8. **مدل تهدید نسبتاً آگاهانه**: RBAC، refresh rotation، API-key گارد، هندلر خطای environment-aware.

## ۸) نقاط ضعف / ریسک

1. **کلید JWT پیشفرض هاردکد** — بحرانیترین ریسک (جعل توکن اگر `.env` غایب/ضعیف باشد).
2. **middlewareهای امنیتی (rate-limit، security headers) کد مرده** — در main.py ثبت نشدهاند.
3. **سرویسهای placeholder** (`auth/ledger/notification/reporting/workflow`) — معماری اعلامی با واقعیت اجرایی (مونولیت FastAPI) همخوانی ندارد.
4. **بلاکچین صرفاً شبیهسازی in-memory** — «غیرقابلتغییربودن» نمایشی است (tx_hash جعلی uuid، بدون hash-chain/امضا/persistence)؛ در صورت ادعای production منجر به گمراهی.
5. **Stateهای in-memory متعدد** (کربن، مارکتپلیس، رجیستری بلاکچین) — از بین رفتن داده با ریاستارت.
6. **تعدادی ماژول علمی صرفاً اسکلت** (crop, hydrology, erosion, groundwater, plants, mrv, risk, finance, ml و…) با مدلهای Pydantic خالی — عدم تطابق فهرست قابلیتها با واقعیت.
7. **دو جدول پارامتر vG موازی** (`soil/physics.py` و `soil/water_retention.py` با مقادیر متفاوت) — ریسک ناسازگاری نتایج.
8. **init_db (create_all) در کنار Alembic** — ریسک schema drift.
9. **SQLite در production** + `check_same_thread=False`؛ CORS/Credentials؛ `seed-demo` فعال؛ طول رمز ۶ کاراکتر؛ access token ۷ روزه.
10. **عدم enforce کردن accept_tos** و نبود TOTP/2FA، نبود refresh-token revoke list (بجز rotation)، نبود logging ساختاریافته مرکزی (فقط logging استاندارد).
11. فایلهای بکاپ متعدد در ریشه و درخت سورس (main.py.bak*، settings.py.backup*، alembic.backup) — آلودگی مخزن.

## ۹) پیشنهادها

1. **فوری (امنیت):** حذف پیشفرضهای dev از `settings.py` (یا fail-fast اگر `secret_key` در production برابر پیشفرض باشد)؛ تولید `SECRET_KEY` قوی و اجباری کردن آن در `.env`؛ ثبت واقعی `RateLimitMiddleware` و `SecurityHeadersMiddleware` در `main.py`؛ فعالسازی rate-limit؛ کوتاهکردن عمر access token (۱۵-۳۰ دقیقه)؛ min length رمز ≥۸ با policy؛ غیرفعالسازی `seed-demo` و `/debug/routes` در production.
2. **دیتا و State:** جایگزینی رجیستریهای in-memory (بلاکچین/کربن/مارکت) با جدولهای SQLAlchemy (الگوی `services/ecowallet/service.py` درست است)؛ یا persistence دورهای + قفل تراکنشی.
3. **بلاکچین:** یا حذف ادعای «بلاکچین» و مستندسازی simulation (با hash-chain واقعی ساده: هش زنجیرهای از تراکنشها + امضا) یا اتصال به شبکه واقعی (Polygon RPC در settings هست ولی خاموش). حداقل: hash بلاک قبلی در tx_hash و نگهداری در DB.
4. **همگنسازی موتور:** ادغام دو جدول vG؛ حذف یا تکمیل ماژولهای placeholder (حذف از `__init__`/روترها تا با واقعیت کد تطبیق کند)؛ انتقال RUSLE/ET0 از wrapper به ماژولهای domain.
5. **فرایند:** جایگزینی `create_all` با alembic-only؛ پاکسازی فایلهای بکاپ از مخزن (به `.gitignore`/archives)؛ CI با اجرای تستهای C++ + pytest + lint (در `.github` هست — بررسی شود).
6. **قابلیت مشاهده:** افزودن OpenTelemetry/متریهای Prometheus، request-id فعال (کدش موجود است ولی ثبت نشده)، لاگ متمرکز.
7. **تستهای امنیتی:** افزودن تستهایی برای نبود default secret، enforce TOS، عدم دسترسی seed-demo در production، و فعال بودن middlewareها.

---

*گزارش بر اساس خواندن مستقیم کد تهیه شده؛ موارد دارای ابهام با «مبهم/نیازمند بررسی» مشخص شدهاند (قدرت واقعی کلیدهای `.env`، وضعیت CI، و وجود قرارداد `.sol` در جای دیگر مخزن).*
