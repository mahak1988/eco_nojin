# S-STRUCT — قرارداد لایه‌بندی

> هر ماژول دامنه **دقیقاً** این پنج نقش را دارد و هیچ نقشی نمی‌تواند دو پیاده‌سازی داشته باشد.

**الگوی مرجع:** `services/commerce/` و `services/reporting/`
**دروازه:** G5 (قرارداد ساختاری، تحلیل AST) — فاز ۳

## نقش‌ها

```
models/       مدل‌های ORM. تنها جایی که SQLAlchemy وارد می‌شود.
schemas/      مدل‌های Pydantic. تنها جایی که FastAPI به آن‌ها اشاره می‌کند.
repository/   تنها لایه‌ای که Session می‌گیرد و query می‌نویسد.
service/      تنها جایی که منطق کسب‌وکار نوشته می‌شود. هرگز DB.
routers/      فقط: parse → call service → shape response. هرگز DB، هرگز منطق.
```

## قواعد مکانیکی

| قاعده | دلیل | وضعیت فعلی |
|---|---|---|
| `routers/**` نباید `select(`، `db.query`، `db.add`، `db.execute` داشته باشد | منطق در روتر، آزمون‌ناپذیر | نقض در ۶+ روتر |
| `service/**` نباید `Session` بگیرد | نشت لایه | نقض در `carbon/` |
| `repository/**` نباید از `routers` import کند | وابستگی معکوس | — |
| هر بسته `__init__.py` داشته باشد | import قابل پیش‌بینی | ۱۰ بسته فاقد — **فاز ۱ رفع شد** |
| یک getter برای هر سرویس | بدون `init_*`/`get_*` دوگانه | ۱۰+ singleton بدون قفل |

## نقض‌های ثبت‌شده

| فایل | نقض |
|---|---|
| `commerce/routers/commerce.py:79-80,104-109` | دو `select()` خام در روتر |
| `inventory/routers/inventory.py:158-161` | `__import__("sqlalchemy").select` داخل هندلر |
| `admin_content.py:120,133-134` | نوشتن در روتر |
| `admin_overview.py:50-61` | ۷ `db.query().count()` در یک تابع |
| `ai/admin_assistant.py:140-199` | ۹ کوئری همگام از داخل `async def` — **بلوکه‌کننده حلقه رویداد** |
| `ai/support_agent.py:159` | `async def` با `db.query()` همگام |
| `carbon/service.py` + `carbon/repository.py` | دو سبک DB در یک محدوده: `AsyncSession` و `Session` |
| `marketplace/` | سه سبک موازی: `AsyncSession`، `hub.get_session()`، `Session.query()` |

## I/O همگام در `async def`

هر فراخوانی بلوک‌کننده داخل یک هندلر async، حلقه رویداد را برای **تمام** درخواست‌های هم‌زمان متوقف می‌کند. نقاط ثبت‌شده:

| محل | کار |
|---|---|
| `ai/admin_assistant.py:249` | ۹ `db.query()` |
| `ai/support_agent.py:119,123` | `db.query()` |
| `api_gateway/eventbus/dlq.py:74,103,152,189` | SQLite در ۵ متد `async def` |
| `backup/service.py` | فایل — **فاز ۱ رفع شد** (`asyncio.to_thread`) |
| `reporting/service.py:77-80` | `mkdir` + `write_text` |
| `marketplace/hub_service.py:1237` | `hub.get_session()` در `async def` |

## ترتیب اجرا

پس از رفع P0ها، مهاجرت لایه‌بندی در فاز ۴ بلوک ۴ (هفته ۱۰-۱۱) انجام می‌شود: به‌ترتیب ریسک صعودی، هر ماژول یک PR.
