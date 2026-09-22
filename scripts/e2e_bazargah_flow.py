"""E2E flow: order -> payment(bank) -> escrow hold -> delivery confirm -> escrow release + notifications.

Run: .venv/Scripts/python.exe scripts/e2e_bazargah_flow.py
"""

from __future__ import annotations

import os
import sys
import uuid
import warnings

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.abspath("./data/e2e_bazargah.db")
os.environ["DB_ECHO"] = "0"

warnings.filterwarnings("ignore")

sys.path.insert(0, ".")

from fastapi.testclient import TestClient  # noqa: E402

from database.hub import hub  # noqa: E402
from database.models import User  # noqa: E402
from services.api_gateway.auth import create_access_token, hash_password  # noqa: E402

EMAIL = "e2e-buyer@econojin.local"
results = []


def step(ok, label):
    results.append((ok, label))
    print(("PASS " if ok else "FAIL ") + label, flush=True)


def _create_schema() -> None:
    import database.models  # noqa: F401  (register all platform tables)
    import services.marketplace.models  # noqa: F401
    import services.notification.models_db  # noqa: F401
    from database.base import Base

    Base.metadata.create_all(bind=hub.get_sqlalchemy_engine())


def ensure_user():
    with hub.get_session() as s:
        from sqlalchemy import select

        row = s.execute(select(User).where(User.email == EMAIL)).scalar_one_or_none()
        if row:
            return row.id
        from sqlalchemy import text

        uid = "e2e-buyer-0001"
        s.execute(
            text(
                "INSERT INTO users (id, email, hashed_password, full_name, role, language, is_email_verified, created_at, updated_at) VALUES (:i, :e, :h, :f, 'buyer', 'fa', 0, datetime('now'), datetime('now'))"
            ),
            {"i": uid, "e": EMAIL, "h": hash_password("E2e!Passw0rd"), "f": "E2E Buyer"},
        )
        s.commit()
        return uid


def main():
    _create_schema()
    user_id = ensure_user()
    # Real catalog row (no demo): approved product owned by an approved seller
    with hub.get_session() as s:
        from services.marketplace.models import (
            MarketplaceProduct,
            MarketplaceProductStatus,
            MarketplaceSeller,
        )

        if s.get(MarketplaceSeller, "e2e-seller-0001") is None:
            s.add(
                MarketplaceSeller(
                    id="e2e-seller-0001",
                    user_id=user_id,
                    village_id="v-e2e",
                    shop_name="فروشگاه E2E",
                    status="active",
                    is_verified=True,
                )
            )
        if s.get(MarketplaceProduct, "e2e-product-0001") is None:
            s.add(
                MarketplaceProduct(
                    id="e2e-product-0001",
                    seller_id="e2e-seller-0001",
                    name="عسل طبیعی E2E",
                    slug="e2e-honey",
                    description="محصول واقعی تست انتها-به-انتها",
                    category="honey",
                    price=350000,
                    stock=100,
                    unit="kg",
                    village_id="v-e2e",
                    organic=True,
                    status=MarketplaceProductStatus.APPROVED,
                )
            )
        s.commit()

    token = create_access_token({"sub": user_id})
    from services.api_gateway.main import app

    client = TestClient(app, raise_server_exceptions=False)

    def hdr():
        return {"Authorization": "Bearer " + token, "Idempotency-Key": str(uuid.uuid4())}

    r = client.get("/api/v1/marketplace/products/e2e-product-0001?__direct=1")
    product = r.json()["products"][0]
    pid = product["id"]
    step(r.status_code == 200, "catalog: product " + pid)

    r = client.post(
        "/api/v1/marketplace/orders",
        json={"product_id": pid, "buyer_name": "E2E Buyer", "quantity_kg": 10},
        headers=hdr(),
    )
    ok = r.status_code == 200
    order = r.json() if ok else {}
    order_id = order.get("order_id", "")
    total = float(order.get("total_price") or 0)
    step(ok and bool(order_id), "order created: %s total=%.0f IRR" % (order_id, total))

    r = client.post(
        "/api/v1/marketplace/cart",
        json={"items": [{"product_id": pid, "quantity": 1}]},
        headers=hdr(),
    )
    step(r.status_code == 200, "authenticated cart add -> 200")

    r = client.post(
        "/api/v1/marketplace/payments",
        json={
            "order_id": order_id,
            "amount": total,
            "payment_method": "bank",
            "description": "E2E",
        },
        headers=hdr(),
    )
    ok = r.status_code == 200
    payment = r.json() if ok else {}
    payment_id = payment.get("id", "")
    step(
        ok and payment.get("status") == "awaiting_verification",
        "bank payment initiated: " + payment_id,
    )

    r = client.post(
        "/api/v1/marketplace/payments/%s/confirm" % payment_id,
        json={"ref_id": "TRK-E2E-001"},
        headers=hdr(),
    )
    ok = r.status_code == 200 and r.json().get("escrow") == "held"
    step(ok, "payment verified -> escrow HELD")

    r = client.post("/api/v1/marketplace/orders/%s/confirm" % order_id, headers=hdr())
    ok = r.status_code == 200 and int(r.json().get("escrow_released") or 0) >= 1
    step(ok, "delivery confirmed -> escrow RELEASED to seller")

    r = client.get("/api/v1/marketplace/notifications", headers=hdr())
    titles = " | ".join(n["title"] for n in r.json().get("notifications", []))
    ok = r.status_code == 200 and r.json().get("count", 0) >= 2
    step(ok, "notifications for buyer: %s [%s]" % (r.json().get("count"), titles[:90]))

    failed = [lbl for okk, lbl in results if not okk]
    print("")
    print(
        "E2E RESULT: %d/%d passed%s"
        % (
            len(results) - len(failed),
            len(results),
            ("" if not failed else "  FAILED: " + "; ".join(failed)),
        ),
        flush=True,
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
