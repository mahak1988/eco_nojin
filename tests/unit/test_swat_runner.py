"""Tests for the SWAT+ runner (subprocess wrapper + output.hru parser)."""

import sys

import pytest

from engine.hydroma.simulation.runners.swat_runner import (
    SwatConfig,
    SwatRunner,
    SwatUnavailable,
    parse_output_hru,
)

# Documented SWAT+ output.hru layout (subset): header searched by name.
HEADER = "AREA(km2) PRECIP(mm) ET(mm) RUNOFF(mm) SEDYLD(t/ha)"
HRU1 = "1.0 800 500 120 2.5"
HRU2 = "2.0 800 450 80 1.0"


def _write_hru(path, header=HEADER, rows=(HRU1, HRU2)):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n")
        for row in rows:
            fh.write(row + "\n")
    return path


class TestParseOutputHru:
    def test_parses_and_aggregates(self, tmp_path):
        path = _write_hru(tmp_path / "output.hru")
        result = parse_output_hru(str(path))
        assert result["hru_count"] == 2
        assert result["area_ha"] == 300.0  # (1.0 + 2.0) km2 * 100
        assert result["runoff_mm"] == pytest.approx((120 * 1.0 + 80 * 2.0) / 3.0, abs=0.001)
        # sediment: sum of sedyld (t/ha) * area (ha)
        assert result["sedyld_t"] == pytest.approx(2.5 * 100 + 1.0 * 200)

    def test_missing_header_raises(self, tmp_path):
        path = tmp_path / "output.hru"
        path.write_text("just some text\n", encoding="utf-8")
        with pytest.raises(SwatUnavailable, match="header"):
            parse_output_hru(str(path))

    def test_missing_columns_raises(self, tmp_path):
        path = _write_hru(tmp_path / "output.hru", header="AREA(km2) PRECIP(mm) RUNOFF(mm)")
        with pytest.raises(SwatUnavailable, match="missing expected columns"):
            parse_output_hru(str(path))


class TestSwatRunner:
    def test_missing_executable_raises(self, tmp_path):
        runner = SwatRunner(SwatConfig(executable=r"C:\nonexistent\swat.exe", project_dir=str(tmp_path)))
        with pytest.raises(SwatUnavailable, match="swat.tamu.edu"):
            runner.run()

    def test_missing_project_raises(self, tmp_path):
        runner = SwatRunner(SwatConfig(executable=sys.executable, project_dir=str(tmp_path / "nope")))
        with pytest.raises(SwatUnavailable, match="project directory"):
            runner.run()

    def test_success_with_mocked_subprocess(self, tmp_path, monkeypatch):
        exe = tmp_path / "swat.exe"
        exe.write_bytes(b"")
        project = tmp_path / "proj"
        project.mkdir()
        _write_hru(project / "output.hru")

        def _fake_run(cmd, cwd=None, capture_output=True, text=True, timeout=None):
            assert cwd == str(project)
            return type("P", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(
            "engine.hydroma.simulation.runners.swat_runner.subprocess.run", _fake_run
        )
        runner = SwatRunner(SwatConfig(executable=str(exe), project_dir=str(project)))
        result = runner.run()
        assert result["data_source"] == "simulated"
        assert result["model"].startswith("SWAT+")
        assert result["area_ha"] == 300.0

    def test_nonzero_exit_raises(self, tmp_path, monkeypatch):
        exe = tmp_path / "swat.exe"
        exe.write_bytes(b"")
        project = tmp_path / "proj"
        project.mkdir()

        def _fake_run(cmd, cwd=None, capture_output=True, text=True, timeout=None):
            return type("P", (), {"returncode": 1, "stdout": "", "stderr": "boom"})()

        monkeypatch.setattr(
            "engine.hydroma.simulation.runners.swat_runner.subprocess.run", _fake_run
        )
        runner = SwatRunner(SwatConfig(executable=str(exe), project_dir=str(project)))
        with pytest.raises(SwatUnavailable, match="exited with code 1"):
            runner.run()
