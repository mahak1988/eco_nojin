"""
Supabase database models for Eco Nojin.

These models map to the platform_* tables in Supabase.
They complement existing eco_nojin models without modifying them.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class PlatformLandscape:
    """Landscape (village/region) in the platform."""
    id: Optional[UUID] = None
    name: str = ""
    slug: str = ""
    country: str = ""
    province: Optional[str] = None
    geo_boundary: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PlatformProfile:
    """User profile in the platform."""
    id: Optional[UUID] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    language: str = "fa"
    kyc_level: int = 0
    wallet_address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class PlatformCarbonProject:
    """Carbon project in the platform."""
    id: Optional[UUID] = None
    landscape_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    name: str = ""
    project_type: str = ""
    area_ha: float = 0.0
    duration_years: int = 0
    status: str = "draft"
    credits_issued: float = 0.0
    credits_retired: float = 0.0
    tx_hash: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class PlatformCarbonCredit:
    """Carbon credit in the platform."""
    id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    amount: float = 0.0
    issued_at: Optional[datetime] = None
    retired: bool = False
    tx_hash: Optional[str] = None
