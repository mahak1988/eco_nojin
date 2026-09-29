"""The four unresolved conductivity rows announce themselves.

The publication could not be obtained: four routes were tried and all are
blocked (the search provider returns 403, DuckDuckGo and its lite front end
serve a bot challenge, Bing returns unrelated results, Mojeek returns 403). So
the four values stay.

What changes is that they are no longer silent. A caller who asks for one gets
a warning naming the texture, the value, the interval its own physics permits,
and the command that closes the conflict once the source is in hand.

This module also holds the validator that would have caught the table already
in the repository, and the tests that the closing path is real: a CSV that
violates the fineness ordering is refused rather than recorded as verified.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from pathlib import Path

import pytest

from engine.data.physics_guard import (
    PhysicsWarning,
    disputed_rows,
    warn_if_disputed,
)
from engine.data.soil_table import FINENESS_ORDER, SOIL_PARAMETERS, get_params

REPO = pathlib.Path(__file__).resolve().parents[2]


class TestDisputedRows:
    def test_exactly_four_rows_are_disputed(self) -> None:
        rows = disputed_rows()
        assert set(rows) == {"silt", "sandy_clay_loam", "silty_clay", "clay"}, (
            f"the disputed set changed to {sorted(rows)}; the publication may "
            f"have been applied, or a new conflict appeared"
        )

    def test_three_have_empty_intervals_and_one_is_outside(self) -> None:
        rows = disputed_rows()
        empty = {t for t, v in rows.items() if v["empty_interval"]}
        assert empty == {"silt", "sandy_clay_loam", "silty_clay"}, sorted(empty)
        clay = rows["clay"]
        assert not clay["empty_interval"]
        assert clay["value_cm_per_day"] > clay["admissible_max"]

    def test_the_eight_sound_rows_are_not_disputed(self) -> None:
        sound = set(FINENESS_ORDER) - set(disputed_rows())
        assert len(sound) == 8, sorted(sound)

    def test_get_params_warns_on_a_disputed_row(self) -> None:
        with pytest.warns(PhysicsWarning, match="clay"):
            get_params("clay")

    def test_get_params_does_not_warn_on_a_sound_row(self, recwarn) -> None:
        get_params("loam")
        assert not [w for w in recwarn if issubclass(w.category, PhysicsWarning)]

    def test_the_warning_names_the_value_and_the_interval(self) -> None:
        with pytest.warns(PhysicsWarning) as caught:
            get_params("sandy_clay_loam")
        message = str(caught[0].message)
        assert "31.4" in message
        assert "neighbours contradict each other" in message
        assert "apply_published_table" in message

    def test_warn_if_disputed_is_silent_for_a_sound_row(self, recwarn) -> None:
        warn_if_disputed("sand")
        assert not recwarn


class TestClosingPath:
    """The command that closes this has to work, or the warning is a dead end."""

    @staticmethod
    def _run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", *args],
            cwd=str(REPO),
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _write(name: str, body: str) -> Path:
        """Write a fixture CSV.

        pytest's ``tmp_path`` is avoided deliberately: its numbered-directory
        cleanup raises ``PermissionError`` on this Windows host, and a permission
        error in fixture teardown is indistinguishable from a real failure in
        the report.
        """
        scratch = REPO / "engine" / "data" / ".scratch"
        scratch.mkdir(exist_ok=True)
        path = scratch / name
        path.write_text(body, encoding="utf-8")
        return path

    def test_the_current_table_would_be_refused(self) -> None:
        """The validator applied to the table already in the repository.

        If this passes silently, the validator is not checking what it claims.
        """
        from engine.data.apply_published_table import check_against_physics

        problems = check_against_physics(
            {t: {"ks_cm_per_day": SOIL_PARAMETERS[t]["Ks"]} for t in FINENESS_ORDER}
        )
        assert problems, "the existing table should fail its own validator"

    def test_a_conforming_table_passes_the_validator(self) -> None:
        from engine.data.apply_published_table import check_against_physics

        good = {t: {"ks_cm_per_day": 100.0 / (i + 1)} for i, t in enumerate(FINENESS_ORDER)}
        assert check_against_physics(good) == []

    def test_a_nonconforming_table_is_refused_without_writing(self) -> None:
        bad = self._write(
            "bad.csv",
            "texture,ks_cm_per_day,reference\nsand,712.8,Test\nclay,4.8,Test\n",
        )
        table = REPO / "engine" / "data" / "soil_vg_table.csv"
        before = table.read_text(encoding="utf-8")
        result = self._run("engine.data.apply_published_table", "--from", str(bad))
        assert result.returncode == 1, result.stdout
        assert "REFUSED" in result.stdout
        assert table.read_text(encoding="utf-8") == before, (
            "a refused table must not have been written"
        )

    def test_a_table_without_a_citation_is_refused(self) -> None:
        """The defect being closed was an uncited attribution; do not repeat it."""
        no_citation = self._write(
            "nocite.csv",
            "texture,ks_cm_per_day\n"
            + "".join(f"{t},{100.0 / (i + 1)}\n" for i, t in enumerate(FINENESS_ORDER)),
        )
        result = self._run(
            "engine.data.apply_published_table", "--from", str(no_citation), "--dry-run"
        )
        assert result.returncode == 1, result.stdout
        assert "reference" in result.stdout

    def test_a_conforming_cited_table_is_accepted_in_dry_run(self) -> None:
        good = self._write(
            "good.csv",
            "texture,ks_cm_per_day,reference\n"
            + "".join(
                f"{t},{100.0 / (i + 1)},Test Publication 1988\n"
                for i, t in enumerate(FINENESS_ORDER)
            ),
        )
        result = self._run("engine.data.apply_published_table", "--from", str(good), "--dry-run")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "nothing written" in result.stdout
