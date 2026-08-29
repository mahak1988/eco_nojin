# 🗺️ نقشه اقدامات باقی‌مانده (نیازمند تصمیم انسانی)

## 🔴 اولویت بالا
- [ ] **چرخش اسرار:** اگر `.env.bak` یا `contracts/.env` قبلاً جایی به اشتراک گذاشته شده،
      کلیدهای Supabase / private key بلاکچین را عوض کنید.
- [ ] `contracts/.env` بررسی شود (private key هاردهت) — مطمئن شوید فقط در گیت ignored است نه حذف.

## 🟠 پاکسازی رسوب‌ها (بعد از بازبینی — دستورات پیشنهادی)
- [ ] `analysis.json/` پوشه است نه فایل! محتوایش را ببینید:
      `Get-ChildItem "analysis.json" -Recurse`
- [ ] پوشه `src/` تک‌فایلی ریشه (بقایای CRA):
      `Move-Item src\* _quarantine\old_src\ -Force` (بعد از ساخت پوشه)
- [ ] یکی‌کردن `frontend/src/context/` و `contexts/`:
      `Select-String -Path frontend\src\**\*.ts*,frontend\src\**\*.tsx -Pattern "from ['\"].*context" -List`
- [ ] کدام locales استفاده می‌شود؟ `i18n/locales` یا `locales`؟ بالا را ببینید.
- [ ] ۴ سیستم مهاجرت موازی (`alembic/`, `migrations/`, `supabase/migrations/`,
      `services/supabase/migrations/`) → یکی رسمی تعیین و بقیه آرشیو شوند.
- [ ] ۳ لایه بلاکچین (`contracts/`, `blockchain/`, `services/business_modules/blockchain/`) → تجمیع.
- [ ] `frontend/src/pages/_legacy_models/` → برنامه حذف/ادغام.

## 🟡 کیفیت کد (تدریجی)
- [ ] مهاجرت ۴۲۱ مورد `print()` به `structlog` (نصب دارید).
      شروع: `git grep -n "print(" -- "*.py" | Measure-Object -Line`
- [ ] `engine/hydroma/config/settings.py` — آدرس‌های localhost از env خوانده شوند:
      ```python
      # قبل:  BACKEND_URL = "http://localhost:8000"
      # بعد:
      from pydantic_settings import BaseSettings
      class Settings(BaseSettings):
          backend_url: str = "http://localhost:8000"
          class Config: env_file = ".env"
      ```
- [ ] `passlib==1.7.4` قدیمی است — در ارتقای بعدی با `bcrypt` مستقیم جایگزین شود.
- [ ] `python-jose` و `PyJWT` هر دو نصب‌اند — یکی کافی است (PyJWT توصیه می‌شود).

## 🔵 فرانت‌اند
- [ ] نصب تست: `pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom`
      و اولین تست برای `components/payment` (درگاه پرداخت = بالاترین ریسک).
- [ ] `pnpm dlx depcheck` → حذف `georaster-layer-for-leaflet`، `terraformer`،
      `@types/mapbox-gl` (اگر تأیید شد).
- [ ] `pnpm dlx vite-bundle-visualizer` → بررسی باندل.

## 📦 داده‌ها
- [ ] `data/` و کش‌ها الان از گیت خارج‌اند (درست است)، ولی برای استقرار سرور باید
      استراتژی sync داده داشته باشید (S3/MinIO یا اسکریپت restore).
- [ ] `pnpm-lock.yaml` کامیت شده؟ بررسی: `git ls-files frontend | findstr lock`
