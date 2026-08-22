"""API endpoints for Blockchain Ledger."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.business_modules.blockchain.carbon_registry import get_carbon_registry
from services.business_modules.blockchain.supply_chain import get_supply_chain_registry
from services.business_modules.blockchain.web3_provider import get_web3_provider

router = APIRouter(prefix="/api/v1/blockchain", tags=["Blockchain Ledger"])


# ============================================================================
# Pydantic Models
# ============================================================================


class RegisterProjectRequest(BaseModel):
    owner: str = Field(..., min_length=1, max_length=100)
    project_type: str = Field(..., min_length=1, max_length=100)
    area_ha: float = Field(..., gt=0, le=100000)
    duration_years: int = Field(..., ge=1, le=100)


class VerifyProjectRequest(BaseModel):
    verifier: str = Field(..., min_length=1, max_length=100)


class IssueCreditsRequest(BaseModel):
    amount: float = Field(..., gt=0, le=1000000)
    owner: str = Field(..., min_length=1)


class TransferCreditsRequest(BaseModel):
    credit_id: str
    from_owner: str
    to_owner: str


class RetireCreditsRequest(BaseModel):
    owner: str = Field(..., min_length=1)


class RegisterProductRequest(BaseModel):
    producer: str = Field(..., min_length=1, max_length=100)
    batch_number: str = Field(..., min_length=1, max_length=100)
    initial_event: str = Field("harvested", max_length=50)
    location: str = Field("", max_length=200)
    notes: str = Field("", max_length=500)


class AddTraceEventRequest(BaseModel):
    product_id: str
    event_type: str = Field(..., max_length=50)
    location: str = Field(..., max_length=200)
    actor: str = Field(..., min_length=1, max_length=100)
    notes: str = Field("", max_length=500)


# ============================================================================
# Carbon Registry Endpoints
# ============================================================================


@router.post("/carbon/projects")
def register_carbon_project(payload: RegisterProjectRequest):
    """Register a new carbon project on blockchain."""
    registry = get_carbon_registry()
    project = registry.register_project(
        owner=payload.owner,
        project_type=payload.project_type,
        area_ha=payload.area_ha,
        duration_years=payload.duration_years,
    )

    return {
        "project_id": project.project_id,
        "owner": project.owner,
        "project_type": project.project_type,
        "area_ha": project.area_ha,
        "duration_years": project.duration_years,
        "status": project.status.value,
        "tx_hash": project.tx_hash,
        "created_at": project.created_at.isoformat(),
    }


@router.post("/carbon/projects/{project_id}/verify")
def verify_carbon_project(project_id: str, payload: VerifyProjectRequest):
    """Verify a carbon project."""
    registry = get_carbon_registry()

    try:
        project = registry.verify_project(project_id, payload.verifier)
        return {
            "project_id": project.project_id,
            "status": project.status.value,
            "verifier": project.verifier,
            "verified_at": project.verified_at.isoformat(),
            "tx_hash": project.tx_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/carbon/projects/{project_id}/issue")
def issue_carbon_credits(project_id: str, payload: IssueCreditsRequest):
    """Issue carbon credits for a verified project."""
    registry = get_carbon_registry()

    try:
        credit = registry.issue_credits(project_id, payload.amount, payload.owner)
        return {
            "credit_id": credit.credit_id,
            "project_id": credit.project_id,
            "owner": credit.owner,
            "amount": credit.amount,
            "issued_at": credit.issued_at.isoformat(),
            "tx_hash": credit.tx_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/carbon/credits/transfer")
def transfer_carbon_credits(payload: TransferCreditsRequest):
    """Transfer carbon credits between owners."""
    registry = get_carbon_registry()

    try:
        credit = registry.transfer_credits(
            payload.credit_id,
            payload.from_owner,
            payload.to_owner,
        )
        return {
            "credit_id": credit.credit_id,
            "from": payload.from_owner,
            "to": payload.to_owner,
            "amount": credit.amount,
            "tx_hash": credit.tx_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/carbon/credits/{credit_id}/retire")
def retire_carbon_credits(credit_id: str, payload: RetireCreditsRequest):
    """Retire carbon credits (permanently remove from circulation)."""
    registry = get_carbon_registry()

    try:
        credit = registry.retire_credits(credit_id, payload.owner)
        return {
            "credit_id": credit.credit_id,
            "owner": credit.owner,
            "amount": credit.amount,
            "retired": credit.retired,
            "retired_at": credit.retired_at.isoformat(),
            "tx_hash": credit.tx_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/carbon/projects/{project_id}")
def get_carbon_project(project_id: str):
    """Get carbon project details."""
    registry = get_carbon_registry()
    project = registry.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project.project_id,
        "owner": project.owner,
        "project_type": project.project_type,
        "area_ha": project.area_ha,
        "duration_years": project.duration_years,
        "status": project.status.value,
        "credits_issued": project.credits_issued,
        "credits_retired": project.credits_retired,
        "verifier": project.verifier,
        "created_at": project.created_at.isoformat(),
        "tx_hash": project.tx_hash,
    }


@router.get("/carbon/credits/{credit_id}")
def get_carbon_credit(credit_id: str):
    """Get carbon credit details."""
    registry = get_carbon_registry()
    credit = registry.get_credit(credit_id)

    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")

    return {
        "credit_id": credit.credit_id,
        "project_id": credit.project_id,
        "owner": credit.owner,
        "amount": credit.amount,
        "issued_at": credit.issued_at.isoformat(),
        "retired": credit.retired,
        "retired_at": credit.retired_at.isoformat() if credit.retired_at else None,
        "tx_hash": credit.tx_hash,
    }


@router.get("/carbon/stats")
def carbon_stats():
    """Get carbon registry statistics."""
    registry = get_carbon_registry()
    return registry.get_stats()


# ============================================================================
# Supply Chain Endpoints
# ============================================================================


@router.post("/supply-chain/products")
def register_supply_chain_product(payload: RegisterProductRequest):
    """Register a new product in supply chain."""
    registry = get_supply_chain_registry()
    product = registry.register_product(
        producer=payload.producer,
        batch_number=payload.batch_number,
        initial_event=payload.initial_event,
        location=payload.location,
        notes=payload.notes,
    )

    return {
        "product_id": product.product_id,
        "producer": product.producer,
        "batch_number": product.batch_number,
        "created_at": product.created_at.isoformat(),
        "events_count": len(product.events),
        "tx_hash": product.tx_hash,
    }


@router.post("/supply-chain/products/{product_id}/events")
def add_trace_event(product_id: str, payload: AddTraceEventRequest):
    """Add a trace event to a product."""
    registry = get_supply_chain_registry()

    try:
        event = registry.add_event(
            product_id=product_id,
            event_type=payload.event_type,
            location=payload.location,
            actor=payload.actor,
            notes=payload.notes,
        )
        return {
            "event_id": event.event_id,
            "product_id": event.product_id,
            "event_type": event.event_type,
            "location": event.location,
            "actor": event.actor,
            "timestamp": event.timestamp.isoformat(),
            "tx_hash": event.tx_hash,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/supply-chain/products/{product_id}")
def get_supply_chain_product(product_id: str):
    """Get product with full trace history."""
    registry = get_supply_chain_registry()
    product = registry.get_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "product_id": product.product_id,
        "producer": product.producer,
        "batch_number": product.batch_number,
        "created_at": product.created_at.isoformat(),
        "verified": product.verified,
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "location": e.location,
                "actor": e.actor,
                "notes": e.notes,
                "timestamp": e.timestamp.isoformat(),
                "tx_hash": e.tx_hash,
            }
            for e in product.events
        ],
        "tx_hash": product.tx_hash,
    }


@router.get("/supply-chain/products/{product_id}/history")
def get_product_history(product_id: str):
    """Get full trace history for a product."""
    registry = get_supply_chain_registry()

    try:
        events = registry.get_product_history(product_id)
        return {
            "product_id": product_id,
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "location": e.location,
                    "actor": e.actor,
                    "notes": e.notes,
                    "timestamp": e.timestamp.isoformat(),
                    "tx_hash": e.tx_hash,
                }
                for e in events
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/supply-chain/stats")
def supply_chain_stats():
    """Get supply chain statistics."""
    registry = get_supply_chain_registry()
    return registry.get_stats()


# ============================================================================
# Blockchain Info Endpoints
# ============================================================================


@router.get("/health")
def blockchain_health():
    """Get blockchain service status."""
    return {
        "status": "operational",
        "service": "Blockchain Ledger",
        "mode": "simulation",  # Research mode uses in-memory simulation
        "features": {
            "carbon_registry": True,
            "supply_chain": True,
            "smart_contracts": True,
            "transaction_tracking": True,
        },
        "note": "In-memory simulation for research. Integrate real blockchain for production.",
    }


@router.get("/info")
def blockchain_info():
    """Get blockchain network information."""
    provider = get_web3_provider()
    try:
        w3 = provider.connect()
        return {
            "connected": True,
            "block_number": w3.eth.block_number,
            "chain_id": w3.eth.chain_id,
            "accounts_count": len(provider.get_accounts()),
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
