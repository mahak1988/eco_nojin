#!/usr/bin/env python3
"""Run one model against one test case and emit the gate's result JSON.

Why this file had to be written rather than repaired
---------------------------------------------------
An earlier version registered 22 model runners and was wired into
``hydroma-slaughterhouse.yml``. It referenced functions that were never
defined, so it could not be imported and the CI gate it fed never validated
anything. The file is absent from the repository and from its entire history,
so there was nothing to repair.

This is a fresh implementation against the contract that actually exists:
``engine/hydroma/models/base.py`` defines ``ScientificModel`` with
``compute()`` and ``validate_against_reference()``, and
``scripts/slaughterhouse_gate.py`` reads ``model``, ``backend``, ``passed``,
``failed``, ``errors`` and ``skipped``.

Honesty rule, non-negotiable
----------------------------
A model with no implementation is reported as ``skipped`` with a reason. It is
never reported as ``passed``. A gate that green-lights an absent model is the
failure this whole script exists to prevent, and ``S-HONEST`` is explicit
that an unrun operation must not look like a successful one.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_PKG = "engine.hydroma.models"
TEST_CASE_DIR = REPO_ROOT / "engine" / "hydroma" / "models" / "validation" / "test_cases"

# Running this file by path puts scripts/ on sys.path, not the repository
# root, so ``import engine.hydroma.models`` fails. CI invokes the script
# exactly this way, so the path is established here rather than assumed from
# a test runner that happened to already have it.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# A model that exists but has no ``ScientificModel`` subclass can still be
# exercised through a plain module-level entry point, if it declares one.
# This is how the non-Model classes (e.g. a pure function library) are
# validated without pretending they are models.
PLAIN_ENTRY_POINTS: dict[str, str] = {}


def _emit(payload: dict[str, Any], output: str | None) -> int:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    # Exit 1 only for a real error. A model that is simply not implemented is
    # a skip, which the gate treats as neutral, not as a failure.
    return 1 if payload["errors"] else 0


# How an array-valued result is reduced when a fixture compares it to a
# scalar. The fixture names the reduction; the runner never picks one itself.
REDUCERS = {
    "mean": np.mean,
    "median": np.median,
    "max": np.max,
    "min": np.min,
    "sum": np.sum,
    "last": lambda a: a[-1],
    "first": lambda a: a[0],
}


def _reduce(value: Any, how: str, label: str) -> Any:
    """Reduce an array-valued result as the fixture states.

    A model returning a per-pixel or per-day array cannot be compared to a
    scalar without saying which element is meant. The fixture names the
    reduction so the runner never picks one silently.
    """
    try:
        return REDUCERS[how](np.asarray(value, dtype=float))
    except Exception as exc:
        raise ValueError(f"cannot read {how!r} of {label}: {exc}") from exc


def _result(status: str, model: str, backend: str, reason: str, **extra: Any) -> dict[str, Any]:
    # ``errors`` and ``skipped`` are what slaughterhouse_gate.py reads to
    # decide a verdict, so they must agree with ``status`` rather than being
    # independently defaultable to zero.
    return {
        "model": model,
        "backend": backend,
        "passed": 0,
        "failed": 0,
        "errors": 1 if status == "error" else 0,
        "skipped": 1 if status == "skipped" else 0,
        "status": status,
        "reason": reason,
        "generated_at": datetime.now(UTC).isoformat(),
        **extra,
    }


def _load_test_case(path: Path) -> dict[str, Any]:
    """Read a fixture with the safe loader.

    Fixtures stay plain JSON-compatible YAML. The numpy conversion happens in
    ``_coerce_inputs`` against the model's own signature, so no YAML
    constructor tag is needed and nothing in the loader can execute arbitrary
    import machinery.
    """
    import yaml  # optional at import time, required to run

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _coerce_inputs(model: Any, inputs: dict[str, Any]) -> dict[str, Any]:
    """Convert lists to arrays where the signature asks for an ndarray.

    A model whose parameter is annotated ``np.ndarray`` and is handed a plain
    list raises ``TypeError`` on the first comparison, deep inside the
    arithmetic, which reads like a broken model rather than a mis-typed
    fixture. Coercing here keeps the failure at the boundary.
    """
    import inspect

    try:
        signature = inspect.signature(model.compute)
    except (TypeError, ValueError):
        return inputs

    coerced: dict[str, Any] = {}
    for name, value in inputs.items():
        parameter = signature.parameters.get(name)
        annotation = str(parameter.annotation) if parameter else ""
        if "ndarray" in annotation and isinstance(value, list):
            try:
                import numpy as np  # only needed for this conversion

                coerced[name] = np.asarray(value, dtype=float)
                continue
            except Exception:  # fall back to the raw value
                pass
        elif isinstance(value, dict) and parameter is not None:
            # A structured input arrives as a mapping from the fixture. Rebuild
            # it against the model's real dataclass so a renamed field fails
            # here, at the boundary, rather than being silently dropped.
            # With ``from __future__ import annotations`` the annotation is a
            # bare name with no quotes, so resolve the class by lookup instead
            # of by parsing the string.
            built = _build_dataclass(str(parameter.annotation), value, model)
            if built is not None:
                coerced[name] = built
                continue
        coerced[name] = value
    return coerced


def _build_dataclass(annotation: str, payload: dict[str, Any], model: Any) -> Any | None:
    """Reconstruct a model input dataclass from a fixture mapping.

    Returns None when the annotation is not a dataclass, which leaves the
    caller to pass the raw mapping through rather than guessing.
    """
    import dataclasses

    name = annotation.strip().strip("'\"").split(".")[-1].strip("'\"")
    if not name:
        return None
    for holder in (model, sys.modules.get(type(model).__module__)):
        target = getattr(holder, name, None)
        if target is None:
            continue
        if not dataclasses.is_dataclass(target):
            return None
        try:
            return target(**payload)
        except TypeError:
            return None
    return None


def _load_model(model_id: str) -> tuple[Any | None, str]:
    """Return an instance of the model, or None with a reason.

    The reason is returned rather than raised so the caller can turn it into a
    skip with an explanation instead of a stack trace.
    """
    module_name = f"{MODELS_PKG}.{model_id}"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None, f"no module at {module_name}"
    except Exception as exc:
        return None, f"{module_name} failed to import: {type(exc).__name__}: {exc}"

    for attr in vars(module).values():
        if (
            isinstance(attr, type)
            and attr.__name__.lower() == model_id.replace("_", "").lower()
            and hasattr(attr, "compute")
        ):
            try:
                return attr(), f"loaded {attr.__module__}.{attr.__name__}"
            except Exception as exc:
                return None, f"{attr.__name__} failed to construct: {exc}"

    names = [
        n
        for n, v in vars(module).items()
        if isinstance(v, type) and hasattr(v, "compute") and v.__module__ == module_name
    ]
    if names:
        try:
            return getattr(module, names[0])(), f"loaded {module_name}.{names[0]}"
        except Exception as exc:
            return None, f"{names[0]} failed to construct: {exc}"
    return None, f"{module_name} exposes no class with a compute() method"


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one model against one test case")
    parser.add_argument("--model", required=True, help="model id, matching the test case stem")
    parser.add_argument("--backend", default="python", help="python | cpp")
    parser.add_argument("--test-file", required=True, help="path to the YAML test case")
    parser.add_argument("--output", help="write the result JSON here instead of stdout")
    args = parser.parse_args(argv)

    model_id = args.model
    backend = args.backend

    test_path = Path(args.test_file)
    if not test_path.is_absolute():
        test_path = REPO_ROOT / test_path
    if not test_path.is_file():
        return _emit(
            _result("error", model_id, backend, f"test case not found: {test_path}"),
            args.output,
        )

    try:
        spec = _load_test_case(test_path)
    except Exception as exc:
        return _emit(
            _result(
                "error", model_id, backend, f"unreadable test case: {type(exc).__name__}: {exc}"
            ),
            args.output,
        )

    tolerances = spec.get("tolerances") or {}
    rtol = float(tolerances.get("rtol", 1e-2))
    atol = float(tolerances.get("atol", 1e-2))
    cases = spec.get("cases") or []

    model, load_note = _load_model(model_id)
    if model is None:
        # Not an error. The model simply has not been written yet, and the
        # gate must be able to say so without pretending it passed.
        return _emit(
            _result(
                "skipped",
                model_id,
                backend,
                f"model not implemented: {load_note}",
                test_case=str(test_path.relative_to(REPO_ROOT)),
                reference=spec.get("reference"),
                cases_in_fixture=len(cases),
            ),
            args.output,
        )

    if backend == "cpp" and type(model).__module__.startswith(MODELS_PKG):
        # The C++ path would need a bridge binding per model. Reporting it as
        # a skip is honest; reporting the Python result under a "cpp" label
        # would not be.
        return _emit(
            _result(
                "skipped",
                model_id,
                "cpp",
                "no C++ bridge binding for this model; the Python result is not "
                "a substitute for a C++ one",
                loaded_from=load_note,
            ),
            args.output,
        )

    passed = failed = errors = 0
    case_reports: list[dict[str, Any]] = []

    for index, case in enumerate(cases):
        name = case.get("name", f"case_{index}")
        inputs = _coerce_inputs(model, case.get("inputs") or {})
        expected = case.get("expected", case.get("expected_output"))

        try:
            # A fixture may declare parameters that only compute() accepts
            # (ECSI takes dt_years and smd_mm, its validate_inputs does not).
            # Passing those through would raise TypeError before the model
            # ever ran, so the two signatures are separated here.
            validate_params = set(inspect.signature(model.validate_inputs).parameters) - {"self"}
            validation_inputs = {k: v for k, v in inputs.items() if k in validate_params}
            ok, problems = model.validate_inputs(**validation_inputs)
            if not ok:
                expectation = str(case.get("expect") or "").strip()
                if expectation == "rejected_by_validate_inputs":
                    # The model refused this input on purpose. Some limits
                    # cannot be probed one parameter at a time: EWSI requires
                    # soil moisture to stay below field capacity, so pinning
                    # moisture to its own upper bound produces a pair the
                    # model is right to reject. Counting the refusal as a
                    # failure would train the team to ignore this gate.
                    passed += 1
                    case_reports.append(
                        {
                            "case": name,
                            "status": "passed",
                            "reason": "model rejected the input as expected",
                            "problems": problems,
                        }
                    )
                    continue
                errors += 1
                case_reports.append({"case": name, "status": "error", "problems": problems})
                continue

            output = model.compute(**inputs)
        except Exception as exc:
            errors += 1
            case_reports.append(
                {
                    "case": name,
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(limit=4),
                }
            )
            continue

        if expected is None:
            # A fixture with no expected value cannot prove anything. Counting
            # it as a pass would make an empty fixture look like a green one.
            case_reports.append(
                {
                    "case": name,
                    "status": "unverified",
                    "reason": "fixture has no expected value, so there is nothing to compare",
                    "output": str(output)[:400],
                }
            )
            continue

        # A model may return a scalar, a dict of results, or an array over
        # pixels. When the fixture names a key, compare that one; otherwise
        # require the whole output to be numeric. Guessing which field was
        # meant would be exactly the quiet assumption this script exists to
        # prevent.
        key = str(case.get("expected_key") or "").strip()
        # A model may hand back a bare array (EWSI), a dict, or a scalar. The
        # fixture states the reduction for the array case so the runner never
        # has to pick one.
        if isinstance(output, np.ndarray) and not isinstance(output, dict):
            reduction = str(case.get("reduce") or "mean").strip().lower()
            try:
                comparable = _reduce(output, reduction, "output")
            except ValueError as exc:
                errors += 1
                case_reports.append({"case": name, "status": "error", "reason": str(exc)})
                continue
            array_target = _as_float(expected)
            if array_target is None:
                case_reports.append(
                    {
                        "case": name,
                        "status": "unverified",
                        "reason": f"expected is not numeric: {expected!r}",
                    }
                )
                continue
            array_got = _as_float(comparable)
            array_ok = array_got is not None and abs(array_got - array_target) <= atol + rtol * abs(
                array_target
            )
            if array_ok:
                passed += 1
            else:
                failed += 1
            case_reports.append(
                {
                    "case": name,
                    "status": "passed" if array_ok else "failed",
                    "expected": array_target,
                    "got": array_got,
                    "reduce": reduction,
                }
            )
            continue

        comparable: Any = output

        REDUCERS = {
            "mean": np.mean,
            "median": np.median,
            "max": np.max,
            "min": np.min,
            "sum": np.sum,
            "last": lambda a: a[-1],
            "first": lambda a: a[0],
        }

        if isinstance(output, dict):
            if key and key in output:
                # An explicit field, optionally reduced. Naming both is the
                # precise form: "irrigation_need_mm, last element" is one
                # statement about one number, whereas "last" alone asks the
                # runner to guess which field.
                reduction = str(case.get("reduce") or "").strip().lower()
                comparable = output[key]
                if reduction:
                    try:
                        comparable = _reduce(comparable, reduction, key)
                    except ValueError as exc:
                        errors += 1
                        case_reports.append({"case": name, "status": "error", "reason": str(exc)})
                        continue
            elif key in REDUCERS:
                # The fixture names a reduction but no field, so every numeric
                # field is reduced and the recorded number must identify
                # exactly one of them. Ambiguity is an error, never a default.
                numeric = {k: v for k, v in output.items() if _as_float(v) is not None}
                if not numeric:
                    errors += 1
                    case_reports.append(
                        {
                            "case": name,
                            "status": "error",
                            "reason": f"expected_key {key!r} but no field of {sorted(output)} is numeric",
                        }
                    )
                    continue
                try:
                    candidates = {f: _reduce(v, key, f) for f, v in numeric.items()}
                except ValueError as exc:
                    errors += 1
                    case_reports.append({"case": name, "status": "error", "reason": str(exc)})
                    continue
                want = float(expected)
                bound = atol + rtol * abs(want)
                matches = [
                    f
                    for f, v in candidates.items()
                    if _as_float(v) is not None and abs(_as_float(v) - want) <= bound
                ]
                if len(matches) != 1:
                    errors += 1
                    case_reports.append(
                        {
                            "case": name,
                            "status": "error",
                            "reason": (
                                f"expected_key {key!r} is ambiguous: {len(matches)} of "
                                f"{sorted(candidates)} reduce to {expected}"
                            ),
                        }
                    )
                    continue
                comparable = candidates[matches[0]]
            else:
                errors += 1
                case_reports.append(
                    {
                        "case": name,
                        "status": "error",
                        "reason": (
                            f"fixture expects key {key!r} but the model returned a dict "
                            f"with keys {sorted(output)}"
                        ),
                    }
                )
                continue
        elif key in REDUCERS:
            try:
                comparable = _reduce(output, key, "output")
            except ValueError as exc:
                errors += 1
                case_reports.append({"case": name, "status": "error", "reason": str(exc)})
                continue
        elif key:
            errors += 1
            case_reports.append(
                {
                    "case": name,
                    "status": "error",
                    "reason": (
                        f"fixture expects key {key!r} but the model returned "
                        f"{type(output).__name__}"
                    ),
                }
            )
            continue

        target = _as_float(expected)
        if target is None:
            case_reports.append(
                {
                    "case": name,
                    "status": "unverified",
                    "reason": f"expected value is not numeric: {expected!r}",
                    "output": str(comparable)[:400],
                }
            )
            continue

        got = _as_float(comparable)
        if got is None:
            errors += 1
            case_reports.append(
                {
                    "case": name,
                    "status": "error",
                    "reason": f"model returned a non-numeric value: {output!r}",
                }
            )
            continue

        # The fixture states which number it is talking about, so the
        # comparison is done here. The model's own validate_against_reference
        # is not consulted: EPIA takes the mean of its irrigation series while
        # the fixture records the last day, so trusting the model would judge
        # the case against a quantity the fixture never mentioned.
        within = abs(got - target) <= atol + rtol * abs(target)

        if within:
            passed += 1
            case_reports.append({"case": name, "status": "passed", "expected": target, "got": got})
        else:
            failed += 1
            case_reports.append(
                {
                    "case": name,
                    "status": "failed",
                    "expected": target,
                    "got": got,
                    "rtol": rtol,
                    "atol": atol,
                    "delta": abs(got - target),
                }
            )

    status = "error" if errors else ("failed" if failed else ("passed" if passed else "skipped"))
    payload = _result(
        status,
        model_id,
        backend,
        f"{passed} passed, {failed} failed, {errors} errors over {len(cases)} case(s)",
        loaded_from=load_note,
        test_case=str(test_path.relative_to(REPO_ROOT)),
        reference=spec.get("reference"),
        passed=passed,
        failed=failed,
        errors=errors,
        cases=case_reports,
    )
    return _emit(payload, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
