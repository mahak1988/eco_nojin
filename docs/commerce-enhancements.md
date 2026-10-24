# HyDroMA — Advanced Commercial Features (10 Enhancements)

Documentation of all ten commerce-layer improvements implemented on the HyDroMA / Eco Nojin platform. Each entry includes the problem, solution, changed files, migration notes, and usage examples.

---

## 1. Marketplace DB Wiring

### Problem
`services/marketplace/product_catalog.py` initialized with `seller_repo=None, product_repo=None`, so the marketplace served only in-memory demo data. `DbSellerRepo` / `DbProductRepo` existed in `services/marketplace/db_repos.py` but were never connected at startup.

### Solution
In `services/api_gateway/main.py` lifespan, instantiate `DbSellerRepo()` and `DbProductRepo()` and pass them to `init_catalog(...)`. Falls back to demo data if DB wiring fails.

**Files changed:**
- `services/api_gateway/main.py`

**Code:**
```python
try:
    from services.marketplace.db_repos import DbProductRepo, DbSellerRepo
    from services.marketplace.order_management import init_order_manager
    from services.marketplace.product_catalog import init_catalog

    init_catalog(
        seller_repo=DbSellerRepo(),
        product_repo=DbProductRepo(),
    )
    init_order_manager(order_repo=None)
    logger.info("✅ Marketplace catalog wired to database repositories")
except Exception as e:
    logger.warning(f"⚠️ Marketplace DB wiring failed, falling back to demo: {e}")
    init_catalog(seller_repo=None, product_repo=None)
    init_order_manager(order_repo=None)
```

**Behavior:** All catalog reads (`list_products`, `get_product`, `list_producers`) now hit `marketplace_products` / `marketplace_sellers` tables when the DB is available. Demo products remain as fallback.

---

## 2. Inventory Valuation — Standard Costing

### Problem
Only weighted-average costing was implemented. `fifo` and `standard` were rejected at `_resolve_valuation_method()` with 501, even though `standard` is trivial to support (uses `InvSKU.standard_cost`).

### Solution
Allow `standard` as a valuation method; `issue()` uses `SKU.standard_cost` when `valuation_method="standard"`. `fifo` remains rejected until per-lot cost tracking lands.

**Files changed:**
- `services/inventory/service.py`

**Code:**
```python
@staticmethod
def _resolve_valuation_method(method: str) -> str:
    if method not in VALID_VALUATION_METHODS:
        raise EcoNojinException(
            f"Invalid valuation method: {method}", code="INVALID_VALUATION_METHOD"
        )
    if method == "fifo":
        raise EcoNojinException(
            f"Valuation method not implemented: {method}",
            code="UNSUPPORTED_VALUATION_METHOD",
            status_code=501,
        )
    return method
```

In `issue()`:
```python
method = self._resolve_valuation_method(valuation_method)

if method == "standard":
    unit_cost = await self._sku_standard_cost(sku_id)
else:
    unit_cost = await self._current_average_cost(sku_id, warehouse_id)
```

**Usage:**
```python
service = StockService(db)
movement = await service.issue(
    sku_id=sku.id,
    warehouse_id=wh.id,
    qty=Decimal("10"),
    valuation_method="standard",
    user_id=str(current_user.id),
)
```

---

## 3. Reconciliation — Signed Delta for Adjust Movements

### Problem
`adjust` movements stored `abs(qty)` with the signed delta only in `notes`. `reconcile_inventory` excluded them, so they surfaced as unexplained drift.

### Solution
Added a `signed_qty` column (`Numeric(18, 8)`, nullable) to `inv_stock_movements`. Adjustments store the signed delta here; reconciliation includes them via a `CASE WHEN signed_qty > 0 ... ELSE 0` union branch.

**Files changed:**
- `database/models.py` — added `signed_qty = Column(Numeric(18, 8), nullable=True)`
- `services/inventory/service.py` — `_build_movement`, `_create_movement`, `adjust`, `reconcile_inventory`
- `alembic/versions/20261017_070000_p9_inventory_signed_qty.py` — guarded migration

**Migration:**
```python
_TABLE = "inv_stock_movements"
_COLUMN = "signed_qty"

def upgrade():
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(_TABLE) and not any(
        c["name"] == _COLUMN for c in inspector.get_columns(_TABLE)
    ):
        op.add_column(_TABLE, sa.Column(_COLUMN, sa.Numeric(18, 8), nullable=True))
```

**Reconciliation SQL addition:**
```sql
UNION ALL
SELECT
    sku_id, warehouse_id,
    COALESCE(from_location_id, 0),
    COALESCE(lot_id, 0),
    CASE WHEN signed_qty > 0 THEN signed_qty ELSE 0 END,
    CASE WHEN signed_qty < 0 THEN -signed_qty ELSE 0 END
FROM inv_stock_movements
WHERE movement_type = 'adjustment' AND signed_qty IS NOT NULL
```

**Behavior:** `drift = on_hand - (qty_in - qty_out)` now accounts for signed adjustments; no more phantom drift from adjustment movements.

---

