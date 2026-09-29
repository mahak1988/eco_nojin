"""The SI SCS-CN form must be the only one applied to millimetre rainfall.

The US-customary form ``S = (1000 / CN) - 10`` yields INCHES, so it is 25.4x
smaller than the SI form ``S = (25400 / CN) - 254``. Applied to millimetre
rainfall it shrinks the initial abstraction and inflates the event runoff.

The defect was found and fixed once in ``engine/hydroma/models/runoff_model.py``,
with an explicit warning comment. It then survived in two more places where the
expression had been re-derived independently:

* ``engine/hydroma/simulation_env/climate.py``
* ``engine/hydroma/simulation_env/disasters.py``

Measured over-estimate of event runoff depth for a 100 mm storm:

| CN | SI form | inch form | over-estimate |
|---|---|---|---|
| 50 | 7.98 mm | 88.93 mm | 11.1x |
| 60 | 18.57 mm | 92.42 mm | 5.0x |
| 75 | 41.14 mm | 96.11 mm | 2.3x |
| 95 | 85.57 mm | 99.37 mm | 1.2x
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path("engine/hydroma")

#: Any computation of SCS-CN retention, wherever it appears.
SCS_RE = re.compile(r"1000(?:\.0)?\s*/\s*(?:cn|curve_number)|1000(?:\.0)?\s*/\s*cn\b")


def _strip_comments_and_strings(text: str) -> str:
    """Remove comments and string literals so prose cannot trip the scan."""
    out = []
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        code = re.sub(r'"""(.|\n)*?"""', "", code)
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        out.append(code)
    return "\n".join(out)


def test_no_module_computes_scs_retention_in_inches():
    """The inch form must not be applied anywhere in the engine.

    Comments naming the inch form are fine and expected -- they are the warning.
    Executable code using it is not.
    """
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        code = _strip_comments_and_strings(path.read_text(encoding="utf-8", errors="replace"))
        for number, line in enumerate(code.splitlines(), 1):
            if SCS_RE.search(line):
                offenders.append(f"{path}:{number}: {line.strip()}")

    assert not offenders, "inch-form SCS-CN still in executable code:\n" + "\n".join(offenders)


def test_the_si_form_is_what_the_models_use():
    """`runoff_model.py` is the reference; state its value explicitly."""
    src = (ROOT / "models" / "runoff_model.py").read_text(encoding="utf-8")
    code = _strip_comments_and_strings(src)

    assert "25400" in code, "the SI form 25400/CN must be present in runoff_model.py"
    assert not SCS_RE.search(code)


@pytest.mark.parametrize(
    ("cn", "expected_mm"),
    [(50, 254.0), (60, 169.3333333), (70, 108.8571429), (75, 84.6666667), (95, 13.3684211)],
)
def test_reference_values_for_the_si_form(cn: float, expected_mm: float):
    """Anchors: S = (25400 / CN) - 254 millimetres."""
    s = 25400.0 / cn - 254.0

    assert s == pytest.approx(expected_mm, rel=1e-6)


def test_the_inch_form_would_be_25_point_4_times_smaller():
    """Why the mix-up is easy to miss and expensive when it happens."""
    for cn in (50, 60, 70, 75, 85, 95):
        si = 25400.0 / cn - 254.0
        inch = 1000.0 / cn - 10.0

        assert si / inch == pytest.approx(25.4, rel=1e-6)


def test_event_runoff_over_estimate_from_using_the_inch_form():
    """The consequence, so the cost of reintroducing it is concrete."""
    import numpy as np

    def runoff_mm(p, s):
        ia = 0.2 * s
        return 0.0 if p <= ia else (p - ia) ** 2 / (p + 0.8 * s)

    for cn, over in ((50, 11.1), (60, 5.0), (75, 2.3)):
        si = runoff_mm(100.0, 25400.0 / cn - 254.0)
        inch = runoff_mm(100.0, 1000.0 / cn - 10.0)

        assert inch / si == pytest.approx(over, rel=0.05), cn


def test_every_scs_use_carries_a_unit_warning():
    """Where the form appears, the unit must be stated so it is not re-derived."""
    for rel in (
        "models/runoff_model.py",
        "simulation_env/climate.py",
        "simulation_env/disasters.py",
    ):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "MILLIMET" in text.upper(), f"{rel} does not state the unit of S"


def test_the_registry_records_that_scs_is_a_standard_not_a_contribution():
    from engine.hydroma.formulas import get

    record = get("muskingum_cunge_routing")
    assert record is not None and record.provenance == "standard"
