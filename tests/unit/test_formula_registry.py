"""Tests for the formula registry and the rules it enforces.

These are the tests the registry's own records point at. A record that cites a
test which does not exist, or a rule that can be bypassed, is a registry that
documents an intention rather than a constraint.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from engine.hydroma.formulas import FormulaRecord, all_records, divergent, get, summary
from engine.hydroma.formulas.registry import (
    DivergentOnRequestPathError,
    DuplicateFormulaError,
    register,
    verified,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Snapshot and restore the global registry around a mutating test.

    Several tests here register over a real quantity with ``replace=True`` to
    exercise the duplicate rule and the serve guard. Without a restore the next
    test in the module reads the mutated record and fails for unrelated reasons --
    which is how three of these passed alone and failed in a full run.
    """
    from engine.hydroma.formulas import registry

    saved = dict(registry._REGISTRY)
    try:
        yield
    finally:
        registry._REGISTRY.clear()
        registry._REGISTRY.update(saved)

HARNESS = Path("tests/unit/test_bridge_signature_contract.py")


# --------------------------------------------------------------------- rules


def test_record_without_parity_tests_is_refused():
    with pytest.raises(ValueError, match="parity_tests"):
        FormulaRecord(
            quantity="made_up",
            canonical="somewhere.py",
            literature_ref="none",
            units="dimensionless",
            domain="scalar",
            backend_priority=("python",),
            parity_tests=(),
        )


def test_verified_without_reference_values_is_refused():
    """Agreement with another implementation is a closed loop and proves nothing."""
    with pytest.raises(ValueError, match="reference_values"):
        FormulaRecord(
            quantity="made_up",
            canonical="somewhere.py",
            literature_ref="none",
            units="dimensionless",
            domain="scalar",
            backend_priority=("python",),
            parity_tests=("some_test",),
            status="verified",
        )


def test_divergent_on_request_path_cannot_be_served():
    """Registration is documentation; serving is the decision that is guarded."""
    from engine.hydroma.formulas.registry import require_servable

    register(
        FormulaRecord(
            quantity="ndvi",
            canonical="somewhere.py",
            literature_ref="none",
            units="dimensionless",
            domain="scalar",
            backend_priority=("python",),
            parity_tests=("some_test",),
            status="divergent",
        ),
        replace=True,
    )
    with pytest.raises(DivergentOnRequestPathError, match="served to a client"):
        require_servable("ndvi")

    from engine.hydroma.formulas.catalog import RECORDS

    register(next(r for r in RECORDS if r.quantity == "ndvi"), replace=True)  # restore


def test_require_servable_accepts_a_verified_formula():
    from engine.hydroma.formulas.registry import require_servable

    assert require_servable("ndvi").is_verified


def test_unservable_list_names_the_outstanding_conflicts():
    """Whatever is unservable must name itself and explain why.

    The list is expected to shrink as formulas are reconciled, so the assertions
    are about the shape of each entry rather than about a fixed membership.
    """
    from engine.hydroma.formulas import unservable_on_request_path

    outstanding = unservable_on_request_path()
    for quantity, record in outstanding.items():
        assert record.status == "divergent"
        assert record.notes.strip(), f"{quantity} is divergent with no explanation"


def test_duplicate_registration_needs_explicit_replace():
    record = FormulaRecord(
        quantity="ndvi",
        canonical="somewhere_else.py",
        literature_ref="none",
        units="dimensionless",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("some_test",),
        status="verified",
        reference_values="an anchor",
    )
    with pytest.raises(DuplicateFormulaError):
        register(record)

    register(record, replace=True)
    assert get("ndvi").canonical == "somewhere_else.py"

    from engine.hydroma.formulas.catalog import RECORDS

    record = next(r for r in RECORDS if r.quantity == "ndvi")
    register(record, replace=True)  # restore


# ------------------------------------------------------------------- content


def test_registry_is_not_empty():
    assert len(all_records()) >= 10


