# فاز تکمیلی — ممیزی عمیق فرانت‌اند: فایل‌های خالی/استاب (اصلاح ممیزی ۵۸)

> تاریخ: 2026-08-27 · پاسخ به بازخورد: ممیزی قبلی (۵۸) فایل‌های ۶۶بایتی فقط-کامنت و پوشه خالی را در خروجی کوتاه‌شده نشان نداد. این ممیزی کامل است.

## اسکن: ۱۶۴ فایل در `frontend/src` (خطوط مؤثر، نه خطوط فیزیکی)
### حذف‌شده — ۱۷ استاب فقط-کامنت (۶۶ بایت، بدون هیچ کد/export)
- `hooks/`: useApi.ts، useAuth.ts، useDebounce.ts، useLocalStorage.ts
- `locales/`: index.ts
- `services/`: auth.ts، geodata.ts
- `store/`: index.ts، useAuthStore.ts، useDataStore.ts، useUIStore.ts
- `types/`: api.ts، index.ts، models.ts
- `utils/`: constants.ts، format.ts، validators.ts

> همه‌شان در git ردیابی می‌شدند اما هیچ‌جا import نشده بودند (بیلد سبز = اثبات). حذف با `git rm`؛ اگر بعداً لازم شدند با محتوای واقعی ساخته می‌شوند.

### پرشده — `vite-env.d.ts`
- فقط کامنت بود؛ محتوای استاندارد `/// <reference types="vite/client" />` نوشته شد (فایل مرجع Vite — حذف نمی‌شود).

### پوشه خالی
- `components/3d/weather/` حذف شد (خالی؛ git پوشه خالی را ردیابی نمی‌کند).

### نگهداری‌شده (واقعی، کوچک)
- ۱۲ صفحه یک‌خطی `pages/` (RothCModel، SWATModel، Support، SystemStatus و…) — مینی‌فای اما محتوای JSX واقعی و روت‌شده؛ کیفیت صفحه‌ها قابل ارتقاست نه حذف.
- بشکه‌های `components/*/index.ts`، `config.ts`، `index.css`، `services/api.ts`، `store/simulatorStore.ts`، `store/useStore.ts`، `hooks/useThemeMode.ts` — استفاده‌شده.

## درس ثبت‌شده برای ممیزی‌های بعدی
- معیار «خط مؤثر» (بدون کامنت/whitespace) به‌کار رود، نه تعداد خط فیزیکی.
- خروجی اسکن کامل نمایش داده شود (در ۵۸ فقط ۴۰ مورد آخر دیده شد).
- برای فایل‌های خالی: بررسی import با الگوی مسیر-دایرکتوری (`@/hooks`) هم لازم است؛ اینجا بیلد سبز سند کافی بود.

## وضعیت نهایی
- pytest ۷۹ پاس · بیلد 3.00s · درخت پاک · commit بعدی شامل این پاکسازی.
