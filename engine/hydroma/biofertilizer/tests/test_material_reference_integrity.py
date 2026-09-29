"""Reference integrity between the recipe catalogue and the material catalogue.

Why this file exists
-------------------
``FORMULATIONS[*]["material_composition"]`` is a JSON string mapping a material
code to kg/ha. Every consumer of that string resolves the code against
``MATERIALS`` through a *guarded* lookup, so an unknown code does not raise --
it is skipped:

* ``FormulationOptimizer._calculate_nutrients``  (``advanced_calculator.py``)
  guards with ``if code in self.materials``; an unknown code contributes no N,
  P, K or C.
* ``FormulationOptimizer._calculate_cost`` and ``CostBenefitCalculator.analyze``
  guard the same way; an unknown code contributes no money.
* ``ScaleCalculator.scale`` uses ``self.materials.get(code, {}).get(
  "cost_per_ton_usd", 0)``, so an unknown code is quoted to the client at
  **zero cost**.

Meanwhile ``total_kg_per_ha`` is a hand-written total that does include it, and
``GET /api/nojin/recipes/<code>`` serves the composition verbatim. The result is
a recipe that reports its full tonnage and a quote that excludes a fifth of it,
with no error anywhere.

That is not hypothetical: ``NOJIN-ARID-1`` carried ``"MIN-025": 5000`` and no
material with that code has ever existed. 5000 kg/ha and its cost vanished from
every computed total. The pre-existing check missed it because
``test_cn_ratio_balanced`` skips the codes it cannot resolve::

    mat = next((m for m in MATERIALS if m["material_code"] == code), None)
    if mat:            # <- unknown code falls through and is silently ignored

So the rule this module enforces is the opposite: an unknown code is a hard
failure, and the checker is itself tested against a deliberately broken
composition so it cannot be neutered into passing again.

The ``cn_ratio`` rule
---------------------
``cn_ratio`` is not an independent measurement. It is the quotient of the
``carbon_pct`` and ``nitrogen_pct`` in the same row, and it is computed that way
everywhere it is actually used: ``FormulationOptimizer._calculate_nutrients``
derives ``C_kg / N_kg`` from those two fields and never reads ``cn_ratio``, and
``test_cn_ratio_balanced`` derives it the same way. The stored column is a
hand-entered number that only ever reaches a client as a display label
(``routers/nojin.py`` serves ``material.cn_ratio`` straight off the row).

Where the two disagreed, the hand-entered value was the wrong one: five of the
seven rows that carry both a carbon and a nitrogen percentage were arithmetic
transpositions, and one of them (PLM-001, stored 25.0) is the "C/N optimization
at 25-30" figure from that row's own ``modern_research`` note -- an application
*target* for a finished mix, transcribed as a *material property*. The seventh,
PLM-003, matches its quotient exactly, which is the signature of the one row
that was computed rather than guessed. Six rows were corrected to the quotient;
``carbon_pct`` and ``nitrogen_pct`` were left alone because they are the inputs
three calculators multiply through every recipe.

Seventeen rows store a ``cn_ratio`` with no ``carbon_pct`` at all, and two more
(``CAR-021``, ``SPC-036``) state a carbon and a nitrogen percentage but no
ratio. Neither group is a disagreement -- a number is missing, not two in
conflict -- so they are excluded from the check and named here so the exclusion
is a decision rather than an oversight. Filling either group in would be
fabricating a measurement.
"""

from __future__ import annotations

import json

import pytest

from engine.hydroma.biofertilizer.data import FORMULATIONS, MATERIALS

CODES = frozenset(m["material_code"] for m in MATERIALS)

#: Derived-value tolerance. carbon_pct/nitrogen_pct carry one decimal, so the
#: quotient of two of them is meaningful to roughly that precision.
CN_TOLERANCE = 0.05


def composition_of(recipe: dict) -> dict[str, float]:
    """The recipe's composition as a dict, whether stored as JSON or a dict."""
    composition = recipe["material_composition"]
    return json.loads(composition) if isinstance(composition, str) else composition


def unknown_codes(composition: dict[str, float], known: frozenset[str] = CODES) -> list[str]:
    """Codes in ``composition`` that are absent from the material catalogue."""
    return sorted(code for code in composition if code not in known)