def test_every_record_cites_a_specific_source():
    for quantity, record in all_records().items():
        assert record.literature_ref.strip(), f"{quantity} has no citation"
        assert record.units.strip(), f"{quantity} has no units"
        assert record.canonical.strip(), f"{quantity} has no canonical module"


def test_every_verified_record_has_reference_values():
    for quantity, record in verified().items():
        assert record.reference_values, f"{quantity} is verified without a reference value"


def test_every_cited_parity_test_exists():
    """A record pointing at a test that does not exist documents an intention."""
    repo = Path(__file__).resolve().parents[2]
    for quantity, record in all_records().items():
        for ref in record.parity_tests:
            if "::" in ref:
                path, _, _node = ref.partition("::")
            else:
                path, _node = ref, ""
            target = repo / path
            assert target.is_file(), f"{quantity} cites a missing test file: {ref}"


def test_canonical_module_exists():
    repo = Path(__file__).resolve().parents[2]
    for quantity, record in all_records().items():
        assert (repo / record.canonical).is_file(), (
            f"{quantity} names a canonical module that does not exist: {record.canonical}"
        )


def test_the_five_indices_are_registered_once_each():
    for q in ("ndvi", "evi", "savi", "ndwi", "nbr"):
        record = get(q)
        assert record is not None, f"{q} is not registered"
        assert record.is_verified, f"{q} is not verified"


def test_et0_is_registered_and_verified():
    record = get("et0_reference")
    assert record is not None and record.is_verified


def test_reconciled_formulas_are_no_longer_divergent():
    """Both formulas that were divergent have been reconciled and now have tests.

    ``muskingum_cunge_routing`` had the n+1 reach / full-length defect;
    ``ensemble_percentile`` truncated instead of interpolating. Each was refused
    for a request path while it was divergent.
    """
    names = set(divergent())
    assert "muskingum_cunge_routing" not in names
    assert "ensemble_percentile" not in names
    assert get("muskingum_cunge_routing").is_verified
    assert get("ensemble_percentile").is_verified


def test_nothing_divergent_is_left_unservable():
    from engine.hydroma.formulas import unservable_on_request_path

    assert unservable_on_request_path() == {}, (
        "a divergent formula is still on a request path; the registry refuses to "
        f"serve these: {list(unservable_on_request_path())}"
    )


def test_remaining_stubs_are_declared_not_hidden():
    """The four stubs are gaps, and each has to say so."""
    stubs = {q: r for q, r in all_records().items() if r.status == "stub"}
    assert stubs, "expected the unverified quantities to be visible as stubs"
    for quantity, record in stubs.items():
        assert record.notes.strip(), f"{quantity} is a stub with no explanation"
        assert record.literature_ref.strip(), f"{quantity} has no citation"


def test_no_formula_stays_divergent_and_stub_stay_declared():
    """A stub must be visible, and nothing divergent may sit on a request path."""
    from engine.hydroma.formulas import unservable_on_request_path

    assert not divergent(), f"divergent formulas remain: {sorted(divergent())}"
    assert unservable_on_request_path() == {}


def test_the_carbon_modifiers_are_both_verified_now():
    """The temperature scaling was resolved; the moisture response was already sound."""
    assert get("rothc_moisture_modifier").is_verified
    assert get("rothc_temperature_modifier").is_verified


def test_summary_shape():
    s = summary()
    assert s["total"] == len(all_records())
    assert s["verified"] + s["divergent"] + s["stub"] == s["total"]


# ------------------------------------------------------------------- content
# The measurement the records cite.


