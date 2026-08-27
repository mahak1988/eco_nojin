# فاز ۷ — ممیزی کربن و بازار اعتبار (MRV سطح ۲)

> وضعیت: **کامل و تأیید زنده** · commit این چرخه · بیلد سبز 3.06s · pytest ۶۳ پاس

## ۱) تعریف (مستند ۵۱)
فاز ۷: تبدیل دادههای تأییدشده به اعتبار کربن قابل پیگیری؛ فاز ۸ (بعدی): مقیاس بینالمللی.

## ۲) Migration 0006 — توابع امن ممیزی
- `auditor_vote(verification_id, vote, confidence, comment)` — SECURITY DEFINER + بررسی نقش (admin/auditor) داخل تابع؛ `validator_id = auth.uid()`؛ vote فقط approved/rejected.
- `admin_issue_credits(p_project_id, p_amount)` — SECURITY DEFINER + بررسی ادمین؛ درج اعتبار در `platform_carbon_credits` + افزایش `credits_issued` + تغییر وضعیت پروژه به `verified` + ثبت در `token_transactions` (نوع CCT، رویداد reward — مطابق CHECK های موجود).
- نکات فنی حلشده: ابهام ستون خروجی RETURNS TABLE با ستون جدول (تغییر نام به out_*)، PostgREST تطبیق نام پارامتر (p_*)، محدودیتهای CHECK جدول تراکنشها.

## ۳) بکاند
- `services/audit/certificate_pdf.py` — گواهی اعتبار PDF فارسی RTL (fpdf2 + Tahoma + arabic-reshaper، همان ماشین MRV): کد اعتبارسنجی، پروژه، مساحت، tCO2e، مالک، مرجع استاندارد.
- `services/api_gateway/routers/audit.py` — `GET /api/v1/audit/queue`، `POST /api/v1/audit/vote`، `POST|GET /api/v1/audit/credits`، `GET /api/v1/audit/certificate/{project_id}` (همه با JWT کاربر؛ RLS/توابع تصمیم میگیرند).

## ۴) تست E2E زنده (`scripts/test_phase7_e2e.py`)
- ثبتنام ادمین/کشاورز تست ← پروفایل ← bootstrap نقش ← ساخت پروژه ← **صدور 42.5 tCO2e** ← فهرست اعتبارها (۱) ← **گواهی PDF (۲۰۰، ۴۴۹۹۳ بایت)**.
- کشاورز در همه مسیرها رد شد: صدور اعتبار (`not_admin`)، تغییر نقش (`not_admin`)، رأی ممیزی (`not_authorized`).
- پاکسازی کامل داده تست.

## ۵) فرانت
- `AuditCard.tsx` — صف راستیآزمایی (حالت خالی صادقانه)، فرم صدور اعتبار (فقط مدیر)، فهرست اعتبارها + دکمه دانلود گواهی PDF. نقش از /profile.

## قدم بعدی
فاز ۸ (تعریفشده در مستند ۵۱): استانداردهای بینالمللی (ISO 14064/SDG/FAO/OGC)، API مکانی GeoJSON مبتنی بر PostGIS، دوزبانه FA/EN، استقرار رایگان (Vercel + Render/Railway).
