# ماتریس اتصال سطح‌به‌سطح — جدول دیتابیس ← endpoint ← صفحه

**تاریخ:** ۲۰۲۶/۰۹/۲۸ · **روش:** تولید خودکار از `openapi.json` + `page-catalog.ts` + `contract-gaps.json` + `data/econojin.db`

**جمع کل:** 489 مسیر منتشرشده · 145 جدول دیتابیس · 600 ورودی کاتالوگ · 37 شکاف قرارداد

| دامنه | endpoint منتشرشده | endpoint گمشده | کاتالوگ (live/capability/planned/unavailable) | جداول دیتابیس | رکوردها | وضعیت |
|---|---:|---:|---|---|---:|---|
| marketplace | 106 | 1 | 17/7/49/54 | 24 | 450 | ⚠️ 1 مسیر مصرف‌شده بدون قرارداد |
| workspace | 28 | 1 | 14/0/28/4 | 7 | 2632 | ⚠️ 1 مسیر مصرف‌شده بدون قرارداد |
| hydroma | 87 | 1 | 1/51/29/52 | 31 | 263 | ⚠️ 1 مسیر مصرف‌شده بدون قرارداد |
| admin | 50 | 1 | 8/0/28/4 | 11 | 209 | ⚠️ 1 مسیر مصرف‌شده بدون قرارداد |
| research | 7 | 0 | 1/1/10/6 | 0 | 0 | 🟡 endpoint دارد، داده ندارد (حالت خالی صادقانه) |
| learning | 0 | 1 | 5/0/16/10 | 1 | 0 | ❌ endpoint ندارد |
| auth | 44 | 0 | — | 6 | 605 | ✅ endpoint + دادهٔ واقعی |
| system | 15 | 0 | 6/0/28/3 | 3 | 1 | ✅ endpoint + دادهٔ واقعی |
| public | 4 | 30 | 79/0/39/12 | 0 | 0 | ⚠️ 30 مسیر مصرف‌شده بدون قرارداد |
| inclusive | 19 | 0 | 1/0/28/9 | 0 | 0 | 🟡 endpoint دارد، داده ندارد (حالت خالی صادقانه) |
| other | 26 | 0 | — | 0 | 0 | 🟡 endpoint دارد، داده ندارد (حالت خالی صادقانه) |

## جداول کلیدی هر دامنه با رکوردهای واقعی

**marketplace** — `daily_earnings`=450 · `product`=0 · `com_order`=0 · `inv_sku`=0 · `inv_warehouses`=0 · `disputes`=0 · `dispute_events`=0 · `shipments`=0 · `shipment_events`=0 · `marketplace_escrow_entries`=0 · `entrepreneur_profiles`=0 · `b2b_demands`=0

**workspace** — `fin_journal_entry`=900 · `fin_idempotency_key`=675 · `ecowallet`=605 · `fin_journal_batch`=450 · `fin_account`=2 · `ledgerentry`=0 · `ecotransaction`=0

**hydroma** — `land_profiles`=210 · `nojin_materials`=43 · `nojin_soil_types`=10 · `iot_devices`=0 · `mrvobservation`=0 · `simulationrun`=0 · `farms`=0 · `soil_analyses`=0 · `satellite_analyses`=0 · `calibrationrecorddb`=0 · `modelversiondb`=0 · `carbon_projects`=0

**admin** — `auditlog`=209 · `settings`=0 · `audit_event`=0 · `int_outbox_event`=0 · `errorlog`=0 · `carbon_audit_log`=0 · `content_items`=0 · `api_keys`=0 · `content_versions`=0 · `content_translations`=0 · `admin_audit_logs`=0

**learning** — `quality_certificates`=0

**auth** — `users`=605 · `password_reset_tokens`=0 · `oauth_connections`=0 · `api_keys`=0 · `auth_users`=0 · `auth_refresh_tokens`=0

**system** — `alembic_version`=1 · `analytics_snapshots`=0 · `compute_jobs`=0

## نحوهٔ خواندن

| نشان | معنا |
|---|---|
| ✅ | endpoint منتشرشده + جدول دیتابیس با رکورد واقعی → قابل اتصال و نمایش |
| 🟡 | endpoint موجود است ولی جدول خالی است → فقط «حالت خالی صادقانه» مجاز است |
| ⚠️ | کد مسیرهایی را صدا می‌زند که در قرارداد نیستند (نیازمند `CONTRACT_REQUEST_CODE_USED_37.md`) |
| ❌ | هیچ endpoint منتشرشده‌ای برای این دامنه وجود ندارد |