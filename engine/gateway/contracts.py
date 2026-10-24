"""Data contracts for the Engine Gateway.

Step 1 of the A-1 remediation: the request, result, specification and error
dataclasses that make up the gateway's public data surface. The definitions are
reproduced verbatim from `engine/gateway/__init__.py`; only the module
boundary moved, so the public surface stays byte-identical.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UnitSpec:
    """Unit specification for a value."""
    unit: str
    si_equivalent: float = 1.0
    uncertainty: float | None = None


@dataclass
class ProvenanceSpec:
    """Provenance initialization for a computation."""
    source: str
    source_type: str  # OBSERVATION, MODEL_OUTPUT, LOCAL_KNOWLEDGE, etc.
    trust_level: float = 1.0
    provenance_id: str | None = None


@dataclass
class UncertaintySpec:
    """Uncertainty metadata initialized to 'not estimated'."""
    uncertainty_type: str = "NOT_ESTIMATED"
    value: float | None = None
    unit: str | None = None
    method: str | None = None
    confidence_level: float | None = None


@dataclass
class ExecutionMetadata:
    """Metadata captured during execution."""
    gateway_version: str = "1.0.0"
    timestamp: str | None = None
    execution_id: str | None = None
    engine_version: str | None = None
    cpp_backend: bool = False
    trace_id: str | None = None


@dataclass
class ModelSpec:
    """Specification of the scientific model to use."""
    model_id: str
    model_version: str
    model_name: str
    model_type: str
    domain: str
    purpose: str
    assumptions: list[str]
    limitations: list[str]


@dataclass
class InputSpec:
    """Specification of a single input parameter."""
    name: str
    value: float
    unit: UnitSpec
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    normalized_value: float | None = None
    normalized_unit: str | None = None


@dataclass
class GatewayRequest:
    """A request to the Engine Gateway.

    All requests to the engine must pass through this structure.
    """
    model_id: str
    inputs: dict[str, Any]
    input_units: dict[str, UnitSpec]
    provenance: ProvenanceSpec
    parameters: dict[str, Any] = field(default_factory=dict)
    uncertainty: UncertaintySpec | None = None
    execution_metadata: ExecutionMetadata | None = field(default_factory=ExecutionMetadata)


@dataclass
class GatewayResult:
    """A normalized result from the Engine Gateway.

    Every result includes provenance, uncertainty, and execution metadata.
    The ``evidence_id`` links the result to the Evidence item generated for
    the execution; ``execution.trace_id`` is the shared key for the full
    provenance chain.

    ``data_source`` records where the inputs to this result came from so that
    no computed value can be mislabeled as a measurement (INV-007).
    """
    values: dict[str, Any]
    output_units: dict[str, UnitSpec]
    model: ModelSpec
    provenance: ProvenanceSpec
    uncertainty: UncertaintySpec
    execution: ExecutionMetadata
    data_source: str
    validation: list[ValidationResult] = field(default_factory=list)
    evidence_id: str | None = None
    evidence: Any = None


@dataclass
class GatewayError:
    """A normalized error from the Engine Gateway."""
    error_code: str
    message: str
    model_id: str | None
    validation_errors: list[str] = field(default_factory=list)
    execution: ExecutionMetadata | None = None
    evidence_id: str | None = None


__all__ = [
    "UnitSpec",
    "ProvenanceSpec",
    "UncertaintySpec",
    "ExecutionMetadata",
    "ModelSpec",
    "InputSpec",
    "ValidationResult",
    "GatewayRequest",
    "GatewayResult",
    "GatewayError",
]
