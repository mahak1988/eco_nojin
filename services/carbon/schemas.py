"""
Pydantic schemas and domain errors for the sustainable / auditable carbon-credit
MRV backend.

This is the accounting layer behind the carbon credit ledger:
  register -> submit -> verify -> issue -> transfer/retire -> freeze/unfreeze

Honesty rules enforced here and in ``CarbonService``:
  * No fabricated cryptographic hash is ever produced. The idempotency key is
    stored verbatim (see ``IdempotencyKey``).
  * No claim of endorsement by a real Validation/Verification Body (VVB).
    Verification is the honest, methodology-aligned check produced by
    ``services.carbon.verification`` plus the data-provenance flag returned by
    ``CarbonMrvMotor`` (``modelled_estimate`` vs ``field_verified``).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class CreditState(StrEnum):
    """Lifecycle states mirrored on ``CarbonCredit``."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    VERIFIED = "VERIFIED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


# --------------------------------------------------------------------------- #
# Domain errors
# --------------------------------------------------------------------------- #
class CarbonError(Exception):
    """Base class for carbon-ledger domain errors."""


class ProjectNotFoundError(CarbonError):
    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")


class ProjectNotVerifiedError(CarbonError):
    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(
            f"Project {project_id} is not verified; only verified projects may issue credits"
        )


class IssueNotAllowedError(CarbonError):
    """Raised when a project lacks the evidence floor for issuance."""

    def __init__(self, project_id: str, reasons: list[str]) -> None:
        self.project_id = project_id
        self.reasons = reasons
        super().__init__(
            f"Cannot issue credits for project {project_id}: "
            f"field_verified or MRV documents required ({', '.join(reasons)})"
        )


class CreditNotFoundError(CarbonError):
    def __init__(self, credit_id: str) -> None:
        self.credit_id = credit_id
        super().__init__(f"Credit not found: {credit_id}")


class CreditStateError(CarbonError):
    def __init__(self, credit_id: str, message: str) -> None:
        self.credit_id = credit_id
        super().__init__(f"Credit {credit_id}: {message}")


class FrozenCreditError(CarbonError):
    def __init__(self, credit_id: str) -> None:
        self.credit_id = credit_id
        super().__init__(
            f"Credit {credit_id} is frozen (unfreeze before modifying) or is under authority review"
        )


class NotHolderError(CarbonError):
    def __init__(self, credit_id: str, holder: str) -> None:
        self.credit_id = credit_id
        super().__init__(f"Credit {credit_id} is not held by {holder}")


class DoubleIssuanceError(CarbonError):
    def __init__(self, credit_id: str) -> None:
        self.credit_id = credit_id
        super().__init__(f"Credit {credit_id} already issued (idempotency guard)")


class InsufficientAvailableError(CarbonError):
    def __init__(self, credit_id: str, requested: Decimal, available: Decimal) -> None:
        self.credit_id = credit_id
        super().__init__(f"Credit {credit_id}: cannot retire {requested} (available {available})")


# Re-export pydantic's ValidationError so callers can catch the Pydantic-level
# input errors raised when request payloads fail field validation. (It is
# already imported above and listed in ``__all__``.)


# --------------------------------------------------------------------------- #
# Request / response schemas


# --------------------------------------------------------------------------- #
# Request / response schemas
# --------------------------------------------------------------------------- #
class RegisterProjectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    project_type: str = Field("afforestation", max_length=80)
    area_ha: float = Field(..., gt=0)
    methodology: str = Field("vm0032", max_length=120)
    standard: str | None = Field(None, max_length=120)
    region: str | None = Field(None, max_length=80)
    duration_years: int = Field(..., ge=1, le=100)
    owner_id: str = Field(..., min_length=1, max_length=64)
    mrv_documents: list[str] | None = None
    # Optional: kept for callers that carry the raw geometry/WKT payload.
    geometry: str | None = None
    baseline_activity: str | None = None
    has_financing: bool = False


