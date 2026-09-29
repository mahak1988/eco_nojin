"""S00 — Baseline integrity: the engine has not moved since the last review.

What this test is for
---------------------
Phase 3 of the integration plan changes equations. Each of those changes is
individually justified by a standard, but the *blast radius* is not obvious:
changing the field-capacity depth moves plant-available water, which moves
leaching, which moves the crop water requirement, which moves the irrigation
schedule. Six modules move because one line moved.

This test is the tripwire that makes that blast radius attributable. It runs
every reference case in ``engine/baseline/cases.py``, compares the result
against the recorded ``R18.json``, and fails with a per-field report naming
every value that moved.

What it does not do
-------------------
It does not assert that the engine is *correct*. Several recorded values are
known wrong — sand's available water is under-reported by 99 %, the biochar
annual rate is 117x too high, a dam reports 107 913 m3 required and 840 m3
provided. This test freezes that state on purpose: the correction commits of
Phase 3 are then readable, one field at a time, instead of arriving as one
unreviewable wave.

Tolerance
---------
Relative 1e-9. The capture is deterministic pure Python with no timestamps, no
UUIDs, no network and no rasters, so there is nothing legitimate that moves a
recorded value. A change above this band is always a real change to the
engine, a real change to a case, or a real change to the environment.
"""

from __future__ import annotations

import pytest

from engine.baseline import capture as harness, cases as case_module


class TestBaselineIntegrity:
    def test_live_capture_matches_the_recorded_baseline(self) -> None:
        """The whole point of the package, as one report.

        A failure here lists each changed field with its relative change, so a
        reviewer can see whether the effect is the one the commit message
        promised or a side effect somewhere else in the engine.
        """
        recorded = harness._load(harness.BASELINE_PATH)
        live = case_module.capture()
        changed, structural = harness.compare(recorded, live)

        if structural:
            listed = "\n".join(f"  {p}" for p in structural[:30])
            pytest.fail(
                f"{len(structural)} field(s) exist in one capture but not the other.\n"
                f"A case or field was added or removed without regenerating the "
                f"baseline. If that was deliberate:\n"
                f"  python -m engine.baseline.capture --regenerate\n\n{listed}"
            )

        if changed:
            ordered = sorted(changed, key=lambda e: -(e["relative"] or 0.0))
            lines = [
                f"  {(e['relative'] or 0.0):.3e}  {e['baseline']!r:>18} -> "
                f"{e['live']!r:<18} {e['path']}"
                for e in ordered[:40]
            ]
            if len(changed) > 40:
                lines.append(f"  ... and {len(changed) - 40} more")
            pytest.fail(
                f"{len(changed)} recorded value(s) changed since baseline "
                f"{recorded.get('baseline_id', '?')}.\n\n"
                f"{'relative':>11}  {'baseline':>18}   {'live':<18} path\n"
                + "\n".join(lines)
                + "\n\nIf the change is intended and justified by a standard:\n"
                "  python -m engine.baseline.capture --regenerate\n"
                "and cite the standard in the commit message."
            )

    def test_every_case_produced_a_non_empty_capture(self) -> None:
        """A case that silently returns nothing would look like a pass."""
        live = case_module.capture()
        empty = sorted(name for name, value in live.items() if not value)
        assert not empty, f"cases returning an empty capture: {empty}"

    def test_case_list_matches_the_recorded_names(self) -> None:
        """Removing a case removes the ability to attribute a future change.

        A case that disappears from ``CASES`` must also disappear from
        ``case_names`` in the baseline file, and the file must say so. This
        test forces that decision to be explicit rather than incidental.
        """
        recorded = harness._load(harness.BASELINE_PATH)
        assert list(live_names := case_module.case_names()) == recorded["case_names"], (
            "the case list changed:\n"
            f"  now:       {live_names}\n"
            f"  recorded:  {recorded['case_names']}\n"
            f"Removing a case removes the ability to attribute a later change to "
            f"whatever that case was witnessing. Regenerate deliberately:\n"
            f"  python -m engine.baseline.capture --regenerate"
        )

    def test_baseline_records_its_own_schema(self) -> None:
        recorded = harness._load(harness.BASELINE_PATH)
        assert recorded["schema_version"] == harness.SCHEMA_VERSION
        assert recorded["rel_tolerance"] == harness.REL_TOLERANCE
        assert recorded["baseline_id"], "the baseline must name its review"

    def test_baseline_holds_no_authored_expectation(self) -> None:
        """Guards the honesty rule the package depends on.

        The baseline is generated by running the engine, so it records the
        engine's state rather than asserting what the engine should be. If
        someone starts hand-editing values into the JSON to make a failing
        comparison pass, this test notices that the file no longer matches a
        fresh capture and says so.
        """
        recorded = harness._load(harness.BASELINE_PATH)
        live = case_module.capture()
        assert harness._flatten(recorded["cases"]).keys() == harness._flatten(live).keys()
        changed, _ = harness.compare(recorded, live)
        assert not changed, (
            f"{len(changed)} value(s) differ; the baseline file has been edited "
            f"by hand instead of regenerated"
        )


