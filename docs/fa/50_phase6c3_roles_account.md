# فاز ۶ (بخش C-3) — نقشها (admin/auditor) + حساب واقعی

> تاریخ: 2026-08-27 · اجرا و تأیید زنده روی دیتابیس ابری.

## ۱) Migration 0004 — RLS نقشمحور
- توابع کمکی `is_admin()` / `is_auditor()` (SECURITY INVOKER — RLS را دور نمیزنند).
- `admin_set_role(target, new_role)` — SECURITY DEFINER با **بررسی ادمین داخل تابع** (الگوی استاندارد Supabase برای توابع مدیریتی؛ غیرادمین خطای `not_admin` میگیرد). دسترسی فقط به authenticated.
- سیاستها: users (خودی + ادمین)، projects (خودی + ادمین)، memberships (خودی + ادمین)، token_transactions (خودی + ادمین)، validators (فقط ادمین)، validation_votes (خودی + auditor)، verifications (auditor/ادمین)، carbon_projects (ادمین).
- `verification_queue` و `dashboard_stats` VIEW هستند ← `security_invoker = on` تا RLS جدول پایه اعمال شود.

## ۲) Migration 0005 — حذف سیاستهای باز قدیمی (نکته امنیتی مهم)
- ۴ سیاست قدیمی «Enable all for …» پیدا شد که دسترسی کامل بدون شرط (حتی anon روی users) میدادند و RLS را بیاثر میکردند: users، projects، standards، verifications. حذف شدند.
- ✅ تأیید زنده: anon → `[]` روی users؛ کشاورز → فقط ردیف خودش؛ ادمین → همه.

## ۳) اندپوینتهای ادمین
- `GET /api/v1/supabase/admin/users?token=…` — فهرست کاربران (RLS تصمیم میگیرد چه کسی چه چیزی ببیند).
- `POST /api/v1/supabase/admin/role?token=…&user_id=…&role=…` — تغییر نقش از طریق RPC؛ ✅ تست: ادمین ارتقا داد (`true`)، کشاورز → `not_admin`.
- چیپ «نقش: مدیر/ممیزی/کشاورز» در MarketplaceCard (از /profile).

## ۴) حساب واقعی — آماده ورود
- کاربر GoTrue موجود: **hassansadeghi28@gmail.com** (از 2026-06-18) — ردیفهای ازدسترفتهاش backfill شد:
  - `public.users` (اکو ۱۰۰) ✅
  - `platform_profiles` با `role = admin` ✅
- **ورود:** صفحه ورود برنامه ← ایمیل + رمز خودت. اگر رمز را فراموش کردهای: Supabase Dashboard ← Authentication ← Users ← ارسال بازیابی.

## ۵) تستها
- pytest: ۶۳ پاس. بیلد: سبز 2.72s. دادههای تست پاکسازی شد (۴ کاربر test + ردیفهای orphan).

## قدم بعدی
- ورود با حساب واقعی ← ساخت اولین پروژه کربن واقعی از داشبورد.
- جریان ممیزی: افزودن verifier به validators (ادمین) ← رأیگیری validation_votes ← status در verification_queue.
