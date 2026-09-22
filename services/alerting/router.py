"""Alerting API Router."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.alerting.service import AlertService
from services.alerting.schemas import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertResponse,
    AlertSummary,
)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_alert_service(db: AsyncSession = Depends(get_db)) -> AlertService:
    return AlertService(db)


# =============================================================================
# Alert Rules
# =============================================================================


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    data: AlertRuleCreate,
    service: AlertService = Depends(get_alert_service),
):
    """Create a new alert rule."""
    return await service.create_rule(data)


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: AlertService = Depends(get_alert_service),
):
    """List alert rules with filtering."""
    return await service.list_rules(
        severity=severity,
        enabled=enabled,
        owner=owner,
        page=page,
        page_size=page_size,
    )


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: str,
    service: AlertService = Depends(get_alert_service),
):
    """Get an alert rule by ID."""
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    update: AlertRuleUpdate,
    service: AlertService = Depends(get_alert_service),
):
    """Update an alert rule."""
    rule = await service.update_rule(rule_id, update)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: str,
    service: AlertService = Depends(get_alert_service),
):
    """Delete an alert rule."""
    success = await service.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")


# =============================================================================
# Alerts
# =============================================================================


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(
        None, description="Filter by status (firing, resolved, acknowledged, suppressed)"
    ),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    service: AlertService = Depends(get_alert_service),
):
    """List alerts with filtering."""
    return await service.list_alerts(
        status=status,
        severity=severity,
        rule_id=rule_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
):
    """Get an alert by ID."""
    alert = await service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    user_id: str = Query(..., description="ID of user acknowledging"),
    note: Optional[str] = Query(None, description="Acknowledgment note"),
    service: AlertService = Depends(get_alert_service),
):
    """Acknowledge an alert."""
    success = await service.acknowledge_alert(alert_id, user_id, note)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    alert = await service.get_alert(alert_id)
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    service: AlertService = Depends(get_alert_service),
):
    """Manually resolve an alert."""
    success = await service.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = await service.get_alert(alert_id)
    return alert


@router.post("/{alert_id}/suppress", response_model=AlertResponse)
async def suppress_alert(
    alert_id: str,
    duration_seconds: int = Query(3600, ge=60, description="Suppression duration in seconds"),
    service: AlertService = Depends(get_alert_service),
):
    """Suppress an alert for a duration."""
    success = await service.suppress_alert(alert_id, duration_seconds)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert = await service.get_alert(alert_id)
    return alert


# =============================================================================
# Summary & Stats
# =============================================================================


@router.get("/summary", response_model=AlertSummary)
async def get_alert_summary(
    service: AlertService = Depends(get_alert_service),
):
    """Get alert summary statistics."""
    return await service.get_summary()
