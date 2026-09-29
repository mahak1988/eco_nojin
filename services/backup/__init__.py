"""Backup/Restore Automation Service for Eco Nojin.

Provides automated backup scheduling, restore operations, and backup verification.
"""

# ``BackupConfig`` and ``BackupJob`` are ORM models, not Pydantic schemas. They
# live in .models; importing them from .schemas made this package unimportable.
from .models import BackupConfig, BackupJob
from .schemas import (
    BackupConfigCreate,
    BackupConfigUpdate,
    BackupJobResponse,
    BackupSummary,
    RestoreRequest,
    RestoreResponse,
)
from .service import BackupNotImplementedError, BackupService

__all__ = [
    "BackupConfig",
    "BackupConfigCreate",
    "BackupConfigUpdate",
    "BackupJob",
    "BackupJobResponse",
    "BackupNotImplementedError",
    "BackupService",
    "BackupSummary",
    "RestoreRequest",
    "RestoreResponse",
]
