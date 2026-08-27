# فاز ۶ (بخش C) — تکمیل و تأیید زنده روی دیتابیس ابری

> تاریخ: 2026-08-27 · همه موارد زیر روی پروژه واقعی Supabase (`cpncggavcfplewlhvvnw`) اجرا و تأیید شد.

## ۱) بلاکر ثبتنام — ریشهیابی و رفع (علت خطای 500)
- تریگر `on_auth_user_created` روی `auth.users` تابع `handle_new_user()` را اجرا میکند که در جدول `public.users` درج میکند.
- **علت خطا:** تابع به ستون `company` ارجاع میداد که در جدول `users` وجود نداشت ← درج شکست ← «Database error saving new user».
- **رفع:** `alter table public.users add column if not exists company text;` — کمخطر، تریگر دستنخورده.
- ✅ تست: ثبتنام کاربر تست → `{"status":"ok","user_id":"7140f3f9-..."}`

## ۲) Migration 0001 — اجرا روی دیتابیس ابری
- PostGIS **3.3.7** نصب شد؛ جدول `platform_badges` ساخته شد؛ RLS روی همه جدولهای واقعی فعال شد.
- اصلاح مسیر: `verification_queue` یک **VIEW** است — RLS فقط روی جدولهای واقعی (relkind='r') فعال میشود.
- سیاستها با اسکیمای واقعی (از `services/supabase/migrations/001_platform_tables.sql`): `platform_profiles.id = auth.users.id` ← سیاستها `auth.uid() = id`؛ `memberships.user_id` و `carbon_projects.owner_id` درست.
- جدولهای ناشناخته (users/projects/validators/…) فقط RLS (deny-all) گرفتند تا اسکیماشان معلوم شود.

## ۳) جریان کامل «ثبتنام ← پروژه ← پروفایل» — تأیید زنده
1. ثبتنام: `ok` ✅
2. ورود: access_token (931 کاراکتر) ✅
3. ساخت پروژه کربن: `owner_id = auth.uid` (خطای FK اولیه رفع شد چون پروفایل ساخته نشده بود) ✅
4. فهرست پروژههای خودی: `count=1` ✅
5. پروفایل PUT (ساخت با `id = auth.uid`) و GET ✅
6. RLS: بازارچه برای anon فقط استانداردها را نشان میدهد (پروژهها deny) ✅
7. داده تست پاکسازی شد (کاربر، پروفایل، پروژه) — دیتابیس تمیز.

## ۴) PostGIS واقعی — query مکانی
- Migration `0002_postgis_nearest.sql`: backfill ۲۰ نقطه از GeoJSON به ستون `geo_point` (geography) + تابع `nearest_landscapes` (SECURITY INVOKER).
- ✅ تأیید متقابل: تهران (35.7, 51.4) → `1.56 km` هم با PostGIS و هم Haversine.
- اندپوینت `GET /api/v1/supabase/geo/nearest` حالا `engine: "postgis"` برمیگرداند (fallback به Haversine).

## ۵) ابزار مدیریتی
- `scripts/supabase_admin.py` — با PAT (بدون پسورد دیتابیس): `diagnose` / `migrate` / `verify` / `query`.

## ۶) تستها
- pytest: **۶۳ پاس، ۰ خطا** (رفع ۴ conftest جاافتاده: reporting/auth/admin/analytics).
- بیلد فرانت: سبز 3.22s.

## قدم بعدی (پیشنهادی)
- حساب واقعی خودت بساز (ثبتنام حالا کار میکند) ← ساخت اولین پروژه واقعی از داشبورد.
- LMS ابری (جدول courses/progress در Supabase).
- نقشهای (roles: farmer/admin/auditor) با `platform_memberships.role` + سیاستهای RLS نقشمحور.