def derivable_cn_rows() -> list[dict]:
    """Materials that store all three of carbon_pct, nitrogen_pct and cn_ratio.

    A row with a carbon and a nitrogen percentage but no stored ratio is a
    different case -- one number missing, not two in conflict -- and is handled
    by :func:`ratio_derivable_but_unstated` instead.
    """
    rows = []
    for mat in MATERIALS:
        carbon = mat.get("carbon_pct")
        nitrogen = mat.get("nitrogen_pct")
        if carbon is None or not nitrogen or mat.get("cn_ratio") is None:
            continue
        rows.append({**mat, "derived_cn": carbon / nitrogen})
    return rows


def ratio_derivable_but_unstated() -> list[str]:
    """Materials whose C/N is derivable but which store no cn_ratio at all."""
    return sorted(
        m["material_code"]
        for m in MATERIALS
        if m.get("cn_ratio") is None and m.get("carbon_pct") and m.get("nitrogen_pct")
    )


class TestTheGuardItself:
    """The checker must bite, or every test built on it is decorative."""

    def test_the_guard_reports_a_code_that_does_not_exist(self):
        broken = {"MIN-011": 8000, "MIN-025": 5000, "PLM-003": 3000}
        assert unknown_codes(broken) == ["MIN-025"]

    def test_the_guard_returns_empty_for_a_known_composition(self):
        assert unknown_codes(composition_of(FORMULATIONS[0])) == []

    def test_the_guard_does_not_accept_a_near_miss(self):
        """MIN-025 must not be silently accepted because CAR-025 exists."""
        assert unknown_codes({"CAR-025": 5000, "MIN-025": 5000}) == ["MIN-025"]


class TestRecipeReferencesResolve:
    """The integrity check that would have caught MIN-025, and the next one."""

    def test_every_recipe_material_code_exists_in_materials(self):
        dangling = {
            recipe["recipe_code"]: unknown_codes(composition_of(recipe)) for recipe in FORMULATIONS
        }
        dangling = {code: bad for code, bad in dangling.items() if bad}
        assert not dangling, (
            "recipe(s) reference material codes that do not exist in MATERIALS. "
            "Each such code is skipped by the guarded lookups in "
            "advanced_calculator.py, so its kg and its cost vanish from every "
            "computed total while total_kg_per_ha still counts them, and "
            "ScaleCalculator quotes it at zero cost. dangling = "
            f"{dangling}"
        )

    @pytest.mark.parametrize("recipe", FORMULATIONS, ids=[r["recipe_code"] for r in FORMULATIONS])
    def test_no_single_recipe_has_a_dangling_reference(self, recipe):
        bad = unknown_codes(composition_of(recipe))
        assert not bad, (
            f"{recipe['recipe_code']} references {bad}, which is not in MATERIALS "
            f"({len(MATERIALS)} codes). Fix the composition, do not delete the code."
        )

    @pytest.mark.parametrize("recipe", FORMULATIONS, ids=[r["recipe_code"] for r in FORMULATIONS])
    def test_recipe_composition_sums_to_its_declared_total(self, recipe):
        """Catches the other half of the defect: a fix that drops the kg.

        ``total_kg_per_ha`` is written by hand. If a composition entry is
        removed instead of repointed, the totals stop agreeing and the recipe
        quietly under-applies.
        """
        total = sum(composition_of(recipe).values())
        assert total == recipe["total_kg_per_ha"], (
            f"{recipe['recipe_code']} composition sums to {total} kg/ha but "
            f"total_kg_per_ha is {recipe['total_kg_per_ha']}"
        )


