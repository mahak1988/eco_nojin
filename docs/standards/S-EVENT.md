# S-EVENT — قرارداد رویداد و یکپارچگی

> **یک** پشته رویداد، **یک** طرح‌واره، و هر تغییر state از طریق outbox.

**نسخه مرجع:** `services/api_gateway/eventbus/` (گارد وابستگی اختیاری، `nats_lifespan` آماده)
**دروازه:** G2 + قرارداد schema — فاز ۳

## چرا این استاندارد

سه پشته NATS موازی، که یک رویداد منطقی را بسته به اینکه کدام‌کدام منتشرش کند روی subject متفاوتی می‌نشاند:

| پیاده‌سازی | مصرف‌کننده | نگاشت subject |
|---|---|---|
| `api_gateway/eventbus/` | `outbox_worker.py:19` | `f"{prefix}.{subject}"` |
| `event_bus/` | `workers/event_worker.py:7` | `subject_for(...)` |
| `orchestrator/src/messaging/bus.py` | ارکستراتور | — |

`NATSConfig` و `EventBusConfig` مو‌به‌مو یکسان‌اند و **منطق نگاشت متفاوت** دارند.

## وضعیت فعلی — چرا بحرانی است

**ناشر:** ۹ تابع منتشر تعریف شده، **۲ فراخوانی**. هفت ناشر هرگز صدا زده نمی‌شود. هیچ ناشری برای کیف پول، دفتر، مالی، تجارت یا موجودی وجود ندارد — در حالی که `outbox_worker.py:154,162` subjectهای `wallet.` و `ledger.` را نگاشت می‌کند که هیچ تولیدکننده‌ای نمی‌رساند.

**لایه کسب‌وکار رویداد-ساکت است.** هیچ تغییر state در کربن، بازارگاه، مالی، تجارت، دفتر یا موجودی رویدادی منتشر نمی‌کند.

**Outbox نویسنده ندارد.** `OutboxService.add_event` تعریف شده و **هیچ‌کس صدایش نمی‌زند**. `IntOutboxEvent` فقط خوانده می‌شود. یعنی تغییر وضعیت و انتشار رویداد در هیچ‌جا اتمیک نیست.

**مصرف‌کننده سیاه‌چاله است.** `event_bus/worker.py:160-164` در نبود handler پیام را **ack** می‌کند و دور می‌ریزد.

**DLQ کد مرده است.** `add_to_dlq` هیچ فراخوانی ندارد؛ `nats_client.py:313-321` یک `nak()` خام بدون backoff می‌زند. پیام سمی با تمام سرعت بازارسالی می‌شود.

## قواعد سخت

| قاعده | وضعیت فعلی |
|---|---|
| یک پشته؛ `NATSConfig` واحد | ✗ سه پشته |
| هر تغییر state از طریق outbox | ✗ صفر نویسنده |
| ستون `available_at` + backoff پایدار | ✗ `RETRY_BACKOFF_BASE` تعریف‌شده، بی‌استفاده |
| `processed_at` فقط نشانه تکمیل | ✗ دوگانه: نشانه claim و تکمیل |
| مصرف‌کننده بدون handler → `nak` نه `ack` | ✗ ack می‌کند |
| DLQ از مسیر خطا تغذیه شود | ✗ بی‌فراخوان |
| هر رویداد: `event_id` (ULID)، `schema_version`، `occurred_at`، `trace_id` | ناهمگن |
| هر event type **یک** مصرف‌کننده، با آزمون | ✗ ۷ از ۹ بدون مصرف‌کننده |

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

فاز ۴ بلوک ۱ (هفته ۴-۵)، زیرساخت افقی، کم‌ریسک‌ترین بلوک با اثر گسترده.
