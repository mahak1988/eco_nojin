"""Phase 5 — the toleration ledger must be accountable, not just truthful.

``tests/contract/test_g2_no_fabricated_success.py`` already checks the parts of
``docs/standards/tolerated-degradations.yaml`` that decide whether a *file* is
still there: the status enum, one owner and one review date per entry, unique
ids, and that each declared ``path:`` still exists on disk. This module
deliberately does not repeat any of that.

It checks the parts that decide whether anyone is *answerable* for the debt:

1. every entry names an owner that matches the ``D-<n>`` convention the other
   gate keys on, and a ``review_by`` that is a real calendar date;
2. every entry's status comes from the S-HONEST enum, and a toleration that
   claims ``not_implemented`` is not silently downgraded to ``ok`` — an entry
   marked ``ok`` describes a working path and has no business in this file;
3. no entry's ``path:`` points into ``tests/``. A toleration is a claim about
   production behaviour. Pointing one at a test file registers the *test suite*
   as known-incomplete, which is a category error that hides a real defect
   behind a passing assertion, and it survives deleting the module under test.

A path-existence check is deliberately absent here; see the module docstring of
the G2 gate, which owns it. Duplicating it would mean two tests to update when
the ledger moves, and only one of them would be read.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "standards" / "tolerated-degradations.yaml"

# S-HONEST status enum. Mirrors the set in test_g2_no_fabricated_success.py on
# purpose: if one moves, the other must move with it, and the diff says why.
VALID_STATUSES = {"ok", "degraded", "stale", "unavailable", "not_implemented"}

# A status that means "this path does what it claims to do". A path in this
# ledger that reports `ok` is not a toleration; it is a normal working path that
# someone filed by mistake, and it makes the ledger's own count a lie.
WORKING_STATUSES = {"ok"}

OWNER_PATTERN = re.compile(r"^D-\d+$")
REVIEW_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@pytest.fixture(scope="module")
def entries() -> list[dict]:
    if not REGISTRY.exists():
        pytest.fail(f"{REGISTRY} is missing; the S-HONEST ledger cannot be audited")
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "the ledger must be a mapping with a 'tolerations' key"
    tolerations = data.get("tolerations")
    assert isinstance(tolerations, list), "the ledger declares no 'tolerations' list"
    assert tolerations, "the ledger declares no tolerations"
    return tolerations


@pytest.fixture(scope="module")
def by_id(entries: list[dict]) -> dict[str, dict]:
    return {e["id"]: e for e in entries}


class TestEntryShape:
    """The minimum a row needs before anyone can be asked to act on it."""

    def test_every_entry_names_an_owner(self, entries: list[dict]):
        missing = [e.get("id", "<no id>") for e in entries if not e.get("owner")]
        assert not missing, f"entries with no owner: {missing}"

    def test_every_owner_uses_the_declared_convention(self, entries: list[dict]):
        """`D-<n>` so the owner column is machine-checkable, not a free-text name."""
        bad = [
            f"{e['id']}={e['owner']!r}"
            for e in entries
            if not OWNER_PATTERN.match(str(e.get("owner", "")))
        ]
        assert not bad, f"owners that break the D-<n> convention: {bad}"

    def test_every_entry_has_a_review_by_date(self, entries: list[dict]):
        missing = [e.get("id", "<no id>") for e in entries if e.get("review_by") is None]
        assert not missing, f"entries with no review_by: {missing}"

    def test_every_review_date_is_a_real_calendar_date(self, entries: list[dict]):
        r"""`2026-13-45` satisfies a naive \d{4}-\d{2}-\d{2} regex; this does not."""
        bad: list[str] = []
        for entry in entries:
            raw = str(entry.get("review_by", ""))
            if not REVIEW_PATTERN.match(raw):
                bad.append(f"{entry['id']}={raw!r} (not YYYY-MM-DD)")
                continue
            try:
                dt.date.fromisoformat(raw)
            except ValueError:
                bad.append(f"{entry['id']}={raw!r} (not a real date)")
        assert not bad, f"unusable review_by values: {bad}"

    def test_every_entry_declares_a_status_from_the_enum(self, entries: list[dict]):
        bad = [
            f"{e.get('id')}={e.get('status')!r}"
            for e in entries
            if e.get("status") not in VALID_STATUSES
        ]
        assert not bad, f"statuses outside the S-HONEST enum {sorted(VALID_STATUSES)}: {bad}"

    def test_every_entry_states_a_reason(self, entries: list[dict]):
        """A toleration with no reason cannot be triaged, only tolerated."""
        thin = [e["id"] for e in entries if len(str(e.get("reason", "")).strip()) < 20]
        assert not thin, f"entries whose reason is too thin to triage: {thin}"


class TestNoTolerationHidesBehindATest:
    """The rule that makes this file worth having separately from G2."""

    def test_no_path_points_into_tests(self, entries: list[dict]):
        offenders = [
            f"{e['id']} -> {e['path']}"
            for e in entries
            if e["path"].split(":")[0].rstrip("/").replace("\\", "/").startswith("tests/")
        ]
        assert not offenders, (
            "these tolerations point into tests/ — a test suite is not a known-incomplete "
            "production path, and registering one hides a real defect behind a passing "
            f"assertion:\n  {offenders}"
        )

    def test_no_path_points_into_a_backup_or_vendor_tree(self, entries: list[dict]):
        """A path under a scratch tree is not reviewable debt; it is debris."""
        debris = ("/node_modules/", "/.venv/", "/__pycache__/", "/data/cache/")
        offenders = [
            f"{e['id']} -> {e['path']}"
            for e in entries
            if any(d in "/" + e["path"].rstrip("/") + "/" for d in debris)
        ]
        assert not offenders, f"tolerations pointing at non-source trees: {offenders}"


class TestStatusesAreNotSoftened:
    """A ledger that quietly upgrades itself is how under-reporting starts."""

    def test_no_entry_claims_status_ok(self, entries: list[dict]):
        offenders = [
            f"{e['id']} ({e.get('reason', '')[:60]}...)"
            for e in entries
            if e.get("status") in WORKING_STATUSES
        ]
        assert not offenders, (
            "a working path does not belong in the toleration ledger; remove these entries "
            f"rather than leaving them filed as debt: {offenders}"
        )

    def test_not_implemented_and_degraded_are_not_interchangeable(self, entries: list[dict]):
        """`not_implemented` means the code is absent; `degraded` means it runs and lies.

        Collapsing the two hides which entries are unbuilt (and therefore have
        no behaviour to review) and which are actively wrong at runtime.
        """
        by_status: dict[str, list[str]] = {}
        for e in entries:
            by_status.setdefault(str(e.get("status")), []).append(e["id"])
        for status in ("not_implemented", "degraded"):
            assert status in by_status, (
                f"the ledger declares no '{status}' entries at all, which means the "
                "distinction between unbuilt and actively-wrong has been abandoned"
            )


class TestTheEntriesPhaseFiveVerifiedStillPointAtTheDebt:
    """Spot-checks that the phase 5 re-audit did not rot on the next edit.

    Each of these is a claim the ledger makes in prose. If the code is fixed,
    the assertion fails and the entry must be deleted — the file's own rule is
    that a resolved row is removed, not re-dated.
    """

    def test_traceability_still_discards_its_digest(self, by_id: dict[str, dict]):
        entry = by_id["traceability-verify-integrity"]
        source = (ROOT / entry["path"].split(":")[0]).read_text(encoding="utf-8")
        assert "verify_integrity" in source
        # The computed digest is still discarded: the expression is a bare call
        # whose value is never bound, and the function still returns a constant.
        body = source.split("def verify_integrity", 1)[1]
        assert re.search(r"sha256\(.*\)\.hexdigest\(\)\[:\d+\]", body), (
            "verify_integrity no longer computes a discarded digest — delete this entry"
        )
        assert re.search(r"return True\b", body), (
            "verify_integrity no longer returns a constant — re-read and delete or narrow"
        )

    def test_nlg_still_manufactures_evidence_when_nothing_matches(self, by_id: dict[str, dict]):
        entry = by_id["nlg-fabricated-evidence"]
        source = (ROOT / entry["path"].split(":")[0]).read_text(encoding="utf-8")
        assert re.search(r"if not evidence:", source), (
            "the fabricated-evidence fallback in services/ai/nlg.py is gone — "
            "delete this entry or narrow it to whatever replaced it"
        )

    def test_trust_score_still_returns_no_events(self, by_id: dict[str, dict]):
        entry = by_id["trust-score-constant"]
        source = (ROOT / entry["path"].split(":")[0]).read_text(encoding="utf-8")
        body = source.split("def _get_user_events", 1)[1]
        assert re.search(r"return \[\]", body.split("def ", 1)[0]), (
            "_get_user_events no longer returns [] — every user is no longer pinned to "
            "BASE_SCORE; delete this entry or narrow it"
        )

    def test_jobs_still_adds_a_pydantic_schema_to_the_session(self, by_id: dict[str, dict]):
        entry = by_id["jobs-create-and-update"]
        source = (ROOT / entry["path"].split(":")[0]).read_text(encoding="utf-8")
        create = source.split("def create_job", 1)[1].split("async def ", 1)[0]
        assert re.search(r"self\.db\.add\(data\)", create), (
            "create_job no longer passes the Pydantic schema to db.add — narrow this "
            "entry to whatever remains (update_job_status may still raise NameError)"
        )
