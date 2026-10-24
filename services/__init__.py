"""EcoCoin Ecosystem - Main Entry Point"""

from __future__ import annotations

from .ecosystem import ActivityType, EcosystemService, VerificationStatus
from .ecosystem.trust_score import TrustScoreService

try:
    from .oracle import DataSource, OracleService
    from .privacy import PrivacyVault
except ImportError:
    # Optional dependency absent (cryptography for the vault): the re-exported
    # name must fall back to None. mypy binds the try-branch symbol to the
    # class type, so both codes are needed per site; the try/except itself is
    # unchanged, so runtime behaviour is identical.
    DataSource = None  # type: ignore[assignment, misc]
    OracleService = None  # type: ignore[assignment, misc]
    PrivacyVault = None  # type: ignore[assignment, misc]

try:
    from .satellite import SatelliteService, SatelliteSource
except ImportError:
    # Optional dependency absent (aiohttp for the CDSE client): same optional
    # re-export fallback as above, same per-site codes.
    SatelliteService = None  # type: ignore[assignment, misc]
    SatelliteSource = None  # type: ignore[assignment, misc]

__all__ = [
    "ActivityType",
    "DataSource",
    "EcosystemService",
    "OracleService",
    "PrivacyVault",
    "SatelliteService",
    "SatelliteSource",
    "TrustScoreService",
    "VerificationStatus",
]