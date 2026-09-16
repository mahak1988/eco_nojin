# گزارش فنی-حقوقی اکوکوین و اعتبار کربن — برای مدیریت

> **نوع سند:** مستند رسمی توسعه (Development Official Document)
> **تاریخ تدوین:** 2026-09-16
> **محدوده:** فقط docs/report — بدون تغییر در کد، سایت یا مخزن
> **وضعیت:** برای بررسی مدیریتی؛ پرهیز از ادعاهای پشتیبانی‌نشده

---

## فهرست مطالب

1. [خلاصهٔ اجرایی](#۱-خلاصه-اجرایی)
2. [معماری سیستم](#۲-معماری-سیستم)
3. [مرزهای اعتماد](#۳-مرزهای-اعتماد)
4. [چرخهٔ صدور اعتبار](#۴-چرخه-صدور-اعتبار)
5. [MRV / VVB / رجیستری](#۵-mrv-vvb-رجیستری)
6. [جلوگیری از احتساب دوگانه](#۶-جلوگیری-از-احتساب-دوگانه)
7. [بلاکچین در مقابل شبیه‌سازی](#۷-بلاکچین-در-مقابل-شبیه‌سازی)
8. [نقش‌های قرارداد هوشمند](#۸-نقش‌های-قرارداد-هوشمند)
9. [AML / KYC / Freeze / Audit](#۹-aml--kyc--freeze--audit)
10. [چارچوب‌های حقوقی بین‌المللی](#۱۰-چارچوب‌های-حقوقی-بین-المللی)
11. [گیت‌های حوزهٔ قضایی](#۱۱-گیت‌های-حوزه-قضایی)
12. [برنامهٔ ۳۰/۶۰/۹۰ روزه](#۱۲-برنامه-۳۰۶۰۹۰-روزه)
13. [معیارهای پذیرش](#۱۳-معیارهای-پذیرش)
14. [راهنمای تست و استقرار](#۱۴-راهنمای-تست-و-استقرار)
15. [Disclaimer حقوقی](#۱۵-disclaimer-حقوقی)
16. [منابع رسمی](#۱۶-منابع-رسمی)

---

## ۱. خلاصهٔ اجرایی

اکو نوژن یک سیستم چندلایه شامل موتور علمی MRV (RothC/ERA5/SoilGrids/KoBo)، کیف‌پول DB-backed (EcoWallet با تقسیم ۷۰/۱۵/۱۰/۵)، و رجیستری کربن (شبیه‌ساز درون‌حافظه‌ای) است. قرارداد CarbonCredit.sol (ERC20 با نقش‌های MINTER/PAUSER/VERIFIER) توسعه‌یافته اما منتشر نشده است. پروتکل deploy.js صاحب ۵ قرارداد دیگر را منتشر می‌کند اما CarbonCredit را نادیده می‌گیرد.

نتیجهٔ کلیدی: زیرساخت علمی MRV وجود دارد اما گواهی یا اعتبار کربن معتبر هنوز صادر نمی‌شود. فرانت‌اِند ادعاهایی مبنی بر ثبت روی بلاکچین پالیگون و استانداردهای Verra/Puro-Earth/ISO 14064-2 دارد که با وضعیت واقعی کد همخوانی ندارد. این سند صرفاً تحلیل و مستندسازی است؛ هیچ تغییری در سایت یا کد اعمال نشده.

## ۲. معماری سیستم (Architecture)

### ۲.۱ نمودار معماری سطح بالا

```
+---------------------------+-------------+----------------+---------------+
| ACCESS CHANNELS           |             |                |               |
| Web(PWA) | USSD | SMS | Voice| Bot | API | Mobile |             |
+---------------------------+-------------+----------------+---------------+
                               |
                     +---------+---------+
                     |   API GATEWAY    |
                     |   (FastAPI)      |
                     +---------+---------+
                               |
+------------------------------------------------------------------------------+
|                     HyDroMa SCIENTIFIC ENGINE                                |
|------------------------------------------------------------------------------|
| Soil | Carbon | Watershed | Satellite | Scenarios | Marketplace | Blockchain  |
| Climate | Hydrology | Erosion | Biofertilizer | Materials | MRV | Standards  |
+------------------------------------------------------------------------------+
                               |
+--------------------------------------------------+
|                 DATA LAYER                        |
|  PostgreSQL/SQLite  |  File Storage  |  S3/MinIO  |
+--------------------------------------------------+
                               |
+--------------------------------------------------+
|              BUSINESS MODULES                     |
|  Blockchain(CarbonRegistry) | Carbon(RothC/VVB)  |
|  EcoWallet(DB)              | Finance(Ledger)    |
+--------------------------------------------------+
                               |
+--------------------------------------------------+
|         SMART CONTRACT LAYER (Off-chain)         |
|  CarbonCredit.sol(ERC20) | Hardhat+ethers.js     |
|  deploy.js(5 contracts, NOT CarbonCredit)        |
+--------------------------------------------------+
```

### ۲.۲ لایه‌های سیستم

| لایه | مسئولیت | فایل‌های کلیدی | وضعیت |
|------|---------|----------------|--------|
| دسترسی | کانال‌های تعامل کاربر | Next.js 15, USSD, SMS, Voice | فعال (dev) |
| گیت‌وی | مسیریابی API، احراز هویت | services/api_gateway/ | فعال (dev) |
| علمی | محاسبات MRV، تخمین کربن | engine/hydroma/{carbon,mrv}/ | فعال |
| ازین | کیف‌پول، تراکنش‌ها | services/ecowallet/{ledger,distribution}.py | فعال (DB) |
| کربن | پروژه‌ها، اعتبارات | services/carbon/, services/business_modules/blockchain/ | شبیه‌ساز |
| قرارداد | ERC20 CarbonCredit | contracts/src/CarbonCredit.sol | تست (نه deploy) |
| داده | پایگاه داده، مهاجرت | database/, alembic/ | فعال |

### ۲.۳ جریان دادهٔ MRV به اعتبار

دادهٔ واقعی (ERA5, SoilGrids, Sentinel-2, KoBo)
   |
   v
MRV L1 Satellite: NDVI/EVI/SATI/NDMI (Numba-accelerated)
   |
MRV L2 IoT: Sensor readings + QA/QC (validate_reading)
   |
MRV L3 Citizen: Field reports (KoboToolbox-style)
   |
   v
NojinMRVEngine.generate_report()
   |
   v
CarbonCreditCalculator: CO2e = (current_SOC - baseline_SOC) * area * 3.67
   |
   v
Verification (services/carbon/verification.py):
  baseline, additionality, leakage, permanence
   |
   v
ALL pass -> Issue credits | ANY fail -> Return failed checks verbatim
```



## ۳. مرزهای اعتماد (Trust Boundaries)

### ۳.۱ ماتریس اعتماد

| منبع داده/عملیات | سطح اعتماد | مبنای ارزیابی | شواهد |
|---|---|---|---|
| داده‌های ماهواره‌ای ERA5/Sentinel-2 | بالا | API عمومی Copernicus/CDSE | Sentinel2Integration با endpoint واقعی |
| مدل RothC پیش‌بینی ترشح کربن | بالا | مدل علمی مقبول | rothc_service.py: ۲۰ سال، confidence=0.92 |
| SoilGrids/SoilProfile | بالا | دیتاست عمومی ISRIC | MRV Level 1 inputs |
| قرائت IoT (Level 2) | متوسط | QA/QC screening (mrv/qa.py) | is_usable() gate |
| گزارش‌های شهروندی (Level 3) | متوسط-پایین | KoboToolbox-style forms | صداقت‌سنجی نیازمند |
| رجیستری کربن | پایین | dict درون‌حافظه‌ای | uuid.uuid4().hex[:64] tx_hash |
| Blockchain ledger | پایین | In-memory simulation | web3_provider.py mode: simulation |
| قیمت‌گذاری اعتبار | متوسط | منابع بازار | PRICES_USD_PER_TON |
| CarbonCredit.sol | ندارد | Deploy نشده | deploy.js نادیده می‌گیرد |
| فرانت‌اِند ادعاها | بسیار پایین | Verra/Puro-Earth بدون VVB | سبزشویی |

### ۳.۲ تعاریف بولی (Boolean Claims)

| ادعای سیستم | مقدار حقیقی |
|---|---|
| اعتبار روی بلاکچین ثبت شده | FALSE — رجیستری درون‌حافظه‌ای |
| VVB مستقل تأیید کرده | FALSE — هیچ VVB مستقلی وجود ندارد |
| ISO 14064-2 گواهی صادر شده | FALSE — MRV فقط simplified accounting |
| پالیگون tx_hash: 0x... | FALSE — UUID ساختگی است |
| MRV با دادهٔ واقعی محاسبه می‌شود | TRUE (با برچسب modelled_estimate) |
| VVB می‌تواند تأیید کند | CONDITIONAL — چارچوب verification.py آماده |

### ۳.۳ حدود اعتماد

TRUSTED: ERA5/Climate data, Sentinel-2, RothC, SoilGrids, MRV QA/QC
SEMI-TRUSTED: IoT sensors, Citizen reports, Credit estimates, Oracle report (internal)
UNTRUSTED: CarbonRegistry tx_hashes, Blockchain state (dict), CarbonCredit.sol, Frontend claims

---

## ۴. چرخهٔ صدور اعتبار (Lifecycle Issuance)

### ۴.۱ مراحل چرخهٔ زندگی اعتبار

[1] ثبت پروژه (Register): DRAFT -> SUBMITTED — مساحت، نوع، مدت، baseline_activity
[2] تأیید متدولوژی (Verify): SUBMITTED -> VERIFIED — 4 بررسی (baseline/additionality/leakage/permanence)
[3] صدور اعتبار (Issue): VERIFIED -> ACTIVE — CO2e = dSOC * area * 3.67, 15% buffer
[4] انتقال (Transfer): ACTIVE -> محدود — نیاز به رضایت (AML/KYC gate)
[5] بازنشستگی (Retire): ACTIVE -> RETIRED — دائمی، justification اجباری
[6] اعتبارسنجی مجدد: هر ۵ سال — چارچوب ندارد

### ۴.۲ وضعیت فعلی هر مرحله

| مرحله | پیاده‌سازی | کد | وضعیت |
|---|---|---|---|
| ثبت پروژه | کامل | carbon_registry.py:register_project() | DB-backed |
| تأیید متدولوژی | صادقانه | services/carbon/verification.py | explicit pass/fail |
| صدور اعتبار | کامل (شبیه‌ساز) | carbon_registry.py:issue_credits() | توکن real نیست |
| انتقال | شبیه‌ساز | carbon_registry.py:transfer_credits() | بدون KYC فعال |
| بازنشستگی | کامل (شبیه‌ساز) | carbon_registry.py:retire_credits() | دائمی |
| اعتبارسنجی مجدد | ندارد | — | چارچوب ندارد |
| Issue به ZK | ندارد | — | آینده |

---

## ۵. MRV / VVB / رجیستری

### ۵.۱ MRV (Monitoring, Reporting, Verification)

| Level | منبع | ابزار | وضعیت |
|---|---|---|---|
| L1 Satellite | Sentinel-2 L2A (CDSE) | satellite_cdse.py | فعال — endpoint واقعی |
| L2 IoT | حسگرهای میدانی | mrv/qa.py validate_reading | QA/QC |
| L3 Citizen | KoboToolbox-style | mrv/schemas.py CitizenReport | فعال |

NojinMRVEngine: Sentinel2Integration (CDSE API) + CarbonCreditCalculator (CO2e=ΔSOC×area×3.67) + verification 4 checks. سنتیل uncertainty_pct=15%. MRV صراحتاً NOT a certification (docs/fa/43: W-001).

### ۵.۲ VVB (Validation/Verification Body)

| جنبه | وضعیت |
|---|---|
| VVB مستقل | ❌ NO |
| استاندارد | VM0042 cited, not certified |
| بررسی اصولی | 4 checks explicit in verification.py |
| میزبانی | — |
| گواهی صادر | ❌ NO — verification_status = pending |

### ۵.۳ رجیستری کربن

**شبیه‌ساز فعلی** (services/business_modules/blockchain/carbon_registry.py):
- CarbonRegistry: projects dict + credits dict + _tx_counter
- tx_hash = 0x{uuid.uuid4().hex[:64]} — ساختگی، از دست می‌رود با ریست سرور
- Status flow: DRAFT -> SUBMITTED -> VERIFIED -> ACTIVE -> RETIRED
- API: POST /carbon/projects, /verify, /issue, /transfer, /retire; GET /carbon/stats
- Health endpoint: "mode": "simulation" — صریحاً research mode

**رجیستری واقعی مورد نیاز**: مستقل از پلتفرم، URN/DOI شناسه، timestamp اثبات‌شده، API عمومی.

---

## ۶. جلوگیری از احتساب دوگانه (Double Counting)

### ۶.۱ وضعیت فعلی

| مکانیزم | وضعیت | جزئیات |
|---|---|---|
| Corresponding Adjustment (ماده ۶ پاریس) | پیاده نشده | هیچ مکانیزمی |
| شناسه يکتای مرکزی | ندارد | UUID ساختگي، قابل تکرار |
| Registry lock | ندارد | هیچ قفل مرکزی |
| Double-entry ledger | موجود | ledger.py (اکوکوین فاقد) |
| Retired flag | موجود (شبیه‌ساز) | carbon_registry.py:retire_credits() |
| Cross-registry check | ندارد | هیچ ارتباطی با VCS/GS |

### ۶.۲ ماده ۶ پاریس و ارتباط

- ماده ۶.۲: Transfer of Mitigation Outcomes (TMOs) — corresponding adjustments required
- ماده ۶.۴: Article 6 Supervisory Body (PACM) — verification of ITMOs
- بدون corresponding adjustment = احتساب دوگانه = نقض پروتکل پاریس
- وضعیت فعلی: هیچ مکانیزمی پیاده نشده

### ۶.۳ چارچوب پیشنهادی پیشگیری از احتساب دوگانه

1. شناسه یکتای جهانی: هر اعتبار با URN/DOI شناسه‌سازی شود
2. پس از صدور در رجیستری: بازرسی توسط VVB مستقل
3. Corresponding Adjustment: در صورت انتقال بین‌المللی (ماده ۶.۲)
4. Central Registry Lock: قبل از mint/burn، بررسی تلف‌نشدن
5. Periodic Reconciliation: مقایسه روزانه رجیستری‌ها

---

## ۷. بلاکچین در مقابل شبیه‌سازی (Blockchain vs Simulation)

### ۷.۱ مقایسه

| جنبه | بلاکچین واقعی | شبیه‌ساز فعلی |
|---|---|---|
| ذخیره‌سازی | دائمی، غیرقابل تغییر | dict درون‌حافظه — از دست می‌رود |
| tx_hash | cryptographically signed | uuid.uuid4().hex[:64] — ساختگی |
| غیرقابل‌تغییری | تضمین‌شده | NO |
| دسترسی عمومی | API RPC عمومی | فقط درون‌سرور |
| توزیع‌شوندگی | گره‌های متعدد | Singleton |
| هزینه معامله | Gas fee | صفر |
| وضعیت پروژه | 0x... قابل تأیید | 0x{uuid} — غیرقابل تأیید |

### ۷.۲ وضعیت نرم‌افزار بلاکچین

| مؤلفه | وضعیت | مسیر |
|---|---|---|
| CarbonCredit.sol | آماده (testnet-ready) | contracts/src/CarbonCredit.sol |
| Hardhat config | فعال | contracts/hardhat.config.js |
| deploy.js | ۵ قرارداد (CarbonCredit حذف) | contracts/scripts/deploy.js |
| Web3 provider | simulation mode | services/business_modules/blockchain/web3_provider.py |
| Blockchain Ledger | In-memory | services/business_modules/blockchain/ledger.py |
| Tests | ۳۱۲ تست واحد | tests/unit/test_blockchain.py |
| Polygon RPC | لم‌شده | نیاز به تنظیم |

### ۷.۳ مارش روی بلاکچین

فاز ۱ (اکنون): In-memory registry + CarbonCredit.sol آماده
فاز ۲: Deploy به local hardhat network -> تست ۳۱۲ تست
فاز ۳: Testnet (Mumbai/Amoy) -> verify + audit
فاز ۴: Mainnet (Polygon) -> زنده‌سازی

---

## ۸. نقش‌های قرارداد هوشمند (Smart-Contract Roles)

### ۸.۱ قرارداد CarbonCredit.sol

| عنصر | جزئیات |
|---|---|
| استاندارد | ERC20 + ERC20Burnable + ERC20Pausable + AccessControl + ReentrancyGuard |
| نام | Eco Nojin Carbon Credit (ENCC) |
| ساخت | MAX_SUPPLY = 1,000,000,000 x 10^18 |
| VERSION | 2.0.0 |
| MIN_MINT | 1 x 10^18 |

### ۸.۲ نقش‌ها (AccessControl)

| نقش | keccak256 | تخصیص | عملیات |
|---|---|---|---|
| DEFAULT_ADMIN_ROLE | - | deployer | مدیریت کلی |
| MINTER_ROLE | keccak256("MINTER_ROLE") | deployer | registerProject, mint |
| PAUSER_ROLE | keccak256("PAUSER_ROLE") | deployer | pause/unpause |
| VERIFIER_ROLE | keccak256("VERIFIER_ROLE") | deployer | verifyProject |

### ۸.۳ توابع کلیدی

| تابع | نقش مورد نیاز | modifier | عملکرد |
|---|---|---|---|
| registerProject | MINTER_ROLE | whenNotPaused | ثبت پروژه + emit ProjectRegistered |
| verifyProject | VERIFIER_ROLE | projectExists | verified=true + emit ProjectVerified |
| mint | MINTER_ROLE | whenNotPaused+nonReentrant+projectExists | ساخت توکن، max supply check |
| retire | any (owner) | whenNotPaused+nonReentrant | _burn + totalRetiredCredits++ |
| pause | PAUSER_ROLE | - | _pause() |
| unpause | PAUSER_ROLE | - | _unpause() |

### ۸.۴ ساختار CarbonProject در قرارداد

struct CarbonProject { uint id, string projectId, projectType, location, address owner, startDate, verified, active, totalCreditsMinted, metadataURI }

### ۸.۵ Events

ProjectRegistered(id, projectId, owner), ProjectVerified(id, verifier), CreditsMinted(projectId, to, amount), CreditsRetired(retiredBy, amount, reason)

### ۸.۶ عدم تطابق deploy.js

deploy.js ۵ قرارداد منتشر می‌کند: IdentitySBT, MarketplaceLiability, EscrowWithDispute, BrandLicense, PaymentSplitter. CarbonCredit.sol حذف شده. بنابراین هیچ ERC20 واقعی روی زنجیره وجود ندارد.

---

## ۹. AML / KYC / Freeze / Audit

### ۹.۱ وضعیت فعلی AML/KYC

| مورد | وضعیت | مبنای حقوقی |
|---|---|---|
| KYC/AML اجرایی | ندارد | - |
| ToS ماده ۳.۲ | خطور | "بدون رضایت قابل مسدودسازی نیست" - مغایر FATF |
| احراز هویت API | require_user | فقط auth basic |
| Transaction monitoring | ندارد | - |
| Suspicious activity reporting | ندارد | - |
| Audit log | جزئی | ledger.py: EcoTransaction records |
| Freezing capability | قانونی ندارد | CarbonCredit.pause() = توقف کلاژ |
| سجل حسابرسی | planned | database.models.AuditEntry |

### ۹.۲ CAP requirement در ToS

LEGAL_COMPLIANCE.md: "ECO is not sold to public", "No ICO/IEO/IDO", "No profit promise"

ماده ۳.۲ فعلی: "without consent, not transferable or freezeable" -> MUST BE REVISED

FATF Recommendation 15 + Virtual Asset Guidance: Legal seizure upon judicial order is mandatory

اصلاح پیشنهادی: "Digital asset subject to legal seizure per AML laws and valid judicial orders; voluntary transfer requires user consent."

### ۹.۳ Freeze و Pausability

| سطح | مکانیزم | وضعیت |
|---|---|---|
| Smart contract | CarbonCredit.pause() | آماده - deploy نشده |
| API level | ندارد | نیاز به endpoint /admin/freeze |
| حساب کاربری | ندارد | services/auth - placeholder |
| دارایی | ندارد | هیچ asset freeze |

### ۹.۴ Audit

| نوع | وضعیت | مسیر |
|---|---|---|
| قرارداد هوشمند | آماده، پشتیبانی نشده | CarbonCredit.sol آماده، audit نشده |
| پن‌تست | جزئی | pen_test_scan.md, CVE-2025-66478 |
| MRV audit | ندارد | VVB مستقل لازم |
| حسابرسی مالی | double-entry | services/finance/wallet_service.py |
| گزارش حسابرسی رسمی | ندارد | - |

---
## ۱۰. چارچوب‌های حقوقی بین‌المللی

### ۱۰.۱ MiCA (Markets in Crypto-Assets Regulation) — EU

| جنبه | وضعیت | منبع |
|---|---|---|
| MiCA (Regulation 2023/1114) | قابل اعمال | EUR-Lex: 32023R1114 |
| توکن کاربردی (utility token) | ممکن است معاف | MiCA Article 3(5) |
| احتکار/عرضه | ❌ ندارد | LEGAL_COMPLIANCE.md |
| ESG disclosure | نیاز دارد | MiCA Art. 60 |
| وضعیت | Draft compliance; no formal opinion | نیاز به مشاور حقوقی EU |

### ۱۰.۲ GENIUS (Guiding and Establishing National Innovation for U.S. Stablecoins)

| جنبه | وضعیت |
|---|---|
| Stablecoin regulation | اکوکوین stablecoin نیست |
| Applicability | Low — if ECO remains utility-only |
| Federal/State oversight | SEC/CFTC jurisdiction if securities classification |
| Recommendation | Monitor; not currently in scope |

### ۱۰.۳ FATF (Financial Action Task Force)

| جنبه | وضعیت |
|---|---|
| Recommendation 15 (Virtual Assets) | Applicable |
| Travel Rule (R.16) | Not implemented |
| Risk-based approach | Not documented |
| ToS conflict | Art. 3.2 "not freezeable" = VIOLATION of R.15 |
| SAR (Suspicious Activity Reporting) | Not implemented |

### ۱۰.۴ UNCITRAL (United Nations Commission on International Trade Law)

| جنبه | وضعیت |
|---|---|
| MLEC (Model Law on Electronic Commerce) | Foundation for e-transactions |
| Model Law on Secured Transactions | Applicable if credit lending |
| Cross-border recognition | Need legal opinion per jurisdiction |
| Digital identity | Not yet addressed |

### ۱۰.۵ ماده ۶ پاریس (Paris Agreement Article 6)

| جنبه | وضعیت |
|---|---|
| Art. 6.1 ITMOs | Not yet claiming |
| Art. 6.2 TMOs + corresponding adjustments | NOT IMPLEMENTED |
| Art. 6.4 PAMC | Not applicable yet |
| Additionality rules | verification.py has logic |
| Risk of double counting | HIGH without mechanism |

### ۱۰.۶ ICVCM (Integrity Council for the Voluntary Carbon Market)

| جنبه | وضعیت |
|---|---|
| CCPs (Core Carbon Principles) | Not yet aligned |
| Qualification process | Not applicable |
| Registry assessment | Not done |
| Recommended next step | Adopt CCPs before any VCM activity |

### ۱۰.۷ VCMI (Voluntary Carbon Markets Integrity Initiative)

| جنبه | وضعیت |
|---|---|
| Claims code | Not reviewed |
| Quality framework | Pending |
| Recommended next step | Review before marketing claims |

### ۱۰.۸ CORSIA (Carbon Offsetting and Reduction Scheme for International Aviation)

| جنبه | وضعیت |
|---|---|
| Applicability | Low (aviation sector) |
| Eligible credits | Not yet issued |
| Recommended | Monitor for future integration |

### ۱۰.۹ استانداردهای گواهی (Verra/Puro/Gold Standard/ISO 14064)

| استاندارد | وضعیت |
|---|---|
| Verra VCS | Cited in frontend; NO project registered |
| Gold Standard | Cited in frontend; NO project registered |
| Puro-Earth | Cited in frontend; NOT applicable to soil carbon |
| ISO 14064-2 | MRV methodology placeholder only |
| Verra VM0042 | Cited as methodology reference |
| ICVCM CCP | Not assessed |

---

## ۱۱. گیت‌های حوزهٔ قضایی (Jurisdiction Gating)

### ۱۱.۱ ماتریس گیت حوزه قضایی

| حوزه | وضعیت فعلی | گیت مورد نیاز | حداقل برای عرضه |
|---|---|---|---|
| ایران | توکن خدماتی؛ معامله محدود | قانون بانک مرکزی + SEO | مشاوره بانک مرکزی |
| اتحادیه اروپا | MiCA قابل اعمال | ESG disclosure + CASP license | MiCA CASP registration |
| انگلستان | FCA guidance | FCA authorization if security | FCA review |
| آمریکا | Howey test passed (utility) | SEC no-action letter | SEC/GAO opinion |
| سنگاپور | MAS PSA | license if payment token | MAS license |
| UAE | VARA | VARA registration | VARA license |
| کانادا | CSA SN 21-329 | provincial securities review | provincial SEC |
| استرالیا | ASIC guidance | consumer protection review | ASIC opinion |

### ۱۱.۲ گیت اجرایی

```
DisplayClaim:
  if (EcoCoin claims carbon credit or transferable):
    gate: legal_opinion per jurisdiction
    gate: VVB_independent_certification
    gate: registry_verified_in_country
    gate: AML_KYC_compliance
    gate: freeze_mechanism_active
    return: ALLOW or BLOCK_WITH_REASON
```

### ۱۱.۳ پرهیز از ادعاهای پشتیبانی‌نشده

| ادعای پشتیبانی‌نشده | جایگزین مجاز |
|---|---|
| "اعتبار کربن معادل ۱ تن CO2" | "تخمین MRV: X ton CO2e (modelled_estimate)" |
| "ثبت روی پالیگون" | "ثبت در رجیستری داخلی (شبیه‌ساز)" |
| "استاندارد Verra/Puro" | "مرجع محاسبه بر اساس VM0042" |
| "قابل عرضه در بازار" | "قابل redeemed درون‌پلتفرمی" |
| "گواهی ISO 14064-2" | "MRV ساده‌شده، گواهی ندارد" |
| "بدون رضایت قابل مسدودسازی نیست" | "قابل توقیف به موجب قانون" |

---

## ۱۲. برنامهٔ ۳۰/۶۰/۹۰ روزه

### ۱۲.۱ بازه ۳۰ روزه (G0-G1)

| # | اقدام | مسئول | نتیجه |
|---|---|---|---|
| 1 | حذف ادعای "ثبت پالیگون" از فرانت‌اِند | فرانت‌اِند + حقوقی | رفع سبزشویی |
| 2 | حذف ادعای "Verra/Puro-Earth" از فرانت‌اِند | فرانت‌اِند | رفع ادعای گواهی |
| 3 | اضافه کردن برچسب "simplified / not certified" به MRV | علمی + فرانت‌اِند | شفافیت |
| 4 | اصلاح ماده ۳.۲ ToS (freezeable) | حقوقی | انطباق FATF |
| 5 | تأیید شخصیت حقوقی "دشت امید نارون" | حقوقی + برند | اصلاح نام فوتر |
| 6 | اصلاح تاریخ بیانیه (2025 -> 2026) | برند | رفع خطای تاریخی |
| 7 | بازبینی ToS توسط مشاور حقوقی | حقوقی | نظر حقوقی |

### ۱۲.۲ بازه ۶۰ روزه (G2)

| # | اقدام | مسئول | نتیجه |
|---|---|---|---|
| 1 | CarbonCredit.sol به deploy.js اضافه یا حذف | بلاکچین | وضوح deployment |
| 2 | شناسه یکتا + corresponding adjustment | بلاکچین + MRV | پیشگیری احتساب دوگانه |
| 3 | چارچوب VVB مستقل | علمی + حقوقی | اعتبارسنجی |
| 4 | Migration audit | حسابرس | صحت داده |
| 5 | KYC/AML workflow implementation | engineering | انطباق FATF |
| 6 | Transaction monitoring | engineering | suspicious activity |

### ۱۲.۳ بازه ۹۰ روزه (G3-G5)

| # | اقدام | مسئول | نتیجه |
|---|---|---|---|
| 1 | نظر حقوقی مستقل (SEC/MiCA/CBI) | حقوقی | G3 clearance |
| 2 | Blockchain testnet deployment | بلاکچین | پایان فاز ۲ |
| 3 | VVB selection + MOU | علمی | شروع اعتبارسنجی |
| 4 | ICVCM CCP alignment assessment | علمی | کیفیت |
| 5 | FPIC for local communities | جامعه | انطباق اجتماعی |
| 6 | Annual impact report framework | MRV | شفافیت |
| 7 | ToS Article 3.4 (50%) operationalized | حقوقی + مالی | شفافیت درآمد |

---

## ۱۳. معیارهای پذیرش (Acceptance Criteria)

### ۱۳.۱ برنامه ۳۰ روزه

| # | AC | شرط |
|---|---|---|
| AC-30-1 | صفر ادعای بلاکچین عمومی | grep site.ts: no "Polygon" |
| AC-30-2 | صفر ادعای "Verra/Puro registered" | grep site.ts: no "registered" |
| AC-30-3 | برچسب MRV visible | "simplified" OR "not certified" present |
| AC-30-4 | ToS Art. 3.2 frozen | text contains "legal seizure" |
| AC-30-5 | نام حقوقی صحیح | footer = confirmed entity name |
| AC-30-6 | تاریخ صحیح | no "2025" in declaration |

### ۱۳.۲ برنامه ۶۰ روزه

| # | AC | شرط |
|---|---|---|
| AC-60-1 | CarbonCredit.sol deployable | deploy.js includes CarbonCredit |
| AC-60-2 | Unique identifier system | no duplicate project IDs |
| AC-60-3 | KYC/AML workflow | auth + verification endpoints |
| AC-60-4 | Transaction monitoring | logging + alert rules |
| AC-60-5 | VVB framework documented | VVB_list.md present |
| AC-60-6 | All 312 blockchain tests pass | pytest tests/unit/test_blockchain.py |

### ۱۳.۳ برنامه ۹۰ روزه

| # | AC | شرط |
|---|---|---|
| AC-90-1 | Independent legal opinion | opinion letter per jurisdiction |
| AC-90-2 | Testnet contract live | CarbonCredit on testnet |
| AC-90-3 | 5-year audit complete | auditor report available |
| AC-90-4 | VVB MOU signed | partnership agreement |
| AC-90-5 | CCP assessment done | ICVCM report |
| AC-90-6 | FPIC framework | community consent records |

---

## ۱۴. راهنمای تست و استقرار (Test/Deployment Runbook)

### ۱۴.۱ تست‌های فعلی

| مجموعه | فایل | تعداد | وضعیت |
|---|---|---|---|
| Blockchain unit | tests/unit/test_blockchain.py | ~۳۱۲ | ✅ (registry + supply chain + API) |
| Carbon verification | services/carbon/verification.py | manual | ✅ 4 checks |
| EcoWallet ledger | services/ecowallet/ledger.py | unit | ✅ DB-backed |
| Distribution engine | services/ecowallet/distribution.py | unit | ✅ 70/15/10/5 |
| MRV QA | engine/hydroma/mrv/qa.py | integration | ✅ explicit pass/fail |
| API integration | tests/integration/test_carbon_phase8.py | 5 | ✅ |
| Pen test | pen_test_scan.md | annual | ⚠️ CVE-2025-66478 |

### ۱۴.۲ راهنمای استقرار (Deployment Runbook)

```
PRE-DEPLOYMENT CHECKLIST:
  [ ] All 312 blockchain tests pass
  [ ] All carbon ACs verified (AC-30-1 through AC-90-6)
  [ ] Legal opinion letter obtained per jurisdiction
  [ ] ToS Art. 3.2 updated (freezeable)
  [ ] No unsupported claims in frontend
  [ ] MRV labels present (simplified/field_verified)
  [ ] VVB framework documented
  [ ] KYC/AML workflow operational
  [ ] Transaction monitoring active
  [ ] Audit logging enabled
  [ ] Incident response plan drafted
  [ ] Privacy policy updated
  [ ] CORS allowlist explicit (not *)
  [ ] Secrets in vault (not .env)
  [ ] CarbonCredit.sol audited

DEPLOYMENT STEPS (blockchain):
  1. Deploy to local Hardhat network
     $ cd contracts && npx hardhat run scripts/deploy.js --network localhost
  2. Verify all 6 contracts deployed (incl. CarbonCredit)
  3. Run 312 blockchain tests
     $ pytest tests/unit/test_blockchain.py -v
  4. Deploy to testnet (Mumbai/Amoy)
     $ npx hardhat run scripts/deploy.js --network mumbai
  5. Verify on Polygonscan
  6. Run integration tests against testnet

DEPLOYMENT STEPS (carbon registry):
  1. Run migrations
     $ alembic upgrade head
  2. Verify CarbonProjectRepository CRUD
  3. Verify VerificationOracle report generation
  4. Enable API endpoints
  5. Monitor for double-counting

ROLLBACK PLAN:
  - Disable blockchain endpoints at API gateway
  - Revert to in-memory CarbonRegistry
  - Log all operations to audit table
  - Notify compliance team
```

### ۱۴.۳ نمونه تست واحد (excerpt)

```python
# tests/unit/test_blockchain.py
class TestCarbonRegistry:
    def test_register_project(self):
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        assert project.project_id.startswith("proj_")
        assert project.status == ProjectStatus.SUBMITTED
        assert project.tx_hash.startswith("0x")

    def test_issue_credits_unverified_project(self):
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        with pytest.raises(ValueError):
            registry.issue_credits(project.project_id, 50.0, "owner1")

    def test_retire_credits(self):
        registry = CarbonRegistry()
        project = registry.register_project("owner1", "afforestation", 100, 10)
        registry.verify_project(project.project_id, "verifier1")
        credit = registry.issue_credits(project.project_id, 50.0, "owner1")
        retired = registry.retire_credits(credit.credit_id, "owner1")
        assert retired.retired is True
```

---

## ۱۵. Disclaimer حقوقی و پرهیز از ادعاهای پشتیبانی‌نشده

### ۱۵.۱ Disclaimer حقوقی

> این سند صرفاً تحلیل و مستندسازی است و مشاوره حقوقی محسوب نمی‌شود. هیچ تصمیم حقوقی، مجوز یا سازگاری قوانین به‌درآمده از این سند. ادعاهایی در این سند دربارهٔ قوانین، مجوزها و ریسک‌های حقوقی بر اساس تحلیل فعلی پروژه و مستندات موجود تهیه شده و ممکن است تغییر کنند. پیش از هر اقدام حقوقی، از مشاور حقوقی متخصص استفاده شود.

> این سند هیچ تغییری در کد، سایت، پایگاه داده، یا هیچ فایل دیگری در مخزن ایجاد نکرده است.

### ۱۵.۲ پرهیز از ادعاهای پشتیبانی‌نشده

این سند صراحتاً پشتیبانی نمی‌کند از:
- هیچ ادعایی مبنی بر اینکه اکوکوین اعتبار کربن معتبر است (بدون VVB مستقل)
- هیچ ادعایی مبنی بر ثبت روی بلاکچین پالیگون (قرارداد deploy نشده)
- هیچ ادعایی مبنی بر انطباق با Verra/Puro-Earth/Gold Standard (هیچ پروژه ثبت‌شده)
- هیچ ادعایی مبنی بر قابل عرضه یا معامله (LEGAL_COMPLIANCE: بدون ICO/IDO)
- هیچ ادعایی مبنی بر حداقل ۵۰٪ به جوامع محلی (عددی تعریف نشده)
- هیچ ادعایی مبنی بر امنیت کامل سیستم (CVE-2025-66478 فعال)
- هیچ ادعایی مبنی بر گواهی ISO 14064-2 (MRV فقط simplified accounting)
- هیچ ادعایی مبنی بر CarbonCredit.sol فعال (deploy نشده)

### ۱۵.۳ ادعاهای مجاز (داخل سند)

| ادعای مجاز | مبنای مستند |
|---|---|
| MRV با RothC/ERA5/SoilGrids محاسبه می‌شود | carbon_mrv.py, rothc_service.py |
| EcoWallet DB-backed با تقسیم 70/15/10/5 | distribution.py |
| CarbonCredit.sol ERC20 با نقش‌های mint/burn/pause | contracts/src/CarbonCredit.sol |
| رجیستری شبیه‌ساز درون‌حافظه‌ای است | carbon_registry.py |
| VVB مستقل وجود ندارد | docs/fa/43, docs/en/05 |
| MRV simplified accounting است | docs/en/05 |
| CarbonCredit.sol deploy نشده | deploy.js |
| CVE-2025-66478 در Next.js 15.1.6 | docs/security/CVE-2025-66478 |

---
## ۱۶. منابع رسمی

### ۱۶.۱ چارچوب‌های حقوقی و استانداردها

| منبع | URL | تاریخ دسترسی |
|---|---|---|
| MiCA Regulation (EU) 2023/1114 | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023R1114 | 2026-09-16 |
| FATF Recommendations (Version 2025) | https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html | 2026-09-16 |
| FATF Virtual Assets Guidance | https://www.fatf-gafi.org/en/topics/virtual-assets/VA-timeline.html | 2026-09-16 |
| Paris Agreement Article 6 | https://unfccc.int/process-and-meetings/the-paris-agreement/article-6 | 2026-09-16 |
| ICVCM Core Carbon Principles | https://icvcm.org/core-carbon-principles/ | 2026-09-16 |
| VCMI Claims Code | https://vcmi.org/vcmi-claims-code/ | 2026-09-16 |
| CORSIA ICAO | https://www.icao.int/environmental-protection/corsia/Pages/default.aspx | 2026-09-16 |
| UNCITRAL Model Law on Electronic Commerce | https://uncitral.un.org/en/texts/trade/electronic_commerce/uncitral_model_law_on_electronic_commerce | 2026-09-16 |
| ISO 14064-2:2019 | https://www.iso.org/standard/80259.html | 2026-09-16 |
| ISO 14065:2020 | https://www.iso.org/standard/80260.html | 2026-09-16 |
| EU Green Claims Directive (2024/825) | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024L00825 | 2026-09-16 |
| GENIUS Act (US) | https://www.congress.gov/bill/118th-congress/senate-bill/3593 | 2026-09-16 |
| Verra VCS Standard | https://verra.org/project/vcs-standard/ | 2026-09-16 |
| Gold Standard | https://www.goldstandard.org/ | 2026-09-16 |
| Howey Test (SEC) | https://www.sec.gov/news/public-statement/statement-clayton-2018-11-16 | 2026-09-16 |
| SEC Digital Assets Guidance | https://www.sec.gov/topic/digital-assets | 2026-09-16 |
| EU Crowdfunding Regulation (2020/1503) | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32020R1503 | 2026-09-16 |
| Copernicus Data Space Ecosystem | https://dataspace.copernicus.eu/ | 2026-09-16 |
| SoilGrids (ISRIC) | https://www.isric.org/explore/soilgrids | 2026-09-16 |
| ERA5 Climate Reanalysis | https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels | 2026-09-16 |
| IPCC AR6 | https://www.ipcc.ch/report/ar6/syr/ | 2026-09-16 |
| UNCCD | https://www.unccd.int/ | 2026-09-16 |

### ۱۶.۲ منابع داخلی پروژه

| منبع | مسیر | تاریخ |
|---|---|---|
| LEGAL_COMPLIANCE.md | /LEGAL_COMPLIANCE.md | August 2026 |
| Eco Coin Statement Assessment | docs/fa/64_eco_coin_statement_assessment.md | 2026-09-08 |
| Architecture | docs/ARCHITECTURE.md | — |
| Security Privacy | docs/en/06_security_privacy.md | — |
| Standards | docs/en/05_standards.md | — |
| Phase 8 Token Carbon | docs/en/20_phase8_token_carbon.md | — |
| Carbon Credit Contract | contracts/src/CarbonCredit.sol | — |
| Deploy Script | contracts/scripts/deploy.js | — |
| Carbon Registry | services/business_modules/blockchain/carbon_registry.py | — |
| Carbon Verification | services/carbon/verification.py | — |
| RothC Service | services/carbon/rothc_service.py | — |
| MRV Engine | engine/hydroma/mrv/nojin_mrv.py | — |
| EcoWallet Ledger | services/ecowallet/ledger.py | — |
| Distribution | services/ecowallet/distribution.py | — |
| Blockchain API | services/api_gateway/routers/blockchain.py | — |
| CVE-2025-66478 | docs/security/CVE-2025-66478.md | — |
| Pen Test | pen_test_scan.md | — |
| Blockchain Tests | tests/unit/test_blockchain.py | — |

### ۱۶.۳ حدود سند

- **نطاق:** فقط docs/report/ — هیچ تغییری در کد، سایت، پایگاه داده، یا مخزن
- **تاریخ:** 2026-09-16
- **بررسی:** برای مدیریت — نیاز به تأیید حقوقی، فنی، و حسابرسی
- **نسخه:** v1.0-draft

---

*این سند بر اساس بررسی مستقیم کدهای موجود در تاریخ 2026-09-16 تهیه شده است. هیچ فایلی در مخزن تغییر نکرده است. منابع حقوقی فهرست‌شده صرفاً چارچوب ارجاع‌اند و جایگزین مشاورهٔ حقوقی رسمی نیستند.*
