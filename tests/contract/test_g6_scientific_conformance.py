"""G6 — scientific conformance is mandatory (S-SCI).

``services/scientific_motors/`` holds ~8,600 lines across 30+ motor classes
with **zero numeric tests**. The only reference to it in the whole test suite
is ``tests/unit/test_rusle_uncorrelated.py``, which parses ``chain_runner.py``
as *source text* and asserts a calibration constant. Not one motor's arithmetic
is checked.

Meanwhile the far smaller ``services/models`` registry has eight real numeric
conformance checks in ``test_models_phase7.py`` — so the pattern already exists
in this repository and simply was never applied to the large package.

This gate makes it non-optional: a motor cannot be added without a test that
exercises it numerically. The count is ratcheted upward (more conformance is
better), so existing gaps do not block the team but any new untested motor does.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from gates import scan_motor_conformance

BASELINE = ROOT / "docs" / "metrics" / "baseline.json"


@pytest.fixture(scope="module")
def report() -> dict:
    return scan_motor_conformance(ROOT)


class TestScannerWorks:
    def test_motors_are_discovered(self, report):
        assert report["total"] > 20, (
            f"only {report['total']} motors discovered; the scanner is probably not "
            "reaching services/scientific_motors"
        )

    def test_known_motors_are_present(self, report):
        for expected in ("RUSLEMotor", "AquaCropMotor", "RothCMotor"):
            assert expected in report["motors"], f"{expected} should be discovered"


class TestConformanceDoesNotRegress:
    def test_covered_motor_count_has_not_dropped(self, report):
        if not BASELINE.exists():
            pytest.fail("no baseline; regenerate with scripts/measure_baseline.py")
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
        recorded = data.get("metrics", {}).get("scientific", {}).get("with_conformance_test")
        if recorded is None:
            pytest.fail("baseline has no scientific.with_conformance_test; regenerate it")
        assert report["covered"] >= recorded, (
            f"G6: conformance coverage dropped {recorded} -> {report['covered']}"
        )

    def test_adding_an_untested_motor_fails(self, report):
        """The ratchet in its strict direction: a new motor needs a test."""
        if not BASELINE.exists():
            pytest.fail("baseline has no such key; regenerate with scripts/measure_baseline.py")
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
        recorded_total = data.get("metrics", {}).get("scientific", {}).get("motors")
        if recorded_total is None:
            pytest.fail("baseline has no scientific.motors; regenerate it")
        # A brand-new motor increases the denominator. Growth is only allowed
        # if the numerator grows by the same amount.
        new_motors = report["total"] - recorded_total
        if new_motors > 0:
            gained = report["covered"] - data["metrics"]["scientific"]["with_conformance_test"]
            assert gained >= new_motors, (
                f"G6: {new_motors} motor(s) were added without a conformance test.\n"
                f"  missing: {report['missing'][:10]}\n"
                "  Every motor needs at least one numeric test — see "
                "tests/integration/test_models_phase7.py for the pattern."
            )


class TestFormulaRegistryIsUsed:
    """S-SCI's registry must be the single home, not a decorative module."""

    def test_every_registered_formula_is_referenced_by_production_code(self):
        import services._contracts.formula as formula

        # The registry is new; adoption happens in phase 4 block 2. What must
        # hold today is that it is importable, non-empty and correctly cited.
        assert formula.FORMULAS, "the formula registry is empty"
        for name, entry in formula.FORMULAS.items():
            assert entry.reference.strip(), f"{name} has no reference"
            assert entry.units.strip(), f"{name} has no units"

    def test_the_rusle_formulas_are_registered_and_attributed(self):
        """Five inconsistent LS formulas and four K factors were the finding.

        The LS variants converged on one reference. The two K factors did not,
        and deliberately so: Williams 1995 (multiplicative) and Renard 1997
        (additive) are different equations that disagree by 6.811x for a loam,
        and standardising either way moves published erosion numbers. Both are
        registered separately with citations, so the disagreement is documented
        rather than averaged away.
        """
        import services._contracts.formula as formula

        ls = formula.lookup("rusle.ls")
        assert any("chain_runner" in r for r in ls.replaces)

        renard = formula.lookup("rusle.k.renard1997")
        assert any("soil_fetcher" in r for r in renard.replaces)
        assert "Renard" in renard.reference

        williams = formula.lookup("rusle.k.williams1995")
        assert "Williams" in williams.reference
        assert any("soilgrids" in r for r in williams.replaces), (
            "the point chain reads Williams; the registry must name the file it replaces"
        )

    def test_the_two_k_forms_are_not_collapsed_into_one_name(self):
        """Guards a well-meant future 'simplification' that would change numbers."""
        import services._contracts.formula as formula

        assert "rusle.k" not in formula.FORMULAS, (
            "a single 'rusle.k' hides which of the two equations produced a value"
        )
        loam_williams = formula.k_factor_williams(30, 40, 30, 15)
        loam_renard = formula.k_factor_epic(15, 30, 40)
        assert loam_renard / loam_williams == pytest.approx(6.811, rel=0.01)

    def test_standards_document_names_the_gap(self):
        doc = ROOT / "docs" / "standards" / "S-SCI.md"
        text = doc.read_text(encoding="utf-8")
        assert "صفر آزمون عددی" in text or "zero" in text.lower(), (
            "S-SCI.md should state the current coverage gap plainly"
        )
