"""Marketplace repositories — database-backed persistence for marketplaces and members."""

from datetime import datetime

from sqlalchemy.orm import Session

from services.marketplace.models import Marketplace, MarketplaceMember, MarketplaceSeller


class MarketplaceRepository:
    """Repository for marketplaces."""

    def __init__(self, db: Session):
        self.db = db

    def create_marketplace(self, data: dict) -> Marketplace:
        marketplace = Marketplace(**data)
        self.db.add(marketplace)
        self.db.commit()
        self.db.refresh(marketplace)
        return marketplace

    def get_marketplace(self, marketplace_id: str) -> Marketplace | None:
        return self.db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()

    def get_marketplace_by_slug(self, slug: str) -> Marketplace | None:
        return self.db.query(Marketplace).filter(Marketplace.slug == slug).first()

    def list_marketplaces(
        self,
        marketplace_type: str | None = None,
        village_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ):
        query = self.db.query(Marketplace)
        if marketplace_type:
            query = query.filter(Marketplace.marketplace_type == marketplace_type)
        if village_id:
            query = query.filter(Marketplace.village_id == village_id)
        if status:
            query = query.filter(Marketplace.status == status)
        return query.limit(limit).all()

    def update_marketplace(self, marketplace_id: str, **kwargs) -> Marketplace | None:
        marketplace = self.get_marketplace(marketplace_id)
        if not marketplace:
            return None
        for key, value in kwargs.items():
            if hasattr(marketplace, key):
                setattr(marketplace, key, value)
        marketplace.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(marketplace)
        return marketplace


class MarketplaceMemberRepository:
    """Repository for marketplace members."""

    def __init__(self, db: Session):
        self.db = db

    def add_member(self, data: dict) -> MarketplaceMember:
        member = MarketplaceMember(**data)
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_member(self, member_id: str) -> MarketplaceMember | None:
        return self.db.query(MarketplaceMember).filter(MarketplaceMember.id == member_id).first()

    def list_members(self, marketplace_id: str) -> list[MarketplaceMember]:
        return (
            self.db.query(MarketplaceMember)
            .filter(MarketplaceMember.marketplace_id == marketplace_id)
            .all()
        )

    def get_member_by_user(self, marketplace_id: str, user_id: str) -> MarketplaceMember | None:
        return (
            self.db.query(MarketplaceMember)
            .filter(
                MarketplaceMember.marketplace_id == marketplace_id,
                MarketplaceMember.user_id == user_id,
            )
            .first()
        )


class MarketplaceShopRepository:
    """Repository for shops (sellers) under marketplaces."""

    def __init__(self, db: Session):
        self.db = db

    def create_shop(self, data: dict) -> MarketplaceSeller:
        shop = MarketplaceSeller(**data)
        self.db.add(shop)
        self.db.commit()
        self.db.refresh(shop)
        return shop

    def list_shops(self, marketplace_id: str, limit: int = 50) -> list[MarketplaceSeller]:
        return (
            self.db.query(MarketplaceSeller)
            .filter(MarketplaceSeller.marketplace_id == marketplace_id)
            .limit(limit)
            .all()
        )

    def get_shop_by_user(self, marketplace_id: str, user_id: str) -> MarketplaceSeller | None:
        return (
            self.db.query(MarketplaceSeller)
            .filter(
                MarketplaceSeller.marketplace_id == marketplace_id,
                MarketplaceSeller.user_id == user_id,
            )
            .first()
        )
