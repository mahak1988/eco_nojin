"""SWAT+ runner (Phase 3, sprint 2): subprocess wrapper + output.hru parser.

SWAT+ is a compiled watershed model (text I/O). This runner executes the
binary via subprocess and parses the HRU-level output into basin aggregates.

Honesty: the executable must be provided by the operator (download from
swat.tamu.edu). When it is missing, :class:`SwatUnavailable` is raised with
a clear message — no simulated fallback is fabricated here.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any

import numpy as np

from engine.hydroma.simulation.runners.base import ModelRunner

OUTPUT_HRU = "output.hru"
# Column names searched (case-insensitive) in the output.hru header.
COL_RUNOFF = "runoff"
COL_SEDYLD = "sedyld"
COL_AREA = "area"


class SwatUnavailable(RuntimeError):
    """Raised when the SWAT+ executable or project is not available."""


@dataclass(frozen=True)
class SwatConfig:
    """SWAT+ executable + project layout."""

    executable: str
    project_dir: str
    run_timeout_s: float = 600.0
    output_file: str = OUTPUT_HRU


def parse_output_hru(path: str) -> dict[str, Any]:
    """Parse an SWAT+ output.hru file into basin aggregates.

    The header row is located by scanning for a line containing the AREA
    column name; values are read by column name (case-insensitive), so the
    parser tolerates column-order differences between SWAT+ versions.

    Returns:
        dict with area_ha, runoff_mm (area-weighted), sedyld_t (total),
        hru_count.
    """
    header_idx = None
    header_parts: list[str] = []
    rows: list[list[str]] = []

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.split()
            if not parts:
                continue
            if header_idx is None:
                lowered = [p.lower() for p in parts]
                if any("area" in p for p in lowered):
                    header_idx = len(rows) + 1
                    header_parts = parts
                continue
            rows.append(parts)

    if header_idx is None:
        raise SwatUnavailable("output.hru has no recognizable header (AREA column)")

    def col_index(name_fragment: str) -> int | None:
        for i, part in enumerate(header_parts):
            if name_fragment in part.lower():
                return i
        return None

    idx_area = col_index(COL_AREA)
    idx_runoff = col_index(COL_RUNOFF)
    idx_sedyld = col_index(COL_SEDYLD)
    if idx_area is None or idx_runoff is None or idx_sedyld is None:
        raise SwatUnavailable(
            f"output.hru header missing expected columns "
            f"(area={idx_area}, runoff={idx_runoff}, sedyld={idx_sedyld})"
        )

    total_area_km2 = 0.0
    weighted_runoff = 0.0
    total_sedyld = 0.0
    parsed_rows = 0
    for parts in rows:
        if len(parts) <= max(idx_area, idx_runoff, idx_sedyld):
            continue
        try:
            area_km2 = float(parts[idx_area])
            runoff_mm = float(parts[idx_runoff])
            sedyld = float(parts[idx_sedyld])
        except ValueError:
            continue
        if not np.isfinite(area_km2) or area_km2 <= 0:
            continue
        total_area_km2 += area_km2
        weighted_runoff += runoff_mm * area_km2
        total_sedyld += sedyld * area_km2 * 100.0  # t/ha * ha
        parsed_rows += 1

    if parsed_rows == 0 or total_area_km2 <= 0:
        raise SwatUnavailable("output.hru contains no parseable data rows")

    return {
        "area_ha": round(total_area_km2 * 100.0, 2),
        "runoff_mm": round(weighted_runoff / total_area_km2, 3),
        "sedyld_t": round(total_sedyld, 3),
        "hru_count": parsed_rows,
    }


class SwatRunner(ModelRunner):
    """Execute a SWAT+ project and parse its HRU output."""

    name = "SWAT+"
    version = "2.x (binary)"

    def __init__(self, config: SwatConfig) -> None:
        self._config = config

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """Run the project and return basin aggregates.

        Accepted kwargs: ``executable``/``project_dir`` overrides the config.
        """
        executable = kwargs.get("executable", self._config.executable)
        project_dir = kwargs.get("project_dir", self._config.project_dir)
        output_file = kwargs.get("output_file", self._config.output_file)

        import os

        if not executable or not os.path.isfile(executable):
            raise SwatUnavailable(
                "SWAT+ executable not found; download it from swat.tamu.edu "
                "and set the executable path (no simulated fallback is fabricated)"
            )
        if not os.path.isdir(project_dir):
            raise SwatUnavailable(f"SWAT+ project directory not found: {project_dir}")

        # SWAT+ runs in its project directory (text I/O convention).
        proc = subprocess.run(
            [executable],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=self._config.run_timeout_s,
        )
        if proc.returncode != 0:
            raise SwatUnavailable(
                f"SWAT+ exited with code {proc.returncode}: {(proc.stderr or '')[-300:]}"
            )

        output_path = os.path.join(project_dir, output_file)
        if not os.path.isfile(output_path):
            raise SwatUnavailable(f"SWAT+ produced no {output_file} in {project_dir}")
        result = parse_output_hru(output_path)
        result["data_source"] = "simulated"
        result["model"] = "SWAT+ (binary, subprocess)"
        return result
