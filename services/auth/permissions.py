"""Unified Capability/Permission Matrix for Eco Nojin.

Single source of truth for roles, capabilities, and territory-specific permissions.
Resolves BG-012: 4 role collections in 4 files unreconciled.

Merges:
- settings.allowed_roles (farmer,advisor,admin,researcher,organization,tourist)
- api_gateway.auth.ALL_ROLES (farmer,advisor,admin,security_admin,content_admin,user_admin)
- Landscape governance roles (council_member, landscape_manager, etc.)
- Multi-capability user model (eco.md §8, §164)
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

# =============================================================================
# ROLE DEFINITIONS (Unified)
# =============================================================================

class PlatformRole(StrEnum):
    """Platform-wide roles (merged from settings.allowed_roles + ALL_ROLES)."""

    # Core platform roles (from settings.allowed_roles)
    FARMER = "farmer"
    ADVISOR = "advisor"
    ADMIN = "admin"
    RESEARCHER = "researcher"
    ORGANIZATION = "organization"
    TOURIST = "tourist"

    # Admin sub-roles (from api_gateway.auth.ALL_ROLES)
    SECURITY_ADMIN = "security_admin"
    CONTENT_ADMIN = "content_admin"
    USER_ADMIN = "user_admin"

    # Landscape governance roles (from landscape_governance.role)
    COUNCIL_MEMBER = "council_member"
    LANDSCAPE_MANAGER = "landscape_manager"
    TERRITORY_STEWARD = "territory_steward"
    VILLAGE_REPRESENTATIVE = "village_representative"


# =============================================================================
# CAPABILITY DEFINITIONS (eco.md §164 — capability-based + territory-specific)
# =============================================================================

class Capability(StrEnum):
    """Platform capabilities (not roles — capabilities are granted, roles bundle capabilities)."""

    # --- Auth/Access ---
    PLATFORM_ACCESS = "platform.access"
    ADMIN_PANEL = "admin.panel"
    SECURITY_AUDIT = "security.audit"

    # --- Territory (Landscape) ---
    TERRITORY_VIEW = "territory.view"
    TERRITORY_CREATE = "territory.create"
    TERRITORY_UPDATE = "territory.update"
    TERRITORY_VERIFY = "territory.verify"           # PATCH /territories/{id}/verify
    TERRITORY_REGISTRY = "territory.registry"       # manage verification/representative status

    # --- Governance (Landscape) ---
    GOVERNANCE_VIEW = "governance.view"
    GOVERNANCE_MANAGE = "governance.manage"         # add/remove members
    GOVERNANCE_TERM = "governance.term"             # delegation/expiration
    GOVERNANCE_AUDIT = "governance.audit"           # deactivate/reactivate

    # --- Marketplace ---
    MARKETPLACE_BROWSE = "marketplace.browse"
    MARKETPLACE_SELL = "marketplace.sell"           # requires territory seller auth
    MARKETPLACE_MANAGE = "marketplace.manage"       # seller dashboard
    MARKETPLACE_VERIFY = "marketplace.verify"       # seller verification

    # --- Tourism ---
    TOURISM_BROWSE = "tourism.browse"
    TOURISM_GUIDE = "tourism.guide"                 # create/manage tours
    TOURISM_HOST = "tourism.host"                   # accommodations
    TOURISM_BOOK = "tourism.book"

    # --- Culture ---
    CULTURE_VIEW = "culture.view"
    CULTURE_CREATE = "culture.create"
    CULTURE_MODERATE = "culture.moderate"           # access_level filtering

    # --- Knowledge (Daneshyar) ---
    KNOWLEDGE_BROWSE = "knowledge.browse"
    KNOWLEDGE_CONTRIBUTE = "knowledge.contribute"
    KNOWLEDGE_MODERATE = "knowledge.moderate"

    # --- Projects/Restoration ---
    PROJECT_VIEW = "project.view"
    PROJECT_CREATE = "project.create"
    PROJECT_PARTICIPATE = "project.participate"
    PROJECT_VERIFY = "project.verify"

    # --- Hydroma/Environmental ---
    HYDROMA_VIEW = "hydroma.view"
    HYDROMA_ANALYZE = "hydroma.analyze"

    # --- Economy/Rewards ---
    REWARDS_VIEW = "rewards.view"
    REWARDS_CLAIM = "rewards.claim"
    ECO_COIN_TRANSFER = "ecocoin.transfer"

    # --- Admin ---
    USER_MANAGE = "user.manage"
    CONTENT_MODERATE = "content.moderate"
    SECURITY_CONFIG = "security.config"


# =============================================================================
# ROLE → CAPABILITY MAPPING (Global defaults)
# Territory-specific grants override via territory_capabilities()
# =============================================================================

ROLE_CAPABILITIES: dict[PlatformRole, set[Capability]] = {
    # --- Platform Base ---
    PlatformRole.FARMER: {
        Capability.PLATFORM_ACCESS,
        Capability.TERRITORY_VIEW,
        Capability.MARKETPLACE_BROWSE,
        Capability.MARKETPLACE_SELL,
        Capability.TOURISM_BROWSE,
        Capability.TOURISM_BOOK,
        Capability.CULTURE_VIEW,
        Capability.KNOWLEDGE_BROWSE,
        Capability.PROJECT_VIEW,
        Capability.PROJECT_PARTICIPATE,
        Capability.HYDROMA_VIEW,
        Capability.REWARDS_VIEW,
        Capability.REWARDS_CLAIM,
    },
    PlatformRole.ADVISOR: {
        Capability.PLATFORM_ACCESS,
        Capability.TERRITORY_VIEW,
        Capability.TERRITORY_CREATE,
        Capability.KNOWLEDGE_BROWSE,
        Capability.KNOWLEDGE_CONTRIBUTE,
        Capability.PROJECT_VIEW,
        Capability.HYDROMA_VIEW,
        Capability.HYDROMA_ANALYZE,
    },
    PlatformRole.ADMIN: {
        # Admin gets all platform capabilities (will be filtered by sub-role)
        *list(Capability),
    },
    PlatformRole.RESEARCHER: {
        Capability.PLATFORM_ACCESS,
        Capability.TERRITORY_VIEW,
        Capability.KNOWLEDGE_BROWSE,
        Capability.KNOWLEDGE_CONTRIBUTE,
        Capability.KNOWLEDGE_MODERATE,
        Capability.HYDROMA_VIEW,
        Capability.HYDROMA_ANALYZE,
        Capability.PROJECT_VIEW,
    },
    PlatformRole.ORGANIZATION: {
        Capability.PLATFORM_ACCESS,
        Capability.TERRITORY_VIEW,
        Capability.MARKETPLACE_BROWSE,
        Capability.MARKETPLACE_SELL,
        Capability.PROJECT_CREATE,
        Capability.PROJECT_PARTICIPATE,
        Capability.CULTURE_CREATE,
        Capability.REWARDS_VIEW,
    },
    PlatformRole.TOURIST: {
        Capability.PLATFORM_ACCESS,
        Capability.TERRITORY_VIEW,
        Capability.MARKETPLACE_BROWSE,
        Capability.TOURISM_BROWSE,
        Capability.TOURISM_BOOK,
        Capability.CULTURE_VIEW,
        Capability.REWARDS_VIEW,
    },

    # --- Admin Sub-roles (restricted admin) ---
    PlatformRole.SECURITY_ADMIN: {
        Capability.PLATFORM_ACCESS,
        Capability.ADMIN_PANEL,
        Capability.SECURITY_AUDIT,
        Capability.SECURITY_CONFIG,
        Capability.USER_MANAGE,
    },
    PlatformRole.CONTENT_ADMIN: {
        Capability.PLATFORM_ACCESS,
        Capability.ADMIN_PANEL,
        Capability.CONTENT_MODERATE,
        Capability.CULTURE_MODERATE,
        Capability.KNOWLEDGE_MODERATE,
    },
    PlatformRole.USER_ADMIN: {
        Capability.PLATFORM_ACCESS,
        Capability.ADMIN_PANEL,
        Capability.USER_MANAGE,
    },

    # --- Landscape Governance (territory-specific, granted via governance membership) ---
    PlatformRole.COUNCIL_MEMBER: {
        Capability.GOVERNANCE_VIEW,
        Capability.TERRITORY_REGISTRY,
        Capability.TERRITORY_VERIFY,
    },
    PlatformRole.LANDSCAPE_MANAGER: {
        Capability.GOVERNANCE_VIEW,
        Capability.GOVERNANCE_MANAGE,
        Capability.TERRITORY_REGISTRY,
        Capability.TERRITORY_VERIFY,
        Capability.MARKETPLACE_VERIFY,
    },
    PlatformRole.TERRITORY_STEWARD: {
        Capability.TERRITORY_VIEW,
        Capability.TERRITORY_CREATE,
        Capability.TERRITORY_UPDATE,
        Capability.TERRITORY_REGISTRY,
        Capability.TERRITORY_VERIFY,
        Capability.GOVERNANCE_VIEW,
        Capability.GOVERNANCE_MANAGE,
        Capability.GOVERNANCE_TERM,
        Capability.GOVERNANCE_AUDIT,
    },
    PlatformRole.VILLAGE_REPRESENTATIVE: {
        Capability.TERRITORY_VIEW,
        Capability.TERRITORY_REGISTRY,
        Capability.TERRITORY_VERIFY,
        Capability.GOVERNANCE_VIEW,
        Capability.MARKETPLACE_VERIFY,
    },
}


# =============================================================================
# TERRITORY-SPECIFIC CAPABILITY RESOLUTION (eco.md §164)
# =============================================================================

@lru_cache(maxsize=256)
def territory_capabilities(
    user_id: str,
    village_id: str,
) -> set[Capability]:
    """
    Resolve capabilities for a user in a specific territory.

    Per eco.md §164: A user may be:
      - verified producer in Territory A
      - ordinary participant in Territory B
      - admin in one organization
      - store manager for one brand

    Global role capabilities are BASE; territory membership ADDS capabilities.
    """
    from database.hub import hub
    from services.landscape.models import LandscapeGovernanceMember

    base_caps = set()
    # Get user's global role (would come from JWT/user record)
    # For now, base is empty — territory membership provides all capabilities
    # In full implementation, merge with user's global role capabilities.

    try:
        with hub.get_session() as session:
            member = session.query(LandscapeGovernanceMember).filter(
                LandscapeGovernanceMember.user_id == user_id,
                LandscapeGovernanceMember.village_id == village_id,
                LandscapeGovernanceMember.is_active,
            ).first()

            if member:
                role = PlatformRole(member.role)
                return ROLE_CAPABILITIES.get(role, set())
    except Exception:
        pass

    return base_caps


def has_capability(user_id: str, capability: Capability, village_id: str | None = None) -> bool:
    """Check if user has capability (optionally in a territory)."""
    if village_id:
        caps = territory_capabilities(user_id, village_id)
        return capability in caps
    # Global check — would need user's global role from JWT
    return False


# =============================================================================
# HELPERS FOR COMPATIBILITY (migrate from old role strings)
# =============================================================================

LEGACY_ROLE_MAP: dict[str, PlatformRole] = {
    "farmer": PlatformRole.FARMER,
    "advisor": PlatformRole.ADVISOR,
    "admin": PlatformRole.ADMIN,
    "researcher": PlatformRole.RESEARCHER,
    "organization": PlatformRole.ORGANIZATION,
    "tourist": PlatformRole.TOURIST,
    "security_admin": PlatformRole.SECURITY_ADMIN,
    "content_admin": PlatformRole.CONTENT_ADMIN,
    "user_admin": PlatformRole.USER_ADMIN,
    "council_member": PlatformRole.COUNCIL_MEMBER,
    "landscape_manager": PlatformRole.LANDSCAPE_MANAGER,
    "territory_steward": PlatformRole.TERRITORY_STEWARD,
    "village_representative": PlatformRole.VILLAGE_REPRESENTATIVE,
    # Legacy
    "regular": PlatformRole.FARMER,
    "cooperative": PlatformRole.ORGANIZATION,
    "ngo": PlatformRole.ORGANIZATION,
}


def normalize_role(role_str: str) -> PlatformRole:
    """Map legacy role string to PlatformRole enum."""
    return LEGACY_ROLE_MAP.get(role_str.lower(), PlatformRole.FARMER)


def get_capabilities_for_role(role_str: str) -> set[Capability]:
    """Get capabilities for a legacy role string (for migration)."""
    role = normalize_role(role_str)
    return ROLE_CAPABILITIES.get(role, set())


# =============================================================================
# SETTINGS SYNC (sync with settings.allowed_roles)
# =============================================================================

def sync_settings_allowed_roles() -> list[str]:
    """
    Returns the canonical allowed_roles list for settings.allowed_roles.

    This replaces the comma-separated string in settings.allowed_roles
    with the canonical list from PlatformRole.
    """
    return [r.value for r in PlatformRole if r not in {
        PlatformRole.SECURITY_ADMIN,
        PlatformRole.CONTENT_ADMIN,
        PlatformRole.USER_ADMIN,
        PlatformRole.COUNCIL_MEMBER,
        PlatformRole.LANDSCAPE_MANAGER,
        PlatformRole.TERRITORY_STEWARD,
        PlatformRole.VILLAGE_REPRESENTATIVE,
    }]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PlatformRole",
    "Capability",
    "ROLE_CAPABILITIES",
    "territory_capabilities",
    "has_capability",
    "normalize_role",
    "get_capabilities_for_role",
    "sync_settings_allowed_roles",
    "LEGACY_ROLE_MAP",
]