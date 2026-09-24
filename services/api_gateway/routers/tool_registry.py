"""Tool Registry API — 62 tools/services mapping (Phase 2 prerequisite).

Combines algorithms from innovation_registry.json (H01-H25)
with scientific models from services.models.registry (22 models).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.hub import hub
from database.models import ToolRegistryEntry
from services.api_gateway.auth import require_admin

router = APIRouter(prefix="/api/v1/tool-registry", tags=["tool-registry"])

VALID_DOMAINS = {
    "climate",
    "water",
    "soil",
    "carbon",
    "crop",
    "seed",
    "modeling",
    "economic",
    "social",
}

VALID_CATEGORIES = {
    "algorithm",
    "model",
    "dataset",
    "service",
    "workflow",
}

VALID_FIDELITIES = {"official", "simplified", "experimental"}


class ToolRegistryCreate(BaseModel):
    tool_id: str = Field(..., min_length=1, max_length=32, pattern=r"^[A-Z0-9_-]+$")
    name_fa: str = Field(..., min_length=1, max_length=200)
    name_en: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., min_length=1, max_length=50)
    category: str = Field(..., min_length=1, max_length=50)
    fidelity: str | None = Field(default=None, max_length=20)
    reference: str | None = Field(default=None, max_length=300)
    description: str | None = None
    formula: str | None = None
    service_slug: str | None = Field(default=None, max_length=100)
    endpoint_path: str | None = Field(default=None, max_length=200)
    phase: int | None = Field(default=None, ge=1, le=10)
    is_active: bool = True


class ToolRegistryUpdate(BaseModel):
    name_fa: str | None = Field(default=None, min_length=1, max_length=200)
    name_en: str | None = Field(default=None, min_length=1, max_length=200)
    domain: str | None = Field(default=None, min_length=1, max_length=50)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    fidelity: str | None = Field(default=None, max_length=20)
    reference: str | None = Field(default=None, max_length=300)
    description: str | None = None
    formula: str | None = None
    service_slug: str | None = Field(default=None, max_length=100)
    endpoint_path: str | None = Field(default=None, max_length=200)
    phase: int | None = Field(default=None, ge=1, le=10)
    is_active: bool | None = None


def get_db():
    with hub.get_session() as session:
        yield session


def _to_response(tool: ToolRegistryEntry) -> dict:
    return {
        "id": tool.id,
        "tool_id": tool.tool_id,
        "name_fa": tool.name_fa,
        "name_en": tool.name_en,
        "domain": tool.domain,
        "category": tool.category,
        "fidelity": tool.fidelity,
        "reference": tool.reference,
        "description": tool.description,
        "formula": tool.formula,
        "service_slug": tool.service_slug,
        "endpoint_path": tool.endpoint_path,
        "phase": tool.phase,
        "is_active": tool.is_active,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
        "updated_at": tool.updated_at.isoformat() if tool.updated_at else None,
    }


def _validate_domain(domain: str) -> str:
    if domain not in VALID_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain '{domain}'. Valid domains: {', '.join(sorted(VALID_DOMAINS))}",
        )
    return domain


def _validate_category(category: str) -> str:
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{category}'. Valid categories: {', '.join(sorted(VALID_CATEGORIES))}",
        )
    return category


def _validate_fidelity(fidelity: str | None) -> str | None:
    if fidelity is not None and fidelity not in VALID_FIDELITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid fidelity '{fidelity}'. Valid fidelities: {', '.join(sorted(VALID_FIDELITIES))}",
        )
    return fidelity


# --- Public read endpoints ---


@router.get("", response_model=dict)
def list_tools(
    domain: str | None = Query(None, max_length=50),
    category: str | None = Query(None, max_length=50),
    fidelity: str | None = Query(None, max_length=20),
    phase: int | None = Query(None, ge=1, le=10),
    is_active: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List tools with optional filters."""
    stmt = select(ToolRegistryEntry)

    if domain:
        _validate_domain(domain)
        stmt = stmt.where(ToolRegistryEntry.domain == domain)
    if category:
        _validate_category(category)
        stmt = stmt.where(ToolRegistryEntry.category == category)
    if fidelity:
        _validate_fidelity(fidelity)
        stmt = stmt.where(ToolRegistryEntry.fidelity == fidelity)
    if phase:
        stmt = stmt.where(ToolRegistryEntry.phase == phase)
    if is_active is not None:
        stmt = stmt.where(ToolRegistryEntry.is_active == is_active)

    stmt = stmt.order_by(ToolRegistryEntry.domain, ToolRegistryEntry.tool_id)
    stmt = stmt.limit(limit).offset(offset)

    results = db.execute(stmt).scalars().all()
    return {"count": len(results), "tools": [_to_response(t) for t in results]}