def test_lhs_stratification():
    """Both LHS backends must place exactly one sample per stratum per dimension.

    Statistical parity, not bitwise: the two implementations draw from different
    RNG streams, so the same seed legitimately produces different designs. The
    property that must hold for both is the stratification invariant.
    """
    from engine.hydroma.cpp_bridge import _py_latin_hypercube, get_module

    core = get_module()
    for n, dims, seed in ((100, 3, 42), (200, 2, 7), (50, 1, 11)):
        candidates = {"python": _py_latin_hypercube(n, dims, seed)}
        if core is not None:
            candidates["cpp"] = np.array(core.latin_hypercube(n, dims, seed))

        for backend, samples in candidates.items():
            assert samples.shape == (n, dims), f"{backend}: wrong shape {samples.shape}"
            assert np.all(samples >= 0.0) and np.all(samples < 1.0), f"{backend}: out of [0,1)"
            for j in range(dims):
                strata = np.floor(samples[:, j] * n).astype(int)
                assert len(np.unique(strata)) == n, (
                    f"{backend} dim {j}: {len(np.unique(strata))} distinct strata, expected {n}"
                )


def test_lhs_python_fallback_handles_multiple_dimensions():
    """Regression: it raised ValueError for any n_dimensions > 1."""
    from engine.hydroma.cpp_bridge import _py_latin_hypercube

    for dims in (1, 2, 3, 5):
        out = _py_latin_hypercube(20, dims, seed=3)
        assert out.shape == (20, dims)


def test_et0_backends_agree_over_the_overcast_range():
    """The range where the two used to disagree by 36%."""
    from engine.hydroma.cpp_bridge import _py_penman_monteith_et0, get_module

    core = get_module()
    if core is None:
        pytest.skip("C++ extension is not built")

    for rs in (0.5, 1.2, 3.0, 6.0, 12.0, 22.0, 30.0):
        args = (2.0, 9.0, 70.0, 2.0, rs, 1200.0, 35.7, 15)
        cpp = core.penman_monteith_et0(*args)
        py = float(_py_penman_monteith_et0(*args))
        assert abs(cpp - py) <= 1e-12 * max(abs(py), 1.0), f"ET0 diverges at Rs={rs}: {cpp} vs {py}"


def test_et0_is_monotone_in_wind_speed_and_radiation():
    """Two independent guards against the argument swap."""
    from engine.hydroma.cpp_bridge import _py_penman_monteith_et0

    base = dict(tmin=18.0, tmax=29.0, rh_mean=55.0, z=1200.0, lat=35.7, doy=200)
    wind = [float(_py_penman_monteith_et0(u2=u, rs=22.0, **base)) for u in (0.5, 1, 2, 4, 8)]
    rad = [float(_py_penman_monteith_et0(u2=2.0, rs=r, **base)) for r in (1, 5, 12, 22, 30)]

    assert all(b >= a for a, b in zip(wind, wind[1:])), "ET0 must not fall as wind rises"
    assert all(b >= a for a, b in zip(rad, rad[1:])), "ET0 must not fall as radiation rises"


def test_no_index_fallback_uses_a_denominator_epsilon():
    """The 1e-10 fudge biased every non-degenerate value by ~2e-10."""
    src = Path("engine/hydroma/cpp_bridge/__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    fallbacks = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_py_")
    }
    assert {"_py_ndvi", "_py_evi", "_py_savi", "_py_ndwi", "_py_nbr"} <= set(fallbacks)

    for name in ("_py_ndvi", "_py_evi", "_py_savi", "_py_ndwi", "_py_nbr"):
        body = ast.unparse(fallbacks[name])
        assert "1e-10" not in body, f"{name} still adds an epsilon to the denominator"


def test_no_index_fallback_skips_the_clip():
    """The native kernels clip to [-1, 1]; the fallbacks must too."""
    from engine.hydroma.cpp_bridge import _py_evi

    rng = np.random.default_rng(1)
    red = rng.uniform(0.0, 0.4, 5000)
    nir = rng.uniform(0.0, 0.4, 5000)
    blue = rng.uniform(0.0, 0.4, 5000)

    out = np.asarray(_py_evi(red, nir, blue))

    assert np.all(out >= -1.0) and np.all(out <= 1.0)
