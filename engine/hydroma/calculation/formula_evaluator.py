#!/usr/bin/env python3
"""
موتور ارزیابی فرمول هیدروما

A small, allow-listed expression evaluator for indicator formulas.

Correctness contract
--------------------
The evaluator never returns a number for a formula it could not compute. This is
the change from the previous version, which returned ``0.0`` for *every* failure
mode -- unparsable syntax, unknown name, division by zero, overflow, non-numeric
result. Because a real index that happens to be zero is indistinguishable from
an error that returned zero, an agronomist could not tell a computed value from a
typo that silently became ``0``. Two concrete failures that hid behind that:

- an unresolved identifier was replaced with ``0``, so ``rainfal_mm * 2``
  (a typo) evaluated to ``0.0`` and looked like a valid answer;
- ``sum`` was absent from the module-level allow-list that ``safe_eval`` consults
  for ``Call`` nodes, so every ``Σ(...)`` indicator -- the notation the knowledge
  base uses for aggregation -- raised and was swallowed to ``0.0``.

Failures now raise :class:`FormulaEvaluationError` naming the cause. Callers that
genuinely want the old lenient behaviour pass ``strict=False``.

Limits
------
``pow`` is permitted, so ``2.0 ** 10000000`` is a CPU and memory exhaustion
vector. Magnitude and length are bounded, and evaluation depth is capped. The
previous version had no bound of any kind.
"""

import ast as _ast
import math
import math as _math
import operator as _operator
import re

#: Maximum accepted magnitude of an intermediate or final value. Above this the
#: expression is treated as abusive rather than merely wrong.
MAX_MAGNITUDE = 1e300

#: Maximum accepted operator-precedence nesting depth. Guards the recursive
#: descent walker against ``1+1+1+...`` nested deeply enough to blow the stack.
MAX_DEPTH = 64

#: Maximum accepted expression length in characters.
MAX_LENGTH = 2000

#: Maximum accepted ``**`` exponent. Without this, pow alone is a DoS.
MAX_EXPONENT = 1000


