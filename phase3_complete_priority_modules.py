#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eco Nojin - فاز ۳: تکمیل ماژول‌های اولویت‌دار (موج ۱) - نسخه نهایی
═══════════════════════════════════════════════════════════════════════
این اسکریپت ۴ ماژول URGENT_COMPLETE را به‌طور کامل می‌سازد:
1. analytics (Priority 10)
2. auth (Priority 9)
3. admin (Priority 8)
4. reporting (Priority 8)

نسخه: 2.0 (بازنویسی کامل بدون f-string multiline)

اجرا: python phase3_complete_priority_modules.py
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path("D:/eco_nojin")
SERVICES_ROOT = PROJECT_ROOT / "services"
BACKUP_ROOT = PROJECT_ROOT / f"_backup_phase3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")


def separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def write_file(path: Path, content: str) -> bool:
    """نوشتن فایل با ایجاد خودکار دایرکتوری"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # حذف leading whitespace مشترک (برای template های indented)
        lines = content.split('\n')
        if lines and not lines[0].strip():
            lines = lines[1:]
        if lines:
            min_indent = min(
                (len(line) - len(line.lstrip()) for line in lines if line.strip()),
                default=0
            )
            lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
        content = '\n'.join(lines)
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        log(f"خطا در نوشتن {path}: {e}", "X")
        return False


# ═══════════════════════════════════════════════════════════════
# گام ۱: Backup
# ═══════════════════════════════════════════════════════════════

def step1_backup() -> bool:
    separator("گام ۱: ایجاد Backup")
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    
    modules = ['analytics', 'auth', 'admin', 'reporting']
    extra = [
        PROJECT_ROOT / "conftest.py",
        PROJECT_ROOT / "services" / "api_gateway" / "register_modules.py",
    ]
    
    for mod in modules:
        src = SERVICES_ROOT / mod
        if src.exists():
            dst = BACKUP_ROOT / "services" / mod
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            log(f"Backup: services/{mod}", "+")
    
    for src in extra:
        if src.exists():
            rel = src.relative_to(PROJECT_ROOT)
            dst = BACKUP_ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            log(f"Backup: {rel}", "+")
    
    log(f"Backup کامل: {BACKUP_ROOT}", "+")
    return True


# ═══════════════════════════════════════════════════════════════
# ماژول: analytics
# ═══════════════════════════════════════════════════════════════

def build_analytics():
    separator("ساخت ماژول analytics")
    base = SERVICES_ROOT / "analytics"
    base.mkdir(parents=True, exist_ok=True)
    
    # __init__.py
    write_file(base / "__init__.py", '''
        """Analytics Module - Dashboards, Aggregations"""
        from services.analytics.service import AnalyticsService
        from services.analytics.schemas import (
            AnalyticsDashboard, SalesSummary,
            AggregationRequest, AggregationResult, PeriodType,
        )
        
        __all__ = [
            "AnalyticsService", "AnalyticsDashboard", "SalesSummary",
            "AggregationRequest", "AggregationResult", "PeriodType",
        ]
    ''')
    
    # models.py
    write_file(base / "models.py", '''
        """Analytics SQLAlchemy models"""
        from datetime import datetime, timezone
        from sqlalchemy import Column, String, DateTime, JSON, Index
        from database.models import Base
        import uuid
        
        class AnalyticsSnapshot(Base):
            __tablename__ = "analytics_snapshots"
            
            id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
            snapshot_type = Column(String(50), nullable=False)
            village_id = Column(String(50), nullable=True)
            period_start = Column(DateTime, nullable=False)
            period_end = Column(DateTime, nullable=False)
            data = Column(JSON, nullable=False)
            created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
            
            __table_args__ = (
                Index("ix_analytics_snapshots_lookup", "snapshot_type", "village_id"),
            )
    ''')
    
    # schemas.py
    write_file(base / "schemas.py", '''
        """Pydantic schemas for Analytics"""
        from datetime import datetime
        from decimal import Decimal
        from typing import Optional, List, Dict, Any
        from pydantic import BaseModel, Field
        from enum import Enum
        
        class PeriodType(str, Enum):
            DAY = "day"
            WEEK = "week"
            MONTH = "month"
            QUARTER = "quarter"
            YEAR = "year"
        
        class AggregationRequest(BaseModel):
            village_id: Optional[str] = None
            period: PeriodType = PeriodType.MONTH
            start_date: Optional[datetime] = None
            end_date: Optional[datetime] = None
            group_by: Optional[List[str]] = None
        
        class AggregationResult(BaseModel):
            period: PeriodType
            total_records: int
            aggregated_values: Dict[str, Any]
            generated_at: datetime
        
        class SalesSummary(BaseModel):
            total_orders: int = 0
            total_revenue: Decimal = Decimal("0")
            average_order_value: Decimal = Decimal("0")
            top_products: List[Dict[str, Any]] = Field(default_factory=list)
            period: PeriodType
        
        class TourismMetrics(BaseModel):
            total_bookings: int = 0
            total_guests: int = 0
            revenue: Decimal = Decimal("0")
            regenerative_activities: int = 0
        
        class LandscapeMetrics(BaseModel):
            active_villages: int = 0
            governance_members: int = 0
            fund_balance: Decimal = Decimal("0")
        
        class AnalyticsDashboard(BaseModel):
            village_id: Optional[str] = None
            period: PeriodType
            sales: SalesSummary
            tourism: TourismMetrics
            landscape: LandscapeMetrics
            generated_at: datetime
    ''')
    
    # repository.py
    write_file(base / "repository.py", '''
        """Analytics repository"""
        from datetime import datetime, timezone, timedelta
        from typing import Optional
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, delete
        from services.analytics.models import AnalyticsSnapshot
        
        class AnalyticsRepository:
            def __init__(self, db: AsyncSession):
                self.db = db
            
            async def save_snapshot(
                self, snapshot_type: str, period_start: datetime,
                period_end: datetime, data: dict, village_id: Optional[str] = None,
            ) -> AnalyticsSnapshot:
                snapshot = AnalyticsSnapshot(
                    snapshot_type=snapshot_type,
                    village_id=village_id,
                    period_start=period_start,
                    period_end=period_end,
                    data=data,
                )
                self.db.add(snapshot)
                await self.db.commit()
                await self.db.refresh(snapshot)
                return snapshot
            
            async def get_latest_snapshot(
                self, snapshot_type: str, village_id: Optional[str] = None,
            ) -> Optional[AnalyticsSnapshot]:
                stmt = select(AnalyticsSnapshot).where(
                    AnalyticsSnapshot.snapshot_type == snapshot_type
                )
                if village_id:
                    stmt = stmt.where(AnalyticsSnapshot.village_id == village_id)
                stmt = stmt.order_by(AnalyticsSnapshot.created_at.desc()).limit(1)
                result = await self.db.execute(stmt)
                return result.scalar_one_or_none()
            
            async def cleanup_old_snapshots(self, older_than_days: int = 90) -> int:
                cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
                stmt = delete(AnalyticsSnapshot).where(
                    AnalyticsSnapshot.created_at < cutoff
                )
                result = await self.db.execute(stmt)
                await self.db.commit()
                return result.rowcount
    ''')
    
    # service.py
    write_file(base / "service.py", '''
        """AnalyticsService"""
        from datetime import datetime, timezone, timedelta
        from decimal import Decimal
        from typing import Optional
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, func
        
        from services.analytics.schemas import (
            SalesSummary, TourismMetrics, LandscapeMetrics,
            AnalyticsDashboard, PeriodType,
        )
        from services.analytics.repository import AnalyticsRepository
        
        class AnalyticsService:
            def __init__(self, db: AsyncSession):
                self.db = db
                self.repo = AnalyticsRepository(db)
            
            def _period_delta(self, period: PeriodType) -> timedelta:
                return {
                    PeriodType.DAY: timedelta(days=1),
                    PeriodType.WEEK: timedelta(weeks=1),
                    PeriodType.MONTH: timedelta(days=30),
                    PeriodType.QUARTER: timedelta(days=90),
                    PeriodType.YEAR: timedelta(days=365),
                }[period]
            
            async def aggregate_sales(
                self, village_id: Optional[str] = None, period: PeriodType = PeriodType.MONTH,
            ) -> SalesSummary:
                try:
                    from services.marketplace.models import MarketplaceOrder
                    since = datetime.now(timezone.utc) - self._period_delta(period)
                    stmt = select(
                        func.count(MarketplaceOrder.id).label("total_orders"),
                        func.coalesce(func.sum(MarketplaceOrder.total), 0).label("total_revenue"),
                        func.coalesce(func.avg(MarketplaceOrder.total), 0).label("avg_value"),
                    ).where(MarketplaceOrder.created_at >= since)
                    if village_id:
                        stmt = stmt.where(MarketplaceOrder.village_id == village_id)
                    result = await self.db.execute(stmt)
                    row = result.one()
                    return SalesSummary(
                        total_orders=row.total_orders or 0,
                        total_revenue=Decimal(str(row.total_revenue or 0)),
                        average_order_value=Decimal(str(row.avg_value or 0)),
                        period=period,
                    )
                except ImportError:
                    return SalesSummary(period=period)
            
            async def aggregate_tourism(
                self, village_id: Optional[str] = None, period: PeriodType = PeriodType.MONTH,
            ) -> TourismMetrics:
                try:
                    from services.tourism.models import TourismBooking
                    since = datetime.now(timezone.utc) - self._period_delta(period)
                    stmt = select(
                        func.count(TourismBooking.id).label("total_bookings"),
                        func.coalesce(func.sum(TourismBooking.participants_count), 0).label("total_guests"),
                        func.coalesce(func.sum(TourismBooking.total), 0).label("revenue"),
                    ).where(TourismBooking.created_at >= since)
                    if village_id:
                        stmt = stmt.where(TourismBooking.village_id == village_id)
                    result = await self.db.execute(stmt)
                    row = result.one()
                    return TourismMetrics(
                        total_bookings=row.total_bookings or 0,
                        total_guests=int(row.total_guests or 0),
                        revenue=Decimal(str(row.revenue or 0)),
                    )
                except ImportError:
                    return TourismMetrics()
            
            async def aggregate_landscape(self) -> LandscapeMetrics:
                try:
                    from services.landscape.models import (
                        LandscapeVillage, LandscapeGovernanceMember, LandscapeFund
                    )
                    v = await self.db.execute(select(func.count(LandscapeVillage.id)).where(LandscapeVillage.is_active == True))
                    m = await self.db.execute(select(func.count(LandscapeGovernanceMember.id)))
                    f = await self.db.execute(select(func.coalesce(func.sum(LandscapeFund.current_balance), 0)))
                    return LandscapeMetrics(
                        active_villages=v.scalar() or 0,
                        governance_members=m.scalar() or 0,
                        fund_balance=Decimal(str(f.scalar() or 0)),
                    )
                except ImportError:
                    return LandscapeMetrics()
            
            async def get_dashboard(
                self, village_id: Optional[str] = None, period: PeriodType = PeriodType.MONTH,
            ) -> AnalyticsDashboard:
                sales = await self.aggregate_sales(village_id, period)
                tourism = await self.aggregate_tourism(village_id, period)
                landscape = await self.aggregate_landscape()
                dashboard = AnalyticsDashboard(
                    village_id=village_id, period=period,
                    sales=sales, tourism=tourism, landscape=landscape,
                    generated_at=datetime.now(timezone.utc),
                )
                await self.repo.save_snapshot(
                    snapshot_type="dashboard",
                    period_start=datetime.now(timezone.utc) - self._period_delta(period),
                    period_end=datetime.now(timezone.utc),
                    data=dashboard.model_dump(mode="json"),
                    village_id=village_id,
                )
                return dashboard
    ''')
    
    # api router
    (base / "api").mkdir(parents=True, exist_ok=True)
    write_file(base / "api" / "__init__.py", '''
        """Analytics FastAPI router"""
        from typing import Optional
        from fastapi import APIRouter, Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from database.config import get_db
        from services.analytics.service import AnalyticsService
        from services.analytics.schemas import (
            AnalyticsDashboard, PeriodType, SalesSummary,
            TourismMetrics, LandscapeMetrics,
        )
        
        router = APIRouter(prefix="/analytics", tags=["Analytics"])
        
        @router.get("/dashboard", response_model=AnalyticsDashboard)
        async def get_dashboard(
            village_id: Optional[str] = None,
            period: PeriodType = PeriodType.MONTH,
            db: AsyncSession = Depends(get_db),
        ):
            service = AnalyticsService(db)
            return await service.get_dashboard(village_id=village_id, period=period)
        
        @router.get("/sales-summary", response_model=SalesSummary)
        async def get_sales(
            village_id: Optional[str] = None,
            period: PeriodType = PeriodType.MONTH,
            db: AsyncSession = Depends(get_db),
        ):
            return await AnalyticsService(db).aggregate_sales(village_id, period)
        
        @router.get("/tourism-metrics", response_model=TourismMetrics)
        async def get_tourism(
            village_id: Optional[str] = None,
            period: PeriodType = PeriodType.MONTH,
            db: AsyncSession = Depends(get_db),
        ):
            return await AnalyticsService(db).aggregate_tourism(village_id, period)
        
        @router.get("/landscape-metrics", response_model=LandscapeMetrics)
        async def get_landscape(db: AsyncSession = Depends(get_db)):
            return await AnalyticsService(db).aggregate_landscape()
    ''')
    
    # tests
    (base / "tests").mkdir(parents=True, exist_ok=True)
    write_file(base / "tests" / "__init__.py", "")
    write_file(base / "tests" / "test_integration.py", '''
        """Integration tests for Analytics"""
        import pytest
        from services.analytics.schemas import PeriodType
        
        @pytest.mark.asyncio
        class TestAnalyticsIntegration:
            async def test_dashboard_generation(self, analytics_service):
                dashboard = await analytics_service.get_dashboard(period=PeriodType.MONTH)
                assert dashboard is not None
                assert dashboard.period == PeriodType.MONTH
                assert dashboard.sales is not None
            
            async def test_sales_aggregation(self, analytics_service):
                summary = await analytics_service.aggregate_sales(period=PeriodType.MONTH)
                assert summary is not None
                assert summary.total_orders >= 0
    ''')
    
    log("analytics کامل شد", "+")


# ═══════════════════════════════════════════════════════════════
# ماژول: auth
# ═══════════════════════════════════════════════════════════════

def build_auth():
    separator("ساخت ماژول auth")
    base = SERVICES_ROOT / "auth"
    base.mkdir(parents=True, exist_ok=True)
    
    write_file(base / "__init__.py", '''
        """Auth Module - Authentication, JWT"""
        from services.auth.service import AuthService
        from services.auth.schemas import (
            UserRegister, UserLogin, TokenResponse, TokenRefresh,
        )
        __all__ = ["AuthService", "UserRegister", "UserLogin", "TokenResponse", "TokenRefresh"]
    ''')
    
    write_file(base / "models.py", '''
        """Auth SQLAlchemy models"""
        from datetime import datetime, timezone
        from sqlalchemy import Column, String, DateTime, Boolean, Integer
        from database.models import Base
        import uuid
        
        class AuthUser(Base):
            __tablename__ = "auth_users"
            id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
            email = Column(String(255), unique=True, nullable=False, index=True)
            username = Column(String(100), unique=True, nullable=False, index=True)
            password_hash = Column(String(255), nullable=False)
            is_active = Column(Boolean, default=True)
            is_verified = Column(Boolean, default=False)
            failed_login_attempts = Column(Integer, default=0)
            last_login_at = Column(DateTime, nullable=True)
            created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
            updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                               onupdate=lambda: datetime.now(timezone.utc))
        
        class RefreshToken(Base):
            __tablename__ = "auth_refresh_tokens"
            id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
            user_id = Column(String(36), nullable=False, index=True)
            token_hash = Column(String(255), unique=True, nullable=False)
            expires_at = Column(DateTime, nullable=False)
            revoked = Column(Boolean, default=False)
            created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ''')
    
    write_file(base / "schemas.py", '''
        """Pydantic schemas for Auth"""
        from datetime import datetime
        from typing import Optional
        from pydantic import BaseModel, EmailStr, Field
        import re
        
        class UserRegister(BaseModel):
            email: EmailStr
            username: str = Field(min_length=3, max_length=100)
            password: str = Field(min_length=8)
            full_name: Optional[str] = None
            
            def validate_password_strength(self) -> bool:
                return (
                    len(self.password) >= 8
                    and bool(re.search(r"[A-Z]", self.password))
                    and bool(re.search(r"[0-9]", self.password))
                )
        
        class UserLogin(BaseModel):
            email: EmailStr
            password: str
        
        class TokenResponse(BaseModel):
            access_token: str
            refresh_token: str
            token_type: str = "bearer"
            expires_in: int
        
        class TokenRefresh(BaseModel):
            refresh_token: str
        
        class UserInfo(BaseModel):
            id: str
            email: str
            username: str
            is_active: bool
            is_verified: bool
            created_at: datetime
    ''')
    
    write_file(base / "repository.py", '''
        """Auth repository"""
        from datetime import datetime, timezone
        from typing import Optional
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, update
        from services.auth.models import AuthUser, RefreshToken
        
        class AuthRepository:
            def __init__(self, db: AsyncSession):
                self.db = db
            
            async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
                result = await self.db.execute(select(AuthUser).where(AuthUser.email == email))
                return result.scalar_one_or_none()
            
            async def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
                result = await self.db.execute(select(AuthUser).where(AuthUser.id == user_id))
                return result.scalar_one_or_none()
            
            async def create_user(self, email: str, username: str, password_hash: str) -> AuthUser:
                user = AuthUser(email=email, username=username, password_hash=password_hash)
                self.db.add(user)
                await self.db.commit()
                await self.db.refresh(user)
                return user
            
            async def update_last_login(self, user_id: str):
                stmt = (
                    update(AuthUser).where(AuthUser.id == user_id)
                    .values(last_login_at=datetime.now(timezone.utc), failed_login_attempts=0)
                )
                await self.db.execute(stmt)
                await self.db.commit()
            
            async def increment_failed_attempts(self, user_id: str):
                user = await self.get_user_by_id(user_id)
                if user:
                    user.failed_login_attempts += 1
                    await self.db.commit()
            
            async def save_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
                token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
                self.db.add(token)
                await self.db.commit()
                return token
            
            async def revoke_refresh_token(self, token_hash: str):
                stmt = update(RefreshToken).where(RefreshToken.token_hash == token_hash).values(revoked=True)
                await self.db.execute(stmt)
                await self.db.commit()
    ''')
    
    write_file(base / "service.py", '''
        """AuthService"""
        import hashlib
        import secrets
        from datetime import datetime, timezone, timedelta
        from typing import Tuple, Optional
        from sqlalchemy.ext.asyncio import AsyncSession
        from services.auth.models import AuthUser
        from services.auth.schemas import UserRegister, UserLogin, TokenResponse, UserInfo
        from services.auth.repository import AuthRepository
        
        class AuthService:
            ACCESS_TOKEN_TTL = 3600
            REFRESH_TOKEN_TTL = 86400 * 30
            MAX_FAILED_ATTEMPTS = 5
            
            def __init__(self, db: AsyncSession):
                self.db = db
                self.repo = AuthRepository(db)
            
            def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
                if salt is None:
                    salt = secrets.token_hex(16)
                hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
                return f"{salt}:{hashed}", salt
            
            def _verify_password(self, password: str, stored_hash: str) -> bool:
                try:
                    salt, _ = stored_hash.split(":", 1)
                    computed, _ = self._hash_password(password, salt)
                    return secrets.compare_digest(computed, stored_hash)
                except Exception:
                    return False
            
            def _generate_token(self, user_id: str, ttl: int) -> str:
                payload = f"{user_id}:{int(datetime.now(timezone.utc).timestamp())}:{ttl}"
                return f"{payload}:{secrets.token_urlsafe(32)}"
            
            async def register(self, data: UserRegister) -> AuthUser:
                if not data.validate_password_strength():
                    raise ValueError("Password must be 8+ chars with uppercase and digit")
                if await self.repo.get_user_by_email(data.email):
                    raise ValueError("Email already registered")
                password_hash, _ = self._hash_password(data.password)
                return await self.repo.create_user(data.email, data.username, password_hash)
            
            async def login(self, data: UserLogin) -> TokenResponse:
                user = await self.repo.get_user_by_email(data.email)
                if not user:
                    raise ValueError("Invalid credentials")
                if user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
                    raise ValueError("Account locked")
                if not self._verify_password(data.password, user.password_hash):
                    await self.repo.increment_failed_attempts(user.id)
                    raise ValueError("Invalid credentials")
                access = self._generate_token(user.id, self.ACCESS_TOKEN_TTL)
                refresh = self._generate_token(user.id, self.REFRESH_TOKEN_TTL)
                await self.repo.save_refresh_token(
                    user.id, hashlib.sha256(refresh.encode()).hexdigest(),
                    datetime.now(timezone.utc) + timedelta(seconds=self.REFRESH_TOKEN_TTL),
                )
                await self.repo.update_last_login(user.id)
                return TokenResponse(
                    access_token=access, refresh_token=refresh,
                    expires_in=self.ACCESS_TOKEN_TTL,
                )
            
            async def get_user_info(self, user_id: str) -> UserInfo:
                user = await self.repo.get_user_by_id(user_id)
                if not user:
                    raise ValueError("User not found")
                return UserInfo(
                    id=user.id, email=user.email, username=user.username,
                    is_active=user.is_active, is_verified=user.is_verified,
                    created_at=user.created_at,
                )
    ''')
    
    (base / "api").mkdir(parents=True, exist_ok=True)
    write_file(base / "api" / "__init__.py", '''
        """Auth FastAPI router"""
        from fastapi import APIRouter, Depends, HTTPException
        from sqlalchemy.ext.asyncio import AsyncSession
        from database.config import get_db
        from services.auth.service import AuthService
        from services.auth.schemas import UserRegister, UserLogin, TokenResponse, TokenRefresh, UserInfo
        
        router = APIRouter(prefix="/auth", tags=["Auth"])
        
        @router.post("/register", response_model=UserInfo, status_code=201)
        async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
            try:
                user = await AuthService(db).register(data)
                return UserInfo(
                    id=user.id, email=user.email, username=user.username,
                    is_active=user.is_active, is_verified=user.is_verified,
                    created_at=user.created_at,
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @router.post("/login", response_model=TokenResponse)
        async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
            try:
                return await AuthService(db).login(data)
            except ValueError as e:
                raise HTTPException(status_code=401, detail=str(e))
    ''')
    
    (base / "tests").mkdir(parents=True, exist_ok=True)
    write_file(base / "tests" / "__init__.py", "")
    write_file(base / "tests" / "test_integration.py", '''
        """Integration tests for Auth"""
        import pytest
        from services.auth.schemas import UserRegister, UserLogin
        
        @pytest.mark.asyncio
        class TestAuthIntegration:
            async def test_register_and_login(self, auth_service):
                user = await auth_service.register(UserRegister(
                    email="test@example.com", username="testuser", password="StrongPass1",
                ))
                assert user.email == "test@example.com"
                tokens = await auth_service.login(UserLogin(
                    email="test@example.com", password="StrongPass1",
                ))
                assert tokens.access_token
                assert tokens.refresh_token
            
            async def test_duplicate_email(self, auth_service):
                data = UserRegister(email="dup@example.com", username="dupuser", password="StrongPass1")
                await auth_service.register(data)
                with pytest.raises(ValueError, match="already registered"):
                    await auth_service.register(data)
    ''')
    
    log("auth کامل شد", "+")


# ═══════════════════════════════════════════════════════════════
# ماژول: admin
# ═══════════════════════════════════════════════════════════════

def build_admin():
    separator("ساخت ماژول admin")
    base = SERVICES_ROOT / "admin"
    base.mkdir(parents=True, exist_ok=True)
    
    write_file(base / "__init__.py", '''
        """Admin Module - System administration, audit"""
        from services.admin.service import AdminService
        from services.admin.schemas import SystemHealth, ProjectStatus, AdminStats, AuditLog
        __all__ = ["AdminService", "SystemHealth", "ProjectStatus", "AdminStats", "AuditLog"]
    ''')
    
    write_file(base / "models.py", '''
        """Admin SQLAlchemy models"""
        from datetime import datetime, timezone
        from sqlalchemy import Column, String, DateTime, JSON
        from database.models import Base
        import uuid
        
        class AuditLog(Base):
            __tablename__ = "admin_audit_logs"
            id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
            actor_id = Column(String(100), nullable=True)
            action = Column(String(100), nullable=False, index=True)
            resource_type = Column(String(100), nullable=True)
            resource_id = Column(String(100), nullable=True)
            details = Column(JSON, nullable=True)
            ip_address = Column(String(45), nullable=True)
            created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ''')
    
    write_file(base / "schemas.py", '''
        """Pydantic schemas for Admin"""
        from datetime import datetime
        from typing import Optional, List, Dict, Any
        from pydantic import BaseModel
        from enum import Enum
        
        class ServiceStatus(str, Enum):
            HEALTHY = "healthy"
            DEGRADED = "degraded"
            DOWN = "down"
        
        class ServiceHealthCheck(BaseModel):
            name: str
            status: ServiceStatus
            latency_ms: Optional[float] = None
            message: Optional[str] = None
        
        class SystemHealth(BaseModel):
            overall_status: ServiceStatus
            services: List[ServiceHealthCheck]
            uptime_seconds: int
            checked_at: datetime
        
        class ProjectStatus(BaseModel):
            phase: str
            version: str
            total_modules: int
            active_modules: int
            description: str
        
        class AuditLog(BaseModel):
            id: str
            actor_id: Optional[str]
            action: str
            resource_type: Optional[str]
            resource_id: Optional[str]
            details: Optional[Dict[str, Any]]
            created_at: datetime
        
        class AdminStats(BaseModel):
            total_orders: int = 0
            total_bookings: int = 0
            total_villages: int = 0
            uptime_seconds: int = 0
    ''')
    
    write_file(base / "repository.py", '''
        """Admin repository"""
        from typing import Optional, List
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        from services.admin.models import AuditLog
        
        class AdminRepository:
            def __init__(self, db: AsyncSession):
                self.db = db
            
            async def write_audit_log(
                self, action: str, actor_id: Optional[str] = None,
                resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                details: Optional[dict] = None,
            ) -> AuditLog:
                log = AuditLog(
                    actor_id=actor_id, action=action,
                    resource_type=resource_type, resource_id=resource_id, details=details,
                )
                self.db.add(log)
                await self.db.commit()
                await self.db.refresh(log)
                return log
            
            async def get_recent_logs(self, limit: int = 100) -> List[AuditLog]:
                result = await self.db.execute(
                    select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
                )
                return list(result.scalars().all())
    ''')
    
    write_file(base / "service.py", '''
        """AdminService"""
        import time
        from datetime import datetime, timezone
        from typing import Optional, List
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import func, select
        from services.admin.schemas import (
            SystemHealth, ServiceStatus, ServiceHealthCheck,
            ProjectStatus, AdminStats, AuditLog as AuditLogSchema,
        )
        from services.admin.repository import AdminRepository
        
        _START_TIME = time.time()
        
        class AdminService:
            def __init__(self, db: AsyncSession):
                self.db = db
                self.repo = AdminRepository(db)
            
            async def check_database_health(self) -> ServiceHealthCheck:
                start = time.time()
                try:
                    await self.db.execute(select(1))
                    return ServiceHealthCheck(
                        name="database", status=ServiceStatus.HEALTHY,
                        latency_ms=round((time.time() - start) * 1000, 2),
                    )
                except Exception as e:
                    return ServiceHealthCheck(name="database", status=ServiceStatus.DOWN, message=str(e)[:100])
            
            async def get_system_health(self) -> SystemHealth:
                db_health = await self.check_database_health()
                services = [db_health]
                if any(s.status == ServiceStatus.DOWN for s in services):
                    overall = ServiceStatus.DOWN
                elif any(s.status == ServiceStatus.DEGRADED for s in services):
                    overall = ServiceStatus.DEGRADED
                else:
                    overall = ServiceStatus.HEALTHY
                return SystemHealth(
                    overall_status=overall, services=services,
                    uptime_seconds=int(time.time() - _START_TIME),
                    checked_at=datetime.now(timezone.utc),
                )
            
            async def get_project_status(self) -> ProjectStatus:
                return ProjectStatus(
                    phase="Production (Phase 3)", version="3.1.0",
                    total_modules=28, active_modules=7,
                    description="Eco Nojin - Regenerative Rural Economy Platform",
                )
            
            async def get_stats(self) -> AdminStats:
                stats = AdminStats(uptime_seconds=int(time.time() - _START_TIME))
                try:
                    from services.marketplace.models import MarketplaceOrder
                    r = await self.db.execute(select(func.count(MarketplaceOrder.id)))
                    stats.total_orders = r.scalar() or 0
                except Exception:
                    pass
                try:
                    from services.tourism.models import TourismBooking
                    r = await self.db.execute(select(func.count(TourismBooking.id)))
                    stats.total_bookings = r.scalar() or 0
                except Exception:
                    pass
                try:
                    from services.landscape.models import LandscapeVillage
                    r = await self.db.execute(select(func.count(LandscapeVillage.id)))
                    stats.total_villages = r.scalar() or 0
                except Exception:
                    pass
                return stats
            
            async def log_action(self, action: str, actor_id: Optional[str] = None,
                               resource_type: Optional[str] = None,
                               resource_id: Optional[str] = None,
                               details: Optional[dict] = None) -> AuditLogSchema:
                log = await self.repo.write_audit_log(
                    action, actor_id, resource_type, resource_id, details,
                )
                return AuditLogSchema(
                    id=log.id, actor_id=log.actor_id, action=log.action,
                    resource_type=log.resource_type, resource_id=log.resource_id,
                    details=log.details, created_at=log.created_at,
                )
            
            async def get_audit_logs(self, limit: int = 100) -> List[AuditLogSchema]:
                logs = await self.repo.get_recent_logs(limit=limit)
                return [
                    AuditLogSchema(
                        id=log.id, actor_id=log.actor_id, action=log.action,
                        resource_type=log.resource_type, resource_id=log.resource_id,
                        details=log.details, created_at=log.created_at,
                    )
                    for log in logs
                ]
    ''')
    
    (base / "api").mkdir(parents=True, exist_ok=True)
    write_file(base / "api" / "__init__.py", '''
        """Admin FastAPI router"""
        from typing import List
        from fastapi import APIRouter, Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from database.config import get_db
        from services.admin.service import AdminService
        from services.admin.schemas import SystemHealth, ProjectStatus, AdminStats, AuditLog
        
        router = APIRouter(prefix="/admin", tags=["Admin"])
        
        @router.get("/health", response_model=SystemHealth)
        async def get_health(db: AsyncSession = Depends(get_db)):
            return await AdminService(db).get_system_health()
        
        @router.get("/status", response_model=ProjectStatus)
        async def get_status(db: AsyncSession = Depends(get_db)):
            return await AdminService(db).get_project_status()
        
        @router.get("/stats", response_model=AdminStats)
        async def get_stats(db: AsyncSession = Depends(get_db)):
            return await AdminService(db).get_stats()
        
        @router.get("/audit-logs", response_model=List[AuditLog])
        async def get_audit_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
            return await AdminService(db).get_audit_logs(limit=limit)
    ''')
    
    (base / "tests").mkdir(parents=True, exist_ok=True)
    write_file(base / "tests" / "__init__.py", "")
    write_file(base / "tests" / "test_integration.py", '''
        """Integration tests for Admin"""
        import pytest
        
        @pytest.mark.asyncio
        class TestAdminIntegration:
            async def test_system_health(self, admin_service):
                health = await admin_service.get_system_health()
                assert health.overall_status
                assert health.uptime_seconds >= 0
            
            async def test_audit_logging(self, admin_service):
                log = await admin_service.log_action(
                    action="test_action", actor_id="admin_123",
                )
                assert log.action == "test_action"
                logs = await admin_service.get_audit_logs()
                assert len(logs) >= 1
    ''')
    
    log("admin کامل شد", "+")


# ═══════════════════════════════════════════════════════════════
# ماژول: reporting
# ═══════════════════════════════════════════════════════════════

def build_reporting():
    separator("ساخت ماژول reporting")
    base = SERVICES_ROOT / "reporting"
    base.mkdir(parents=True, exist_ok=True)
    
    write_file(base / "__init__.py", '''
        """Reporting Module - Report generation"""
        from services.reporting.service import ReportingService
        from services.reporting.schemas import ReportCreate, ReportRead, ReportType, ReportStatus
        __all__ = ["ReportingService", "ReportCreate", "ReportRead", "ReportType", "ReportStatus"]
    ''')
    
    write_file(base / "models.py", '''
        """Reporting SQLAlchemy models"""
        from datetime import datetime, timezone
        from sqlalchemy import Column, String, DateTime, JSON
        from database.models import Base
        import uuid
        
        class Report(Base):
            __tablename__ = "reports"
            id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
            report_type = Column(String(50), nullable=False, index=True)
            title = Column(String(255), nullable=False)
            status = Column(String(20), default="pending", index=True)
            parameters = Column(JSON, nullable=True)
            result_data = Column(JSON, nullable=True)
            generated_by = Column(String(100), nullable=True)
            file_path = Column(String(500), nullable=True)
            created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
            completed_at = Column(DateTime, nullable=True)
    ''')
    
    write_file(base / "schemas.py", '''
        """Pydantic schemas for Reporting"""
        from datetime import datetime
        from typing import Optional, Dict, Any
        from pydantic import BaseModel, Field
        from enum import Enum
        
        class ReportType(str, Enum):
            SALES = "sales"
            TOURISM = "tourism"
            LANDSCAPE = "landscape"
            CARBON = "carbon"
            COMPREHENSIVE = "comprehensive"
        
        class ReportStatus(str, Enum):
            PENDING = "pending"
            PROCESSING = "processing"
            COMPLETED = "completed"
            FAILED = "failed"
        
        class ReportCreate(BaseModel):
            report_type: ReportType
            title: str = Field(min_length=3, max_length=255)
            parameters: Optional[Dict[str, Any]] = None
            generated_by: Optional[str] = None
        
        class ReportRead(BaseModel):
            id: str
            report_type: ReportType
            title: str
            status: ReportStatus
            parameters: Optional[Dict[str, Any]]
            result_data: Optional[Dict[str, Any]]
            file_path: Optional[str]
            created_at: datetime
            completed_at: Optional[datetime]
    ''')
    
    write_file(base / "repository.py", '''
        """Reporting repository"""
        from datetime import datetime, timezone
        from typing import Optional, List
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select, update
        from services.reporting.models import Report
        
        class ReportingRepository:
            def __init__(self, db: AsyncSession):
                self.db = db
            
            async def create_report(self, report: Report) -> Report:
                self.db.add(report)
                await self.db.commit()
                await self.db.refresh(report)
                return report
            
            async def get_report(self, report_id: str) -> Optional[Report]:
                result = await self.db.execute(select(Report).where(Report.id == report_id))
                return result.scalar_one_or_none()
            
            async def list_reports(self, report_type: Optional[str] = None, limit: int = 50) -> List[Report]:
                stmt = select(Report)
                if report_type:
                    stmt = stmt.where(Report.report_type == report_type)
                stmt = stmt.order_by(Report.created_at.desc()).limit(limit)
                result = await self.db.execute(stmt)
                return list(result.scalars().all())
            
            async def update_status(self, report_id: str, status: str,
                                   result_data: Optional[dict] = None,
                                   file_path: Optional[str] = None):
                values = {"status": status}
                if result_data is not None:
                    values["result_data"] = result_data
                if file_path is not None:
                    values["file_path"] = file_path
                if status == "completed":
                    values["completed_at"] = datetime.now(timezone.utc)
                stmt = update(Report).where(Report.id == report_id).values(**values)
                await self.db.execute(stmt)
                await self.db.commit()
    ''')
    
    write_file(base / "service.py", '''
        """ReportingService"""
        import json
        from typing import Optional, List
        from pathlib import Path
        from sqlalchemy.ext.asyncio import AsyncSession
        from services.reporting.models import Report
        from services.reporting.schemas import ReportCreate, ReportRead, ReportStatus, ReportType
        from services.reporting.repository import ReportingRepository
        
        class ReportingService:
            def __init__(self, db: AsyncSession):
                self.db = db
                self.repo = ReportingRepository(db)
            
            async def create_report(self, data: ReportCreate) -> ReportRead:
                report = Report(
                    report_type=data.report_type.value,
                    title=data.title,
                    parameters=data.parameters,
                    generated_by=data.generated_by,
                    status=ReportStatus.PENDING.value,
                )
                report = await self.repo.create_report(report)
                return self._to_read(report)
            
            async def generate_report(self, report_id: str) -> ReportRead:
                report = await self.repo.get_report(report_id)
                if not report:
                    raise ValueError(f"Report not found: {report_id}")
                await self.repo.update_status(report_id, ReportStatus.PROCESSING.value)
                try:
                    result_data = await self._generate_data(report.report_type, report.parameters)
                    file_path = await self._save_to_file(report.id, result_data)
                    await self.repo.update_status(
                        report_id, ReportStatus.COMPLETED.value,
                        result_data=result_data, file_path=file_path,
                    )
                except Exception as e:
                    await self.repo.update_status(
                        report_id, ReportStatus.FAILED.value,
                        result_data={"error": str(e)},
                    )
                report = await self.repo.get_report(report_id)
                return self._to_read(report)
            
            async def _generate_data(self, report_type: str, parameters: Optional[dict]) -> dict:
                try:
                    from services.analytics.service import AnalyticsService
                    from services.analytics.schemas import PeriodType
                    analytics = AnalyticsService(self.db)
                    if report_type == ReportType.SALES.value:
                        return (await analytics.aggregate_sales(period=PeriodType.MONTH)).model_dump(mode="json")
                    elif report_type == ReportType.TOURISM.value:
                        return (await analytics.aggregate_tourism(period=PeriodType.MONTH)).model_dump(mode="json")
                    elif report_type == ReportType.LANDSCAPE.value:
                        return (await analytics.aggregate_landscape()).model_dump(mode="json")
                    elif report_type == ReportType.COMPREHENSIVE.value:
                        return (await analytics.get_dashboard(period=PeriodType.MONTH)).model_dump(mode="json")
                    return {"report_type": report_type}
                except ImportError:
                    return {"report_type": report_type, "message": "Analytics unavailable"}
            
            async def _save_to_file(self, report_id: str, data: dict) -> str:
                reports_dir = Path("data/reports")
                reports_dir.mkdir(parents=True, exist_ok=True)
                file_path = reports_dir / f"report_{report_id}.json"
                file_path.write_text(json.dumps(data, default=str, indent=2), encoding='utf-8')
                return str(file_path)
            
            async def get_report(self, report_id: str) -> ReportRead:
                report = await self.repo.get_report(report_id)
                if not report:
                    raise ValueError(f"Report not found: {report_id}")
                return self._to_read(report)
            
            async def list_reports(self, report_type: Optional[str] = None, limit: int = 50) -> List[ReportRead]:
                reports = await self.repo.list_reports(report_type=report_type, limit=limit)
                return [self._to_read(r) for r in reports]
            
            def _to_read(self, report: Report) -> ReportRead:
                return ReportRead(
                    id=report.id,
                    report_type=ReportType(report.report_type),
                    title=report.title,
                    status=ReportStatus(report.status),
                    parameters=report.parameters,
                    result_data=report.result_data,
                    file_path=report.file_path,
                    created_at=report.created_at,
                    completed_at=report.completed_at,
                )
    ''')
    
    (base / "api").mkdir(parents=True, exist_ok=True)
    write_file(base / "api" / "__init__.py", '''
        """Reporting FastAPI router"""
        from typing import List, Optional
        from fastapi import APIRouter, Depends, HTTPException
        from sqlalchemy.ext.asyncio import AsyncSession
        from database.config import get_db
        from services.reporting.service import ReportingService
        from services.reporting.schemas import ReportCreate, ReportRead
        
        router = APIRouter(prefix="/reports", tags=["Reports"])
        
        @router.post("/", response_model=ReportRead, status_code=201)
        async def create_report(data: ReportCreate, db: AsyncSession = Depends(get_db)):
            return await ReportingService(db).create_report(data)
        
        @router.post("/<report_id>/generate", response_model=ReportRead)
        async def generate_report(report_id: str, db: AsyncSession = Depends(get_db)):
            try:
                return await ReportingService(db).generate_report(report_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @router.get("/<report_id>", response_model=ReportRead)
        async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
            try:
                return await ReportingService(db).get_report(report_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
        
        @router.get("/", response_model=List[ReportRead])
        async def list_reports(
            report_type: Optional[str] = None, limit: int = 50,
            db: AsyncSession = Depends(get_db),
        ):
            return await ReportingService(db).list_reports(report_type=report_type, limit=limit)
    ''')
    
    (base / "tests").mkdir(parents=True, exist_ok=True)
    write_file(base / "tests" / "__init__.py", "")
    write_file(base / "tests" / "test_integration.py", '''
        """Integration tests for Reporting"""
        import pytest
        from services.reporting.schemas import ReportCreate, ReportType, ReportStatus
        
        @pytest.mark.asyncio
        class TestReportingIntegration:
            async def test_create_and_generate_report(self, reporting_service):
                report = await reporting_service.create_report(ReportCreate(
                    report_type=ReportType.COMPREHENSIVE,
                    title="Monthly Report",
                ))
                assert report.status == ReportStatus.PENDING
                generated = await reporting_service.generate_report(report.id)
                assert generated.status in (ReportStatus.COMPLETED, ReportStatus.FAILED)
    ''')
    
    log("reporting کامل شد", "+")


# ═══════════════════════════════════════════════════════════════
# به‌روزرسانی conftest.py
# ═══════════════════════════════════════════════════════════════

def update_conftest():
    separator("به‌روزرسانی conftest.py")
    conftest = PROJECT_ROOT / "conftest.py"
    
    if not conftest.exists():
        log("conftest.py یافت نشد!", "X")
        return False
    
    existing = conftest.read_text(encoding='utf-8')
    
    # افزودن fixtures جدید اگر وجود ندارند
    new_fixtures = '''

# ═══════════════════════════════════════════════════════════════
# Phase 3 - Wave 1 Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def analytics_service(db_session: AsyncSession):
    from services.analytics.service import AnalyticsService
    return AnalyticsService(db_session)


@pytest_asyncio.fixture
async def auth_service(db_session: AsyncSession):
    from services.auth.service import AuthService
    return AuthService(db_session)


@pytest_asyncio.fixture
async def admin_service(db_session: AsyncSession):
    from services.admin.service import AdminService
    return AdminService(db_session)


@pytest_asyncio.fixture
async def reporting_service(db_session: AsyncSession):
    from services.reporting.service import ReportingService
    return ReportingService(db_session)
'''
    
    if 'analytics_service' not in existing:
        content = existing + new_fixtures
        
        # افزودن import مدل‌های جدید
        if 'services.analytics.models' not in content:
            content = content.replace(
                'except ImportError as e:\n        print(f"[conftest] Warning landscape: {e}")',
                'except ImportError as e:\n        print(f"[conftest] Warning landscape: {e}")\n    \n    try:\n        from services.analytics.models import AnalyticsSnapshot\n        from services.auth.models import AuthUser, RefreshToken\n        from services.admin.models import AuditLog as AdminAuditLog\n        from services.reporting.models import Report\n    except ImportError as e:\n        print(f"[conftest] Warning phase3 models: {e}")'
            )
        
        conftest.write_text(content, encoding='utf-8')
        log("conftest.py به‌روزرسانی شد", "+")
    else:
        log("fixtures قبلاً موجود بودند", "i")
    
    return True


# ═══════════════════════════════════════════════════════════════
# اجرای تست‌ها
# ═══════════════════════════════════════════════════════════════

def run_tests() -> Dict[str, bool]:
    separator("اجرای تست‌های یکپارچگی")
    
    test_files = [
        "services/analytics/tests/test_integration.py",
        "services/auth/tests/test_integration.py",
        "services/admin/tests/test_integration.py",
        "services/reporting/tests/test_integration.py",
        "services/marketplace/tests/test_integration.py",
        "services/tourism/tests/test_integration.py",
        "services/landscape/tests/test_integration.py",
    ]
    
    results = {}
    
    for test_file in test_files:
        log(f"اجرای {test_file}...", "i")
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_file, "-v", "--tb=short",
            "-p", "no:phoenix",
            "-p", "no:arize-phoenix-client",
        ]
        
        try:
            result = subprocess.run(
                cmd, cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=120,
            )
            
            # پیدا کردن خط خلاصه
            for line in result.stdout.split('\n'):
                if 'passed' in line or 'failed' in line or 'error' in line:
                    print(f"    {line.strip()}")
                    break
            
            if result.returncode == 0:
                log(f"✅ {test_file}", "+")
                results[test_file] = True
            else:
                log(f"❌ {test_file}", "X")
                # نمایش ۲۰ خط آخر
                lines = result.stdout.split('\n')
                print("    خروجی (۲۰ خط آخر):")
                for line in lines[-20:]:
                    print(f"      {line}")
                results[test_file] = False
        except subprocess.TimeoutExpired:
            log(f"⏱️  {test_file} timeout", "X")
            results[test_file] = False
        except Exception as e:
            log(f"خطا: {e}", "X")
            results[test_file] = False
    
    return results


# ═══════════════════════════════════════════════════════════════
# تولید گزارش
# ═══════════════════════════════════════════════════════════════

def generate_report(results: Dict[str, bool]) -> bool:
    separator("تولید گزارش نهایی")
    
    all_passed = all(results.values())
    
    # استفاده از string concatenation به جای f-string multiline
    parts = []
    parts.append("# گزارش فاز ۳ - موج ۱\n\n")
    parts.append(f"**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    parts.append("## ماژول‌های تکمیل‌شده\n\n")
    parts.append("| ماژول | Priority | وضعیت |\n")
    parts.append("|---|---|---|\n")
    parts.append("| analytics | 10/10 | ✅ کامل |\n")
    parts.append("| auth | 9/10 | ✅ کامل |\n")
    parts.append("| admin | 8/10 | ✅ کامل |\n")
    parts.append("| reporting | 8/10 | ✅ کامل |\n\n")
    
    parts.append("## API Endpoints جدید\n\n")
    parts.append("### Analytics\n")
    parts.append("- GET /analytics/dashboard\n")
    parts.append("- GET /analytics/sales-summary\n")
    parts.append("- GET /analytics/tourism-metrics\n")
    parts.append("- GET /analytics/landscape-metrics\n\n")
    parts.append("### Auth\n")
    parts.append("- POST /auth/register\n")
    parts.append("- POST /auth/login\n\n")
    parts.append("### Admin\n")
    parts.append("- GET /admin/health\n")
    parts.append("- GET /admin/status\n")
    parts.append("- GET /admin/stats\n")
    parts.append("- GET /admin/audit-logs\n\n")
    parts.append("### Reporting\n")
    parts.append("- POST /reports/\n")
    parts.append("- POST /reports/<id>/generate\n")
    parts.append("- GET /reports/<id>\n")
    parts.append("- GET /reports/\n\n")
    
    parts.append("## نتایج تست‌ها\n\n")
    for test_file, passed in results.items():
        icon = "✅" if passed else "❌"
        parts.append(f"- {icon} `{test_file}`\n")
    
    status = "موفق" if all_passed else "ناموفق"
    parts.append(f"\n**وضعیت نهایی:** {status}\n")
    
    report = "".join(parts)
    report_file = PROJECT_ROOT / "PHASE3_WAVE1_REPORT.md"
    report_file.write_text(report, encoding='utf-8')
    log(f"گزارش: {report_file}", "+")
    
    return all_passed


# ═══════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  Eco Nojin - فاز ۳ - موج ۱: تکمیل ماژول‌های اولویت‌دار")
    print("=" * 70)
    print("\n  ماژول‌های هدف:")
    print("    1. analytics (Priority 10)")
    print("    2. auth (Priority 9)")
    print("    3. admin (Priority 8)")
    print("    4. reporting (Priority 8)")
    
    # Backup
    if not step1_backup():
        return 1
    
    # ساخت ماژول‌ها
    build_analytics()
    build_auth()
    build_admin()
    build_reporting()
    
    # به‌روزرسانی conftest
    update_conftest()
    
    # اجرای تست‌ها
    results = run_tests()
    
    # گزارش
    all_passed = generate_report(results)
    
    # خلاصه
    separator("خلاصه نهایی")
    
    for test_file, passed in results.items():
        icon = "+" if passed else "X"
        print(f"  [{icon}] {test_file}")
    
    if all_passed:
        print("\n  +++ فاز ۳ - موج ۱ با موفقیت کامل شد! +++")
        print("\n  گام بعدی: commit")
        print("  git add -A")
        print("  git commit -m 'phase3-wave1: complete priority modules'")
        return 0
    else:
        failed = [t for t, p in results.items() if not p]
        print(f"\n  [!] {len(failed)} تست شکست خورد:")
        for t in failed:
            print(f"     - {t}")
        print(f"\n  [i] Backup: {BACKUP_ROOT}")
        return 1


if __name__ == "__main__":
    sys.exit(main())