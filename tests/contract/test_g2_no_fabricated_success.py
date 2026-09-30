"""G2 — no fabricated success.

Two halves:

1. **The registry must be true.** ``docs/standards/tolerated-degradations.yaml``
   is the ledger of known-incomplete paths. Every entry must name a path that
   exists, declare a status from the ``S-HONEST`` enum, and have an owner.
2. **Nothing new may appear.** A static scan finds the shapes that actually
   produced fabricated success in this codebase — ``except: pass``, a
   ``verify_*`` that returns a constant, a hardcoded dict claiming success.
   The count is ratcheted against ``docs/metrics/baseline.json``, so existing
   debt is allowed and any increase fails.

The ratchet is what makes the gate usable. A hard zero would be bypassed on day
one; a ratchet cannot be bypassed without editing a file whose whole purpose is
to be reviewed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import ClassVar

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from gates import scan_fabrications

REGISTRY = ROOT / "docs" / "standards" / "tolerated-degradations.yaml"
BASELINE = ROOT / "docs" / "metrics" / "baseline.json"

VALID_STATUSES = {"ok", "degraded", "stale", "unavailable", "not_implemented"}
SUCCESS_STATUSES = {"ok", "degraded", "stale", "unavailable"}


def _registry_text() -> str:
    return REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""


class TestRegistryIsTruthful:
    def test_registry_exists(self):
        assert REGISTRY.exists(), (
            "tolerated-degradations.yaml is the S-HONEST ledger; without it the "
            "gate cannot distinguish known debt from new debt"
        )

    def test_every_entry_declares_a_valid_status(self):
        statuses = set(re.findall(r"^\s+status:\s*(\w+)\s*$", _registry_text(), re.MULTILINE))
        assert statuses, "registry should declare statuses"
        assert statuses <= VALID_STATUSES, (
            f"unknown status in registry: {statuses - VALID_STATUSES}"
        )

    def test_every_entry_has_an_owner_and_a_review_date(self):
        text = _registry_text()
        ids = re.findall(r"^\s+-\s+id:\s*(\S+)\s*$", text, re.MULTILINE)
        assert len(ids) >= 15, f"expected the known-debt ledger to be populated, got {len(ids)}"
        owners = re.findall(r"^\s+owner:\s*(D-\d+)\s*$", text, re.MULTILINE)
        assert len(owners) == len(ids), "every entry needs an owner"
        reviews = re.findall(r"^\s+review_by:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.MULTILINE)
        assert len(reviews) == len(ids), "every entry needs a review_by date"

    def test_entry_ids_are_unique(self):
        ids = re.findall(r"^\s+-\s+id:\s*(\S+)\s*$", _registry_text(), re.MULTILINE)
        duplicates = {i for i in ids if ids.count(i) > 1}
        assert not duplicates, f"duplicate registry ids: {sorted(duplicates)}"

    def test_declared_paths_still_exist(self):
        """A toleration pointing at a deleted file is a lie in the ledger."""
        text = _registry_text()
        paths = re.findall(r"^\s+path:\s*(\S+?)(?::\d+)?\s*$", text, re.MULTILINE)
        missing: list[str] = []
        for raw in paths:
            candidate = raw.rstrip("/")
            if not (ROOT / candidate).exists():
                missing.append(raw)
        assert not missing, (
            "these tolerations point at paths that no longer exist — remove them from the "
            f"ledger:\n  {missing}"
        )


class TestNoNewFabrications:
    @pytest.fixture(scope="class")
    def findings(self):
        return scan_fabrications(ROOT)

    def test_scan_finds_the_known_shapes(self):
        """Guard against a scanner that silently matches nothing."""
        findings = scan_fabrications(ROOT)
        assert len(findings) > 0, "the fabrication scanner is not finding anything; is it working?"

    def test_fabrication_count_has_not_grown(self, findings):
        import json

        if not BASELINE.exists():
            pytest.fail("no baseline; regenerate with scripts/measure_baseline.py")
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        recorded = baseline.get("metrics", {}).get("fabrications", {}).get("count")
        if recorded is None:
            pytest.fail("baseline has no fabrications.count; regenerate it")
        assert len(findings) <= recorded, (
            f"G2: fabricated-success findings grew {recorded} -> {len(findings)}.\n"
            "Either fix the new sites or register them in "
            "docs/standards/tolerated-degradations.yaml. New entries:\n"
            + "\n".join(f"  {f}" for f in sorted(set(findings))[:20])
        )

    def test_no_unregistered_fabrication_looks_new(self):
        """Spot-check that the worst offenders are inside the ledger."""
        ledger = _registry_text()
        for finding in scan_fabrications(ROOT).findings:
            if finding.rule == "G2.dict-claims-success" and "backup" in finding.path:
                assert "backup" in ledger, f"{finding} is a fabricated success outside the ledger"


class TestDetectorItself:
    """The scanner must keep its true positives and reject benign shapes.

    Both arms were wrong at some point during phase 4, in opposite directions,
    so they are pinned here rather than trusted:

    * an early version compared ``"select("``-style strings against bare
      callable names, so a whole rule never fired;
    * a later version flagged every hardcoded ``{"status": "ok"}``, which
      caught the real ``backup`` shape but also 45 legitimate acknowledgements
      such as ``connect_oauth`` returning ``{"status": "success"}`` after
      really connecting.
    """

    CASES: ClassVar[list[tuple[str, str, bool]]] = [
        # (source, expected_flagged, why)
        (
            'def run_backup():\n    return {"verification_status": "passed", "size": 1}\n',
            True,
            "the shape backup actually shipped",
        ),
        ('def check():\n    return {"ok": True}\n', True, "key is a success word"),
        ('def verify():\n    return {"verified": True, "id": 3}\n', True, "key is a success word"),
        ('def connect_oauth():\n    return {"status": "success"}\n', False, "really connected"),
        ('def vote():\n    return {"status": "ok"}\n', False, "really voted"),
        (
            'def admin_health():\n    return {"status": "ok", "message": "x"}\n',
            True,
            "a health response that computes nothing",
        ),
        (
            'def verify_chain():\n    return {"verified": False, "status": "not_implemented",'
            ' "reason": "no hash columns"}\n',
            False,
            "the S-HONEST envelope; a denial, not a claim",
        ),
        (
            'def result():\n    return {"status": "degraded", "reason": "surrogate", "data": 1}\n',
            False,
            "carries the envelope",
        ),
        (
            'def rows():\n    return {"status": "passed", "data": [1, 2]}\n',
            False,
            "carries real data",
        ),
    ]

    @pytest.mark.parametrize(("source", "expected", "why"), CASES, ids=[c[2] for c in CASES])
    def test_case(self, source: str, expected: bool, why: str) -> None:
        import tempfile
        from pathlib import Path as _Path

        sys.path.insert(0, str(ROOT / "tests" / "contract"))
        from gates import scan_fabrications

        with tempfile.TemporaryDirectory(dir=r"C:\Users\hp\AppData\Local\Temp\kilo") as tmp:
            # scan_fabrications(root) walks <root>/services, so the probe must
            # sit under that path or nothing is scanned at all.
            pkg = _Path(tmp) / "services" / "probe"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (pkg / "mod.py").write_text(source, encoding="utf-8")
            findings = [
                f
                for f in scan_fabrications(_Path(tmp)).findings
                if f.rule == "G2.dict-claims-success"
            ]
        assert bool(findings) is expected, f"{why}: expected flagged={expected}, got {findings}"

    def test_the_verification_arm_cannot_widen_silently(self) -> None:
        from gates import VERIFICATION_NAME

        must_match = ["run_backup", "verify_integrity", "compute_land_profile", "reconcile_wallet"]
        must_not_match = ["connect_oauth", "vote", "create_order", "get_balance"]
        for name in must_match:
            assert VERIFICATION_NAME.search(name), f"{name} should be name-gated"
        for name in must_not_match:
            assert not VERIFICATION_NAME.search(name), f"{name} must not be name-gated"

    # ---------------------------------------------------------------------
    # The verify-constant rule had a real false-positive bug. It inspected
    # only the *first* return, so any function with a guard clause was
    # flagged. That produced two false alarms on working security code:
    #   services/two_factor.py:28      verify_totp()  - real pyotp verification
    #                                   after an `if not secret: return False`
    #   services/security/ssrf.py:55   validate_url() - four real checks before
    #                                   its `return True`
    # A gate that reports working security code as stubbed is a gate the team
    # learns to ignore, so the corrected rule is pinned here.
    # ---------------------------------------------------------------------

    VERIFY_CASES: ClassVar[list[tuple[str, bool, str]]] = [
        (
            "def validate_url(url):\n"
            "    if not url:\n"
            "        return False\n"
            "    if '/' in url:\n"
            "        return True\n"
            "    return False\n",
            False,
            "a guard clause is not a constant return",
        ),
        (
            "def verify_totp(secret, code):\n"
            "    if not secret or not code:\n"
            "        return False\n"
            "    return totp.verify(code)\n",
            False,
            "the real verify_totp shape",
        ),
        (
            "def verify_integrity(code):\n"
            "    trace = get(code)\n"
            "    if not trace:\n"
            "        return False\n"
            "    sha256(trace)\n"
            "    return True\n",
            False,
            "two different returns; a judgement call, not a mechanical one",
        ),
        (
            "def validate_everything(x):\n    check(x)\n    return True\n",
            True,
            "no path returns anything else",
        ),
        (
            "def check_solution(x):\n    return False\n",
            True,
            "a single constant return",
        ),
    ]

    @pytest.mark.parametrize(
        ("source", "expected", "why"),
        VERIFY_CASES,
        ids=[c[2] for c in VERIFY_CASES],
    )
    def test_verify_constant_case(self, source: str, expected: bool, why: str) -> None:
        import tempfile
        from pathlib import Path as _Path

        sys.path.insert(0, str(ROOT / "tests" / "contract"))
        from gates import scan_fabrications

        with tempfile.TemporaryDirectory(dir=r"C:\Users\hp\AppData\Local\Temp\kilo") as tmp:
            pkg = _Path(tmp) / "services" / "probe"
            pkg.mkdir(parents=True)
            (pkg / "__init__.py").write_text("", encoding="utf-8")
            (pkg / "mod.py").write_text(source, encoding="utf-8")
            flagged = [
                f
                for f in scan_fabrications(_Path(tmp)).findings
                if f.rule == "G2.verify-returns-constant"
            ]
        assert bool(flagged) is expected, f"{why}: expected flagged={expected}, got {flagged}"


class TestHonestModulesPassTheirOwnGate:
    """The phase 1 fixes must not be reintroduced."""

    def test_ledger_service_no_longer_reports_silent_success(self):
        """AST-based, so the docstring that *explains* the removal is allowed.

        The phase 1 rewrite documents ``{"status": "memory_only"}`` in prose; a
        naive substring check would flag the explanation as the defect.
        """
        import ast

        from services.ledger import service

        tree = ast.parse(Path(service.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
                continue
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and key.value in {"status", "hash"}:
                    values = [v.value for v in node.value.values if isinstance(v, ast.Constant)]
                    if "memory_only" in values:
                        pytest.fail(
                            "ledger.post_entry returning memory_only is the fabricated "
                            "success S-HONEST bans (service.py:"
                            f"{node.lineno})",
                            pytrace=False,
                        )

    def test_ledger_service_makes_no_hash_chain_claim(self):
        from services.ledger import service

        source = Path(service.__file__).read_text(encoding="utf-8").lower()
        # A negated mention is fine; an affirmative one is not.
        allowed = ("**not**", "not provide", "removed", "no longer", "does not", "do not")
        for line in source.splitlines():
            stripped = line.strip()
            if "hash-chain" in stripped or "hash-chained" in stripped:
                assert any(marker in stripped for marker in allowed), (
                    f"ledger/service.py still advertises a hash chain: {line!r}"
                )

    def test_backup_service_has_no_placeholder_dump(self):
        from services.backup import service

        source = Path(service.__file__).read_text(encoding="utf-8")
        assert "This is a placeholder" not in source
        assert 'verification_status = "passed"' not in source
        assert "BackupNotImplementedError" in source, (
            "unimplemented backup modes must raise, not silently succeed"
        )

    def test_contracts_expose_a_status_helper(self):
        import services._contracts.status as status

        assert hasattr(status, "degraded")
        assert hasattr(status, "not_implemented")
        assert "failed" not in {s.value for s in status.Status}
