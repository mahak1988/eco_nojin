"""Oracle Challenge API Router (BG-010)."""
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from database.models import OracleChallenge, OracleImpactMetrics, OracleImpactReport
from services.oracle.schemas import (
    ChallengeStatus,
    OracleChallengeCreate,
    OracleChallengeListResponse,
    OracleChallengeResponse,
    OracleChallengeUpdate,
    OracleImpactMetricsResponse,
    OracleImpactReportCreate,
    OracleImpactReportResponse,
)
from services.oracle.service import OracleService

router = APIRouter(prefix="/api/v1/oracle", tags=["oracle"])


async def get_db() -> AsyncSession:
    async with hub.get_async_session() as session:
        yield session


async def get_oracle_service_dep(db: Annotated[AsyncSession, Depends(get_db)]) -> OracleService:
    return OracleService(None, None)  # Will use db directly for queries


# =============================================================================
# Challenge Endpoints
# =============================================================================


@router.post(
    "/challenges",
    response_model=OracleChallengeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_challenge(
    data: OracleChallengeCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit a challenge against an impact report during challenge window."""
    # Verify impact report exists and is in challenge window
    report_result = await db.execute(
        select(OracleImpactReport).where(
            OracleImpactReport.activity_id == data.activity_id
        )
    )
    report = report_result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact report not found for this activity",
        )

    # Check if already challenged
    if report.challenged:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report already challenged",
        )

    # Check challenge window
    if report.challenge_deadline and report.challenge_deadline < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Challenge window expired",
        )

    # Check for existing challenge
    existing = await db.execute(
        select(OracleChallenge).where(
            OracleChallenge.activity_id == data.activity_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Challenge already exists for this activity",
        )

    # ``datetime`` (and UTC) are imported at module level on purpose: a
    # function-local ``from datetime import datetime`` makes the name local to
    # the whole function, so the challenge-window check above raised
    # UnboundLocalError before reaching this point (S17 T-03).
    import secrets

    challenge = OracleChallenge(
        challenge_id=f"CHL-{secrets.token_hex(8)}",
        activity_id=data.activity_id,
        challenger=data.challenger,
        timestamp=datetime.now(UTC),
    )

    db.add(challenge)
    # Also mark report as challenged
    report.challenged = True
    await db.commit()
    await db.refresh(challenge)

    return _challenge_to_response(challenge)


@router.get(
    "/challenges/{challenge_id}",
    response_model=OracleChallengeResponse,
)
async def get_challenge(
    challenge_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a challenge by ID."""
    result = await db.execute(
        select(OracleChallenge).where(OracleChallenge.challenge_id == challenge_id)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    return _challenge_to_response(challenge)


@router.get(
    "/challenges",
    response_model=OracleChallengeListResponse,
)
async def list_challenges(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    activity_id: Annotated[str | None, Query()] = None,
    upheld: Annotated[bool | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List challenges with filters and pagination."""
    query = select(OracleChallenge).order_by(desc(OracleChallenge.timestamp))

    if activity_id:
        query = query.where(OracleChallenge.activity_id == activity_id)
    if upheld is not None:
        query = query.where(OracleChallenge.upheld == upheld)

    # Count total
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    challenges = result.scalars().all()

    return OracleChallengeListResponse(
        items=[_challenge_to_response(c) for c in challenges],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total else 0,
    )


@router.patch(
    "/challenges/{challenge_id}/resolve",
    response_model=OracleChallengeResponse,
)
async def resolve_challenge(
    challenge_id: str,
    data: OracleChallengeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Resolve a challenge (admin/DAO only)."""
    result = await db.execute(
        select(OracleChallenge).where(OracleChallenge.challenge_id == challenge_id)
    )
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )

    if challenge.upheld is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Challenge already resolved",
        )

    from datetime import UTC, datetime
    challenge.upheld = data.upheld
    challenge.resolved_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(challenge)

    return _challenge_to_response(challenge)


# =============================================================================
# Impact Report Endpoints
# =============================================================================


@router.post(
    "/reports",
    response_model=OracleImpactReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_impact_report(
    data: OracleImpactReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit an impact report for an activity (opens challenge window)."""
    import secrets
    from datetime import UTC, datetime, timedelta

    report = OracleImpactReport(
        report_id=f"RPT-{secrets.token_hex(8)}",
        activity_id=data.activity_id,
        reporter=data.reporter,
        data_type=data.data_type,
        confidence=data.confidence,
        impact_hash=data.impact_hash,
        evidence_commitment=data.evidence_commitment,
        methodology_version=data.methodology_version,
        timestamp=datetime.now(UTC),
        challenge_deadline=datetime.now(UTC) + timedelta(days=data.challenge_window_days),
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return _report_to_response(report)


@router.get(
    "/reports/{report_id}",
    response_model=OracleImpactReportResponse,
)
async def get_impact_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get an impact report by ID."""
    result = await db.execute(
        select(OracleImpactReport).where(OracleImpactReport.report_id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact report not found",
        )
    return _report_to_response(report)


@router.get(
    "/reports",
    response_model=list[OracleImpactReportResponse],
)
async def list_impact_reports(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    activity_id: Annotated[str | None, Query()] = None,
    challenged: Annotated[bool | None, Query()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """List impact reports with filters."""
    query = select(OracleImpactReport).order_by(desc(OracleImpactReport.timestamp))

    if activity_id:
        query = query.where(OracleImpactReport.activity_id == activity_id)
    if challenged is not None:
        query = query.where(OracleImpactReport.challenged == challenged)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()

    return [_report_to_response(r) for r in reports]


# =============================================================================
# Impact Metrics Endpoints
# =============================================================================


@router.get(
    "/metrics/{activity_id}",
    response_model=OracleImpactMetricsResponse,
)
async def get_impact_metrics(
    activity_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get finalized impact metrics for an activity."""
    result = await db.execute(
        select(OracleImpactMetrics).where(
            OracleImpactMetrics.activity_id == activity_id
        ).order_by(desc(OracleImpactMetrics.created_at))
    )
    metrics = result.scalar_one_or_none()
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact metrics not found for this activity",
        )
    return _metrics_to_response(metrics)


# =============================================================================
# Helpers
# =============================================================================


def _challenge_to_response(challenge: OracleChallenge) -> OracleChallengeResponse:
    from datetime import UTC, datetime
    status_val = ChallengeStatus.PENDING
    if challenge.upheld is True:
        status_val = ChallengeStatus.UPHELD
    elif challenge.upheld is False:
        status_val = ChallengeStatus.REJECTED
    elif challenge.timestamp < datetime.now(UTC):
        # Check if expired based on report deadline
        status_val = ChallengeStatus.EXPIRED

    return OracleChallengeResponse(
        id=challenge.id,
        challenge_id=challenge.challenge_id,
        activity_id=challenge.activity_id,
        challenger=challenge.challenger,
        timestamp=challenge.timestamp,
        upheld=challenge.upheld,
        resolved_at=challenge.resolved_at,
        status=status_val,
    )


def _report_to_response(report: OracleImpactReport) -> OracleImpactReportResponse:
    return OracleImpactReportResponse(
        id=report.id,
        report_id=report.report_id,
        activity_id=report.activity_id,
        reporter=report.reporter,
        data_type=report.data_type,
        confidence=report.confidence,
        impact_hash=report.impact_hash,
        evidence_commitment=report.evidence_commitment,
        methodology_version=report.methodology_version,
        timestamp=report.timestamp,
        challenged=report.challenged,
        challenge_deadline=report.challenge_deadline,
    )


def _metrics_to_response(metrics: OracleImpactMetrics) -> OracleImpactMetricsResponse:
    return OracleImpactMetricsResponse(
        id=metrics.id,
        activity_id=metrics.activity_id,
        confidence=metrics.confidence,
        impact_score=metrics.impact_score,
        trust_multiplier=metrics.trust_multiplier,
        survival_factor=metrics.survival_factor,
        scarcity_factor=metrics.scarcity_factor,
        challenge_deadline=metrics.challenge_deadline,
        created_at=metrics.created_at,
    )


# =============================================================================
# Service Dependency
# =============================================================================


async def get_oracle_service(db: Annotated[AsyncSession, Depends(get_db)]) -> OracleService:
    """Get OracleService with DB session."""
    # Note: OracleService currently uses in-memory storage.
    # For full DB integration, we'd pass db to OracleService.
    # For now, we use direct DB queries in router.
    return OracleService(None, None)