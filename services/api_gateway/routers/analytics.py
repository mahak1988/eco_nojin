from datetime import timezone
"""Analytics router - cross-module historical analysis."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.config import get_db
from database.models import (
    CarbonProject,
    EcoTransaction,
    Farm,
    SatelliteAnalysis,
    ScenarioRun,
    SoilAnalysis,
    User,
)
from services.api_gateway.auth import require_user

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/overview")
def get_overview(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get overall platform overview for user."""
    farms = db.query(Farm).filter(Farm.owner_id == user.id).count()
    soil_analyses = db.query(SoilAnalysis).filter(SoilAnalysis.user_id == user.id).count()
    sat_analyses = db.query(SatelliteAnalysis).filter(SatelliteAnalysis.user_id == user.id).count()
    scenarios = db.query(ScenarioRun).filter(ScenarioRun.user_id == user.id).count()
    carbon_projects = db.query(CarbonProject).filter(CarbonProject.user_id == user.id).count()

    total_area = (
        db.query(func.sum(Farm.area_hectares)).filter(Farm.owner_id == user.id).scalar() or 0
    )

    # Latest activities
    recent_soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.user_id == user.id)
        .order_by(SoilAnalysis.analyzed_at.desc())
        .first()
    )
    recent_sat = (
        db.query(SatelliteAnalysis)
        .filter(SatelliteAnalysis.user_id == user.id)
        .order_by(SatelliteAnalysis.analyzed_at.desc())
        .first()
    )

    return {
        "farms_count": farms,
        "total_area_hectares": total_area,
        "soil_analyses_count": soil_analyses,
        "satellite_analyses_count": sat_analyses,
        "scenario_runs_count": scenarios,
        "carbon_projects_count": carbon_projects,
        "latest_soil": {
            "texture": recent_soil.texture,
            "health_score": recent_soil.health_score,
            "date": recent_soil.analyzed_at.isoformat()
            if recent_soil and recent_soil.analyzed_at
            else None,
        }
        if recent_soil
        else None,
        "latest_satellite": {
            "ndvi": recent_sat.ndvi,
            "date": recent_sat.analyzed_at.isoformat()
            if recent_sat and recent_sat.analyzed_at
            else None,
        }
        if recent_sat
        else None,
    }


