# S-EVENT — قرارداد رویداد و یکپارچگی

> **یک** پشته رویداد، **یک** طرح‌واره، و هر تغییر state از طریق outbox.

**نسخه مرجع:** `services/api_gateway/eventbus/` (گارد وابستگی اختیاری، `nats_lifespan` آماده)
**دروازه:** G2 + قرارداد schema — فاز ۳

## چرا این استاندارد

یک زمان سه پشتهٔ NATS موازی وجود داشت که یک رویداد منطقی را بسته به اینکه کدام‌کدام منتشرش کند روی subject متفاوتی می‌نشاند. `NATSConfig` و `EventBusConfig` مو‌به‌مو یکسان بودند و **منطق نگاشت متفاوت** داشتند.

**تconsolidation انجام شد:** `services/event_bus/` و `orchestrator/src/messaging/bus.py` حذف شدند. امروز یک پشته باقی است.

## وضعیت فعلی

**پشتهٔ یکتا:** `services/api_gateway/eventbus/` — شامل `nats_client.py`، `publisher.py`، `retry.py`، `worker.py`.

**گارد:** `tests/contract/test_s_event.py` بازگشتِ `services/event_bus/` و وجود `dlq.py` را رد می‌کند. حذف عمدی است و به‌صورت خودکار اعمال می‌شود.

**نویسندهٔ outbox:** `services/integration/outbox.py` (`add_event`) و مصرف‌کنندهٔ آن `services/integration/outbox_worker.py`. `services/workers/event_worker.py` باقی است.

| قاعده | وضعیت | مرجع |
|---|---|---|
| یک پشته؛ `NATSConfig` واحد | ✅ انجام شد | `tests/contract/test_s_event.py` |
| بدون `dlq.py` موازی | ✅ انجام شد | همان آزمون |
| هر تغییر state از طریق outbox | ✗ **باز** | `outbox.add_event` باید فراخوان شود |
| ستون `available_at` + backoff پایدار | ✗ باز | `retry.py` تعریف‌شده، بی‌استفاده |
| مصرف‌کننده بدون handler → `nak` نه `ack` | ✗ باز | `eventbus/worker.py` |
| DLQ از مسیر خطا تغذیه شود | ✗ باز | `add_to_dlq` بی‌فراخوان |
| هر رویداد: `event_id`، `schema_version`، `occurred_at`، `trace_id` | ناهمگن | باز |

> **دقت در خواندن:** سطرهای ✗ بالا **بدهی باز** هستند، نه توصیف وضعیت حذف‌شده.
> نسخهٔ قبلی این سند، فایل‌هایی را که سال‌ها پیش حذف شده بودند به‌عنوان
> «نقص» توصیف می‌کرد. آن‌ها حذف شدند و حذفشان درست بود.

## درست / نادرست

```python
# ✅ درست — تغییر state و ثبت رویداد در یک تراکنش
async with db.begin():
    await service.update(wallet)
    await outbox.add_event("wallet.balance_changed", payload, id=event_id)

# ❌ نادرست — منتشر کردن بدون تضمین، به‌همراه نوشتن مستقل DB
await publisher.publish_marketplace_event("order.created", payload)
await db.commit()
```


## مهاجرت

تconsolidation پشته انجام شده و با آزمون محافظت می‌شود. بدهی باقی‌مانده —
مخصوصاً «صفر نویسندهٔ outbox» — بدهی معماری است و در
docs/standards/tolerated-degradations.yaml ثبت شده.
