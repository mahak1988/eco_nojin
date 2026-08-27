# فاز ۶ (بخش B) — Auth واقعی در فرانت، نقشه مناطق واقعی، بازارچه روی Supabase

> وضعیت: **پیادهسازی و تستشده** — اندپوینتها 200 · بیلد سبز 3.91s · Commit این چرخه.

## ۱) جایگزینی auth موقت با Supabase واقعی
- `AuthContext.tsx` بازنویسی شد: `login` → `POST /api/v1/auth/supabase/login` (GoTrue)؛
  `register` → `/signup` (پیام تأیید ایمیل صادقانه)؛ توکن در localStorage (`eco_token`)؛ logout پاک میکند
- `RegisterPage` حالا `password` را به register میفرستد
- ⚠️ ثبتنام تا رفع بلاکر GoTrue (خطای 500 سمت پروژه) با پیام واقعی خطا مواجه میشود؛ ورود برای کاربران موجود کار میکند

## ۲) نقشه مناطق واقعی (deck.gl + Supabase)
- `GET /api/v1/supabase/landscapes` → ۲۱ منطقه واقعی از `platform_landscapes` (20 تای آن مختصات GeoJSON Point دارد، تهران)
- `SupabaseMapCard.tsx` — ScatterplotLayer deck.gl با نقاط واقعی + فهرست نام/استان/مختصات + حالت خالی/خطا صادقانه
- ستون `geo_boundary` آماده PostGIS است (migration 0001 ستون geography را اضافه میکند)

## ۳) بازارچه روی همان دیتابیس
- `GET /api/v1/supabase/marketplace` → ۷ استاندارد فعال واقعی (IPCC 2019 Refinement، ISO 17025، NASA EOSDIS، …) + شمارنده پروژهها
- `MarketplaceCard.tsx` — کارت کاتالوگ با دستهبندی (کربن/آزمایشگاه/ماهواره) و لینک منبع

## ۴) فایلهای این فاز
**جدید**: `services/api_gateway/routers/supabase_proxy.py`، `SupabaseMapCard.tsx`، `MarketplaceCard.tsx`
**توسعه**: `AuthContext.tsx` (واقعی)، `RegisterPage.tsx` (password)، `HydromaDashboard.tsx` (دو کارت جدید)، `main.py` (روتِر)

## قدم بعدی (بخش C)
پس از رفع بلاکر ثبتنام: مدیریت پروفایل/نقشها، RLS تأیید روی دیتابیس (اجرای migration 0001)،
ساخت واقعی پروژههای بازارچه (create با RLS)، LMS، و PostGIS query های واقعی.
