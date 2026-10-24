"""Measured load-bearing verdicts for the unvalidated-coefficient registry.

This module is **data**, not logic. It is the measured result of the one
experiment that cannot be repeated cheaply: a 4374-case sweep in which exactly
one numeric literal in ``NojinCalculator`` is rewritten, the rewritten class is
``exec``-ed in a fresh namespace, and the real ``calculate()`` is run over every
case. A constant is *load-bearing* when that single-literal perturbation moves
at least one field of ``NojinResult`` for at least one case.

Measured on **2026-10-02**, against
``engine/hydroma/biofertilizer/calculator.py`` as it stood at that commit.

    source        engine/hydroma/biofertilizer/calculator.py
    class         NojinCalculator
    method        as documented in COEFFICIENT-DEBT.md section 3.1: every
                  numeric literal in every method body, plus every numeric
                  literal inside the six class tables listed below
    perturbation  value -> value * 1.37 + 0.11, or 0.37 where the value is 0
    execution     method bodies: the literal's AST node is rewritten and the
                  module re-parsed from ast.unparse, then exec'd in a fresh
                  namespace. Class tables: the literal is rewritten in a copy of
                  the live class attribute. Either way the file on disk is never
                  modified
    sweep         4374 cases: 243 soils x 2 irrigation states, with crops,
                  seasons, formulations, application methods and 11 strain sets
                  assigned round-robin so all 7 crops, 6 seasons, 3 formulations,
                  3 application methods and every pair in STRAIN_SYNERGY appear
    watched       every field of NojinResult
    result        178 constants, 105 load-bearing, 73 cosmetic

**Result: 178 / 105 / 73.** ``tests/unit/test_unvalidated_coefficients.py``
re-runs the whole sweep and fails if a number here is wrong, so this table cannot
drift away from the source silently.

The first run of this measurement reported 100 load-bearing and 78 cosmetic, and
that number was wrong. Its class-table pass perturbed literal *i+1* while
recording the verdict against literal *i*, because the rewrite helper decremented
its index before comparing it to zero. Method bodies were perturbed at their own
index and were never affected, so only the 22 class-table constants moved; 7 of
their verdicts were wrong and the split became 105 / 73. Both the helper and the
verdicts it produced are gone; the table below is a re-measurement, and the test
now asserts that each perturbation changes exactly the literal it is keyed to, so
the same off-by-one cannot pass again.

``COEFFICIENT-DEBT.md`` section 3 still carries 100 / 78 and the original class
table. That section is history and is superseded by this module; see the section
appended to that document for the discrepancy and its cause.

Why the ``(column, value)`` pairs are stored next to each verdict
--------------------------------------------------------------------
They are the drift detector. :mod:`engine.hydroma.formulas.unvalidated` walks
the same literals in the same order and compares position and value against
this table. Insert a literal into ``_calculate_dosage`` without re-running the
sweep and the walk no longer matches, the scope's validation state becomes
``unclassified``, and every ``NojinResult`` produced from that point carries the
worse state instead of a clean ``unvalidated``.

Why the verdicts are stored rather than recomputed at import
------------------------------------------------------------
The sweep takes 110 seconds. Running it inside ``calculate()`` is not an option.
It is a measured artifact with a verifying test, which is the same arrangement
``docs/knowledge-engine/COEFFICIENT-DEBT.md`` uses for its own tables, except
that this one is machine-readable.
"""

from __future__ import annotations

#: Date the sweep below was run, and the case count it ran.
MEASURED_ON = "2026-10-02"
SWEEP_CASES = 4374