class FormulaEvaluationError(ValueError):
    """Raised when a formula cannot be evaluated.

    Carries the reason and, where applicable, the identifiers that could not be
    resolved, so the caller can report which input was missing.
    """

    def __init__(self, message: str, *, unresolved: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.unresolved = unresolved


_ALLOWED_FUNCS = {
    f: getattr(_math, f)
    for f in (
        "sqrt",
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "log",
        "log2",
        "log10",
        "exp",
        "floor",
        "ceil",
        "fabs",
        "pow",
        "atan2",
        "hypot",
    )
}
#: ``sum`` is what ``Σ(`` is rewritten to. The builtin takes an iterable, while
#: the knowledge base writes ``Σ(a, b, c)`` with separate terms, so a varargs
#: wrapper accepts both spellings.
def _sum(*args):
    if len(args) == 1 and hasattr(args[0], "__iter__"):
        return sum(args[0])
    return sum(args)


#: ``sum`` was missing from the module-level allow-list that ``Call`` nodes
#: consult, so every ``Σ(...)`` aggregation in the knowledge base raised and was
#: silently reported as 0.0.
_ALLOWED_FUNCS.update(
    {"abs": abs, "min": min, "max": max, "round": round, "sum": _sum}
)
_ALLOWED_OPS = {
    _ast.Add: _operator.add,
    _ast.Sub: _operator.sub,
    _ast.Mult: _operator.mul,
    _ast.Div: _operator.truediv,
    _ast.FloorDiv: _operator.floordiv,
    _ast.Mod: _operator.mod,
    _ast.Pow: _operator.pow,
    _ast.USub: _operator.neg,
    _ast.UAdd: _operator.pos,
}


def _guard(value, depth: int = 0):
    """Apply the numeric limits to an intermediate result."""
    if depth > MAX_DEPTH:
        raise FormulaEvaluationError(f"expression nested deeper than {MAX_DEPTH} levels")
    if isinstance(value, complex):
        raise FormulaEvaluationError("complex result")
    if isinstance(value, (int, float)):
        if math.isnan(value):
            raise FormulaEvaluationError("result is NaN")
        if math.isinf(value):
            raise FormulaEvaluationError("result is infinite")
        if abs(value) > MAX_MAGNITUDE:
            raise FormulaEvaluationError(
                f"magnitude {abs(value):.3e} exceeds the limit {MAX_MAGNITUDE:.0e}"
            )
    return value


def _apply_op(op_type, left, right):
    """Apply a binary operator, converting arithmetic errors to a named failure."""
    try:
        return _ALLOWED_OPS[op_type](left, right)
    except ZeroDivisionError as exc:
        raise FormulaEvaluationError("division by zero") from exc
    except OverflowError as exc:
        raise FormulaEvaluationError("numeric overflow") from exc


def safe_eval(node, variables: dict, depth: int = 0):
    """Evaluate an allow-listed AST. Attribute access, subscripting, lambdas,
    comprehensions, comparisons and boolean operators are all rejected."""
    if depth > MAX_DEPTH:
        raise FormulaEvaluationError(f"expression nested deeper than {MAX_DEPTH} levels")
    if isinstance(node, _ast.Expression):
        return safe_eval(node.body, variables, depth)
    if isinstance(node, _ast.Constant):
        if isinstance(node.value, (int, float)):
            return _guard(node.value)
        raise FormulaEvaluationError(f"unsupported constant {node.value!r}")
    if isinstance(node, _ast.Name):
        if node.id in variables:
            return variables[node.id]
        if node.id in _ALLOWED_FUNCS:
            return _ALLOWED_FUNCS[node.id]
        raise FormulaEvaluationError(f"unknown name {node.id!r}", unresolved=(node.id,))
    if isinstance(node, _ast.BinOp):
        left = safe_eval(node.left, variables, depth + 1)
        right = safe_eval(node.right, variables, depth + 1)
        if isinstance(node.op, _ast.Pow) and abs(right) > MAX_EXPONENT:
            raise FormulaEvaluationError(
                f"exponent {right} exceeds the limit {MAX_EXPONENT}"
            )
        return _guard(_apply_op(type(node.op), left, right))
    if isinstance(node, _ast.UnaryOp):
        try:
            return _guard(
                _ALLOWED_OPS[type(node.op)](safe_eval(node.operand, variables, depth + 1))
            )
        except (ZeroDivisionError, OverflowError) as exc:
            raise FormulaEvaluationError(f"unary operation failed: {exc}") from exc
    if isinstance(node, _ast.Tuple):
        return tuple(safe_eval(e, variables, depth + 1) for e in node.elts)
    if isinstance(node, _ast.List):
        return [safe_eval(e, variables, depth + 1) for e in node.elts]
    if isinstance(node, _ast.Call):
        name = node.func.id if isinstance(node.func, _ast.Name) else None
        if name not in _ALLOWED_FUNCS:
            raise FormulaEvaluationError(f"call to a function that is not allowed: {name!r}")
        try:
            return _guard(
                _ALLOWED_FUNCS[name](
                    *(safe_eval(a, variables, depth + 1) for a in node.args)
                )
            )
        except FormulaEvaluationError:
            raise
        except TypeError as exc:
            raise FormulaEvaluationError(f"{name}() called incorrectly: {exc}") from exc
        except (ValueError, ArithmeticError) as exc:
            raise FormulaEvaluationError(f"{name}() failed: {exc}") from exc
    raise FormulaEvaluationError(f"unsupported syntax: {type(node).__name__}")


class FormulaEvaluator:
    """Evaluate an indicator formula against a set of region values."""

    SAFE_FUNCS = frozenset(_ALLOWED_FUNCS)

    def evaluate(
        self,
        formula: str,
        variables: dict[str, float] | None = None,
        *,
        strict: bool = True,
    ) -> float:
        """Return the value of ``formula``.

        Parameters
        ----------
        formula:
            An expression. A leading ``name =`` is stripped.
        variables:
            Values by name.
        strict:
            Raise :class:`FormulaEvaluationError` on failure. With ``strict=False``
            the previous lenient behaviour is available for callers that cannot
            propagate an error; the failure is then still logged, because a silent
            zero is what this change exists to end.
        """
        if not isinstance(formula, str) or not formula.strip():
            raise FormulaEvaluationError("formula is empty")
        if len(formula) > MAX_LENGTH:
            raise FormulaEvaluationError(
                f"formula is {len(formula)} characters, limit is {MAX_LENGTH}"
            )

        variables = dict(variables or {})

        try:
            return self._evaluate(formula, variables)
        except FormulaEvaluationError as exc:
            if strict:
                raise
            import logging

            logging.getLogger(__name__).warning(
                "formula evaluation failed, returning 0.0: %s", exc
            )
            return 0.0

    def _evaluate(self, formula: str, variables: dict[str, float]) -> float:
        expr = formula
        if "=" in expr:
            expr = expr.split("=", 1)[1].strip()

        # Unicode operator translation.
        expr = expr.replace("×", "*").replace("÷", "/")
        expr = expr.replace("^", "**")
        expr = expr.replace("Σ(", "sum(")

        # The knowledge base writes implicit multiplication ("2 rain", "(a+b) c"),
        # which Python's parser rejects. Make it explicit before substituting.
        #
        # The lookahead is restricted to names actually being supplied. Matching
        # any identifier would split scientific notation -- "1e308" would become
        # "1 * e308" and be reported as a missing input.
        if variables:
            names = "|".join(re.escape(n) for n in sorted(variables, key=len, reverse=True))
            expr = re.sub(rf"(?<=[\d\)])\s*(?=(?:{names})\b)", " * ", expr)

        # Names are substituted as text because the knowledge base writes
        # formulas with implicit multiplication, e.g. "2 total_precip". The
        # substitution is length-ordered so a longer name is not clipped by a
        # shorter prefix.
        for var_name in sorted(variables, key=len, reverse=True):
            var_value = variables[var_name]
            if isinstance(var_value, (int, float)):
                expr = re.sub(rf"\b{re.escape(var_name)}\b", f"({var_value!r})", expr)

        # Any identifier still standing after substitution is a name that was not
        # supplied. The previous code replaced it with 0, which turned a typo into
        # a plausible number.
        #
        # Names are collected from the parsed AST, not by scanning the text: a
        # textual scan cannot tell the "e3" inside the literal 1e3 from a real
        # identifier.
        try:
            tree = _ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise FormulaEvaluationError(f"formula does not parse: {exc}") from exc

        unresolved = tuple(
            {
                node.id
                for node in _ast.walk(tree)
                if isinstance(node, _ast.Name)
                and node.id not in variables
                and node.id not in _ALLOWED_FUNCS
            }
        )
        if unresolved:
            raise FormulaEvaluationError(
                "formula references values that were not supplied: "
                + ", ".join(sorted(unresolved)),
                unresolved=unresolved,
            )

        result = safe_eval(tree, self.SAFE_FUNCS)

        if not isinstance(result, (int, float)):
            raise FormulaEvaluationError(
                f"formula evaluated to {type(result).__name__}, not a number"
            )
        return _guard(float(result))
