# فاز ۶ (بخش A) — Supabase: audit، RLS، PostGIS، Auth واقعی، CI/CD

> وضعیت: **پیادهسازی + تست زنده** — audit انجام شد؛ migration آماده؛ CI آماده؛ auth پروکسی تست شد.
> بلاکر: ثبتنام GoTrue فعلاً 500 میدهد (نیازمند بررسی سمت دشبورد Supabase).

## ۱) یافتههای audit (زنده، فقطخواندنی)
- ۱۴ جدول در پروژه: platform_landscapes (۲۱ ردیف)، standards (۷ ردیف)، platform_profiles، platform_carbon_projects/credits، platform_memberships، users، projects، validators، verification_queue، verifications، validation_votes، token_transactions، dashboard_stats
- ⚠️ **RLS فعال نیست: anon به همه جدولها دسترس خواندنی دارد** (شامل users/token_transactions — ریسک جدی پس از ورود داده)
- GoTrue زنده: `/auth/v1/health` → 200 (v2.190.0)
- پکیجها: supabase-py 2.31، pytest 9.1، SQLAlchemy 2.0 نصباند؛ psycopg/geoalchemy2 غایب (فعلاً لازم نیست)

## ۲) تحویلها
- `supabase/migrations/0001_phase6_harden.sql` — (idempotent):
  - `CREATE EXTENSION postgis` + ستونهای geography روی platform_landscapes
  - جدول جاافتاده `platform_badges`
  - **فعالسازی RLS روی همه ۱۵ جدول**
  - سیاستها: خواندن عمومی برای کاتالوگ (landscapes/standards/badges)؛ مالکیت `auth.uid()` برای داده شخصی با `WITH CHECK` (طبق چکلیست امنیتی Supabase: بدون user_metadata، بدون SECURITY DEFINER، TO authenticated + شرط مالکیت)
  - اجرا: دشبورد Supabase ← SQL Editor ← paste ← Run (۱ دقیقه)
- `.github/workflows/ci.yml` — CI رایگان: backend (ruff + compileall + import + pytest) و frontend (pnpm build)
- `services/api_gateway/routers/auth_supabase.py` — پروکسی GoTrue:
  - `POST /api/v1/auth/supabase/signup` (تست: **500 «Database error saving new user»** — بلاکر سمت پروژه)
  - `POST /api/v1/auth/supabase/login` (تست: 400 صحیح برای کاربر ناموجود — پروکسی سالم)
  - `GET /api/v1/auth/supabase/me` (اعتبارسنجی JWT)
  - `POST /api/v1/auth/supabase/admin/delete-user` (فقط service role، هرگز در فرانت)

## ۳) بلاکر ثبتنام — تشخیص و رفع
خطای «Database error saving new user» معمولاً از تریگر خراب روی `auth.users` است (مثلاً تریگر قدیمی که به تابع/ستون حذفشده ارجاع میدهد). رفع: در SQL Editor اجرا کنید:
```sql
select tgname, tgenabled from pg_trigger where tgrelid = 'auth.users'::regclass;
-- تریگرهای مشکوک/خراب را حذف کنید، سپس ثبتنام دوباره تست شود
```
یا اگر `SUPABASE_DB_PASSWORD` را در `.env` بگذارید، خودم مستقیم psql میزنم و تشخیص/رفع را کامل میکنم.

## ۴) ابزارهای رایگان بدون ثبتنام (این چرخه)
- PostGIS (extension)، GitHub Actions (CI)، ruff + pytest؛
- قبلاً فعال: Open-Meteo ERA5، SoilGrids WCS، NASA POWER، SEPAL (FAO)، pyRothC/AquaCrop-OSPy/pySWATPlus/Pywr/pymoo

## قدم بعدی (بخش B)
پس از رفع بلاکر: اتصال Auth به فرانت (جایگزینی auth موقت)، داده مکانی واقعی با PostGIS روی deck.gl، سپس بازارچه/LMS روی همان دیتابیس.
