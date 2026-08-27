# فاز ۶ (بخش C) — پروفایل، پروژه بازارچه با مالکیت واقعی، LMS، query مکانی

> وضعیت: **پیادهسازی و تستشده** — اندپوینتها 200 · بیلد سبز 3.33s · Commit این چرخه.

## ۱) پروفایل و نقشها (RLS-ready)
- `GET /api/v1/supabase/profile?token=` — پروفایل خودی از platform_profiles (اعتبارسنجی JWT با GoTrue)
- `PUT /api/v1/supabase/profile` — upsert با **JWT کاربر** (نه anon) → پس از فعالسازی RLS، سیاست مالکیت `auth.uid() = user_id` اعمال میشود

## ۲) ساخت واقعی پروژه کربن (مالکیت auth.uid)
- `POST /api/v1/supabase/carbon-projects?token=...&name=...&area_ha=...` → درج در `platform_carbon_projects` با `owner_id = auth.uid()` (شناسه کاربر از GoTrue تأیید میشود)
- `GET /api/v1/supabase/carbon-projects?token=` — فهرست پروژههای خودی
- در فرانت (`MarketplaceCard`): فرم ساخت پروژه + «پروژههای من»؛ بدون توکن → پیام صادقانه «وارد شوید»
- ⚠️ جریان کامل نیازمند کاربر واقعی است (تا رفع بلاکر ثبتنام، اندپوینتها خطای token_invalid صادقانه میدهند)

## ۳) Query مکانی واقعی (PostGIS-ready)
- `GET /api/v1/supabase/geo/nearest?lat=&lon=&limit=` — Haversine واقعی روی مختصات GeoJSON ۲۰ نقطه تهران
- تست: تهران (35.7, 51.4) → نزدیکترین 1.56 km
- پس از migration 0001 همان سؤال با `ST_DWithin` روی geography اجرا میشود
- دکمه «نزدیکترین به من» در `SupabaseMapCard`

## ۴) LMS — محتوای آموزشی رایگان و واقعی
- `data/lms/courses.json` — ۳ دوره فارسی (کربن خاک ۱۰۱، MRV و استانداردها، فرسایش و احیا) × ۴ درس
- `GET /api/v1/lms/courses` و `GET /api/v1/lms/courses/{id}` — فهرست + محتوای کامل
- `LmsCard.tsx` — کارت دورهها، باز/بسته شدن درسها، پیشرفت در localStorage (ابریرسانی پس از ساخت جدول LMS)

## ۵) فایلهای این فاز
**جدید**: `data/lms/courses.json`، `services/api_gateway/routers/lms.py`، `LmsCard.tsx`
**توسعه**: `supabase_proxy.py` (profile/carbon-projects/geo)، `MarketplaceCard.tsx` (ساخت پروژه)، `SupabaseMapCard.tsx` (نزدیکترین)، `HydromaDashboard.tsx`

## قدم بعدی
پس از رفع بلاکر ثبتنام + اجرای migration 0001: جریان کامل «ثبتنام ← ساخت پروژه ← پروفایل» با RLS واقعی،
جدولهای LMS در Supabase، و نقشه PostGIS با ST_DWithin.
