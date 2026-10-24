"""API Contract Registry Router."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.errors import safe_detail_for_status
from services.contracts.schemas import (
    CompatibilityResult,
    ContractCreate,
    ContractDiff,
    ContractResponse,
)
from services.contracts.service import ContractRegistry

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_contract_registry(db: Annotated[AsyncSession, Depends(get_db)]) -> ContractRegistry:
    return ContractRegistry(db)


# =============================================================================
# Contract Version Management
# =============================================================================


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def register_contract(
    data: ContractCreate,
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Register a new API contract version."""
    try:
        return await registry.register_contract(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/{service_name}/{version}", response_model=ContractResponse)
async def get_contract(
    service_name: str,
    version: str,
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Get a specific contract version."""
    contract = await registry.get_contract(service_name, version)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract version not found")
    return contract


@router.get("/{service_name}/active", response_model=ContractResponse)
async def get_active_contract(
    service_name: str,
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Get the active contract version for a service."""
    contract = await registry.get_active_contract(service_name)
    if not contract:
        raise HTTPException(status_code=404, detail="No active contract found for service")
    return contract


@router.get("", response_model=list[ContractResponse])
async def list_contracts(
    service_name: Annotated[str | None, Query(description="Filter by service name")] = None,
    is_active: Annotated[bool | None, Query(description="Filter by active status")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)] = None,
):
    """List contract versions with filtering."""
    return await registry.list_contracts(
        service_name=service_name,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.post("/{service_name}/{version}/deprecate", status_code=status.HTTP_200_OK)
async def deprecate_contract(
    service_name: str,
    version: str,
    reason: Annotated[str, Query(description="Reason for deprecation")],
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Deprecate a contract version."""
    success = await registry.deprecate_contract(service_name, version, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Contract version not found")
    return {"status": "deprecated", "service_name": service_name, "version": version}


# =============================================================================
# Compatibility Analysis
# =============================================================================


@router.get("/{service_name}/compatibility", response_model=CompatibilityResult)
async def check_compatibility(
    service_name: str,
    from_version: Annotated[str, Query(description="Source version")],
    to_version: Annotated[str, Query(description="Target version")],
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Check compatibility between two contract versions."""
    try:
        return await registry.check_compatibility(service_name, from_version, to_version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


@router.get("/{service_name}/diff", response_model=ContractDiff)
async def get_contract_diff(
    service_name: str,
    from_version: Annotated[str, Query(description="Source version")],
    to_version: Annotated[str, Query(description="Target version")],
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Get detailed diff between two contract versions."""
    try:
        from_spec = await registry.get_contract(service_name, from_version)
        to_spec = await registry.get_contract(service_name, to_version)

        if not from_spec or not to_spec:
            raise HTTPException(status_code=404, detail="One or both contract versions not found")

        # Reuse the diff logic from the service
        from services.contracts.service import ContractRegistry as CR

        diff = CR._diff_openapi_specs({}, from_spec["spec"], to_spec["spec"])

        return ContractDiff(
            added_endpoints=diff["added_endpoints"],
            removed_endpoints=diff["removed_endpoints"],
            modified_endpoints=diff["modified_endpoints"],
            added_schemas=diff["added_schemas"],
            removed_schemas=diff["removed_schemas"],
            modified_schemas=diff["modified_schemas"],
            breaking_changes=diff["breaking_changes"],
            safe_changes=diff["safe_changes"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


# =============================================================================
# Contract Test Runs
# =============================================================================


@router.post("/{service_name}/{version}/test-runs", status_code=status.HTTP_201_CREATED)
async def record_test_run(
    service_name: str,
    version: str,
    test_data: dict,
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)],
):
    """Record a contract test run result."""
    # Get contract version ID
    contract = await registry.get_contract(service_name, version)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract version not found")

    return await registry.record_test_run(contract["id"], test_data)


@router.get("/{service_name}/{version}/test-runs")
async def get_test_history(
    service_name: str,
    version: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    registry: Annotated[ContractRegistry, Depends(get_contract_registry)] = None,
):
    """Get test run history for a contract version."""
    contract = await registry.get_contract(service_name, version)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract version not found")

    return await registry.get_test_history(contract["id"], page, page_size)