class VerifyProjectRequest(BaseModel):
    """Verification: methodology checks + MRV motor run for data provenance."""

    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: str = Field(..., min_length=3, max_length=64)

    # Motor / SOC inputs (the honest accounting source of truth)
    soc_initial_t_ha: float = Field(..., ge=0)
    soc_final_t_ha: float = Field(..., ge=0)
    area_ha: float = Field(..., gt=0)
    measured_soc_t_ha: float | None = None
    measurements: list[dict[str, Any]] = Field(default_factory=list)
    methodology: str = Field("vm0032", max_length=120)
    permanence_factor: float = Field(0.85, gt=0, le=1)

    # VM0042-style methodology checks
    baseline_activity: str = Field(..., min_length=1, max_length=200)
    has_financing: bool = False
    would_happen_without_project: bool = False
    activity_displacement: bool = False
    market_leakage: bool = False
    commitment_years: int = Field(30, ge=1)
    risk_flag: bool = False

    @field_validator("measurements")
    @classmethod
    def _validate_measurements(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for m in v:
            if not isinstance(m, dict) or "year" not in m or "soc_t_ha" not in m:
                raise ValueError("each measurement must have 'year' and 'soc_t_ha'")
        return v


class IssueCreditsRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    project_id: str = Field(..., min_length=3, max_length=64)
    vintage_year: int = Field(..., ge=1980, le=2100)
    soc_initial_t_ha: float = Field(..., ge=0)
    soc_final_t_ha: float = Field(..., ge=0)
    area_ha: float = Field(..., gt=0)
    measured_soc_t_ha: float | None = None
    measurements: list[dict[str, Any]] = Field(default_factory=list)
    methodology: str = Field("vm0032", max_length=120)
    permanence_factor: float = Field(0.85, gt=0, le=1)
    # The raw client key is stored verbatim — never hashed or fabricated.
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    issued_by: str = Field(..., min_length=1, max_length=120)

    # Optional Motor / SOC inputs used to re-run the MRV motor at issuance time.
    soc_initial_t_ha: float = 0.0
    soc_final_t_ha: float = 0.0
    area_ha: float = 0.0
    measured_soc_t_ha: float | None = None
    methodology: str = Field("vm0032", max_length=120)
    permanence_factor: float = Field(0.85, gt=0, le=1)

    @field_validator("measurements")
    @classmethod
    def _validate_measurements(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for m in v:
            if not isinstance(m, dict) or "year" not in m or "soc_t_ha" not in m:
                raise ValueError("each measurement must have 'year' and 'soc_t_ha'")
        return v
    # Optional: retained for callers that record who issued the credit.
    issued_by: str | None = None


class TransferRequest(BaseModel):
    credit_id: str = Field(..., min_length=1, max_length=64)
    to_holder_id: str = Field(..., min_length=1, max_length=64)
    actor: str = Field(..., min_length=1, max_length=120)
    idempotency_key: str | None = Field(None, min_length=8, max_length=128)
    # Optional legacy aliases: explicit sender and partial amount.
    from_holder: str | None = None
    to_holder: str | None = None
    amount: Decimal | None = None


class RetireRequest(BaseModel):
    credit_id: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(..., min_length=1, max_length=500)
    amount: float | None = None  # None => retire the whole lot
    actor: str = Field(..., min_length=1, max_length=120)
    authority: str | None = None
    idempotency_key: str | None = Field(None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def _positive_amount(self) -> RetireRequest:
        if self.amount is not None and self.amount <= 0:
            raise ValueError("retire amount must be positive")
        return self
    # Optional legacy aliases.
    holder_id: str | None = None
    retirement_reason: str | None = None


class FreezeRequest(BaseModel):
    credit_id: str = Field(..., min_length=1, max_length=64)
    actor: str = Field(..., min_length=1, max_length=120)
    authority: str = Field(..., min_length=1, max_length=120)
    reason: str = Field(..., min_length=1, max_length=500)


class UnfreezeRequest(BaseModel):
    credit_id: str = Field(..., min_length=1, max_length=64)
    actor: str = Field(..., min_length=1, max_length=120)
    authority: str = Field(..., min_length=1, max_length=120)
    reason: str = Field(..., min_length=1, max_length=500)


class CreditIssueResult(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    credit_id: str
    serial: str
    state: str
    total_amount: Decimal
    available_amount: Decimal
    retired_amount: Decimal
    data_mode: str
    issued_at: datetime | None = None
    idempotency_key: str
    note: str = (
        "Accounting figure from CarbonMrvMotor (IPCC tC->tCO2e x3.667) with a "
        "permanence/uncertainty deduction. Not a certification by any VVB."
    )


class CreditHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    event_type: str
    actor: str | None = None
    authority: str | None = None
    reason: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime


class CreditStats(BaseModel):
    total_issued: Decimal = Decimal("0")
    total_retired: Decimal = Decimal("0")
    total_active: Decimal = Decimal("0")
    by_state: dict[str, int] = Field(default_factory=dict)


__all__ = [
    "CarbonError",
    "CreditHistoryItem",
    "CreditIssueResult",
    "CreditNotFoundError",
    "CreditState",
    "CreditStateError",
    "CreditStats",
    "DoubleIssuanceError",
    "FreezeRequest",
    "FrozenCreditError",
    "InsufficientAvailableError",
    "IssueCreditsRequest",
    "IssueNotAllowedError",
    "NotHolderError",
    "ProjectNotFoundError",
    "ProjectNotVerifiedError",
    "RegisterProjectRequest",
    "RetireRequest",
    "TransferRequest",
    "UnfreezeRequest",
    "ValidationError",
    "VerifyProjectRequest",
]