class TestNoSilentZeroCost:
    """The consequence the dangling reference produced, pinned at its source."""

    def test_every_recipe_code_resolves_in_every_calculator(self):
        """All four engines index MATERIALS independently; check each one."""
        from engine.hydroma.biofertilizer.advanced_calculator import (
            CostBenefitCalculator,
            FormulationOptimizer,
            ScaleCalculator,
            WaterSavingsCalculator,
        )

        engines = {
            "FormulationOptimizer": FormulationOptimizer(MATERIALS, FORMULATIONS).materials,
            "CostBenefitCalculator": CostBenefitCalculator(MATERIALS).materials,
            "WaterSavingsCalculator": WaterSavingsCalculator(MATERIALS).materials,
            "ScaleCalculator": ScaleCalculator(MATERIALS).materials,
        }
        broken = {}
        for name, index in engines.items():
            missing = {
                recipe["recipe_code"]: unknown_codes(composition_of(recipe), frozenset(index))
                for recipe in FORMULATIONS
            }
            missing = {code: bad for code, bad in missing.items() if bad}
            if missing:
                broken[name] = missing
        assert not broken, f"calculator(s) cannot resolve recipe codes: {broken}"

    @pytest.mark.parametrize("recipe", FORMULATIONS, ids=[r["recipe_code"] for r in FORMULATIONS])
    def test_no_recipe_material_is_quoted_at_zero_cost(self, recipe):
        """ScaleCalculator prices a material it cannot resolve at 0.0 USD/t."""
        from engine.hydroma.biofertilizer.advanced_calculator import ScaleCalculator

        result = ScaleCalculator(MATERIALS).scale(composition_of(recipe), area_ha=10.0)
        unpriced = sorted(
            code for code, qty in result.material_quantities.items() if qty["cost_usd"] <= 0
        )
        assert not unpriced, (
            f"{recipe['recipe_code']} prices {unpriced} at zero cost. A zero here "
            "means the code did not resolve, not that the material is free."
        )


class TestCnRatioIsDerivable:
    """cn_ratio must equal carbon_pct / nitrogen_pct wherever both are present."""

    def test_the_derivation_is_possible_for_at_least_seven_materials(self):
        """Guards the guard: an empty derivation would make the check vacuous."""
        assert len(derivable_cn_rows()) >= 7

    def test_stored_cn_ratio_equals_carbon_over_nitrogen(self):
        wrong = {
            row["material_code"]: {
                "stored": row["cn_ratio"],
                "derived": round(row["derived_cn"], 2),
            }
            for row in derivable_cn_rows()
            if abs(row["cn_ratio"] - row["derived_cn"]) > CN_TOLERANCE
        }
        assert not wrong, (
            "cn_ratio is the quotient of the carbon and nitrogen percentages in "
            "the same row, and it is computed that way in "
            "FormulationOptimizer._calculate_nutrients. A stored value that "
            f"disagrees is a display label contradicting the engine. {wrong}"
        )

    def test_the_corrected_rows_reconcile(self):
        """Pins the six rows that were corrected on 2026-09-29.

        Named individually so a future edit that reintroduces a hand-entered
        ratio fails here with the code in the message.
        """
        by_code = {m["material_code"]: m for m in MATERIALS}
        expected = {
            "PLM-001": 85.0,  # was 25.0 -- the mix target from modern_research
            "PLM-002": 43.75,  # was 18.0
            "PLM-004": 42.0,  # was 60.0
            "PLM-006": 56.25,  # was 30.0
            "PLM-008": 90.0,  # was 80.0
            "PLM-010": 166.67,  # was 100.0
        }
        for code, value in expected.items():
            row = by_code[code]
            assert row["cn_ratio"] == pytest.approx(value, abs=CN_TOLERANCE), (
                f"{code} cn_ratio was changed away from its carbon/nitrogen quotient"
            )
            assert row["cn_ratio"] == pytest.approx(
                row["carbon_pct"] / row["nitrogen_pct"], abs=CN_TOLERANCE
            )

    def test_rows_without_carbon_are_reported_not_guessed(self):
        """The 17 rows with a ratio but no carbon figure stay un-checkable.

        They are asserted absent rather than filled in: fabricating a
        carbon_pct to make a ratio derivable would be inventing a measurement.
        """
        undeclared = [
            m["material_code"]
            for m in MATERIALS
            if m.get("cn_ratio") is not None and m.get("carbon_pct") is None
        ]
        assert len(undeclared) == 17, (
            "the set of materials with a cn_ratio but no carbon_pct changed; "
            f"re-derive rather than assume. now = {undeclared}"
        )

    def test_rows_with_carbon_but_no_stored_ratio_are_reported_not_guessed(self):
        """The mirror case: C/N derivable, cn_ratio simply absent.

        CAR-021 and SPC-036 both state carbon and nitrogen but no ratio. The
        engine never reads the stored ratio, so the absence is inert -- but it
        is listed so that adding one later is a deliberate, checked act.
        """
        assert ratio_derivable_but_unstated() == ["CAR-021", "SPC-036"]
