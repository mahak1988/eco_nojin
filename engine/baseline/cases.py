"""Reference cases for the R18 baseline capture.

Purpose
-------
Phase 3 of the integration plan will change equations in the engine. Every one
of those changes moves a number that other modules consume. Without a recorded
"before" it is impossible to tell an intended correction from an accidental
side effect, which is exactly what the project's Decision 7 (no double
counting) exists to prevent.

This module is the list of quantities to record. It is deliberately *inputs*,
not expected values: no expected number appears anywhere in this package, so
the baseline can never be satisfied by a value copied out of the engine.

Case selection rules
--------------------
1. **Deterministic.** No timestamps, no UUIDs, no network, no rasters.
2. **Defect-sensitive.** Every case is chosen so that a known pending
   correction moves it. A case whose value is insensitive to the fix is
   dead weight in the baseline.
3. **Physically meaningful.** Inputs sit inside the range the function is meant
   to serve, so the recorded numbers are the ones a real user would see.
4. **Cheap.** The whole capture must run in well under a second so it can sit
   in a pre-commit hook.

Adding a case
-------------
Add it here, regenerate the baseline, and say in the commit message which
pending correction it is meant to witness. A case added without that sentence
is a case nobody will remember to check.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np

# Reference day used for every climate case: a hot Mediterranean summer day at
# moderate elevation. Chosen because it exercises both the radiation term and
# the aerodynamic term of FAO-56 eq. 39 with comparable weight.
REF_DAY: dict[str, Any] = {
    "tmin": 22.6,
    "tmax": 30.5,
    "rh_min": 62.0,
    "rh_max": 82.0,
    "wind_speed": 1.7,
    "solar_radiation": 28.4,
    "elevation": 100.0,
    "latitude": 41.9,
    "doy": 193,
}

# 12 USDA textures, coarse to fine. Order is meaningful for the Ks monotonicity
# check the engine currently fails.
TEXTURES = [
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_clay_loam",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
]


def _r(value: Any, digits: int = 10) -> Any:
    """Round a float to a stable number of digits so the JSON is comparable.

    Ten significant digits is far more precision than any physical input here
    carries, so it cannot mask a real change, but it makes the file stable
    against the last-bit noise of a reordered expression.

    Non-finite floats become the strings "NaN", "Infinity" and "-Infinity".
    This is not cosmetic: ``json.dump`` would otherwise write the bare literals
    ``NaN`` and ``Infinity``, which are **not valid JSON** and are rejected by
    strict parsers. Edge cells of a slope or aspect grid legitimately produce
    NaN, so the value has to survive the round trip, and it has to do so as
    something another tool can read.
    """
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if math.isnan(number):
            return "NaN"
        if math.isinf(number):
            return "Infinity" if number > 0 else "-Infinity"
        out = round(number, digits)
        return 0.0 if out == 0 else out
    if isinstance(value, (np.ndarray,)):
        return [_r(v, digits) for v in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_r(v, digits) for v in value]
    if isinstance(value, dict):
        return {str(k): _r(v, digits) for k, v in sorted(value.items())}
    return value


# --------------------------------------------------------------------------
# Group 1 — soil retention. Witnesses the FC_HEAD_CM correction, the
# Carsel & Parrish Ks monotonicity fix, and the positive-head handling.
# --------------------------------------------------------------------------
def soil_retention() -> dict[str, Any]:
    from engine.hydroma.soil.physics import (
        FC_HEAD_CM,
        PWP_HEAD_CM,
        SOIL_PARAMETERS_VG,
        available_water_capacity,
        van_genuchten_k,
        water_content_at,
    )
    from engine.hydroma.soil.water_retention import (
        calculate_available_water,
        calculate_water_retention_curve,
    )

    out: dict[str, Any] = {
        "FC_HEAD_CM": FC_HEAD_CM,
        "PWP_HEAD_CM": PWP_HEAD_CM,
        "table": _r(SOIL_PARAMETERS_VG),
        "awc_cm3_cm3": _r({t: available_water_capacity(t) for t in TEXTURES}),
    }
    # The upper module uses -33 cm; the lower one is scheduled to move to match.
    out["upper_module"] = _r(
        {
            t: {
                "fc33": calculate_water_retention_curve(t)["field_capacity"]["water_content"],
                "wp": calculate_water_retention_curve(t)["wilting_point"]["water_content"],
            }
            for t in TEXTURES
        }
    )
    heads = [0.0, -1.0, -10.0, -33.0, -100.0, -330.0, -1000.0, -15000.0]
    out["theta_at_head"] = _r({t: [water_content_at(h, t) for h in heads] for t in TEXTURES})
    out["k_at_head"] = _r(
        {
            t: [
                van_genuchten_k(
                    h,
                    SOIL_PARAMETERS_VG[t]["theta_r"],
                    SOIL_PARAMETERS_VG[t]["theta_s"],
                    SOIL_PARAMETERS_VG[t]["alpha"],
                    SOIL_PARAMETERS_VG[t]["n"],
                    SOIL_PARAMETERS_VG[t]["Ks"],
                )
                for h in heads
            ]
            for t in TEXTURES
        }
    )
    out["brooks_corey"] = _r(
        [[ph_bc(h) for h in (-10.0, -100.0, -1000.0)] for ph_bc in [lambda h: _bc(h)]]
    )
    out["campbell"] = _r([[_camp(h) for h in (-10.0, -100.0, -1000.0)] for _ in range(1)])
    out["available_water_mm"] = _r(
        [
            calculate_available_water(theta_fc=f, theta_wp=w, root_depth=d)
            for f, w, d in ((0.30, 0.15, 50.0), (0.35, 0.12, 100.0), (0.20, 0.05, 30.0))
        ]
    )
    return out


def _bc(h: float) -> Any:
    from engine.hydroma.soil.physics import brooks_corey_theta

    return brooks_corey_theta(h, 0.05, 0.43, -10.0, 2.0)


def _camp(h: float) -> Any:
    from engine.hydroma.soil.physics import campbell_theta

    return campbell_theta(h, 0.05, 0.43, -10.0, 1.3)


# --------------------------------------------------------------------------
# Group 2 — climate. Witnesses the Rnl addition to eq. 39 and the exponent
# correction in eq. 52, in all three Hargreaves copies.
# --------------------------------------------------------------------------
def climate_et0() -> dict[str, Any]:
    from engine.hydroma.calculations.crop_water_req_calc import (
        CropWaterReqInput,
        CropWaterRequirementCalculator,
    )
    from engine.hydroma.climate import et_calculator as et
    from engine.hydroma.simulation.weather_source import (
        hargreaves_et0 as hargreaves_a,
    )
    from engine.hydroma.simulation_env.weather import hargreaves_et0 as hargreaves_b

    ra = et.calc_extraterrestrial_radiation(REF_DAY["latitude"], REF_DAY["doy"])

    out: dict[str, Any] = {
        "es_table": _r(
            [et.calc_saturation_vapor_pressure(t) for t in (-20, -5, 0, 10, 20, 25, 30, 40)]
        ),
        "delta": _r([et.calc_delta(t) for t in (-20, 0, 20, 25, 40)]),
        "gamma": _r([et.calc_psychrometric(z) for z in (0, 100, 500, 1000, 2000, 4000)]),
        "ra": _r(
            {
                f"{lat}_{doy}": et.calc_extraterrestrial_radiation(float(lat), doy)
                for lat in (-60, -30, 0, 30, 45, 60)
                for doy in (1, 80, 172, 265, 355)
            }
        ),
        "hargreaves_core": _r(
            [
                et.calc_et0_hargreaves(t_min=a, t_max=b, ra_mj=ra)
                for a, b in ((10.0, 25.0), (5.0, 30.0), (20.0, 32.0), (0.0, 40.0))
            ]
        ),
        "penman_monteith": _r(
            [
                et.calc_et0_penman_monteith(et.ClimateData(**{**REF_DAY, "rh_min": r, "rh_max": m}))
                for r, m in ((62, 82), (30, 60), (10, 30), (100, 100))
            ]
        ),
        "auto_select": _r(
            et.calc_et0(
                et.ClimateData(
                    tmin=REF_DAY["tmin"],
                    tmax=REF_DAY["tmax"],
                    latitude=REF_DAY["latitude"],
                    doy=REF_DAY["doy"],
                )
            )
        ),
        "hargreaves_copy_weather_source": _r(
            hargreaves_a(REF_DAY["tmin"], REF_DAY["tmax"], REF_DAY["latitude"], REF_DAY["doy"])
        ),
        "hargreaves_copy_simulation_env": _r(
            hargreaves_b(REF_DAY["tmin"], REF_DAY["tmax"], REF_DAY["latitude"], REF_DAY["doy"])
        ),
    }
    # The fourth copy, which is not FAO-56 eq. 52 at all: it uses Ra**0.5
    # instead of Ra. Driven through its real pydantic contract so the recorded
    # number is the one a user would see.
    cw = CropWaterRequirementCalculator().execute(
        CropWaterReqInput(
            crop_type="wheat",
            planting_date="2026-04-01",
            harvest_date="2026-04-03",
            daily_weather_data=[
                {
                    "date": f"2026-04-0{day + 1}",
                    "t_min_c": REF_DAY["tmin"],
                    "t_max_c": REF_DAY["tmax"],
                    "wind_speed_ms": REF_DAY["wind_speed"],
                    "solar_radiation_mj_m2": REF_DAY["solar_radiation"],
                    "humidity_mean_percent": 72.0,
                }
                for day in range(3)
            ],
            kc_coefficients=[0.4, 0.4, 0.4],
        )
    )
    out["hargreaves_copy_crop_water"] = _r(cw.model_dump() if hasattr(cw, "model_dump") else cw)
    return out


# --------------------------------------------------------------------------
# Group 3 — runoff. Witnesses the peak-flow dimensional fix, the missing
# runoff coefficient in the rational volume, and the spatial CN map.
# --------------------------------------------------------------------------
def runoff() -> dict[str, Any]:
    from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput

    calc = RunoffCalculator()
    out: dict[str, Any] = {}
    for method in ("SCS-CN", "Rational"):
        for cn in (35.0, 50.0, 70.0, 85.0):
            for rain in (12.0, 50.0, 120.0):
                key = f"{method}_cn{int(cn)}_p{int(rain)}"
                out[key] = _r(
                    calc.execute(
                        RunoffInput(
                            precipitation_mm=rain,
                            curve_number=cn,
                            area_ha=2.5,
                            method=method,
                            rational_coefficient=0.6,
                        )
                    ).model_dump()
                )
    out["rational_sweep"] = _r(
        {
            str(c): calc.execute(
                RunoffInput(
                    precipitation_mm=50.0, area_ha=1.0, method="Rational", rational_coefficient=c
                )
            ).model_dump()
            for c in (0.1, 0.2, 0.4, 0.6, 0.8, 1.0)
        }
    )
    return out


def runoff_watershed_helper() -> dict[str, Any]:
    from engine.hydroma.watershed.calculator import calculate_runoff

    return _r(
        {
            f"{a}_{r}": calculate_runoff(float(a), float(r), c)
            for a in (1000, 10_000, 500_000)
            for r in (10.0, 80.0, 200.0)
            for c in (0.0, 0.3, 0.7)
        }
    )


# --------------------------------------------------------------------------
# Group 4 — watershed design and network. The densest defect cluster.
# --------------------------------------------------------------------------
def watershed_design() -> dict[str, Any]:
    from engine.hydroma.watershed.calculator import (
        design_check_dam,
        design_contour_trench,
        design_gully_plug,
        design_half_moon,
        design_terrace,
    )

    out: dict[str, Any] = {"check_dam": {}}
    for area in (5_000.0, 50_000.0, 500_000.0, 5_000_000.0, 50_000_000.0):
        for sed in (1.0, 5.0, 50.0):
            out["check_dam"][f"a{int(area)}_s{int(sed)}"] = _r(
                design_check_dam(5.0, area, 120.0, sediment_yield_t_ha_yr=sed)
            )
    out["check_dam_sweep"] = _r(
        {
            f"a{int(a)}": design_check_dam(s, a, r)
            for a in (10_000.0, 100_000.0, 1_000_000.0)
            for s, r in ((2.0, 80.0), (5.0, 120.0), (15.0, 200.0))
        }
    )
    out["contour_trench"] = _r(
        {f"s{sl}": design_contour_trench(sl, 100_000.0) for sl in (1.0, 3.0, 5.0, 10.0, 20.0, 35.0)}
    )
    out["terrace"] = _r(
        {
            f"s{sl}_a{int(a)}": design_terrace(sl, a)
            for a in (200.0, 5_000.0, 500_000.0)
            for sl in (2.0, 10.0, 22.0, 40.0)
        }
    )
    out["gully_plug"] = _r(
        {
            f"g{g}": design_gully_plug(s, a, gully_width_m=g)
            for a in (5_000.0, 100_000.0)
            for s in (3.0, 15.0, 30.0)
            for g in (1.0, 2.0, 5.0)
        }
    )
    out["half_moon"] = _r(
        {
            f"a{int(a)}": design_half_moon(s, a)
            for a in (500.0, 5_000.0, 50_000.0)
            for s in (3.0, 12.0, 35.0)
        }
    )
    return out


def watershed_network() -> dict[str, Any]:
    from engine.hydroma.watershed.calculator import (
        calculate_horton_ratios,
        calculate_kirpich_tc,
        calculate_strahler_order,
        muskingum_route,
    )

    chain5 = {
        "edges": [
            {"id": "a", "from_node": 1, "to_node": 3},
            {"id": "b", "from_node": 2, "to_node": 3},
            {"id": "c", "from_node": 3, "to_node": 4},
            {"id": "d", "from_node": 4, "to_node": 5},
            {"id": "e", "from_node": 5, "to_node": 6},
        ]
    }
    triangle = {
        "edges": [
            {"id": "a", "from_node": 1, "to_node": 3},
            {"id": "b", "from_node": 2, "to_node": 3},
            {"id": "c", "from_node": 3, "to_node": 4},
        ]
    }
    strahler = _r(
        {
            n: calculate_strahler_order(net)
            for n, net in (("chain5", chain5), ("triangle", triangle))
        }
    )
    return {
        "strahler": strahler,
        "horton": _r(
            {
                "triangle": calculate_horton_ratios(
                    calculate_strahler_order(triangle), {"a": 100.0, "b": 200.0, "c": 300.0}
                ),
                "chain5": calculate_horton_ratios(
                    calculate_strahler_order(chain5),
                    {"a": 100.0, "b": 200.0, "c": 300.0, "d": 300.0, "e": 300.0},
                ),
            }
        ),
        "kirpich": _r(
            {
                f"{length}_{s}": calculate_kirpich_tc(float(length), float(s))
                for length in (100.0, 500.0, 1000.0, 5000.0)
                for s in (0.005, 0.02, 0.1, 0.4)
            }
        ),
        # One stable case and one that must be rejected. The previous case list
        # recorded four combinations and three of them were OUTSIDE the stability
        # window 2Kx <= dt <= 2K(1-x), so the baseline was preserving oscillatory
        # output as though it were a reference. The rejection is now part of the
        # record, and the window is stated so a reader can check any future case.
        "muskingum_window": {
            f"K{k}_x{x}": {
                "dt_min": 2.0 * k * x,
                "dt_max": 2.0 * k * (1.0 - x),
            }
            for k, x in ((1.0, 0.2), (2.0, 0.25), (0.5, 0.0))
        },
        "muskingum_stable": _r(
            muskingum_route(
                np.array([0.0, 10.0, 25.0, 15.0, 5.0, 0.0, 0.0]), 1.0, 0.2, 1.0
            ).tolist()
        ),
        "muskingum_stable_wide": _r(
            muskingum_route(
                np.array([0.0, 10.0, 25.0, 15.0, 5.0, 0.0, 0.0]), 2.0, 0.25, 2.0
            ).tolist()
        ),
        "muskingum_unstable_rejected": _r(_muskingum_rejection()),
    }


def _muskingum_rejection() -> dict[str, Any]:
    """Record the refusal of an unstable step rather than its oscillating output.

    The value recorded is the exception's own diagnostic, so a change to the
    wording of the guidance a caller receives is as visible as a change to a
    number.
    """
    from engine.hydroma.watershed.calculator import muskingum_route

    try:
        muskingum_route(np.array([0.0, 10.0, 25.0, 15.0, 5.0, 0.0, 0.0]), 1.0, 0.2, 10.0)
    except ValueError as exc:
        return {"raised": type(exc).__name__, "message": str(exc)}
    return {"raised": None, "message": "an unstable step was accepted"}


# --------------------------------------------------------------------------
# Group 5 — groundwater. Witnesses the mass-balance clamp and the rounding
# split between totals and series.
# --------------------------------------------------------------------------
def groundwater() -> dict[str, Any]:
    import dataclasses

    from engine.hydroma.groundwater.models import (
        GroundwaterBucketInput,
        calculate_theis_drawdown,
        estimate_aquifer_properties,
        run_groundwater_bucket,
    )

    def bucket(**kw: Any) -> Any:
        result = run_groundwater_bucket(GroundwaterBucketInput(**kw))
        return _r(dataclasses.asdict(result))

    return {
        "bucket_sustainable": bucket(
            initial_storage_mm=200.0, recharge_mm=5.0, pumping_mm=2.0, months=24
        ),
        "bucket_overdraft": bucket(
            initial_storage_mm=200.0, recharge_mm=0.0, pumping_mm=10.0, months=24
        ),
        "bucket_dry": bucket(initial_storage_mm=5.0, recharge_mm=0.0, pumping_mm=50.0, months=12),
        "bucket_derived_recharge": bucket(
            initial_storage_mm=100.0, recharge_mm=None, soil_water_mm=200.0, rcoeff=0.15, months=12
        ),
        "aquifer": _r(
            {
                f"a{a}": estimate_aquifer_properties(1e-5, sy, float(a), d)
                for a, sy, d in ((10_000.0, 0.10, 2.0), (1e6, 0.05, 10.0), (1e4, 0.25, 0.5))
            }
        ),
        "theis": _r(
            {
                f"t{t}": calculate_theis_drawdown(2000.0, 0.0002, 760.0, 30.0, t)
                for t in (0.5, 1.0, 4.0, 16.0, 100.0, 1e4)
            }
        ),
    }


# --------------------------------------------------------------------------
# Group 6 — carbon. Witnesses the biochar area double-count and the range
# bracket inversion.
# --------------------------------------------------------------------------
def carbon() -> dict[str, Any]:
    from engine.hydroma.carbon.calculator import CarbonProjectType, calculate_carbon_sequestration

    out: dict[str, Any] = {}
    for project_type in CarbonProjectType:
        for region in ("tropical", "temperate", "arid"):
            for area, years in ((100.0, 10), (1.0, 1), (2_500.0, 30)):
                key = f"{project_type.value}_{region}_{int(area)}ha_{years}y"
                out[key] = _r(
                    calculate_carbon_sequestration(
                        project_type, area, duration_years=years, region=region
                    )
                )
    return out


# --------------------------------------------------------------------------
# Group 7 — irrigation, salinity, indices, terrain, erosion.
# --------------------------------------------------------------------------
def irrigation() -> dict[str, Any]:
    from engine.hydroma.irrigation.scheduler import (
        calculate_application_depth,
        calculate_interval,
    )

    return {
        "interval": _r(
            {
                f"e{e}_r{r}_p{p}": calculate_interval(float(e), float(r), float(p))
                for e in (2.0, 4.0, 5.0, 6.0, 8.0)
                for r in (50.0, 100.0, 180.0)
                for p in (0.3, 0.55, 0.7)
            }
        ),
        "application_depth": _r(
            {
                f"e{e}_eff{ef}": calculate_application_depth(float(e), float(ef), 0.0)
                for e in (2.0, 5.0, 8.0)
                for ef in (0.5, 0.6, 0.8, 0.95, 1.0)
            }
        ),
        "application_depth_with_rain": _r(
            {
                f"rain{rain}": calculate_application_depth(6.0, 0.8, rain)
                for rain in (0.0, 1.0, 3.0, 6.0)
            }
        ),
    }


def salinity() -> dict[str, Any]:
    from engine.hydroma.soil.salinity import (
        calculate_leaching_requirement,
        calculate_sodic_soil_amendment,
        classify_salinity,
    )

    return {
        "classify": _r(
            {str(ec): classify_salinity(ec) for ec in (0.3, 1.0, 2.5, 5.0, 10.0, 18.0, 30.0)}
        ),
        "leaching": _r(
            {
                f"s{s}_w{w}": calculate_leaching_requirement(float(s), float(w))
                for s, w in ((8.0, 1.0), (15.0, 3.0), (25.0, 8.0), (4.0, 6.0))
            }
        ),
        "sodic": _r(
            {
                f"esp{e}": calculate_sodic_soil_amendment(float(e), 15.0, 1.3)
                for e in (5.0, 10.0, 15.0, 25.0, 40.0)
            }
        ),
    }


def remote_sensing_indices() -> dict[str, Any]:
    """Two copies of NDVI/EVI exist; both are recorded so consolidation is visible."""
    from engine.hydroma.crop.ndvi_analysis import (
        calculate_evi as evi_crop,
        calculate_ndvi as ndvi_crop,
    )
    from engine.hydroma.satellite.processors.indices import (
        calculate_evi as evi_sat,
        calculate_ndvi as ndvi_sat,
    )

    pairs = [(0.05, 0.60), (0.02, 0.35), (0.10, 0.20), (0.00, 0.00), (0.15, 0.15)]
    return {
        "ndvi_crop": _r([ndvi_crop(r, n) for r, n in pairs]),
        "ndvi_satellite": _r([ndvi_sat(np.array([r]), np.array([n]))[0] for r, n in pairs]),
        "evi_crop": _r(
            [
                evi_crop(r, n, b)
                for r, n, b in ((0.05, 0.60, 0.04), (0.02, 0.35, 0.03), (0.10, 0.20, 0.08))
            ]
        ),
        "evi_satellite": _r(
            [
                evi_sat(np.array([r]), np.array([n]), np.array([b]))[0]
                for r, n, b in ((0.05, 0.60, 0.04), (0.02, 0.35, 0.03), (0.10, 0.20, 0.08))
            ]
        ),
    }


def terrain() -> dict[str, Any]:
    from engine.land.slope_aspect import calculate_slope_aspect

    dem = np.array(
        [
            [10.0, 10.0, 10.0, 10.0],
            [10.0, 12.0, 12.0, 10.0],
            [10.0, 12.0, 14.0, 10.0],
            [10.0, 10.0, 10.0, 10.0],
        ]
    )
    slope, aspect = calculate_slope_aspect(dem, 30.0, 30.0)
    return {"slope": _r(slope), "aspect": _r(aspect)}


def erosion() -> dict[str, Any]:
    """RUSLE topographic factor, computed from synthetic planar DEMs.

    ``calculate_ls_factor`` takes a DEM rather than scalars, so the reference
    cases are constant-gradient surfaces. A planar slope is the case with a
    known answer: flow length equals the whole surface and the slope angle is
    exact, so a change in either the D8 accumulation or the McCool steepness
    factor shows up immediately. Four copies of RUSLE exist in the engine and
    none of them is consolidated yet, so all four are exercised through the
    one Python entry point.
    """
    from engine.land.erosion_risk import calculate_ls_factor, calculate_slope_degrees

    out: dict[str, Any] = {}
    for gradient in (0.02, 0.05, 0.15, 0.30, 0.60):
        n = 12
        # Planar surface descending along the row axis at the given gradient.
        dem = np.tile((np.arange(n) * gradient * 30.0)[np.newaxis, :], (n, 1)).astype(float)
        # The DEM must be supplied, not just the slope, because the module
        # derives flow accumulation with D8 internally and refuses to guess
        # when only a slope array is given.
        out[f"g{gradient}"] = {
            "slope_deg_mean": _r(float(np.mean(calculate_slope_degrees(dem, 30.0)))),
            "ls": _r(calculate_ls_factor(dem=dem, cell_size_m=30.0)),
        }
    return out


def soil_table_backends() -> dict[str, Any]:
    """The two backends that used to hold private copies of the table.

    ``physics`` and ``soil_physics_fast`` agree on every parameter, but
    ``soil_physics_fast`` reports Ks in cm/hr, and the land integrator used to
    carry a *different* dataset entirely. All three are captured here so that a
    future change to any of them is attributable, which the original case list
    did not achieve: it read only ``physics.py``.

    The clay row is the reason this group exists. Before consolidation the
    Numba table carried 0.12 cm/hr for clay where ``physics.py`` carried
    0.2000, so consolidation moved the Numba path's clay conductivity by 67 %
    while leaving every Python path bit-identical. That change is a live
    behavioural change and needed somewhere to be written down.
    """
    from engine.data.soil_table import SOIL_PARAMETERS as shared
    from engine.hydroma.cpp_bridge.soil_physics_fast import SOIL_PARAMETERS as numba
    from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG as physics

    return {
        "physics": _r(physics),
        "numba_cm_per_hour": _r(numba),
        "shared_with_provenance": _r(shared),
    }


def land_soil_integrator() -> dict[str, Any]:
    """The land integrator's van Genuchten lookup.

    It carried a private table whose ``theta_s`` differed from the engine's in
    all twelve rows. It now reads the shared one, so its output moved. Captured
    so that the blast radius of that decision is on record.
    """
    from engine.land.integration import SoilIntegrator
    from engine.land.integration.models import SoilTexture

    integrator = SoilIntegrator()
    return {
        texture.value: _r(integrator.estimate_van_genuchten(texture)) for texture in SoilTexture
    }


# --------------------------------------------------------------------------
# The case list. Order is the order in the JSON, so it is part of the schema.
# --------------------------------------------------------------------------
CASES: dict[str, Callable[[], Any]] = {
    "soil_retention": soil_retention,
    "soil_table_backends": soil_table_backends,
    "land_soil_integrator": land_soil_integrator,
    "climate_et0": climate_et0,
    "runoff": runoff,
    "runoff_watershed_helper": runoff_watershed_helper,
    "watershed_design": watershed_design,
    "watershed_network": watershed_network,
    "groundwater": groundwater,
    "carbon": carbon,
    "irrigation": irrigation,
    "salinity": salinity,
    "remote_sensing_indices": remote_sensing_indices,
    "terrain": terrain,
    "erosion": erosion,
}


def capture() -> dict[str, Any]:
    """Run every case and return a JSON-safe nested dict."""
    return {name: fn() for name, fn in CASES.items()}


def case_names() -> list[str]:
    return list(CASES)
