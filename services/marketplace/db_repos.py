"""Real database-backed repositories for the marketplace catalog.

All reads/writes go through the runtime database (SQLite locally,
Postgres in production). No demo data anywhere.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.hub import hub

from .models import (
    MarketplaceProduct,
    MarketplaceProductStatus,
    MarketplaceSeller,
)


def _default_session_factory() -> Callable[[], Iterator]:
    return hub.get_session()


class DbSellerRepo:
    """Reads sellers from the marketplace_sellers table."""

    def __init__(self, session_factory: Callable[[], Iterator] | None = None) -> None:
        self._sf = session_factory or _default_session_factory

    @contextmanager
    def session(self):
        yield self._sf()

    def get_seller(self, seller_id: str):
        with self.session() as s:
            return s.get(MarketplaceSeller, seller_id)

    def get_seller_by_user(self, user_id: str):
        with self.session() as s:
            return s.execute(
                select(MarketplaceSeller).where(MarketplaceSeller.user_id == user_id)
            ).scalar_one_or_none()

    def list_sellers(self, limit: int = 200):
        with self.session() as s:
            return list(
                s.execute(
                    select(MarketplaceSeller)
                    .order_by(MarketplaceSeller.created_at.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )


class DbProductRepo:
    """Reads/writes products from the marketplace_products table (seller eager-loaded)."""

    def __init__(self, session_factory: Callable[[], Iterator] | None = None) -> None:
        self._sf = session_factory or _default_session_factory

    @contextmanager
    def session(self):
        yield self._sf()

    def get_product(self, product_id: str):
        with self.session() as s:
            return s.execute(
                select(MarketplaceProduct)
                .options(joinedload(MarketplaceProduct.seller))
                .where(MarketplaceProduct.id == product_id)
            ).scalar_one_or_none()

    def list_products(
        self,
        category: str | None = None,
        organic_only: bool = False,
        query: str | None = None,
        limit: int = 50,
    ):
        with self.session() as s:
            stmt = (
                select(MarketplaceProduct)
                .options(joinedload(MarketplaceProduct.seller))
                .where(
                    MarketplaceProduct.status.in_(
                        [
                            MarketplaceProductStatus.APPROVED,
                            MarketplaceProductStatus.ACTIVE,
                        ]
                    )
                )
            )
            if category:
                stmt = stmt.where(MarketplaceProduct.category == category)
            if organic_only:
                stmt = stmt.where(MarketplaceProduct.organic.is_(True))
            if query:
                stmt = stmt.where(MarketplaceProduct.name.ilike(f"%{query}%"))
            stmt = stmt.order_by(MarketplaceProduct.created_at.desc()).limit(limit)
            return list(s.execute(stmt).scalars().all())

    def create_product(
        self,
        seller_id: str,
        name: str,
        category: str,
        price: float,
        village_id: str,
        description: str | None = None,
        stock: int = 0,
        unit: str = "kg",
        status: str = "draft",
        organic: bool = False,
    ) -> MarketplaceProduct:
        import uuid

        with self.session() as s:
            row = MarketplaceProduct(
                id=str(uuid.uuid4()),
                seller_id=seller_id,
                name=name,
                slug=f"p-{uuid.uuid4().hex[:16]}",
                description=description,
                category=category,
                price=price,
                stock=stock,
                unit=unit,
                village_id=village_id,
                organic=organic,
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return row

    def update_stock(self, product_id: str, delta: int) -> bool:
        with self.session() as s:
            row = s.get(MarketplaceProduct, product_id)
            if row is None:
                return False
            row.stock = int((row.stock or 0) + delta)
            s.commit()
            return True


class DbOrderRepo:
    """Writes/reads marketplace orders to the ``com_orders`` table.

    Mirrors the subset of ``OrderManager``'s persistence surface that the
    demo path keeps in memory, so orders survive restarts and are queryable
    across services (``services/commerce`` already owns ``ComOrder``; this
    repo only *reads* it here, never mutates the commerce domain).
    """

    def __init__(self, session_factory: Callable[[], Iterator] | None = None) -> None:
        self._sf = session_factory or _default_session_factory

    @contextmanager
    def session(self):
        yield self._sf()

    def create_order(
        self,
        *,
        order_number: str,
        buyer_id: str,
        village_id: str,
        subtotal: float,
        total: float,
        product_id: str | None = None,
        status: str = "pending",
        idempotency_key: str | None = None,
    ):
        import uuid

        from database.models import ComOrder

        with self.session() as s:
            row = ComOrder(
                id=str(uuid.uuid4()),
                order_number=order_number,
                buyer_id=buyer_id,
                seller_id=None,
                status=status,
                subtotal=subtotal,
                total=total,
                currency="IRR",
                idempotency_key=idempotency_key,
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return row

    def get_order(self, order_id: str):
        from database.models import ComOrder

        with self.session() as s:
            return s.get(ComOrder, order_id)

    def list_orders(self, status: str | None = None, limit: int = 50):
        from database.models import ComOrder

        with self.session() as s:
            stmt = select(ComOrder).order_by(ComOrder.created_at.desc()).limit(limit)
            if status:
                stmt = stmt.where(ComOrder.status == status)
            return list(s.execute(stmt).scalars().all())

    def update_order(self, order_id: str, *, status: str) -> bool:
        from database.models import ComOrder

        with self.session() as s:
            row = s.get(ComOrder, order_id)
            if row is None:
                return False
            row.status = status
            s.commit()
            return True