#: Fields of ``NojinResult`` that a load-bearing unsourced constant can move,
#: measured over the same sweep. This is what the label means by "this payload
#: rests on unvalidated numbers": 19 of the result's fields, measured, not
#: asserted. Fields absent from this tuple are decided without a numeric
#: coefficient -- ``land_profile_id`` is copied from the request, ``computed`` and
#: ``data_source`` are literals, ``model`` is the class name, ``seasonal_suitability``
#: is chosen from a hard-coded string list, and ``coefficient_validation`` is this
#: registry reporting on itself.
UNVALIDATED_RESULT_FIELDS: tuple[str, ...] = (
    "carbon_sequestration_potential",
    "expected_nitrogen_fixation_kg_ha",
    "expected_phosphorus_solubilization_pct",
    "expected_potassium_mobility_pct",
    "expected_yield_increase_pct",
    "moisture_suitability",
    "optimal_application_date_offset_days",
    "persistence_days",
    "reapplication_interval_days",
    "recommendations",
    "recommended_dosage_kg_ha",
    "risk_level",
    "soil_compatibility_score",
    "soil_health_improvement_score",
    "strain_compatibility",
    "strain_synergy_score",
    "suitability_score",
    "temperature_suitability",
    "water_efficiency_impact",
)

#: Method name -> the numeric literals in that method body, in ``ast.walk``
#: order, as ``(column_offset, value, load_bearing)``.
METHOD_BODY_VERDICTS: dict[str, tuple[tuple[int, float, bool], ...]] = {
    "_validate_input": (
        (43, 0, False),
        (33, 0, False),
        (59, 14, False),
        (42, 0, False),
        (78, 100, False),
    ),
    "_analyze_multi_strain": (
        (29, 1.0, True),
        (27, 1, True),
        (32, 90, True),
        (42, 0, False),
        (19, 50.0, True),
        (34, 75, False),
        (36, 1, False),
        (34, 60, False),
        (27, 0, False),
        (39, 1, False),
    ),
    "_calculate_dosage": (
        (24, 1.0, True),
        (20, 2.0, True),
        (86, 5.0, True),
        (48, 0.5, False),
        (28, 1.2, True),
        (27, 1.0, True),
        (29, 2, False),
        (50, 2.0, True),
        (28, 0.9, True),
        (56, 200, True),
        (50, 50, True),
    ),
    "_calculate_timing": (
        (20, 10, True),
        (19, 0, True),
        (19, 21, True),
        (20, 7, True),
    ),
    "_calculate_reapplication_interval": (
        (15, 60, True),
        (41, 0.8, True),
    ),
    "_predict_yield_increase": (
        (24, 15.0, True),
        (20, 1.0, True),
        (60, 2.0, True),
        (51, 1.5, False),
        (24, 1.2, True),
        (52, 5, True),
        (42, 1, False),
        (45, 0.5, True),
        (27, 0, False),
        (71, 1, False),
        (24, 0.7, True),
        (47, 50, True),
        (35, 35.0, False),
        (34, 5.0, True),
        (62, 8.5, True),
        (41, 50, True),
    ),
    "_predict_nitrogen_fixation": (
        (24, 30.0, True),
        (21, 1.0, True),
        (44, 50, False),
        (25, 1.3, True),
        (47, 100, True),
        (31, 1, False),
        (46, 150, True),
        (25, 0.8, True),
        (41, 50, True),
        (49, 1, True),
    ),
    "_predict_phosphorus_solubilization": (
        (30, 25.0, True),
        (21, 1.0, True),
        (46, 20, False),
        (25, 1.4, True),
        (47, 100, True),
        (48, 1, False),
        (48, 60, False),
        (25, 0.8, True),
        (41, 50, True),
        (61, 1, True),
        (41, 50.0, False),
    ),
    "_predict_potassium_mobility": (
        (24, 20.0, True),
        (21, 1.0, True),
        (45, 30, False),
        (25, 1.3, True),
        (47, 100, True),
        (42, 1, False),
        (47, 80, False),
        (25, 0.9, True),
        (41, 50, True),
        (49, 1, True),
        (35, 40.0, False),
    ),
    "_assess_soil_compatibility": (
        (16, 100.0, True),
        (37, 1.5, False),
        (21, 5, True),
        (21, 5, False),
        (50, 1, False),
        (36, 10, True),
        (38, 2, True),
        (42, 0.5, True),
        (81, 2.5, False),
        (25, 0.0, False),
        (32, 0, False),
        (65, 1, False),
        (36, 0, False),
        (84, 1, False),
        (42, 0, False),
        (95, 1, False),
        (34, 100.0, True),
        (61, 0, False),
        (96, 1, False),
        (61, 0, False),
        (61, 1, False),
        (66, 0, False),
        (66, 1, False),
    ),
    "_assess_temperature": (
        (31, 0, False),
        (67, 1, False),
        (47, 5, False),
        (86, 5, False),
        (42, 0, False),
        (81, 1, False),
    ),
    "_assess_moisture": (
        (37, 0, False),
        (85, 1, False),
        (28, 20, False),
        (49, 85, True),
    ),
    "_calculate_persistence": (
        (15, 90, True),
        (52, 1.5, False),
        (35, 1.2, True),
        (46, 30, False),
        (35, 0.8, True),
    ),
    "_calculate_soil_health_improvement": (
        (27, 10.0, True),
        (19, 0, True),
        (47, 10, True),
        (48, 1.0, True),
        (23, 5, True),
        (45, 1, False),
        (41, 50, True),
        (38, 25.0, False),
    ),
    "_assess_risk": (
        (28, 80, True),
        (52, 70, True),
        (30, 60, True),
        (54, 50, True),
    ),
    "_calculate_water_efficiency_impact": (
        (31, 15.0, True),
        (52, 1.5, False),
        (36, 5, True),
        (43, 1, False),
    ),
    "_estimate_carbon_sequestration": (
        (29, 0.2, True),
        (42, 10, True),
        (48, 1.0, True),
        (34, 1.5, True),
        (36, 2, False),
    ),
    "_generate_recommendations": (
        (28, 80, True),
        (48, 1.0, True),
        (28, 80, True),
        (30, 60, True),
        (48, 0, False),
        (29, 50, True),
        (50, 1, False),
        (91, 0, False),
        (93, 1, False),
    ),
    "_calculate_suitability": (
        (20, 10, True),
        (47, 10, True),
        (49, 1, False),
        (20, 5, True),
        (41, 50, True),
        (25, 0.0, False),
        (34, 100.0, True),
    ),
    "calibrate_from_trials": ((51, 0, False),),
}

