"""دروازهٔ اعتبار بانک نوآوری برای تست‌های قراردادی.

این تست تضمین می‌کند نسخهٔ ماشین‌خوان بانک نوآوری
(``docs/innovation_backlog.csv``) با اسناد تحلیلی هم‌راستا بماند.

طبق ``docs/standards/S-STRUCT.md``، شکست ساختاری باید در CI مسدود شود نه
اینکه فقط گزارش شود.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKER = REPO_ROOT / "scripts" / "innovation_backlog.py"
BACKLOG_CSV = REPO_ROOT / "docs" / "innovation_backlog.csv"
BACKLOG_DOC = REPO_ROOT / "INNOVATION_BACKLOG_FA.md"
PLAN_DOC = REPO_ROOT / "INNOVATION_EXECUTION_PLAN_FA.md"
ADR_DOC = REPO_ROOT / "docs" / "adr" / "0007-innovation-programme.md"

MIN_ITEMS = 50
MIN_EVOLUTIONARY = 15
MIN_INTEGRATION = 15
MIN_MOONSHOT = 10
MIN_NANO = 5

NANO_CATEGORY = "F"


def _run_tracker(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(TRACKER), *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, (
        f"innovation_backlog.py {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
    )
    return result.stdout


def _parse_summary(text: str) -> dict[str, dict[str, int]]:
    parsed: dict[str, dict[str, int]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.endswith(":") and not line.startswith(" "):
            current = line[:-1].strip()
            parsed[current] = {}
        elif current and line.startswith("  "):
            parts = line.split()
            if len(parts) == 2 and parts[1].isdigit():
                parsed[current][parts[0]] = int(parts[1])
    return parsed


def _read_csv_rows() -> list[dict[str, str]]:
    import csv

    with BACKLOG_CSV.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_tracker_exists() -> None:
    assert TRACKER.is_file(), f"missing tracker script: {TRACKER}"


def test_backlog_csv_validates() -> None:
    output = _run_tracker("validate")
    assert "OK" in output, output


def test_documentation_present() -> None:
    for path in (BACKLOG_DOC, PLAN_DOC, ADR_DOC):
        assert path.is_file(), f"missing innovation document: {path}"


def test_minimum_item_count() -> None:
    rows = _read_csv_rows()
    assert len(rows) >= MIN_ITEMS, f"backlog has {len(rows)} items, minimum is {MIN_ITEMS}"


def test_type_diversity() -> None:
    """حداقل تنوع خواسته‌شده: 15 تکاملی، 15 ادغام، 10 Moonshot."""
    rows = _read_csv_rows()
    counts: dict[str, int] = {}
    for row in rows:
        item_type = (row.get("type") or "").strip().lower()
        counts[item_type] = counts.get(item_type, 0) + 1

    assert counts.get("evolutionary", 0) >= MIN_EVOLUTIONARY, counts
    assert counts.get("integration", 0) >= MIN_INTEGRATION, counts
    assert counts.get("moonshot", 0) >= MIN_MOONSHOT, counts


def test_nano_coverage() -> None:
    """حداقل 5 قلم در دستهٔ نانوفناوری/سخت‌افزار/مواد."""
    rows = _read_csv_rows()
    nano = [row for row in rows if (row.get("category") or "").strip().upper() == NANO_CATEGORY]
    assert len(nano) >= MIN_NANO, f"only {len(nano)} nano items, minimum is {MIN_NANO}"


def test_every_item_has_kpi_and_paths() -> None:
    """هیچ قلمی نباید بدون معیار سنجش یا مسیر هدف باشد."""
    offenders = []
    for row in _read_csv_rows():
        item_id = row.get("id")
        if not (row.get("kpi") or "").strip():
            offenders.append(f"item {item_id}: missing KPI")
        if not (row.get("paths") or "").strip():
            offenders.append(f"item {item_id}: missing target path")
    assert not offenders, "\n".join(offenders)


def test_every_item_has_no_fabrication_awareness() -> None:
    """قلم‌هایی که به داده واقعی وابسته‌اند باید در مسیرشان منبع داده داشته باشند.

    این آزمون از اجرای قانون عدم‌جعل (``S-HONEST``) در سطح برنامه‌ریزی
    محافظت می‌کند: هیچ قلمی نباید بدون مسیر دادهٔ واقعی طراحی شود.
    """
    data_sensitive = {
        "1",
        "3",
        "27",
        "28",
        "42",
        "49",
        "56",
        "57",
        "58",
        "59",
        "60",
        "62",
        "66",
        "99",
    }
    rows = {row["id"].strip(): row for row in _read_csv_rows()}
    missing = []
    for item_id in sorted(data_sensitive):
        row = rows.get(item_id)
        if row is None:
            missing.append(f"item {item_id} not found")
            continue
        paths = (row.get("paths") or "").lower()
        has_data_source = any(
            token in paths
            for token in (
                "satellite",
                "soilgrids",
                "open_meteo",
                "mrv",
                "provenance",
                "audit",
                "dvc",
                "field_monitoring",
                "marketplace",
                "data_manual",
                "fetch_stac",
                "carbon",
                "traceability",
                "data_sources",
                "swat_real",
                "open_meteo",
            )
        )
        if not has_data_source:
            missing.append(f"item {item_id}: no real data source in paths: {paths}")
    assert not missing, "\n".join(missing)


def test_wave_counts_match_plan() -> None:
    """تعداد اقلام هر موج باید با سند برنامهٔ اجرایی هم‌راستا باشد."""
    summary = _parse_summary(_run_tracker("summary"))
    assert summary.get("by wave", {}).get("W0") == 26, summary
    assert summary.get("by wave", {}).get("W3") == 10, summary


def test_ready_command_runs() -> None:
    output = _run_tracker("ready")
    assert "ready to start:" in output, output


def test_blocked_command_runs() -> None:
    output = _run_tracker("blocked")
    assert "blocked:" in output, output


@pytest.mark.parametrize("wave", ["W0", "W1", "W2", "W3"])
def test_status_per_wave(wave: str) -> None:
    output = _run_tracker("status", "--wave", wave)
    assert wave in output, output
