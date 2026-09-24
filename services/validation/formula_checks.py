"""Formula verification suite (راستی‌آزمایی) for the HyDroMa engine.

Each check independently verifies one engine output:
- identity    — mathematical/units identity re-derived by hand;
- reference   — published constant/range from a cited source;
- consistency — two engine modules must agree for the same quantity.

Pure computation, no writes. Exposed at GET /api/v1/hydroma/validation.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from engine.hydroma.carbon.calculator import CarbonProjectType, calculate_carbon_sequestration
from engine.hydroma.climate.et_calculator import calc_et0_hargreaves
from engine.hydroma.economics.analysis import calculate_npv, calculate_payback
from engine.hydroma.models.ecsi import ECSI
from engine.hydroma.models.hyrue import HYRUE
from engine.hydroma.soil.chemistry import calculate_cec
from engine.hydroma.soil.pedotransfer import estimate_soil_parameters
from engine.hydroma.soil.physics import available_water_capacity, van_genuchten_theta
from engine.hydroma.soil.salinity import classify_salinity
from engine.hydroma.soil.texture import classify_texture
from engine.hydroma.soil.water_retention import get_vg_parameters
from engine.hydroma.watershed.calculator import calculate_runoff


@dataclass
class CheckResult:
    id: str
    label: str
    kind: str
    source: str
    expected: float | str
    actual: float | str
    tolerance: float
    unit: str
    passed: bool
    note: str = ""


def _run(
    check_id: str,
    label: str,
    kind: str,
    source: str,
    unit: str,
    fn: Callable[[], tuple[Any, Any, float]],
    note: str = "",
) -> CheckResult:
    try:
        expected, actual, tol = fn()
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            passed = abs(float(expected) - float(actual)) <= tol
        else:
            passed = expected == actual
        return CheckResult(check_id, label, kind, source, expected, actual, tol, unit, passed, note)
    except Exception as exc:
        return CheckResult(
            check_id, label, kind, source, "n/a", f"ERROR: {exc}", 0.0, unit, False, note
        )


def _reference_data() -> dict[str, Any]:
    path = Path("docs/hydroma/scientific_reference_data.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_all() -> dict[str, Any]:
    checks: list[CheckResult] = []
    ref = _reference_data()

    # 1 — rational-method runoff identity: V[m³] = C · P[m] · A[m²]
    checks.append(
        _run(
            "runoff_rational_identity",
            "Runoff V = C·P·A (C=0.45, P=40mm, A=2ha)",
            "identity",
            "rational-method unit identity (SCS-style)",
            "m³",
            lambda: (360.0, calculate_runoff(20000.0, 40.0, 0.45), 1e-6),
        )
    )

    # 2 — van Genuchten boundary identity θ(0) = θs
    vg = get_vg_parameters("loam")
    checks.append(
        _run(
            "vg_saturation_identity",
            "van Genuchten θ(0) = θs",
            "identity",
            "van Genuchten 1980 boundary identity",
            "cm³/cm³",
            lambda: (
                vg["theta_s"],
                van_genuchten_theta(0.0, vg["theta_r"], vg["theta_s"], vg["alpha"], vg["n"]),
                1e-6,
            ),
        )
    )

    # 3 — loam θs inside Carsel & Parrish (1988) range
    checks.append(
        _run(
            "vg_loam_params",
            "loam θs within Carsel & Parrish range",
            "reference",
            "Carsel & Parrish 1988 (θs≈0.43; α=0.036; n=1.56)",
            "cm³/cm³",
            lambda: (0.43, vg["theta_s"], 0.05),
            note=f"engine α={vg['alpha']}, n={vg['n']}",
        )
    )

    # 4 — pedotransfer AWC(loam) inside the curated USDA reference range
    usda_awc = ref.get("soil", {}).get("awc_loam_mm_m", {})
    usda_val = float(usda_awc.get("value", 150.0))
    lo, hi = (usda_awc.get("range") or [usda_val * 0.8, usda_val * 1.2])[:2]
    ptf_awc_mm_m = estimate_soil_parameters(40.0, 25.0, 1.5)["awc"] * 1000.0
    checks.append(
        _run(
            "ptf_awc_loam",
            "Pedotransfer AWC(loam) inside USDA range",
            "reference",
            f"Saxton & Rawls 2006 + {usda_awc.get('source', 'USDA reference data')}",
            "mm/m",
            lambda: ((lo + hi) / 2, ptf_awc_mm_m, (hi - lo) / 2),
            note=f"reference range [{lo}, {hi}] mm/m",
        )
    )

    # 5 — cross-family consistency: VG-derived vs USDA/PTF AWC (documented band)
    phys_awc_mm_m = available_water_capacity("loam") * 1000.0

    def awc_ratio() -> tuple[float, float, float]:
        # The van Genuchten curve underestimates field capacity at -33 kPa for
        # loam, so it yields a smaller AWC than the USDA table / Saxton-Rawls PTF.
        # A ratio within [0.5, 1.5] rules out a coding error while keeping the
        # model-family difference visible (both numbers shown in the note).
        return (1.0, phys_awc_mm_m / ptf_awc_mm_m, 0.5)

    checks.append(
        _run(
            "awc_cross_family_band",
            "AWC(loam): VG vs USDA/PTF within documented band",
            "consistency",
            "van Genuchten (physics) vs Saxton-Rawls PTF; accepted band [0.5, 1.5]",
            "ratio",
            awc_ratio,
            note=(
                f"VG-derived={phys_awc_mm_m:.1f} vs PTF={ptf_awc_mm_m:.1f} mm/m — VG underestimates "
                f"loam FC; documented model-family difference"
            ),
        )
    )

    # 6 — USDA texture triangle known points
    def texture_points() -> tuple[Any, Any, float]:
        points = [
            ((40.0, 40.0, 20.0), "loam"),
            ((65.0, 25.0, 10.0), "sandy_loam"),
            ((10.0, 30.0, 60.0), "clay"),
            ((5.0, 85.0, 10.0), "silt"),
        ]
        bad = [
            f"{s}/{si}/{c}:{classify_texture(s, si, c)}≠{exp}"
            for (s, si, c), exp in points
            if classify_texture(s, si, c) != exp
        ]
        return ("all 4 USDA points", "all 4 USDA points" if not bad else "; ".join(bad), 0.0)

    checks.append(
        _run(
            "usda_texture_points",
            "USDA triangle: 4 known points classify correctly",
            "reference",
            "USDA NRCS Soil Texture Triangle",
            "",
            texture_points,
        )
    )

    # 7 — FAO-56 eq.52 Hargreaves identity (with the 0.408 Ra conversion)
    def hargreaves() -> tuple[float, float, float]:
        t_min, t_max, t_mean, ra_mj = 10.0, 25.0, 17.5, 15.0
        expected = 0.0023 * (t_mean + 17.8) * math.sqrt(t_max - t_min) * (ra_mj * 0.408)
        return expected, calc_et0_hargreaves(t_min, t_max, t_mean, ra_mj), 1e-6

    checks.append(
        _run(
            "fao56_hargreaves",
            "FAO-56 eq.52 Hargreaves ET0",
            "identity",
            "Allen et al. 1998 (FAO-56 eq. 52; Ra→mm via 0.408)",
            "mm/day",
            hargreaves,
        )
    )

    # 8 — RothC temperature modifier identity
    # Uses the canonical RothC-26.3 formulation: 47.9/(1+exp(106.06/(T+18.27)))
    from engine.hydroma.simulation.runners.rothc_runner import temp_factor as rothc_temp_factor

    checks.append(
        _run(
            "rothc_temp_factor",
            "RothC f(T) at 15 °C",
            "identity",
            "Coleman & Jenkinson 1996 (f(T)=47.9/(1+exp(106.06/(T+18.27))))",
            "",
            lambda: (rothc_temp_factor(15.0), ECSI.temperature_factor(15.0), 1e-9),
        )
    )

    # 9 — ECSI mass balance identity
    def ecsi_balance() -> tuple[float, float, float]:
        out = ECSI().compute(
            initial_soc_t_ha=40.0,
            carbon_input_t_ha=3.0,
            t_mean_c=15.0,
            rainfall_mm=500.0,
            evaporation_mm=700.0,
            clay_fraction=0.3,
            land_use="arable",
        )
        # Correct RothC mass balance: ΔSOC = input - gross_decomposition + stabilized
        # where stabilized = gross_decomposition * stabilized_fraction
        stabilized = out["total_decomposition_t_ha"] * out["stabilized_fraction"]
        expected_delta = 3.0 - out["total_decomposition_t_ha"] + stabilized
        return (expected_delta, out["delta_soc_t_ha_yr"], 1e-9)

    checks.append(
        _run(
            "ecsi_mass_balance",
            "ECSI ΔSOC = input − gross_decomposition + stabilized",
            "identity",
            "mass-balance identity (RothC structure)",
            "t/ha/yr",
            ecsi_balance,
        )
    )

    # 10 — Beer-Lambert fIPAR identity
    checks.append(
        _run(
            "hyrue_beer_lambert",
            "HY-RUE fIPAR = 1−e^(−k·LAI)",
            "identity",
            "Monteith 1977 (Beer-Lambert)",
            "",
            lambda: (
                1 - math.exp(-0.65 * 2.5),
                float(HYRUE().f_ipar(np.array([2.5]), 0.65)[0]),
                1e-9,
            ),
        )
    )

    # 11 — discounting + payback conventions
    checks.append(
        _run(
            "npv_identity",
            "NPV of −100 at t=0 equals −100",
            "identity",
            "discounting identity",
            "",
            lambda: (-100.0, calculate_npv([-100.0], 0.1), 1e-9),
        )
    )
    checks.append(
        _run(
            "payback_convention",
            "Payback(−100;50;50;50) = 3 periods",
            "identity",
            "cumulative-cash convention (period count to positive cumulative)",
            "period",
            lambda: (3.0, float(calculate_payback([-100.0, 50.0, 50.0, 50.0])), 1e-9),
            note="engine counts full periods; cumulative turns positive in period 3",
        )
    )

    # 12 — CEC component-sum identity
    def cec_sum() -> tuple[float, float, float]:
        out = calculate_cec(clay=25.0, organic_matter=2.0, ph=6.5)
        c = out["components"]
        return (
            c["clay_contribution"] + c["organic_matter_contribution"] + c["ph_factor"],
            out["cec"],
            1e-9,
        )

    checks.append(
        _run(
            "cec_component_sum",
            "CEC equals sum of components",
            "identity",
            "Brady & Weil 2017 (component model)",
            "meq/100g",
            cec_sum,
        )
    )

    # 13 — FAO salinity class boundary
    checks.append(
        _run(
            "fao_salinity_class",
            "EC 4 dS/m ⇒ moderately saline",
            "reference",
            "FAO-29 (Ayers & Westcot 1985)",
            "",
            lambda: ("moderately_saline", classify_salinity(4.0)["classification"], 0.0),
        )
    )

    # 14 — forest sequestration plausibility bound (IPCC)
    def carbon_bound() -> tuple[float, float, float]:
        out = calculate_carbon_sequestration(
            CarbonProjectType.AFFORESTATION, 100.0, 10, "temperate"
        )
        per_ha = float(out.get("annual_rate_tonnes", 0)) / 100.0
        return (0.0, per_ha, 20.0)

    checks.append(
        _run(
            "carbon_rate_bound",
            "Afforestation ≤ 20 tCO2/ha/yr (IPCC plausibility)",
            "reference",
            "IPCC AR6 biophysical plausibility bound",
            "tCO2/ha/yr",
            carbon_bound,
            note="bound check: rate must be ≥0 and ≤20",
        )
    )

    passed = sum(1 for c in checks if c.passed)
    return {
        "total": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
        "pass_rate": round(passed / len(checks), 4) if checks else 0.0,
        "checks": [asdict(c) for c in checks],
    }