#: Class-table name -> its numeric literals, in ``ast.walk`` order, as
#: ``(column_offset, value, load_bearing)``. These six names are exactly
#: ``COEFFICIENT-DEBT.md`` section 3.1's "class tables"; a new class-level
#: numeric table in ``NojinCalculator`` is picked up by the walk and lands in
#: the ``unclassified`` state until the sweep is re-run.
CLASS_TABLE_VERDICTS: dict[str, tuple[tuple[int, float, bool], ...]] = {
    "CROP_FACTORS": (
        (28, 1.0, True),
        (27, 1.1, True),
        (27, 1.2, True),
        (29, 0.9, True),
        (29, 1.05, True),
        (29, 1.15, True),
        (30, 0.85, True),
    ),
    "OPTIMAL_PH": ((18, 6.0, True), (23, 7.5, True)),
    "OPTIMAL_TEMP_C": ((22, 15, True), (26, 35, True)),
    "OPTIMAL_MOISTURE_PCT": ((28, 40, True), (32, 70, True)),
    "SEASONAL_FACTORS": (
        (18, 1.0, False),
        (18, 0.9, False),
        (16, 1.1, False),
        (18, 0.7, False),
    ),
    "STRAIN_SYNERGY": (
        (74, 1.15, True),
        (73, 1.1, True),
        (81, 1.12, True),
        # 1.20 on (NITROGEN_FIXING, ACC_DEAMINASE) is unreachable, not inert:
        # _analyze_multi_strain looks the pair up as tuple(sorted(...)), and
        # "acc_deaminase" sorts before "nitrogen_fixing", so the key as written
        # can never be found. Measured: the N+ACC synergy score is 87.5, the
        # uncounted average efficacy, not the 105.0 this 1.20 would produce.
        # Left as measured. Reordering the key would change computed output and
        # is a behaviour change, not a registry change.
        (64, 1.2, False),
        (78, 1.18, True),
    ),
}

#: Scope name -> measured counts, kept so the registry never has to recount to
#: report a summary and so a drift between count and verdict is visible.
SCOPE_COUNTS: dict[str, tuple[int, int, int]] = {
    # scope: (total, load_bearing, cosmetic)
    "NojinCalculator": (178, 105, 73),
}