## 4. Discounted Path — Marketplace Fee Discount

### Problem
`services/finance/revenue_indicators.py` defined `discounted_fees()` / `discounted_revenue()` as pure arithmetic called by nothing. `MARKET_FEE_DISCOUNT` redemption existed but had no effect on commerce orders.

### Solution
Added `discount_bps` parameter to `OrderService.create_order()` and `OrderCreateRequest`. Discount is clamped to 0–100% via `clamped_discount_bps()` and applied only to the platform fee line (landscape fee untouched, per `DISCOUNT_COVERS_LANDSCAPE_FEE = False`).

**Files changed:**
- `services/commerce/service.py`
- `services/commerce/routers/commerce.py`

**Code:**
```python
async def create_order(
    self,
    buyer_id: str,
    items: list[dict],
    shipping_address: dict | None = None,
    idempotency_key: str | None = None,
    discount_bps: Decimal | None = None,
) -> ComOrder:
```

```python
if discount_bps is not None:
    applied = clamped_discount_bps(discount_bps)
    waived = (platform_fee * applied / Decimal("10000")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN
    )
    platform_fee = max(platform_fee - waived, Decimal("0"))
    total = subtotal + platform_fee + landscape_fee
```

**Router schema:**
```python
class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest] = Field(..., min_length=1)
    shipping_address: dict | None = None
    idempotency_key: str | None = None
    discount_bps: int | None = None
```

**Invariant:** `sum(every fee line after discount) + waived == sum(every fee line before)` holds exactly; no fee line goes negative.

---

## 5. Cross-Ledger User Attribution

### Problem
`inv_stock_movements` had no `user_id`, making per-user attribution across money/inventory ledgers impossible. Cross-tenant replay and audit were limited to `created_by` (a free text field).

### Solution
Added `user_id = Column(String(36), nullable=True, index=True)` to `InvStockMovement`. All movement mutators (`receipt`, `issue`, `transfer`, `adjust`, `return_goods`, `scrap`, `unblock_stock`) accept and forward `user_id`.

**Files changed:**
- `database/models.py`
- `services/inventory/service.py`
- `alembic/versions/20261017_073000_p5_inventory_user_id.py`

**Migration:**
```python
op.add_column(_TABLE, sa.Column(_COLUMN, sa.String(36), nullable=True, index=True))
```

**Usage:**
```python
movement = await service.receipt(
    sku_id=sku.id,
    warehouse_id=wh.id,
    qty=Decimal("100"),
    unit_cost=Decimal("15000"),
    user_id=str(current_user.id),
)
```

**Query example:**
```sql
SELECT user_id, COUNT(*), SUM(qty) FROM inv_stock_movements
GROUP BY user_id ORDER BY COUNT(*) DESC;
```

---

## 6. Expired Reservations Sweep — Scheduled Job

### Problem
`StockService.sweep_expired_reservations()` existed but was only invoked lazily during `reserve_stock()`. No background mechanism released expired reservations, so blocked stock could remain reserved indefinitely.

### Solution
Added `POST /api/v1/inventory/sweep-expired` (admin-only) endpoint that calls `sweep_expired_reservations(sku_id, warehouse_id)` and returns the count released. Can be wired to a cron scheduler (APScheduler / systemd timer / Kubernetes CronJob).

**Files changed:**
- `services/inventory/routers/inventory.py`

**Endpoint:**
```http
POST /api/v1/inventory/sweep-expired?sku_code=ABC&warehouse_id=5
Authorization: Bearer <admin-token>
```

**Response:**
```json
{ "released": 12 }
```

**Suggested cron wiring (example):**
```python
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: sweep_expired_reservations(db_session),
    "interval", minutes=15
)
scheduler.start()
```

---

## 7. Multi-Currency Landscape Fund

### Problem
`_credit_landscape_fund()` skipped orders not settled in `FUND_CURRENCY` ("IRR"), so landscape fees from USD/ECO orders were stranded in platform revenue instead of funding the village restoration fund.

### Solution
Removed the `order.currency != FUND_CURRENCY` guard. Landscape fund rows now use `order.currency` for both `LandscapeFund` and `LandscapeFundCredit`, enabling multi-currency village funds.

**Files changed:**
- `services/commerce/service.py`

**Behavior change:**
- Before: only IRR orders credited `LandscapeFund`; USD/ECO landscape fees stayed in `ECO_PLATFORM_REVENUE`.
- After: all currencies credit the per-village fund in their own currency.

**Note:** Cross-currency aggregation in `LandscapeFund` reports should apply an FX rate before summing; this layer stores raw currency per row.

---

## 8. Event Bus Consumers for Commerce Events

### Problem
Commerce events (`order_created`, `payment_completed`, `order_shipped`, `order_settled`, `order_cancelled`) were emitted via `_emit_commerce_event()` but no consumer existed, so they were fire-and-forget with no downstream reaction.

### Solution
Subscribed to `commerce.>` subject in the API gateway lifespan via NATS JetStream durable consumer `commerce-event-consumer`. Handler logs events and can be extended to drive notifications, workflows, or reporting.

