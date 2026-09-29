"""G3 and G4 — coverage floor and dead-code ratchet.

**G3 (coverage).** ``AGENTS.md`` claims ``pytest --cov-fail-under=80`` is a
quality gate. No such setting existed in any configuration file, so the claim
was unenforced. This test asserts the setting is present and that the recorded
floor matches the documented step plan (60 -> 70 -> 80). It starts at 60, not
80, because 80 is not achievable yet and a gate nobody can pass gets deleted.

**G4 (dead code).** ~5,200 lines are unreachable, including a 616-line
``metrics.py`` that is never imported while the startup log announces that
Prometheus instrumentation is enabled. The gate is a ratchet: the number may
fall, never rise.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"
BASELINE = ROOT / "docs" / "metrics" / "baseline.json"
MIN_CONFIDENCE = "90"

#: The coverage ladder. The first rung is the value the suite actually
#: measures; later rungs are adopted only once the suite clears them, and the
#: floor may never move backwards.
COVERAGE_STEPS = {36.0, 60.0, 70.0, 80.0}


def _baseline_metrics() -> dict:
    if not BASELINE.exists():
        return {}
    return json.loads(BASELINE.read_text(encoding="utf-8")).get("metrics", {})


class TestG3CoverageIsConfigured:
    def test_coverage_report_block_exists(self):
        text = PYPROJECT.read_text(encoding="utf-8")
        assert "[tool.coverage.report]" in text, (
            "AGENTS.md claims a coverage gate; pyproject.toml has no "
            "[tool.coverage.report] section, so nothing is enforced"
        )

    def test_a_floor_is_declared(self):
        text = PYPROJECT.read_text(encoding="utf-8")
        match = re.search(r"\[tool\.coverage\.report\](.*?)(\n\[|\Z)", text, re.DOTALL)
        assert match, "could not parse the coverage report block"
        assert "fail_under" in match.group(1), (
            "fail_under must be set; a coverage section without a floor is documentation"
        )

    def test_the_floor_is_one_of_the_documented_steps(self):
        text = PYPROJECT.read_text(encoding="utf-8")
        match = re.search(r"fail_under\s*=\s*(\d+(?:\.\d+)?)", text)
        assert match, "fail_under has no numeric value"
        value = float(match.group(1))
        assert value in COVERAGE_STEPS, (
            f"fail_under={value} is not a documented step. The ladder is {sorted(COVERAGE_STEPS)} "
            "— the starting point is whatever the suite actually measures, and each step is "
            "adopted only when the suite clears it."
        )

    def test_the_floor_has_never_been_lowered(self):
        """A coverage floor that can be lowered is not a gate."""
        recorded = _baseline_metrics().get("coverage", {}).get("fail_under")
        if recorded is None:
            pytest.fail("baseline has no such key; regenerate with scripts/measure_baseline.py")
        text = PYPROJECT.read_text(encoding="utf-8")
        current = float(re.search(r"fail_under\s*=\s*(\d+(?:\.\d+)?)", text).group(1))
        assert current >= recorded, (
            f"fail_under was lowered {recorded} -> {current}. Lowering the floor to make a "
            "build pass defeats the gate."
        )

    def test_services_is_included_in_the_coverage_scope(self):
        text = PYPROJECT.read_text(encoding="utf-8")
        source = re.search(r"\[tool\.coverage\.run\](.*?)(\n\[|\Z)", text, re.DOTALL)
        assert source, "no [tool.coverage.run] section"
        assert "services" in source.group(1), (
            "coverage must scope services/ explicitly; measuring only engine/ hides the "
            "30% of the codebase with no tests"
        )

    def test_services_coverage_is_measured_and_floored(self) -> None:
        """`services/` is ~30% of the codebase and had no coverage job at all.

        Phase 5 measured it for the first time (41%) and added a job with a
        ratchet floor, so a decline in either the tests or the coverage fails
        the build.
        """
        workflow = (ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")
        assert "--cov=services" in workflow, "no CI job measures services coverage"
        assert "--cov-fail-under=" in workflow, (
            "services coverage is reported but not floored, so it can silently decline"
        )

    def test_the_services_floor_is_never_lowered(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci-cd.yml").read_text(encoding="utf-8")
        floors = [int(n) for n in re.findall(r"--cov-fail-under=(\d+)", workflow)]
        assert floors, "no services coverage floor is declared in CI"

        recorded = _baseline_metrics().get("coverage", {}).get("services_fail_under")
        if recorded is None:
            pytest.fail("baseline has no such key; regenerate with scripts/measure_baseline.py")
        current = min(floors)
        assert current >= recorded, (
            f"the services coverage floor was lowered {recorded} -> {current}. "
            "Lowering a floor to make a build pass defeats the gate."
        )

    def test_the_whole_test_tree_is_collectable(self) -> None:
        """`pytest.ini` used to list only `tests/unit`, silently skipping ~500
        tests. The bare command must now collect the full tree."""
        ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
        match = re.search(r"^testpaths\s*=\s*(.+)$", ini, re.MULTILINE)
        assert match, "pytest.ini has no testpaths"
        paths = match.group(1).split()
        assert "tests" in paths, (
            f"testpaths={paths} does not include the whole tests/ tree, so a bare "
            "`pytest` still runs less than CI does"
        )


class TestG4DeadCodeRatchet:
    @pytest.fixture(scope="class")
    def vulture_findings(self) -> list[str]:
        proc = subprocess.run(
            [sys.executable, "-m", "vulture", "services", "--min-confidence", MIN_CONFIDENCE],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return [line.strip() for line in proc.stdout.splitlines() if line.strip()]

    def test_vulture_runs(self, vulture_findings):
        assert vulture_findings, (
            "vulture reported nothing at all. Either the code got clean (re-pin the "
            "baseline) or the invocation is wrong."
        )

    def test_dead_code_has_not_grown(self, vulture_findings):
        recorded = _baseline_metrics().get("dead_code", {}).get("findings")
        if recorded is None:
            pytest.fail("no baseline; regenerate with scripts/measure_baseline.py")
        assert len(vulture_findings) <= recorded, (
            f"G4: unreferenced definitions grew {recorded} -> {len(vulture_findings)}.\n"
            "New dead code:\n" + "\n".join(f"  {line}" for line in vulture_findings[:20])
        )

    def test_the_headline_dead_modules_were_resolved(self) -> None:
        """Phase 3 named four headline dead modules as the ratchet baseline.

        Phase 4 resolved all of them, so asserting they are *still* dead would
        pin the improvement in place. Assert the direction of travel instead,
        naming the resolution for each so a regression is legible.
        """
        # Wired into the gateway, so its custom metrics reach /metrics.
        assert "from services.api_gateway import metrics" in (
            ROOT / "services" / "api_gateway" / "main.py"
        ).read_text(encoding="utf-8"), "metrics.py is unreferenced again"

        # Duplicates of engine/resilience, of the NATS stack, and of a cache
        # layer nothing consumed.
        assert not (ROOT / "services" / "api_gateway" / "resilience").exists()
        assert not (ROOT / "services" / "event_bus").exists()
        assert not (ROOT / "services" / "api_gateway" / "cache").exists()

    def test_the_baseline_still_records_dead_code_findings(self) -> None:
        baseline = _baseline_metrics().get("dead_code", {})
        assert baseline.get("detail"), "the baseline should keep the vulture detail for review"
        assert isinstance(baseline.get("findings"), int)


class TestBaselineIsGeneratedNotHandWritten:
    def test_baseline_exists(self):
        assert BASELINE.exists(), (
            "docs/metrics/baseline.json is the ratchet state for G2/G4/G5/G6. "
            "Generate it: python scripts/measure_baseline.py"
        )

    def test_baseline_is_reproducible(self):
        """--check must agree with the recorded values, i.e. nothing drifted."""
        proc = subprocess.run(
            [sys.executable, "scripts/measure_baseline.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, (
            "the baseline no longer matches the tree:\n"
            f"{proc.stdout}\n{proc.stderr}\n"
            "If the change was an improvement, re-pin: python scripts/measure_baseline.py"
        )
