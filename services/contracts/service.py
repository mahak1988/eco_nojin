"""Contract Registry Service - Core business logic for API contract management."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.contracts.models import ContractTestRun, ContractVersionModel
from services.contracts.schemas import (
    ContractResponse,
)


class ContractRegistry:
    """Service for managing API contract versions and compatibility."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Contract Version CRUD
    # =========================================================================

    async def register_contract(self, data: CreateContractRequest) -> ContractResponse:
        """Register a new contract version."""
        # Check if version already exists
        existing = await self.db.execute(
            select(ContractVersionModel).where(
                and_(
                    ContractVersionModel.service_name == data.service_name,
                    ContractVersionModel.version == data.version,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Contract version {data.service_name} v{data.version} already exists")

        # If supersedes specified, verify it exists
        if data.supersedes:
            result = await self.db.execute(
                select(ContractVersionModel).where(ContractVersionModel.id == data.supersedes)
            )
            superseded = result.scalar_one_or_none()
            if not superseded:
                raise ValueError(f"Superseded contract {data.supersedes} not found")

        record = ContractVersionModel(
            service_name=data.service_name,
            version=data.version,
            contract_type=data.contract_type,
            spec=data.spec,
            is_active=True,
            created_by=data.created_by,
            supersedes_id=data.supersedes,
        )

        self.db.add(record)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(record)

        return ContractResponse.model_validate(record)

    async def get_contract(self, service_name: str, version: str) -> dict[str, Any] | None:
        """Get a contract version by service and version."""
        result = await self.db.execute(
            select(ContractVersionModel).where(
                and_(
                    ContractVersionModel.service_name == service_name,
                    ContractVersionModel.version == version,
                )
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        return {
            "id": str(record.id),
            "service_name": record.service_name,
            "version": record.version,
            "contract_type": record.contract_type,
            "spec": record.spec,
            "is_active": record.is_active,
            "created_at": record.created_at,
            "created_by": record.created_by,
            "deprecated_at": record.deprecated_at,
            "deprecation_reason": record.deprecation_reason,
            "supersedes_id": str(record.supersedes_id) if record.supersedes_id else None,
        }

    async def get_active_contract(self, service_name: str) -> dict[str, Any] | None:
        """Get the active contract version for a service."""
        result = await self.db.execute(
            select(ContractVersionModel)
            .where(
                and_(
                    ContractVersionModel.service_name == service_name,
                    ContractVersionModel.is_active,
                )
            )
            .order_by(ContractVersionModel.created_at.desc())
        )
        record = result.scalar_one_or_none()
        if not record:
            return None

        return {
            "id": str(record.id),
            "service_name": record.service_name,
            "version": record.version,
            "contract_type": record.contract_type,
            "spec": record.spec,
            "is_active": record.is_active,
            "created_at": record.created_at,
            "created_by": record.created_by,
        }

    async def list_contracts(
        self,
        service_name: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """List contract versions with filters."""
        query = select(ContractVersionModel)

        if service_name:
            query = query.where(ContractVersionModel.service_name == service_name)
        if is_active is not None:
            query = query.where(ContractVersionModel.is_active == is_active)

        query = query.order_by(desc(ContractVersionModel.created_at))
        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)
        result.scalars().all()

        return [
            {
                "id": str(r.id),
                "service_name": r.service_name,
                "version": r.version,
                "contract_type": r.contract_type,
                "is_active": r.is_active,
                "created_at": r.created_at,
                "created_by": r.created_by,
                "deprecated_at": r.deprecated_at,
                "supersedes_id": str(r.supersedes_id) if r.supersedes_id else None,
            }
            for r in result.scalars().all()
        ]

    async def deprecate_contract(self, service_name: str, version: str, reason: str) -> bool:
        """Deprecate a contract version."""
        result = await self.db.execute(
            select(ContractVersionModel).where(
                and_(
                    ContractVersionModel.service_name == service_name,
                    ContractVersionModel.version == version,
                )
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return False

        record.is_active = False
        record.deprecated_at = datetime.now(UTC)
        record.deprecation_reason = reason

        await self.db.commit()
        return True

    # =========================================================================
    # Compatibility Analysis
    # =========================================================================

    async def check_compatibility(
        self, service_name: str, from_version: str, to_version: str
    ) -> dict[str, Any]:
        """Check compatibility between two contract versions."""
        from_spec = await self.get_contract(service_name, from_version)
        to_spec = await self.get_contract(service_name, to_version)

        if not from_spec or not to_spec:
            raise ValueError("One or both contract versions not found")

        # Compare OpenAPI specs
        diff = self._diff_openapi_specs(from_spec["spec"], to_spec["spec"])
        self._determine_compatibility(diff)

        return {
            "from_version": from_version,
            "to_version": to_version,
            "compatibility": diff["compatibility"],
            "breaking_changes": diff["breaking_changes"],
            "safe_changes": diff["safe_changes"],
            "can_upgrade": diff["compatibility"] in ("full", "backward", "forward"),
            "warnings": diff.get("warnings", []),
        }

    def _diff_openapi_specs(
        self, old_spec: dict[str, Any], new_spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare two OpenAPI specs and identify changes."""
        old_paths = old_spec.get("paths", {})
        new_paths = new_spec.get("paths", {})

        old_endpoints = {
            f"{method.upper()} {path}" for path, methods in old_paths.items() for method in methods
        }
        new_endpoints = {
            f"{method.upper()} {path}" for path, methods in new_paths.items() for method in methods
        }

        added_endpoints = new_endpoints - old_endpoints
        removed_endpoints = old_endpoints - new_endpoints
        common_endpoints = old_endpoints & new_endpoints

        # Check for modified endpoints
        modified_endpoints = []
        for endpoint in common_endpoints:
            method, path = endpoint.split(" ", 1)
            old_op = old_paths.get(path, {}).get(method.lower(), {})
            new_op = new_paths.get(path, {}).get(method.lower(), {})
            if old_op != new_op:
                modified_endpoints.append(endpoint)

        # Schema changes
        old_schemas = set(old_spec.get("components", {}).get("schemas", {}).keys())
        new_schemas = set(new_spec.get("components", {}).get("schemas", {}).keys())

        added_schemas = new_schemas - old_schemas
        removed_schemas = old_schemas - new_schemas
        common_schemas = old_schemas & new_schemas

        # Check modified schemas
        modified_schemas = []
        for schema in common_schemas:
            old_schema = old_spec.get("components", {}).get("schemas", {}).get(schema, {})
            new_schema = new_spec.get("components", {}).get("schemas", {}).get(schema, {})
            if old_schema != new_schema:
                modified_schemas.append(schema)

        # Determine breaking changes
        breaking_changes = []
        safe_changes = []

        # Removed endpoints = breaking
        for ep in removed_endpoints:
            breaking_changes.append({"type": "endpoint_removed", "endpoint": ep})

        # Added endpoints = safe (backward compatible)
        for ep in added_endpoints:
            safe_changes.append({"type": "endpoint_added", "endpoint": ep})

        # Modified endpoints - check if breaking
        for ep in modified_endpoints:
            breaking_changes.append({"type": "endpoint_modified", "endpoint": ep})

        # Removed schemas = potentially breaking
        for schema in removed_schemas:
            breaking_changes.append({"type": "schema_removed", "schema": schema})

        # Added schemas = safe
        for schema in added_schemas:
            safe_changes.append({"type": "schema_added", "schema": schema})

        # Modified schemas - check if breaking
        for schema in modified_schemas:
            safe_changes.append({"type": "schema_modified", "schema": schema})

        # Determine overall compatibility
        if not breaking_changes:
            compatibility = "forward" if added_endpoints or added_schemas else "full"
        elif any(c["type"] == "endpoint_removed" for c in breaking_changes):
            compatibility = "none"
        else:
            compatibility = "backward"

        return {
            "added_endpoints": list(added_endpoints),
            "removed_endpoints": list(removed_endpoints),
            "modified_endpoints": modified_endpoints,
            "added_schemas": list(added_schemas),
            "removed_schemas": list(removed_schemas),
            "modified_schemas": modified_schemas,
            "breaking_changes": breaking_changes,
            "safe_changes": safe_changes,
            "compatibility": compatibility,
        }

    def _determine_compatibility(self, diff: dict[str, Any]) -> str:
        """Determine overall compatibility level."""
        return diff["compatibility"]

    # =========================================================================
    # Contract Test Runs
    # =========================================================================

    async def record_test_run(
        self, contract_version_id: str, test_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Record a contract test run."""
        ContractTestRun(
            contract_version_id=contract_version_id,
            test_type=test_data.get("test_type", "schemathesis"),
            test_tool=test_data.get("test_tool"),
            status=test_data.get("status", "passed"),
            passed=test_data.get("passed", 0),
            failed=test_data.get("failed", 0),
            errors=test_data.get("errors", 0),
            skipped=test_data.get("skipped", 0),
            duration_seconds=test_data.get("duration_seconds"),
            error_details=test_data.get("error_details", {}),
            test_output=test_data.get("test_output"),
            ci_build_id=test_data.get("ci_build_id"),
            ci_branch=test_data.get("ci_branch"),
            ci_commit=test_data.get("ci_commit"),
        )

        self.db.add(record)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(record)

        return {
            "id": str(record.id),
            "contract_version_id": str(record.contract_version_id),
            "status": record.status,
            "passed": record.passed,
            "failed": record.failed,
            "errors": record.errors,
            "skipped": record.skipped,
            "duration_seconds": record.duration_seconds,
            "created_at": record.created_at,
        }

    async def get_test_history(
        self, contract_version_id: str, page: int = 1, page_size: int = 20
    ) -> list[dict[str, Any]]:
        """Get test run history for a contract version."""

        query = (
            select(ContractTestRun)
            .where(ContractTestRun.contract_version_id == contract_version_id)
            .order_by(desc(ContractTestRun.created_at))
        )

        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)
        result.scalars().all()

        return [
            {
                "id": str(r.id),
                "test_type": r.test_type,
                "test_tool": r.test_tool,
                "status": r.status,
                "passed": r.passed,
                "failed": r.failed,
                "errors": r.errors,
                "skipped": r.skipped,
                "duration_seconds": r.duration_seconds,
                "error_details": r.error_details,
                "created_at": r.created_at,
            }
            for r in result.scalars().all()
        ]