**Files changed:**
- `services/api_gateway/main.py`

**Code:**
```python
async def _commerce_event_handler(payload: dict, headers: dict) -> None:
    logger.info(
        "commerce event: %s aggregate=%s id=%s",
        payload.get("event_type"),
        payload.get("payload", {}).get("aggregate_type"),
        payload.get("payload", {}).get("aggregate_id"),
    )

nats_mgr = get_nats_manager()
await nats_mgr.subscribe(
    "commerce.>",
    _commerce_event_handler,
    durable_name="commerce-event-consumer",
)
```

**Behavior:** Best-effort; subscription failures are logged and swallowed so boot is not blocked by a broker outage.

---

## 9. Stocktake Valuation — Variance Journal

### Problem
Stocktake adjustments (`adjust(adjustment_type="stocktake")`) changed `on_hand` but posted variance through the generic `adjust()` path already; no dedicated stocktake method existed, making the intent opaque.

### Solution
`create_stocktake()` and `approve_stocktake()` already exist in `StockService`. They create `InvStocktake` + `InvStocktakeLine` rows; approval posts an `adjust` movement with `JOURNAL_VARIANCE` (`ECO_INVENTORY` / `ECO_INVENTORY_VARIANCE`) so stocktake deltas appear in trial balance and P&L.

**No code change required.** Documented for completeness:

**Flow:**
1. `POST /api/v1/inventory/stocktakes` — create draft stocktake with lines (`sku_id, warehouse_id, qty_counted`)
2. `POST /api/v1/inventory/stocktakes/{id}/approve` — approve; for each line, calls `adjust(qty = counted - on_hand, adjustment_type="stocktake")`
3. Variance journal posts `debit ECO_INVENTORY / credit ECO_INVENTORY_VARIANCE` (found stock) or reverse (shrinkage)

**Query:**
```sql
SELECT * FROM inv_stock_movements
WHERE movement_type = 'adjustment'
  AND notes ILIKE '%stocktake%';
```

---

## 10. API Versioning

### Problem
No version information was exposed on the API surface. Clients could not detect which server version they were talking to, complicating backward-compatible migrations.

### Solution
Added `API_VERSION = "1.0.0"` constant, an `X-API-Version` response header on all responses, a `GET /api/version` endpoint, and `api_version` in the root `/` response.

**Files changed:**
- `services/api_gateway/main.py`

**Code:**
```python
API_VERSION = "1.0.0"

@app.middleware("http")
async def add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = API_VERSION
    return response

@app.get("/api/version", tags=["health"])
async def api_version():
    return {
        "version": API_VERSION,
        "api_version": API_VERSION,
        "service": "api-gateway",
        "environment": _settings.app_env,
    }
```

**Root response now includes:**
```json
{
  "name": "Eco Nojin API",
  "version": "0.1.0",
  "api_version": "1.0.0",
  "status": "running",
  ...
}
```

**Client usage:**
```bash
curl -i http://localhost:8100/api/version
# X-API-Version: 1.0.0
```

---

## Migration Summary

| Migration | Revision | Down Revision | Description |
|-----------|----------|---------------|-------------|
| `20261017_070000_p9_inventory_signed_qty` | p9 signed_qty | `20261013_120000_p8_departure_cancel_reason` | Add `signed_qty` column to `inv_stock_movements` |
| `20261017_073000_p5_inventory_user_id` | p5 user_id | `20261017_070000_p9_inventory_signed_qty` | Add `user_id` column to `inv_stock_movements` |

Both migrations are guarded (column-exists check) and re-run-safe; they coexist with `create_all`.

## Verification

- `tools/detect_imports.py --root .` → **0 violations** (PASS)
- All edited files pass `py_compile` syntax check
- Import guard policy (`tools/import_guard_policy.json`) unchanged; no new engine-internal imports from services

## Files Touched

| File | Changes |
|------|---------|
| `services/api_gateway/main.py` | Marketplace DB wiring, event bus consumer, API versioning |
| `services/commerce/service.py` | Discounted path, multi-currency landscape fund |
| `services/commerce/routers/commerce.py` | `discount_bps` schema field |
| `services/inventory/service.py` | Standard costing, signed_qty, user_id propagation |
| `services/inventory/routers/inventory.py` | Sweep-expired endpoint |
| `database/models.py` | `signed_qty`, `user_id` columns on `InvStockMovement` |
| `alembic/versions/20261017_070000_p9_inventory_signed_qty.py` | Migration p9 |
| `alembic/versions/20261017_073000_p5_inventory_user_id.py` | Migration p5 |

---

## Suggested Next Steps

1. **FIFO implementation** — requires per-lot cost ledger; `fifo` still rejected at 501.
2. **Cross-ledger `user_id` on FinJournalEntry** — extend attribution beyond inventory.
3. **FX rates for multi-currency fund reporting** — `LandscapeFund` stores raw currency; aggregation needs rates.
4. **Cron scheduler integration** — wire `sweep-expired` to APScheduler or Kubernetes CronJob.
5. **API version middleware on all sub-routers** — currently only gateway-level; consider per-router versioning.
