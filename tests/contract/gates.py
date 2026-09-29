"""Analysis engine behind the phase 3 CI gates.

Kept separate from the test files so that ``scripts/measure_baseline.py`` can
run exactly the same scans that CI runs. A gate that measures something
slightly different from the ratchet is worse than no gate at all.

Every scanner returns plain records with a ``rule`` name, a ``path`` and a
``line``, so a failure points at the code that has to change.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SKIP_DIR_PARTS = {
    "__pycache__",
    ".git",
    ".kilo",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "backups",
}

#: Names that identify a database call, used by the S-STRUCT gate.
#: These are matched against *callable names and attribute names*, not source
#: text — an earlier version compared against ``"select("`` with the
#: parenthesis, which never matched a bare attribute name and left the
#: router rule silently reporting zero violations.
DB_NAMES = {
    "select",
    "scalar",
    "scalars",
    "execute",
    "add",
    "add_all",
    "commit",
    "rollback",
    "flush",
    "query",
    "delete",
    "bulk_save_objects",
    "refresh",
    "merge",
}

#: Attribute chains that are unambiguously a session/engine call, even when the
#: bare name would be too generic to list on its own.
DB_ATTRIBUTES = {"query", "execute", "commit", "rollback", "flush", "add", "delete"}


@dataclass(frozen=True, order=True)
class Finding:
    rule: str
    path: str
    line: int
    detail: str

    def __str__(self) -> str:
        return f"{self.rule} {self.path}:{self.line} — {self.detail}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, rule: str, path: Path, node: ast.AST, detail: str, root: Path) -> None:
        self.findings.append(Finding(rule, _rel(path, root), getattr(node, "lineno", 0), detail))

    def __len__(self) -> int:
        return len(self.findings)

    def __iter__(self):
        return iter(self.findings)

    def __bool__(self) -> bool:
        return bool(self.findings)

    def __repr__(self) -> str:
        return f"Report({len(self.findings)} findings, {self.rules()})"

    def rules(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for finding in self.findings:
            out[finding.rule] = out.get(finding.rule, 0) + 1
        return out


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def iter_modules(root: Path, *relative: str, include_tests: bool = False) -> list[Path]:
    """Every Python module under the given roots."""
    out: list[Path] = []
    for rel in relative:
        base = root / rel
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(part in SKIP_DIR_PARTS for part in path.parts):
                continue
            if not include_tests and ("tests" in path.parts or path.name.startswith("test_")):
                continue
            out.append(path)
    return sorted(out)


def parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, ValueError, OSError):
        return None


def _call_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
    return names


def _db_call_name(node: ast.Call) -> str | None:
    """Return the name of a database call, or None.

    Attributes (``db.query(...)``) are matched on the attribute alone, because
    a session/engine is the only thing that has them in this codebase. Bare
    functions are matched against the explicit allowlist, since ``add`` or
    ``delete`` on a plain object is not a database call.
    """
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr in DB_ATTRIBUTES or func.attr in {"scalar", "scalars"}:
            return func.attr
        return None
    if isinstance(func, ast.Name) and func.id in {"select", "scalar", "scalars", "delete"}:
        return func.id
    return None


def _returns_values(node: ast.AST) -> list[ast.AST]:
    """Every ``return`` value in a function body.

    The G2 verify-constant rule needs all of them, not the first: a function
    with a guard clause has an early constant return and a real one after it.
    """
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Return) and child.value is not None
    ]


def _returns_value(node: ast.AST) -> ast.AST | None:
    values = _returns_values(node)
    return values[0] if values else None


# --------------------------------------------------------------------------- #
# G5 — S-STRUCT: layering contract
# --------------------------------------------------------------------------- #


def scan_structure(root: Path) -> Report:
    """Routers must not touch the database; services must not take a Session."""
    report = Report()
    for path in iter_modules(root, "services"):
        parts = path.parts
        if "routers" not in parts and path.name != "routers.py":
            continue
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _db_call_name(node)
                if name:
                    report.add(
                        "G5.router-touches-db",
                        path,
                        node,
                        f"router calls {name}(); DB access belongs in repository/",
                        root,
                    )
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in list(node.args.args) + list(node.args.kwonlyargs):
                    if arg.annotation is not None and _annotation_text(arg.annotation) in {
                        "Session",
                        "AsyncSession",
                    }:
                        report.add(
                            "G5.service-takes-session",
                            path,
                            node,
                            f"{node.name}() annotates a parameter as "
                            f"{_annotation_text(arg.annotation)}; only repository/ may",
                            root,
                        )
    return report


def _annotation_text(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


# --------------------------------------------------------------------------- #
# G2 — S-HONEST: fabricated success
# --------------------------------------------------------------------------- #

#: Functions whose *name* promises verification. A constant return from one of
#: these is the signature of the "verify_*(…): return True" pattern.
VERIFY_NAME = re.compile(
    r"^(verify|validate|check|is_valid|assess|confirm)_|^(verify|validate)$|^_?(verify|validate)_",
    re.IGNORECASE,
)

#: Success strings a hardcoded literal should never carry next to
#: fabricated content.
SUCCESS_LITERALS = {"passed", "ok", "completed", "success", "verified"}

#: Function-name fragments for which a *hardcoded* success assertion is a lie
#: rather than an acknowledgement.
#:
#: ``connect_oauth`` returning ``{"status": "success"}`` after really
#: connecting is honest. ``run_backup`` returning
#: ``{"verification_status": "passed"}`` without taking a backup is not. The
#: difference is not the dict — it is whether the function was supposed to
#: *compute* something. So the broad status-key rule below is gated on these
#: names; the narrow key-named-``ok`` rule is not, because a key literally
#: called ``ok``/``passed``/``verified`` in a hardcoded dict is already a
#: strong signal.
VERIFICATION_NAME = re.compile(
    r"verify|valid|check|measur|comput|assess|audit|monitor|inspect|scan|"
    r"reconcil|health|status|diagnos|validate|evaluat|record|backup|restore|"
    r"integrity|probe|test_",
    re.IGNORECASE,
)

#: Keys whose *value* is a verdict. A success value under one of these is a
#: success assertion even though the key name is not itself a success word.
STATUS_KEYS = {
    "status",
    "verification_status",
    "verify_status",
    "state",
    "outcome",
    "health",
}

#: String values that assert success when found under a STATUS_KEY.
SUCCESS_VALUES = {"passed", "ok", "completed", "success", "verified", "healthy", "pass"}


def scan_fabrications(root: Path) -> Report:
    """Detect the concrete shapes that produced fabricated success."""
    report = Report()
    for path in iter_modules(root, "services"):
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            # `except: pass`
            if isinstance(node, ast.ExceptHandler) and len(node.body) == 1:
                only = node.body[0]
                if isinstance(only, ast.Pass):
                    report.add("G2.except-pass", path, node, "except clause silently passes", root)

            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            all_returns = _returns_values(node)

            # verify_*(...) that can only ever return one constant.
            #
            # Every return in the body must be the SAME boolean constant.
            # Looking at only the first return -- as an earlier version did --
            # flags any function with a guard clause:
            #   two_factor.verify_totp() opens with `if not secret or not code:
            #   return False` and then really calls pyotp, and
            #   ssrf.validate_url() has four real checks before its `return True`.
            # Both were reported as "returns a constant", which is the gate
            # crying wolf on working security code.
            if VERIFY_NAME.match(node.name):
                booleans = [
                    r.value
                    for r in all_returns
                    if isinstance(r, ast.Constant) and isinstance(r.value, bool)
                ]
                if booleans and len(booleans) == len(all_returns) and len(set(booleans)) == 1:
                    report.add(
                        "G2.verify-returns-constant",
                        path,
                        node,
                        f"{node.name}() can only ever return {booleans[0]!r}; "
                        "it has no path that returns anything else",
                        root,
                    )
                    # Reported; do not also try to read it as a dict return.
                    continue

            if not all_returns:
                continue
            returned = all_returns[0]

            # A hardcoded dict that asserts success.
            if isinstance(returned, ast.Dict):
                keys = {k.value for k in returned.keys if isinstance(k, ast.Constant)}
                if keys & {"data", "rows", "result", "value", "count"}:
                    continue

                # Two shapes count as a success assertion:
                #   a) the key IS a success word:        {"ok": True}
                #   b) a status-like key HAS a success value:
                #      {"verification_status": "passed"}
                # Shape (b) is the one that actually shipped: backup returned
                # {"verification_status": "passed", "size_bytes": 142} and this
                # detector only matched shape (a), so the real defect was never
                # flagged.
                # ``broad``: a status-like key holding a success value, e.g.
                #   {"status": "ok"} — only suspicious when the function was
                #   supposed to compute something, so this arm is name-gated.
                # ``narrow``: the key is itself a success word, e.g. {"ok": True}
                #   — already a strong signal, so it is not name-gated.
                broad: list[str] = []
                narrow: list[str] = []
                for key_node, value_node in zip(
                    returned.keys, returned.values, strict=False
                ):
                    if not (
                        isinstance(key_node, ast.Constant)
                        and isinstance(value_node, ast.Constant)
                    ):
                        continue
                    key, value = key_node.value, value_node.value
                    if key in STATUS_KEYS and value in SUCCESS_VALUES:
                        broad.append(f"{key}={value!r}")
                    elif key in SUCCESS_LITERALS:
                        narrow.append(f"{key!r}")

                name_gated = bool(VERIFICATION_NAME.search(node.name))
                asserted = narrow + (broad if name_gated else [])
                if not asserted:
                    continue

                # The S-HONEST envelope is the opposite of a fabricated success
                # and must never be counted as one: an explicit ``status`` key
                # naming the real outcome, or a ``reason`` stating what was not
                # done, is precisely what the standard asks for.
                if "reason" in keys:
                    continue
                if "status" in keys and "status" not in STATUS_KEYS:
                    continue
                # A falsy success value ("verified": False) is a denial, not a
                # claim.
                if all(
                    isinstance(v, ast.Constant) and not v.value
                    for k, v in zip(returned.keys, returned.values, strict=False)
                    if isinstance(k, ast.Constant) and k.value in SUCCESS_LITERALS
                ) and not asserted:
                    continue

                report.add(
                    "G2.dict-claims-success",
                    path,
                    node,
                    f"{node.name}() returns a hardcoded dict asserting success via "
                    f"{sorted(asserted)}; S-HONEST requires Tainted/Provenance",
                    root,
                )
    return report


# --------------------------------------------------------------------------- #
# G6 — S-SCI: every motor needs a numeric conformance test
# --------------------------------------------------------------------------- #

_CONFORMANCE_HINT = re.compile(
    r"conformance|parity|reference_value|known_value|golden", re.IGNORECASE
)


def scan_motor_conformance(root: Path) -> dict[str, Any]:
    """Locate motor classes and check each has a conformance test.

    A motor is a class in ``services/scientific_motors`` that subclasses
    ``AbstractScientificMotor`` or whose name ends in ``Motor``, plus the
    runner classes registered in ``services/simulation/base.py``.
    """
    motors: set[str] = set()
    for path in iter_modules(root, "services/scientific_motors", "services/simulation"):
        tree = parse(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = {_annotation_text(b) for b in node.bases}
                if "AbstractScientificMotor" in bases or node.name.endswith("Motor"):
                    motors.add(node.name)

    test_files = {
        p
        for p in (root / "tests").rglob("test_*.py")
        if not any(s in p.parts for s in SKIP_DIR_PARTS)
    }
    test_files |= {p for p in (root / "services").rglob("test_*.py") if "tests" in p.parts}
    corpus = ""
    for path in sorted(test_files):
        try:
            corpus += path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

    covered = {m for m in motors if m in corpus}
    return {
        "total": len(motors),
        "covered": len(covered),
        "missing": sorted(motors - covered),
        "motors": sorted(motors),
    }
