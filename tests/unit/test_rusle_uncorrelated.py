"""RUSLE must be the plain five-factor product.

A = R * K * LS * C * P, per Foster et al. (1981) and Renard et al., USDA
Agriculture Handbook 703 (1997).

Two places quietly altered it, and a published quantity is involved in both:

* ``engine/hydroma/core/core.py`` multiplied the result by a default
  ``calibration`` of 0.10. It cited nothing, it was not part of RUSLE, and it
  divided the answer by ten. The native kernel at ``erosion.cpp:19`` has never
  applied it, so the two implementations disagreed by a factor of ten.
* ``services/scientific_motors/chain_runner.py`` set
  ``RUSLE_CALIBRATION = 0.10`` under a comment attributing it to Morgan (2005)
  and describing it as "arid regions ~3x". The value is a 10x reduction, the
  stated basis is about 3x, and a calibration described as region-specific was
  applied to every climate.

Neither is an innovation -- both are a standard being altered. So they were
removed, not documented.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path("engine/hydroma")
DRIVERS = Path("services/scientific_motors")


def test_core_rusle_is_the_plain_product():
    from engine.hydroma.core.core import HydromaCore

    # Renard AH-703 worked arithmetic: the result must be the product exactly.
    assert HydromaCore.rusle_soil_loss(2.0, 0.3, 1.5, 0.2, 1.0) == pytest.approx(
        2.0 * 0.3 * 1.5 * 0.2 * 1.0
    )


def test_core_rusle_no_longer_takes_a_calibration():
    """The parameter is gone, so a caller cannot reintroduce a silent factor."""
    from engine.hydroma.core.core import HydromaCore

    with pytest.raises(TypeError):
        HydromaCore.rusle_soil_loss(2.0, 0.3, 1.5, 0.2, 1.0, 0.10)  # type: ignore[call-arg]


def test_core_rusle_matches_the_native_kernel():
    """The Python path and the C++ kernel must agree now that the factor is gone."""
    from engine.hydroma.core.core import HydromaCore
    from engine.hydroma.cpp_bridge import get_module

    core = get_module()
    if core is None:
        pytest.skip("C++ extension is not built")

    r, k, ls, c, p = 150.0, 0.28, 2.1, 0.35, 0.8

    assert core.rusle_annual_soil_loss(r, k, ls, c, p) == pytest.approx(
        HydromaCore.rusle_soil_loss(r, k, ls, c, p), rel=1e-12
    )


def test_chain_runner_calibration_is_neutral():
    src = (DRIVERS / "chain_runner.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    value = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "RUSLE_CALIBRATION":
                    value = ast.literal_eval(node.value)

    assert value == 1.0, f"RUSLE_CALIBRATION is {value!r}; the standard product must be unscaled"


def test_the_morgan_attribution_is_gone():
    """A citation that did not support the number it was attached to must not stay."""
    src = (DRIVERS / "chain_runner.py").read_text(encoding="utf-8")

    assert "Morgan (2005) empirical calibration" not in src


def test_no_default_calibration_remains_in_executable_code():
    """Grep the engine and services for an applied RUSLE calibration.

    The formula documents deliberately quote 0.10 when recording that the factor
    was removed, so this scans executable code only and skips the formulas
    package and comments.
    """
    offenders: list[str] = []
    for base in (Path("engine"), Path("services")):
        for path in base.rglob("*.py"):
            if "formulas" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "calibration" in stripped and any(
                    token in stripped for token in ("0.1", "0.10", "0.30")
                ):
                    offenders.append(f"{path}:{number}: {stripped.strip()}")

    assert not offenders, "a RUSLE calibration is still applied:\n" + "\n".join(offenders)


def test_the_removal_is_recorded_for_every_site_that_had_one():
    """Three sites carried it; all three must be named on the record."""
    from engine.hydroma.formulas import get

    notes = get("rusle_soil_loss").notes

    assert "core/core.py" in notes
    assert "chain_runner.py" in notes
    assert "erosion_rusle.py" in notes, "the third site must be recorded too"


def test_the_registry_records_rusle_as_a_standard():
    from engine.hydroma.formulas import get

    record = get("rusle_soil_loss")

    assert record is not None
    assert record.provenance == "standard"
    assert record.is_verified
    assert "0.10" in record.notes, "the removal must stay on the record"
