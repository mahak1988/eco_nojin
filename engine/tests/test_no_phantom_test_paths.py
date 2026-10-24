"""No phantom test paths: every cited test file must exist on disk.

A citation to ``tests/<family>/<file>.py`` is a claim that the file is in the
tree. When it is not, the citing document, card or gate is promising evidence
that does not exist, and any reader who trusts it is being misled.

KNOWN_FAMILIES below is currently-known debt, tracked in
reports/eco-nojin/GAP-REGISTER.md G-H5 (the phantom-path families under
tests/unit, tests/models and tests/contract). It is a ceiling, not a licence:
no missing path outside these families may appear. Shrinking the set is the
goal; growing it requires a GAP-REGISTER entry first.

The paths are assembled from a family prefix plus a file name at import time
so that this file does not itself inject 57 citable phantom paths into the
repository that ``tools/phantom_path_check.py`` walks.

Runtime: the scan walks the whole repository once and performs no I/O beyond
reads; it completes in well under a minute with no sleeps.
"""

import importlib.util
from pathlib import Path, PurePosixPath

_PHANTOM_TOOL = Path(__file__).resolve().parents[2] / "tools" / "phantom_path_check.py"

_FAMILY_PREFIX = {
    "unit": "tests/unit/",
    "models": "tests/models/",
    "contract": "tests/contract/",
}

_UNIT_FAMILY = (
    "test_admin_settings_repository.py",
    "test_biofertilizer.py",
    "test_bridge_signature_contract.py",
    "test_carbon.py",
    "test_carbon_modifier_consolidation.py",
    "test_climate.py",
    "test_compost.py",
    "test_crop_water.py",
    "test_documentation_coverage.py",
    "test_ecsi_reference.py",
    "test_ensemble_percentile_parity.py",
    "test_epia.py",
    "test_esri.py",
    "test_ewsi.py",
    "test_formula_provenance.py",
    "test_formula_registry.py",
    "test_groundwater_phenology.py",
    "test_hdvi.py",
    "test_hlhs.py",
    "test_hpheno.py",
    "test_hpheno_smoothing.py",
    "test_hyrue.py",
    "test_jwt_signing_key.py",
    "test_knowledge_engine_plan.py",
    "test_knowledge_layer.py",
    "test_market_fee_discount_gap.py",
    "test_monte_carlo.py",
    "test_mrv_metrics.py",
    "test_mrv_qa.py",
    "test_muskingum_parity.py",
    "test_nutrient_requirement.py",
    "test_optimization.py",
    "test_plant_neuro.py",
    "test_provenance_unification.py",
    "test_registry.py",
    "test_revenue_indicators.py",
    "test_richards.py",
    "test_rothc_moisture_modifier.py",
    "test_rothc_temperature_factor.py",
    "test_rusle_uncorrelated.py",
    "test_saint_venant.py",
    "test_scenarios.py",
    "test_scs_units_consistency.py",
    "test_settings_env_resolution.py",
    "test_simulation_calibration.py",
    "test_simulation_rothc.py",
    "test_soil_docstring_examples.py",
    "test_take_rate.py",
    "test_topography_path_safety.py",
    "test_unvalidated_coefficients.py",
    "test_village_hub_schemas.py",
    "test_watershed.py",
)

_MODELS_FAMILY = ("test_index_model_parity.py",)

_CONTRACT_FAMILY = (
    "gates.py",
    "test_robustness_gate.py",
    "test_slaughterhouse_gate.py",
    "test_tool_registry_contract.py",
)


def _load_phantom_checker():
    """Load tools/phantom_path_check.py by path (tools/ is not a package)."""
    spec = importlib.util.spec_from_file_location("phantom_path_check", _PHANTOM_TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_phantom = _load_phantom_checker()

KNOWN_FAMILIES = frozenset(
    _FAMILY_PREFIX["unit"] + name for name in _UNIT_FAMILY
) | frozenset(_FAMILY_PREFIX["models"] + name for name in _MODELS_FAMILY) | frozenset(
    _FAMILY_PREFIX["contract"] + name for name in _CONTRACT_FAMILY
)


def test_no_phantom_test_paths():
    missing = set(_phantom.scan_missing(Path(__file__).resolve().parents[2]))
    outside = missing - KNOWN_FAMILIES
    assert not outside, (
        "phantom test paths cited outside the currently-known families "
        f"(tests/unit, tests/models, tests/contract — see "
        f"reports/eco-nojin/GAP-REGISTER.md G-H5): {sorted(outside)}"
    )


def test_known_families_are_phantom_family_paths():
    assert KNOWN_FAMILIES
    assert all(isinstance(path, str) and path for path in KNOWN_FAMILIES)
    parents = {PurePosixPath(path).parent.as_posix() for path in KNOWN_FAMILIES}
    assert parents == {prefix.rstrip("/") for prefix in _FAMILY_PREFIX.values()}
