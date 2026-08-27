# فاز ۶ (بخش C-2) — LMS ابری + نقشها (زنده)

> تاریخ: 2026-08-27 · اجرا و تأیید روی دیتابیس ابری.

## ۱) Migration 0003 — LMS + نقشها
- جدولها: `lms_courses`، `lms_lessons`، `lms_progress` (کلید مرکب user_id+lesson_id).
- RLS: دورهها و درسها کاتالوگ عمومی؛ پیشرفت فقط مالک (`auth.uid() = user_id` با WITH CHECK).
- `platform_profiles.role` (پیشفرض `farmer`) — سیاستهای نقشمحور پس از ساخت جریان ادمین.
- ✅ هر سه migration (0001/0002/0003) idempotent شدند (drop policy if exists)؛ `supabase_admin.py migrate` همه را به ترتیب اجرا میکند.
- فایل قدیمی فاز ۰ (`00001_auth_roles_rls.sql` — ارجاع به جدول ناموجود farms) به `migrations/legacy/` منتقل شد.

## ۲) Seed محتوای واقعی
- `scripts/seed_lms.py` — ۳ دوره + ۱۲ درس فارسی از `data/lms/courses.json` به ابر (on conflict slug).
- ✅ تأیید: `courses=3, lessons=12`.

## ۳) اندپوینتهای LMS (ابر-اول، fallback محلی)
- `GET /api/v1/lms/courses` — کاتالوگ از `lms_courses` (`source: "supabase"`)
- `GET /api/v1/lms/courses/{id}` — درسها با محتوا از `lms_lessons`
- `GET/POST/DELETE /api/v1/lms/progress?token=...` — پیشرفت خودی با JWT کاربر (RLS)
- ✅ تست زنده: signup → login → mark → get `[lesson_id]` → unmark — همه 200.

## ۴) فرانت
- `LmsCard.tsx` — دورهها از ابر؛ پیشرفت با ورود کاربر روی ابر، بدون ورود localStorage؛ وضعیت همگامسازی صادقانه.
- بیلد: سبز 2.92s.

## تستها
- pytest: ۶۳ پاس (از قبل). بیلد فرانت سبز.

## قدم بعدی
- نقشهای: جریان ادمین/ممیزی (validators) با `platform_memberships.role` + سیاستهای RLS نقشمحور.
