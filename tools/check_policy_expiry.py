#!/usr/bin/env python3
"""Import-guard policy expiry + ratchet check (remediation item B-1).

Reads ``tools/import_guard_policy.json`` as data and reports, one line per
sanctioned exception::

    OK|EXPIRED|OVER-RATCHET <rule> <module> <expires>

An exception is a *dated* debt: it keeps the architecture guard
(``tools/detect_imports.py``) green while a migration is still pending, and
that is only acceptable while somebody has re-confirmed it recently. Two
things make the debt shrink instead of accumulate:

``expires``
    A per-entry ISO date. Past it, the entry is EXPIRED and the tool fails,
    because a sanctioned bridge nobody re-approved is just an undocumented
    violation.

``ratchet``
    ``max_allowed_imports`` (the count the policy currently justifies) and
    ``hard_cap`` (the count at which the policy itself is failing, regardless
    of any single entry's date). Above ``max_allowed_imports`` a warning is
    printed; above ``hard_cap`` every entry is reported OVER-RATCHET and the
    tool fails. The count is the total number of dated entries across all
    rules, so a new carve-out can only be added by removing an old one.
    ``next_review`` is the date the whole policy is re-read; passing it only
    warns (it does not fail the build) so a late review never silently
    becomes an expired exception.

An entry with a missing or unparsable ``expires`` is treated as EXPIRED
(fail closed): an exception without a date is not a decision, it is a leak.

Usage:
    python tools/check_policy_expiry.py
    python tools/check_policy_expiry.py --json

Exit code:
    1 when any entry is EXPIRED or OVER-RATCHET, 0 otherwise.

Stdlib only. Never imports ``engine`` or ``services`` code: it reads a JSON
file, so it is safe to run anywhere the policy file is present.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

#: The policy lives next to this tool, exactly as tools/detect_imports.py resolves it.
POLICY_PATH = Path(__file__).resolve().parent / "import_guard_policy.json"

STATUS_OK = "OK"
STATUS_EXPIRED = "EXPIRED"
STATUS_OVER_RATCHET = "OVER-RATCHET"

#: Section keys inside a rule that hold dated exception entries. A section
#: qualifies when it is a non-empty list of objects carrying a ``module``
#: (``allowed_imports`` today; ``facade_files`` carries ``path`` and is
#: therefore not a dated carve-out).
_ENTRY_SECTIONS = ("allowed_imports",)


def load_policy(policy_path: Path | str = POLICY_PATH) -> dict[str, Any]:
    """Load the policy document.

    Unlike ``tools/detect_imports.py`` this tool does not fall back to
    embedded defaults: a missing or malformed policy is a failure to report,
    not something to paper over, because the guard would then be running on
    unwritten rules.
    """
    path = Path(policy_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - defensive
        raise SystemExit(f"cannot read policy file {path}: {exc}") from exc
    policy = json.loads(text)
    if not isinstance(policy, dict) or not isinstance(policy.get("rules"), dict):
        raise SystemExit(f"malformed policy file {path}: expected an object with a 'rules' object")
    return policy


def policy_entries(policy: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    """Return ``(rule_id, section, entry)`` for every dated exception.

    Deterministically ordered (rule id, then section, then file order) so
    text and JSON output are diffable across runs.
    """
    collected: list[tuple[str, str, dict[str, Any]]] = []
    rules = policy.get("rules", {})
    if not isinstance(rules, dict):  # pragma: no cover - guarded by load_policy
        return collected
    for rule_id in sorted(rules):
        rule = rules[rule_id]
        if not isinstance(rule, dict):
            continue
        for section in _ENTRY_SECTIONS:
            entries = rule.get(section)
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and "module" in entry:
                    collected.append((rule_id, section, entry))
    return collected


def _parse_date(value: Any) -> date | None:
    """Parse an ISO date, returning ``None`` when absent or unparsable."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _expires_is_past(entry: dict[str, Any], today: date) -> bool:
    """True when the entry's ``expires`` has passed (or is missing/invalid)."""
    parsed = _parse_date(entry.get("expires"))
    return parsed is None or today > parsed


