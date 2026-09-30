"""Tests for the formula evaluator's failure behaviour.

The previous evaluator returned ``0.0`` for every failure mode: unparsable
syntax, unknown name, division by zero, overflow, non-numeric result. A real
index that legitimately evaluates to zero was therefore indistinguishable from a
typo, and a typoed variable name was substituted with ``0`` so the formula still
produced a plausible number.

Two concrete failures hid behind that:

* ``rainfal_mm * 2`` (a typo) evaluated to ``0.0`` and looked valid;
* ``sum`` was missing from the allow-list that ``Call`` nodes consult, so every
  ``Σ(...)`` aggregation in the knowledge base raised and was swallowed to ``0.0``.
"""

from __future__ import annotations

import pytest

from engine.hydroma.calculation.formula_evaluator import (
    MAX_EXPONENT,
    FormulaEvaluationError,
    FormulaEvaluator,
)

ev = FormulaEvaluator()


# ------------------------------------------------------------- it still works


def test_arithmetic():
    assert ev.evaluate("2 + 3 * 4") == 14.0
    assert ev.evaluate("(2 + 3) * 4") == 20.0
    assert ev.evaluate("value = 7 / 2") == 3.5


def test_variables_and_implicit_multiplication():
    assert ev.evaluate("2 rain", {"rain": 3.0}) == 6.0
    assert ev.evaluate("a * b", {"a": 2.0, "b": 5.0}) == 10.0


def test_prefixed_name_is_not_clipped_by_a_shorter_one():
    """Substitution is length-ordered so 'total_precip' survives 'total'."""
    out = ev.evaluate("total_precip - total", {"total_precip": 100.0, "total": 40.0})
    assert out == 60.0


def test_allowed_functions():
    assert ev.evaluate("sqrt(16)") == 4.0
    assert ev.evaluate("abs(-3)") == 3.0
    assert ev.evaluate("min(1, 2)") == 1.0
    assert ev.evaluate("max(1, 2)") == 2.0


def test_unicode_operators():
    assert ev.evaluate("2 × 3") == 6.0
    assert ev.evaluate("6 ÷ 3") == 2.0


# ------------------------------------------------------- sigma now works at all


def test_sigma_aggregation_evaluates():
    """Regression: sum was absent from the Call allow-list, so every Σ was 0.0."""
    out = ev.evaluate("Σ(1, 2, 3, 4)")
    assert out == 10.0, "the sigma notation must aggregate, not silently return zero"


def test_sum_function_evaluates():
    assert ev.evaluate("sum(1, 2, 3)") == 6.0


def test_sigma_inside_a_larger_expression():
    assert ev.evaluate("Σ(a, b) * 2", {"a": 1.0, "b": 2.0}) == 6.0


# ------------------------------------------------------- failures now raise


def test_typo_does_not_become_zero():
    """The regression: an unresolved identifier was replaced with 0."""
    with pytest.raises(FormulaEvaluationError) as exc:
        ev.evaluate("rainfal_mm * 2", {"rain_mm": 3.0})
    assert "rainfal_mm" in str(exc.value)
    assert "rainfal_mm" in exc.value.unresolved


def test_missing_input_names_the_variable():
    with pytest.raises(FormulaEvaluationError) as exc:
        ev.evaluate("total_precip - effective_rain", {"total_precip": 100.0})
    assert exc.value.unresolved == ("effective_rain",)


def test_syntax_error_raises():
    with pytest.raises(FormulaEvaluationError, match="does not parse"):
        ev.evaluate("2 +")


def test_empty_formula_raises():
    with pytest.raises(FormulaEvaluationError, match="empty"):
        ev.evaluate("   ")


def test_division_by_zero_raises():
    with pytest.raises(FormulaEvaluationError):
        ev.evaluate("1 / 0")


def test_non_numeric_call_is_reported_as_such():
    """An unknown name is caught before the Call branch, naming the name."""
    with pytest.raises(FormulaEvaluationError, match="call_disallowed"):
        ev.evaluate("call_disallowed(1)")


def test_wrong_arity_is_reported_as_such():
    with pytest.raises(FormulaEvaluationError, match="called incorrectly"):
        ev.evaluate("sqrt(1, 2, 3)")


def test_disallowed_syntax_is_rejected():
    for expr in ("__import__('os')", "[x for x in range(3)]", "a.b", "a[0]", "lambda: 1"):
        with pytest.raises(FormulaEvaluationError):
            ev.evaluate(expr, {"a": 1.0})


def test_error_never_silently_becomes_zero():
    """Every failure path must raise, not return a number."""
    for expr, args in [
        ("2 +", {}),
        ("unknown_name", {}),
        ("1/0", {}),
        ("2 ** 100000", {}),
        ("", {}),
    ]:
        with pytest.raises(FormulaEvaluationError):
            ev.evaluate(expr, args)


# ----------------------------------------------------------------- limits


def test_pow_is_bounded():
    """Regression: pow with no bound is a CPU and memory exhaustion vector."""
    with pytest.raises(FormulaEvaluationError, match=f"exceeds the limit {MAX_EXPONENT}"):
        ev.evaluate(f"2 ** {MAX_EXPONENT + 1}")


def test_deep_nesting_is_bounded():
    """Nested calls drive the recursive walker's depth; redundant parens do not,
    because the parser folds those away before the evaluator sees them."""
    with pytest.raises(FormulaEvaluationError, match="nested deeper"):
        ev.evaluate("abs(" * 200 + "1" + ")" * 200)


def test_long_expression_is_bounded():
    with pytest.raises(FormulaEvaluationError, match="limit"):
        ev.evaluate("1 + " * 2000 + "1")


def test_scientific_notation_is_not_split():
    """Regression guard: a naive implicit-multiplication rule turned 1e308 into
    1 * e308 and reported it as a missing input."""
    assert ev.evaluate("1e3") == 1000.0
    assert ev.evaluate("1.5e2 + 1") == 151.0


def test_infinite_result_is_rejected():
    with pytest.raises(FormulaEvaluationError, match="exceeds the limit"):
        ev.evaluate("1e308 * 1e10")


# ------------------------------------------------- opt-in leniency for callers


def test_non_strict_mode_still_works_but_logs():
    assert ev.evaluate("unknown_name", {}, strict=False) == 0.0
    assert ev.evaluate("1/0", {}, strict=False) == 0.0


# ----------------------------------------------------- the computed-zero case


def test_a_genuine_zero_is_not_an_error():
    """The distinction the old code destroyed: computed zero vs failed."""
    assert ev.evaluate("5 - 5") == 0.0
    assert ev.evaluate("0 * rain", {"rain": 99.0}) == 0.0
