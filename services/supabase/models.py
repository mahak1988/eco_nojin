"""
Supabase database models for Eco Nojin.

These models map to the platform_* tables in Supabase.
They complement existing eco_nojin models without modifying them.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class PlatformLandscape:
    """Landscape (village/region) in the platform."""
    id: UUID | None = None
    name: str = ""
    slug: str = ""
    country: str = ""
    province: str | None = None
    geo_boundary: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PlatformProfile:
    """User profile in the platform."""
    id: UUID | None = None
    phone: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    language: str = "fa"
    kyc_level: int = 0
    wallet_address: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PlatformCarbonProject:
    """Carbon project in the platform."""
    id: UUID | None = None
    landscape_id: UUID | None = None
    owner_id: UUID | None = None
    name: str = ""
    project_type: str = ""
    area_ha: float = 0.0
    duration_years: int = 0
    status: str = "draft"
    credits_issued: float = 0.0
    credits_retired: float = 0.0
    tx_hash: str | None = None
    created_at: datetime | None = None


@dataclass
class PlatformCarbonCredit:
    """Carbon credit in the platform."""
    id: UUID | None = None
    project_id: UUID | None = None
    owner_id: UUID | None = None
    amount: float = 0.0
    issued_at: datetime | None = None
    retired: bool = False
    tx_hash: str | None = None