def _ratchet_values(policy: dict[str, Any]) -> tuple[int | None, int | None, date | None]:
    """Return ``(max_allowed_imports, hard_cap, next_review)`` from the policy."""
    ratchet = policy.get("ratchet")
    if not isinstance(ratchet, dict):
        return None, None, None
    max_allowed = ratchet.get("max_allowed_imports")
    hard_cap = ratchet.get("hard_cap")
    return (
        int(max_allowed) if isinstance(max_allowed, int) else None,
        int(hard_cap) if isinstance(hard_cap, int) else None,
        _parse_date(ratchet.get("next_review")),
    )


def evaluate(policy: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    """Evaluate every dated entry; returns the report payload.

    The payload is what both output formats print. ``status`` precedence per
    entry is EXPIRED before OVER-RATCHET (a date is per-entry evidence, the
    ratchet is a global count), and ``exit_code`` is 1 when either applies.
    """
    today = today or date.today()
    max_allowed, hard_cap, next_review = _ratchet_values(policy)
    entries = policy_entries(policy)
    total = len(entries)
    over_hard = hard_cap is not None and total > hard_cap
    over_max = max_allowed is not None and total > max_allowed
    review_overdue = next_review is not None and today > next_review

    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for rule_id, section, entry in entries:
        expires = entry.get("expires")
        expires_date = _parse_date(expires)
        expired = _expires_is_past(entry, today)
        if expired:
            status = STATUS_EXPIRED
        elif over_hard:
            status = STATUS_OVER_RATCHET
        else:
            status = STATUS_OK
        record = {
            "rule": rule_id,
            "section": section,
            "module": entry.get("module"),
            "expires": expires if isinstance(expires, str) else None,
            "revisit": entry.get("revisit") if isinstance(entry.get("revisit"), str) else None,
            "owner": entry.get("owner") if isinstance(entry.get("owner"), str) else None,
            "days_to_expiry": (expires_date - today).days if expires_date else None,
            "status": status,
        }
        records.append(record)
        if status != STATUS_OK:
            failures.append(record)

    return {
        "tool": "check_policy_expiry",
        "item": "B-1",
        "policy": str(POLICY_PATH),
        "today": today.isoformat(),
        "entries_total": total,
        "max_allowed_imports": max_allowed,
        "hard_cap": hard_cap,
        "over_max_allowed": over_max,
        "over_hard_cap": over_hard,
        "next_review": next_review.isoformat() if next_review else None,
        "review_overdue": review_overdue,
        "expired_count": sum(1 for r in records if r["status"] == STATUS_EXPIRED),
        "entries": records,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "exit_code": 0 if not failures else 1,
    }


def _text_lines(report: dict[str, Any]) -> list[str]:
    """Render the human-readable report (one line per entry, plus a summary)."""
    lines = [
        "Import-guard policy expiry + ratchet (B-1)",
        f"policy: {report['policy']}",
        f"today:  {report['today']}",
        f"entries: {report['entries_total']} "
        f"(max_allowed_imports {report['max_allowed_imports']}, "
        f"hard_cap {report['hard_cap']})",
    ]
    if report["over_max_allowed"] and not report["over_hard_cap"]:
        lines.append(
            "WARNING: allowed_imports count is above max_allowed_imports "
            "but within hard_cap — remove an exception before adding one."
        )
    if report["review_overdue"]:
        lines.append(
            f"WARNING: policy next_review {report['next_review']} has passed — re-read the policy."
        )
    for record in report["entries"]:
        lines.append(
            f"{record['status']} {record['rule']} {record['module']} "
            f"{record['expires'] or 'MISSING'}"
        )
    lines.append(
        f"status: {report['status']} — {report['expired_count']} expired, "
        f"{report['entries_total'] - report['expired_count']} current, "
        f"ratchet {report['entries_total']}/{report['hard_cap']}"
    )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check tools/import_guard_policy.json exceptions for expiry and ratchet drift."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the machine-readable report instead of one line per entry",
    )
    args = parser.parse_args(argv)

    policy = load_policy()
    report = evaluate(policy)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n".join(_text_lines(report)))
    return int(report["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