@router.get("/domains", response_model=list[str])
def list_domains(db: Session = Depends(get_db)):
    """Get all unique domains."""
    stmt = select(ToolRegistryEntry.domain).distinct()
    return [row[0] for row in db.execute(stmt).all() if row[0]]


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    """Get all unique categories."""
    stmt = select(ToolRegistryEntry.category).distinct()
    return [row[0] for row in db.execute(stmt).all() if row[0]]


@router.get("/phases", response_model=list[int])
def list_phases(db: Session = Depends(get_db)):
    """Get all unique phases."""
    stmt = select(ToolRegistryEntry.phase).distinct().where(ToolRegistryEntry.phase.isnot(None))
    return sorted([row[0] for row in db.execute(stmt).all() if row[0]])


@router.get("/{tool_id}", response_model=dict)
def get_tool(tool_id: str, db: Session = Depends(get_db)):
    """Get a specific tool by tool_id."""
    tool = db.execute(
        select(ToolRegistryEntry).where(ToolRegistryEntry.tool_id == tool_id)
    ).scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    return _to_response(tool)


@router.get("/by-service/{service_slug:path}", response_model=dict)
def get_tool_by_service(service_slug: str, db: Session = Depends(get_db)):
    """Get tool by service slug (e.g., models/et0_hargreaves)."""
    tool = db.execute(
        select(ToolRegistryEntry).where(ToolRegistryEntry.service_slug == service_slug)
    ).scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found for service: {service_slug}")

    return _to_response(tool)


# --- Admin write endpoints ---


@router.post("", response_model=dict, status_code=201)
def create_tool(
    payload: ToolRegistryCreate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Create a new tool registry entry."""
    _validate_domain(payload.domain)
    _validate_category(payload.category)
    _validate_fidelity(payload.fidelity)

    # Check duplicate tool_id
    existing = db.execute(
        select(ToolRegistryEntry).where(ToolRegistryEntry.tool_id == payload.tool_id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Tool with tool_id '{payload.tool_id}' already exists",
        )

    tool = ToolRegistryEntry(
        tool_id=payload.tool_id,
        name_fa=payload.name_fa,
        name_en=payload.name_en,
        domain=payload.domain,
        category=payload.category,
        fidelity=payload.fidelity,
        reference=payload.reference,
        description=payload.description,
        formula=payload.formula,
        service_slug=payload.service_slug,
        endpoint_path=payload.endpoint_path,
        phase=payload.phase,
        is_active=payload.is_active,
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return _to_response(tool)


@router.patch("/{tool_id}", response_model=dict)
def update_tool(
    tool_id: str,
    payload: ToolRegistryUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Update a tool registry entry."""
    tool = db.execute(
        select(ToolRegistryEntry).where(ToolRegistryEntry.tool_id == tool_id)
    ).scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    if payload.name_fa is not None:
        tool.name_fa = payload.name_fa
    if payload.name_en is not None:
        tool.name_en = payload.name_en
    if payload.domain is not None:
        _validate_domain(payload.domain)
        tool.domain = payload.domain
    if payload.category is not None:
        _validate_category(payload.category)
        tool.category = payload.category
    if payload.fidelity is not None:
        _validate_fidelity(payload.fidelity)
        tool.fidelity = payload.fidelity
    if payload.reference is not None:
        tool.reference = payload.reference
    if payload.description is not None:
        tool.description = payload.description
    if payload.formula is not None:
        tool.formula = payload.formula
    if payload.service_slug is not None:
        tool.service_slug = payload.service_slug
    if payload.endpoint_path is not None:
        tool.endpoint_path = payload.endpoint_path
    if payload.phase is not None:
        tool.phase = payload.phase
    if payload.is_active is not None:
        tool.is_active = payload.is_active

    db.commit()
    db.refresh(tool)
    return _to_response(tool)


@router.delete("/{tool_id}", response_model=dict)
def delete_tool(
    tool_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Delete a tool registry entry."""
    tool = db.execute(
        select(ToolRegistryEntry).where(ToolRegistryEntry.tool_id == tool_id)
    ).scalar_one_or_none()

    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    db.delete(tool)
    db.commit()
    return {"deleted": True, "tool_id": tool_id}
