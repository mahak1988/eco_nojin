# فاز تکمیلی — همترازی ماژول‌های بک‌اند/فرانت + ممیزی فایل‌های کوچک

> تاریخ: 2026-08-27

## ۱) کارت‌های فرانت برای ماژول‌های بک‌اند (ایجادشده)
| ماژول بک‌اند | اندپوینت | کارت فرانت | تست زنده |
|---|---|---|---|
| انبارداری/مواد | `POST /api/v1/materials/calculate-compost` | `MaterialsCard` | C/N = 30.0 → Optimal (FAO) |
| بیمه شاخص‌محور | `POST /api/v1/insurance/index` + `/capabilities` | `InsuranceCard` | deficit 0.1 → trigger + پرداخت 5.6% |
| حسابداری/کیف پول | `GET /api/v1/ecowallet/stats` + earning/redemption-options | `AccountingCard` | 0 کیف پول (صادقانه) |
| دفتر کل بلاک‌چین | `GET /api/v1/blockchain/carbon/stats` + supply-chain/stats | `BlockchainCard` | همه صفر (صادقانه) |
| گردشگری بوم‌گردی | `GET /api/v1/tourism/status` (روتر جدید) | `TourismCard` | requires_setup + ۴ قابلیت |

- روتر `insurance` که قبلاً در `main.py` ثبت نشده بود، ثبت شد (باگ همترازی).
- سه روتر خالی ۳ خطی (ussd/voice/sync) به اندپوینت‌های وضعیت صادقانه ارتقا یافتند:
  `requires_gateway` (USSd/voice) و `ok` (sync) — دیگر استاب خالی نداریم.

## ۲) ممیزی فایل‌های زیر ۱۰ خط (۳۷۳ فایل)
### تعیین تکلیف
- **نگه‌داری (مشروع)**: همه `__init__.py`ها، بشکه‌های `index.ts`، `database/base.py`، `frontend/src/index.css`، تست‌های placeholder (برچسب‌دار).
- **بیرون از git (روی دیسک می‌مانند)**: ۱۵ دایرکتوری `_backup_*` — از قبل ignore شده بودند؛ `.gitignore` حالا صریحاً `_backup_*/` را دارد. (یک نسخه پشتیبان ~۱ گیگابایتی هم در git نبود.)
- **ارتقا یافته**: روترهای ۳ خطی ussd/voice/sync → وضعیت صادقانه (بالا).

## ۳) حوادث این چرخه
- `.venv` به‌طور ناگهانی خالی شد (pyvenv.cfg + site-packages) — بازسازی با `pip install -r requirements.txt` کامل شد (fastapi/uvicorn/… همه حاضر).
- یادداشت: اگر دوباره رخ داد، بازسازی همان دو قدم است.

## قدم بعدی
- `pnpm -C frontend build` سبز (کارت‌ها) · pytest ۷۹ پاس · تست زنده همه اندپوینت‌ها OK.
- آماده اتصال دامنه + کلید Groq (مستند ۵۷).
