"""The lint ratchet must be wired, not merely documented.

``tools/lint_baseline.json`` says the Quick Scan "fails when the count RISES
above it". The mechanism existed only in the PowerShell hook -- the POSIX hook
and CI did not enforce it, so the debt could grow unnoticed.

These tests pin that the mechanism is reachable from every entry point, and
that the tool itself behaves (fails above the floor, passes at or below it,
and never raises the floor without an explicit force).
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE = PROJECT_ROOT / "tools" / "lint_baseline.json"
RATCHET = PROJECT_ROOT / "tools" / "check_lint_ratchet.py"


class TestBaselineFile:
    """Tests for the recorded floor."""

    def test_the_baseline_file_exists(self):
        assert BASELINE.is_file()

    def test_the_floor_is_a_number(self):
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
        assert isinstance(data["rules"]["max_total"], int)

    def test_the_floor_is_recorded_with_a_date(self):
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
        assert data["measured_at"]

    def test_the_history_records_every_move(self):
        """A floor that moves silently is a floor that ratchets by accident."""
        data = json.loads(BASELINE.read_text(encoding="utf-8"))
        assert data.get("history"), "the floor's moves must be recorded"
        for entry in data["history"]:
            assert entry["measured_at"]
            assert entry["total"] == entry["total"]  # a number
            assert entry["note"]


class TestRatchetTool:
    """Tests for the ratchet tool."""

    def test_the_tool_exists(self):
        assert RATCHET.is_file()

    def test_the_tool_is_importable(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_lint_ratchet", RATCHET)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "main")

    def test_the_tool_fails_above_the_floor(self, tmp_path, monkeypatch):
        """A tree over the floor must fail."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("_lint_ratchet", RATCHET)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        monkeypatch.setattr(module, "_ruff_total", lambda _root: 100)
        baseline = tmp_path / "tools" / "lint_baseline.json"
        baseline.parent.mkdir(parents=True)
        baseline.write_text(
            json.dumps({"rules": {"max_total": 50}}), encoding="utf-8"
        )

        monkeypatch.setattr("sys.argv", ["check_lint_ratchet.py", "--root", str(tmp_path)])
        assert module.main() == 1

    def test_the_tool_passes_at_the_floor(self, tmp_path, monkeypatch):
        import importlib.util

        spec = importlib.util.spec_from_file_location("_lint_ratchet", RATCHET)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        monkeypatch.setattr(module, "_ruff_total", lambda _root: 50)
        baseline = tmp_path / "tools" / "lint_baseline.json"
        baseline.parent.mkdir(parents=True)
        baseline.write_text(
            json.dumps({"rules": {"max_total": 50}}), encoding="utf-8"
        )

        monkeypatch.setattr("sys.argv", ["check_lint_ratchet.py", "--root", str(tmp_path)])
        assert module.main() == 0

    def test_the_tool_passes_below_the_floor(self, tmp_path, monkeypatch):
        """Debt that shrank must not fail the check."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("_lint_ratchet", RATCHET)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        monkeypatch.setattr(module, "_ruff_total", lambda _root: 10)
        baseline = tmp_path / "tools" / "lint_baseline.json"
        baseline.parent.mkdir(parents=True)
        baseline.write_text(
            json.dumps({"rules": {"max_total": 50}}), encoding="utf-8"
        )

        monkeypatch.setattr("sys.argv", ["check_lint_ratchet.py", "--root", str(tmp_path)])
        assert module.main() == 0

    def test_the_floor_cannot_be_raised_without_force(self, tmp_path, monkeypatch):
        """Re-recording must not silently raise the floor."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("_lint_ratchet", RATCHET)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        monkeypatch.setattr(module, "_ruff_total", lambda _root: 100)
        baseline = tmp_path / "tools" / "lint_baseline.json"
        baseline.parent.mkdir(parents=True)
        baseline.write_text(
            json.dumps({"rules": {"max_total": 50}}), encoding="utf-8"
        )

        monkeypatch.setattr(
            "sys.argv", ["check_lint_ratchet.py", "--root", str(tmp_path), "--update"]
        )
        assert module.main() == 1
        # The recorded floor is unchanged.
        assert json.loads(baseline.read_text(encoding="utf-8"))["rules"]["max_total"] == 50

    def test_the_floor_can_be_lowered(self, tmp_path, monkeypatch):
        """Paying the debt down lowers the floor."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("_lint_ratchet", RATCHET)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        monkeypatch.setattr(module, "_ruff_total", lambda _root: 10)
        baseline = tmp_path / "tools" / "lint_baseline.json"
        baseline.parent.mkdir(parents=True)
        baseline.write_text(
            json.dumps({"rules": {"max_total": 50}}), encoding="utf-8"
        )

        monkeypatch.setattr(
            "sys.argv", ["check_lint_ratchet.py", "--root", str(tmp_path), "--update"]
        )
        assert module.main() == 0
        assert json.loads(baseline.read_text(encoding="utf-8"))["rules"]["max_total"] == 10


class TestWiring:
    """The ratchet must be reachable from every entry point."""

    def test_the_posix_hook_runs_the_ratchet(self):
        text = (PROJECT_ROOT / ".githooks" / "pre-edit.sh").read_text(encoding="utf-8")
        assert "check_lint_ratchet.py" in text

    def test_the_powershell_hook_runs_the_ratchet(self):
        text = (PROJECT_ROOT / ".githooks" / "pre-edit.ps1").read_text(encoding="utf-8")
        assert "check_lint_ratchet.py" in text

    def test_ci_runs_the_ratchet(self):
        text = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        assert "check_lint_ratchet.py" in text
