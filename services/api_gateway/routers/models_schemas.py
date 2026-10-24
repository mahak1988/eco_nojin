"""Response models for the models router (public scientific-model catalogue).

Added 2026-10-04. All five routes declared ``response_model=dict``.

The field sets were measured rather than transcribed:

* ``list_models`` -> 10 keys, verified on the live registry
  (description, domain, fidelity, limitations, name_en, name_fa, params,
  reference, slug, validity), 22 models.
* ``run_model("rothc_pools", <defaults>)`` -> ``slug``, ``fidelity``, ``result``,
  ``executed_ms``. Chosen because it is the first model whose every parameter
  has a default, so it is the only one that runs without hand-built kwargs.
* ``pinn_surrogate.status()`` -> ``available``, ``note``.
* ``cpp_bridge.backend_status()`` -> ``cpp_available``, ``backend``,
  ``import_error``, ``telemetry``; the router adds ``available``, ``module_path``,
  ``symbols``, ``numba_available``, ``array_cpp_threshold``.

``fidelity`` is typed as a literal rather than ``str`` because it is a closed
set of three and a client branches on it. An unknown value is now a schema the
reader can see, instead of a string that silently means nothing.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Fidelity = Literal["official", "simplified", "experimental"]


class ModelParamOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    label: str | None = None
    unit: str | None = Field(
        default=None,
        description="SI or scientific unit. Only 7 of 327 gateway schemas carried "
        "a unit before this one; a number without a unit is not a result.",
    )
    default: Any = None
    kind: str | None = None


class ModelSummaryOut(BaseModel):
    """One entry of `list_models` -- the catalogue row."""

    model_config = ConfigDict(extra="allow")

    slug: str
    name_fa: str | None = None
    name_en: str | None = None
    domain: str | None = None
    fidelity: Fidelity | None = None
    reference: str | None = Field(
        default=None, description="The citation a client should show beside the model."
    )
    description: str | None = None
    validity: str | None = None
    limitations: str | None = None
    params: list[ModelParamOut] = Field(default_factory=list)


class ModelsIndexOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    count: int
    fidelity_counts: dict[Fidelity, int] = Field(
        default_factory=dict,
        description="Row count per fidelity badge; official/simplified/experimental.",
    )
    models: list[ModelSummaryOut] = Field(default_factory=list)


class ModelDetailOut(ModelSummaryOut):
    """GET /{slug} -- the catalogue row plus the model card."""


class ModelRunOut(BaseModel):
    """POST /{slug}/run.

    Note this is *not* HydromaRunResponse: this registry has no `provenance`
    field, and adding one would be a claim rather than a serialisation. The
    `fidelity` badge is what this surface honestly carries.
    """

    model_config = ConfigDict(extra="allow")

    slug: str
    fidelity: Fidelity | None = None
    result: Any = Field(default=None, description="The computed value or dict.")
    executed_ms: float | None = Field(
        default=None, description="Wall-clock cost, so a caller can weigh the answer."
    )


class PinnStatusOut(BaseModel):
    """GET /pinn-status. The docstring calls it 'honest' and it is: two fields,
    and `available` is measured rather than asserted."""

    model_config = ConfigDict(extra="allow")

    available: bool
    note: str | None = None


class CppStatusOut(BaseModel):
    """GET /cpp-status.

    Both fields and the import_error string are kept because the module
    deliberately reports the failure rather than hiding it: this router's own
    docstring records that a previous loader disagreed with /health, and the fix
    was to make both read one source.
    """

    model_config = ConfigDict(extra="allow")

    available: bool = Field(default=False, description="Mirrors backend_status()['cpp_available'].")
    backend: str | None = None
    import_error: str | None = Field(
        default=None, description="Populated when the backend failed to load."
    )
    module_path: str | None = None
    symbols: int = Field(default=0, description="Public symbols exported by the loaded module.")
    numba_available: bool = Field(default=False)
    array_cpp_threshold: int | None = None
    telemetry: dict[str, Any] | Any = Field(default_factory=dict)