@router.get("/soil-trends")
def get_soil_trends(
    farm_id: int | None = None,
    days: int = 365,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get soil health trends over time."""
    query = db.query(SoilAnalysis).filter(SoilAnalysis.user_id == user.id)
    if farm_id:
        query = query.filter(SoilAnalysis.farm_id == farm_id)

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    analyses = (
        query.filter(SoilAnalysis.analyzed_at >= cutoff).order_by(SoilAnalysis.analyzed_at).all()
    )

    trend_data = [
        {
            "date": a.analyzed_at.strftime("%Y-%m-%d") if a.analyzed_at else None,
            "health_score": a.health_score,
            "ph": a.ph,
            "organic_matter": a.organic_matter,
            "nitrogen": a.nitrogen,
            "phosphorus": a.phosphorus,
            "potassium": a.potassium,
            "texture": a.texture,
        }
        for a in analyses
    ]

    # Statistics
    if analyses:
        avg_health = sum(a.health_score for a in analyses) / len(analyses)
        max_health = max(a.health_score for a in analyses)
        min_health = min(a.health_score for a in analyses)
        trend = (
            "improving"
            if len(analyses) > 1 and analyses[-1].health_score > analyses[0].health_score
            else "declining"
            if len(analyses) > 1 and analyses[-1].health_score < analyses[0].health_score
            else "stable"
        )
    else:
        avg_health = max_health = min_health = 0
        trend = "no data"

    return {
        "data": trend_data,
        "count": len(analyses),
        "average_health": round(avg_health, 1),
        "max_health": max_health,
        "min_health": min_health,
        "trend": trend,
    }


@router.get("/ndvi-trends")
def get_ndvi_trends(
    farm_id: int | None = None,
    days: int = 365,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Get NDVI trends from satellite analyses."""
    query = db.query(SatelliteAnalysis).filter(SatelliteAnalysis.user_id == user.id)
    if farm_id:
        query = query.filter(SatelliteAnalysis.farm_id == farm_id)

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    analyses = (
        query.filter(SatelliteAnalysis.analyzed_at >= cutoff)
        .order_by(SatelliteAnalysis.analyzed_at)
        .all()
    )

    trend_data = [
        {
            "date": a.analyzed_at.strftime("%Y-%m-%d") if a.analyzed_at else None,
            "ndvi": a.ndvi,
            "evi": a.evi,
            "savi": a.savi,
            "ndwi": a.ndwi,
            "nbr": a.nbr,
        }
        for a in analyses
    ]

    if analyses:
        avg_ndvi = sum(a.ndvi for a in analyses) / len(analyses)
        health_status = (
            "very healthy"
            if avg_ndvi > 0.7
            else "healthy"
            if avg_ndvi > 0.5
            else "moderate"
            if avg_ndvi > 0.3
            else "stressed"
        )
    else:
        avg_ndvi = 0
        health_status = "no data"

    return {
        "data": trend_data,
        "count": len(analyses),
        "average_ndvi": round(avg_ndvi, 3),
        "health_status": health_status,
    }


@router.get("/scenario-impact")
def get_scenario_impact(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get aggregated scenario impact analysis."""
    scenarios = db.query(ScenarioRun).filter(ScenarioRun.user_id == user.id).all()

    by_scenario = {}
    for s in scenarios:
        if s.scenario not in by_scenario:
            by_scenario[s.scenario] = {
                "count": 0,
                "temp_change": 0,
                "precip_change": 0,
                "drought": 0,
            }
        by_scenario[s.scenario]["count"] += 1
        by_scenario[s.scenario]["temp_change"] += s.temp_change or 0
        by_scenario[s.scenario]["precip_change"] += s.precip_change_percent or 0
        by_scenario[s.scenario]["drought"] += s.drought_risk_index or 0

    # Averages
    result = []
    for scenario, data in by_scenario.items():
        n = data["count"]
        result.append(
            {
                "scenario": scenario,
                "runs": n,
                "avg_temp_change": round(data["temp_change"] / n, 2) if n > 0 else 0,
                "avg_precip_change": round(data["precip_change"] / n, 2) if n > 0 else 0,
                "avg_drought_risk": round(data["drought"] / n, 3) if n > 0 else 0,
            }
        )

    return {
        "scenarios": result,
        "total_runs": len(scenarios),
    }


@router.get("/carbon-summary")
def get_carbon_summary(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get carbon project summary."""
    projects = db.query(CarbonProject).filter(CarbonProject.user_id == user.id).all()

    total_area = sum(p.area_hectares for p in projects)
    total_credits = sum(p.credits_issued for p in projects)

    by_status = {}
    for p in projects:
        by_status[p.status] = by_status.get(p.status, 0) + 1

    return {
        "total_projects": len(projects),
        "total_area_hectares": total_area,
        "total_credits_issued": total_credits,
        "by_status": by_status,
        "projects": [
            {
                "name": p.name,
                "project_type": p.project_type,
                "area_hectares": p.area_hectares,
                "credits_issued": p.credits_issued,
                "status": p.status,
                "registered_at": p.registered_at.isoformat() if p.registered_at else None,
            }
            for p in projects
        ],
    }


@router.get("/activity-timeline")
def get_activity_timeline(
    limit: int = 50, user: User = Depends(require_user), db: Session = Depends(get_db)
):
    """Get unified activity timeline across all modules."""
    activities = []

    # Soil analyses
    soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.user_id == user.id)
        .order_by(SoilAnalysis.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    for a in soil:
        if a.analyzed_at:
            activities.append(
                {
                    "type": "soil_analysis",
                    "date": a.analyzed_at.isoformat(),
                    "title": f"Soil analysis - {a.texture}",
                    "detail": f"Health: {a.health_score}, pH: {a.ph}",
                    "icon": "🧪",
                }
            )

    # Satellite analyses
    sat = (
        db.query(SatelliteAnalysis)
        .filter(SatelliteAnalysis.user_id == user.id)
        .order_by(SatelliteAnalysis.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    for a in sat:
        if a.analyzed_at:
            activities.append(
                {
                    "type": "satellite_analysis",
                    "date": a.analyzed_at.isoformat(),
                    "title": "Satellite analysis",
                    "detail": f"NDVI: {a.ndvi:.3f}",
                    "icon": "🛰️",
                }
            )

    # Scenarios
    scn = (
        db.query(ScenarioRun)
        .filter(ScenarioRun.user_id == user.id)
        .order_by(ScenarioRun.run_at.desc())
        .limit(limit)
        .all()
    )
    for s in scn:
        if s.run_at:
            activities.append(
                {
                    "type": "scenario",
                    "date": s.run_at.isoformat(),
                    "title": f"Scenario: {s.scenario}",
                    "detail": f"ΔT: {s.temp_change}°C, Drought: {s.drought_risk_index}",
                    "icon": "📊",
                }
            )

    # Carbon projects
    carb = (
        db.query(CarbonProject)
        .filter(CarbonProject.user_id == user.id)
        .order_by(CarbonProject.registered_at.desc())
        .limit(limit)
        .all()
    )
    for c in carb:
        if c.registered_at:
            activities.append(
                {
                    "type": "carbon_project",
                    "date": c.registered_at.isoformat(),
                    "title": f"Carbon: {c.name}",
                    "detail": f"{c.credits_issued} credits, {c.area_hectares} ha",
                    "icon": "🌱",
                }
            )

    # ECO transactions
    wallet = db.query(EcoWallet).filter(EcoWallet.user_id == user.id).first()
    if wallet:
        txs = (
            db.query(EcoTransaction)
            .filter(EcoTransaction.wallet_id == wallet.id)
            .order_by(EcoTransaction.timestamp.desc())
            .limit(limit)
            .all()
        )
        for t in txs:
            if t.timestamp:
                activities.append(
                    {
                        "type": "eco_transaction",
                        "date": t.timestamp.isoformat(),
                        "title": f"{'Earned' if t.transaction_type == 'earn' else 'Redeemed'} {t.amount} ECO",
                        "detail": t.description or t.category,
                        "icon": "💰" if t.transaction_type == "earn" else "🛒",
                    }
                )

    # Sort by date
    activities.sort(key=lambda x: x["date"], reverse=True)

    return {
        "activities": activities[:limit],
        "count": len(activities),
    }


@router.get("/performance-metrics")
def get_performance_metrics(user: User = Depends(require_user), db: Session = Depends(get_db)):
    """Get performance metrics across all modules."""
    # Soil health distribution
    soil_analyses = db.query(SoilAnalysis).filter(SoilAnalysis.user_id == user.id).all()
    health_distribution = {"excellent": 0, "good": 0, "moderate": 0, "poor": 0}
    for a in soil_analyses:
        if a.health_score >= 80:
            health_distribution["excellent"] += 1
        elif a.health_score >= 60:
            health_distribution["good"] += 1
        elif a.health_score >= 40:
            health_distribution["moderate"] += 1
        else:
            health_distribution["poor"] += 1

    # NDVI distribution
    sat_analyses = db.query(SatelliteAnalysis).filter(SatelliteAnalysis.user_id == user.id).all()
    ndvi_distribution = {"healthy": 0, "moderate": 0, "stressed": 0, "bare": 0}
    for a in sat_analyses:
        if a.ndvi >= 0.6:
            ndvi_distribution["healthy"] += 1
        elif a.ndvi >= 0.4:
            ndvi_distribution["moderate"] += 1
        elif a.ndvi >= 0.2:
            ndvi_distribution["stressed"] += 1
        else:
            ndvi_distribution["bare"] += 1

    return {
        "soil_health_distribution": health_distribution,
        "ndvi_distribution": ndvi_distribution,
        "total_soil_analyses": len(soil_analyses),
        "total_satellite_analyses": len(sat_analyses),
    }