class TestCaptureHarness:
    """The comparison machinery itself, so a broken harness cannot read as a
    clean engine."""

    def test_compare_detects_a_numeric_change(self) -> None:
        changed, structural = harness.compare({"cases": {"a": {"x": 1.0}}}, {"a": {"x": 1.0001}})
        assert not structural
        assert len(changed) == 1
        assert changed[0]["path"] == "a.x"
        assert changed[0]["relative"] == pytest.approx(1e-4, rel=1e-3)

    def test_compare_tolerates_float_noise_below_the_band(self) -> None:
        changed, _ = harness.compare({"cases": {"a": {"x": 1.0}}}, {"a": {"x": 1.0 + 1e-13}})
        assert not changed

    def test_compare_detects_a_missing_field(self) -> None:
        changed, structural = harness.compare(
            {"cases": {"a": {"x": 1.0, "y": 2.0}}}, {"a": {"x": 1.0}}
        )
        assert changed == []
        assert structural == ["a.y"]

    def test_compare_detects_an_added_field(self) -> None:
        _, structural = harness.compare({"cases": {"a": {"x": 1.0}}}, {"a": {"x": 1.0, "z": 3.0}})
        assert structural == ["(added) a.z"]

    def test_compare_detects_a_nan(self) -> None:
        changed, _ = harness.compare({"cases": {"a": {"x": 1.0}}}, {"a": {"x": float("nan")}})
        assert len(changed) == 1
        assert changed[0]["kind"] == "nan"

    def test_compare_handles_zero_to_nonzero(self) -> None:
        changed, _ = harness.compare({"cases": {"a": {"x": 0.0}}}, {"a": {"x": 5.0}})
        assert len(changed) == 1

    def test_compare_does_not_divide_by_zero_for_zero_pairs(self) -> None:
        changed, _ = harness.compare({"cases": {"a": {"x": 0.0}}}, {"a": {"x": 0.0}})
        assert changed == []

    def test_compare_detects_a_changed_string(self) -> None:
        changed, _ = harness.compare({"cases": {"a": {"s": "real"}}}, {"a": {"s": "simulated"}})
        assert len(changed) == 1
        assert changed[0]["kind"] == "value"

    def test_flatten_produces_dotted_paths(self) -> None:
        flat = harness._flatten({"a": {"b": [1, 2]}})
        assert flat == {"a.b[0]": 1, "a.b[1]": 2}

    def test_baseline_file_is_pretty_printed_and_sorted(self) -> None:
        """Keeps diffs readable, which is the point of storing a baseline at all."""
        raw = harness.BASELINE_PATH.read_text(encoding="utf-8")
        assert raw.endswith("\n")
        assert "    " in raw, "expected indented output"
        assert harness.BASELINE_PATH.stat().st_size > 5000, (
            "the baseline is suspiciously small; a case group is probably empty"
        )
