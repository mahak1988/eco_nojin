"""The CODEOWNERS file and the deletion log must agree with each other.

The integration plan's execution-risk table names "ownership without
authority" as a live risk, with the mitigation "add each owner to
CODEOWNERS". That mitigation had never been carried out: the ten domain owners
(D-1 .. D-10) were used throughout the standards, the toleration ledger and
the plan, and nothing connected them to a required review.

These tests keep the three views of the same ownership model in step. They do
not check that CODEOWNERS is *useful* — a placeholder like ``@org/team-name``
makes GitHub fall back to no review requirement while looking configured — but
they do check that it is present, that it covers every domain the ledger
uses, and that no path is claimed by nobody.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
LEDGER = ROOT / "docs" / "standards" / "tolerated-degradations.yaml"
DELETION_LOG = ROOT / "docs" / "metrics" / "deletions.json"

#: The ten domains from the plan's ownership table. Kept literal so a new
#: domain id in the ledger has to be added here deliberately.
DOMAINS = {
    "D-1": "finance",
    "D-2": "marketplace",
    "D-3": "carbon",
    "D-4": "science",
    "D-5": "data",
    "D-6": "platform",
    "D-7": "security",
    "D-8": "ai",
    "D-9": "operations",
    "D-10": "access",
}


@pytest.fixture(scope="module")
def codeowners() -> list[tuple[str, list[str]]]:
    assert CODEOWNERS.exists(), (
        f"{CODEOWNERS.relative_to(ROOT)} is missing. The plan's risk table specifies it as the "
        "mitigation for 'ownership without authority', and without it the ten domain owners "
        "used in the standards and the ledger are advisory only."
    )
    entries: list[tuple[str, list[str]]] = []
    for line in CODEOWNERS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            # A bare pattern with no owner is the failure mode this file exists
            # to prevent: GitHub treats it as having no requirement.
            raise AssertionError(
                f"CODEOWNERS line has a pattern but no owner: {line!r}. "
                "Format is `<pattern> <owner> [...]`."
            )
        entries.append((parts[0], parts[1:]))
    return entries


class TestCodeownersIsUsable:
    def test_it_parses_into_pattern_owner_pairs(self, codeowners):
        assert codeowners, "no CODEOWNERS entries were parsed"

    def test_no_placeholder_handles(self, codeowners):
        """The file ships with a spelling that reads as intentional.

        These handles do not resolve, so GitHub requires no review from
        anyone. That is worse than shipping no CODEOWNERS: the repository looks
        owned. Replacing the handles is a human decision -- it needs real team
        or account names -- so the gate only refuses spellings that announce
        themselves as placeholders, and the file's header states the problem.
        """
        announced = re.compile(r"@org/|@your-|@example|TODO|CHANGEME|REPLACE_ME", re.I)
        bad = [
            f"{pattern} -> {owners}"
            for pattern, owners in codeowners
            if any(announced.search(o) for o in owners)
        ]
        assert not bad, (
            "CODEOWNERS contains self-declared placeholders:\n  " + "\n  ".join(bad)
        )

    def test_the_unresolved_handles_are_disclosed(self, codeowners):
        """The shipped handles are placeholders; that must be visible, not
        buried. If this test is deleted along with the disclosure, the file is
        pretending to be finished."""
        header = CODEOWNERS.read_text(encoding="utf-8")[:2000]
        assert "PLACEHOLDER" in header.upper(), (
            "the CODEOWNERS header must state that the owner handles are placeholders"
        )

    def test_every_entry_names_an_owner(self, codeowners):
        empty = [pattern for pattern, owners in codeowners if not owners]
        assert not empty, f"CODEOWNERS entries with no owner: {empty}"


class TestOwnershipIsConsistent:
    def test_every_ledger_domain_appears_in_the_owners_file(self, codeowners):
        ledger = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
        used = {entry["owner"] for entry in ledger["tolerations"]}
        known = set(DOMAINS)
        unknown = used - known
        assert not unknown, (
            f"the toleration ledger uses owner ids CODEOWNERS does not define: {sorted(unknown)}"
        )
        assert used, "the ledger has no owners at all"

    def test_every_domain_in_the_table_is_declared(self):
        assert set(DOMAINS) == {f"D-{n}" for n in range(1, 11)}

    def test_the_deletion_log_owner_fields_agree(self):
        """A deletion recorded against a domain nobody reviews is the exact
        'ownership without authority' failure, applied to the riskiest action
        in the plan."""
        data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
        known = set(DOMAINS)
        for entry in data["deletions"]:
            phase = entry.get("phase")
            assert phase in {4, 5}, f"{entry['path']}: unexpected phase {phase}"
            owner = entry.get("owner_domain")
            if owner is not None:
                assert owner in known, (
                    f"{entry['path']} is attributed to {owner}, which CODEOWNERS does not define"
                )
        assert known, "the domain table must not be empty"

    def test_the_integrity_gates_are_owned(self, codeowners):
        """The gates must be reviewed by someone; a gate nobody owns is a gate
        nobody maintains."""
        patterns = [p for p, _ in codeowners]
        for required in ("/tests/contract/", "/docs/metrics/"):
            assert any(required in p for p in patterns), (
                f"{required} has no CODEOWNERS entry, so the gates themselves are unowned"
            )


class TestGateCoverageIsNotMissingAPath:
    def test_the_ratcheted_scopes_are_owned(self, codeowners):
        """A ratchet metric that covers a directory nobody reviews will drift."""
        patterns = [p for p, _ in codeowners]
        for scope in ("/services/", "/engine/"):
            assert any(p.startswith(scope) for p in patterns), f"no owner for {scope}"

    def test_no_documented_domain_owns_nothing(self, codeowners):
        """Each domain must appear in at least one owner handle.

        Checked against the owners, not the paths: a domain label is a name
        (``science``), while the paths use their own vocabulary
        (``scientific_motors``), and matching the label against paths would
        pass or fail for reasons unrelated to ownership.
        """
        owners = " ".join(o for _, group in codeowners for o in group).lower()
        for name in DOMAINS.values():
            assert name in owners, f"domain {name} is declared but names no owner handle"
