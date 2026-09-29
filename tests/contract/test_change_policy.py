"""The change policy is written down and stays true of the tree.

Two of the plan's six execution risks are about sequencing rather than code:
the feature freeze blocking delivery, and queues contracting before their
workers are ready. Neither is a thing a test can decide, so they are recorded
in ``docs/standards/change-policy.md`` — and the parts of that record that
*are* checkable are checked here:

* the policy exists and states both mitigations the plan asked for;
* the deletions recorded in the log are individually attributed, which is the
  property that makes the freeze reviewable rather than a blanket excuse;
* nothing in the log is attributed to a domain nobody owns.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs" / "standards" / "change-policy.md"
DELETION_LOG = ROOT / "docs" / "metrics" / "deletions.json"
LEDGER = ROOT / "docs" / "standards" / "tolerated-degradations.yaml"


class TestThePolicyExists:
    def test_it_is_written(self) -> None:
        assert POLICY.exists(), (
            f"{POLICY.relative_to(ROOT)} records the freeze and its exception, and the "
            "adapter-removal ordering rule. Both are decisions, so they belong in a "
            "document a reviewer can read -- not in a commit message."
        )

    def test_it_states_the_freeze_exception_conditions(self) -> None:
        text = POLICY.read_text(encoding="utf-8").lower()
        for condition in ("security", "data-loss", "unblock"):
            assert condition in text, f"the freeze exception should name {condition}"

    def test_it_requires_a_customer_visible_harm_for_an_exception(self) -> None:
        """Without this the exception becomes a preference with a stamp on it."""
        text = POLICY.read_text(encoding="utf-8").lower()
        assert "customer-visible" in text, (
            "an exception must state the harm of not doing it, or it is a preference"
        )

    def test_it_states_the_adapter_removal_ordering_rule(self) -> None:
        text = POLICY.read_text(encoding="utf-8").lower()
        assert "adapter" in text, "the queue-contraction mitigation must be stated"
        assert "last consumer" in text, (
            "the rule is 'remove the shim when the last consumer moves'; the phrase is "
            "what makes it checkable"
        )


class TestTheFreezeIsNarrow:
    def test_the_policy_excludes_debt_reduction_from_the_freeze(self) -> None:
        """Otherwise the freeze is an excuse to stop paying down debt."""
        text = POLICY.read_text(encoding="utf-8").lower()
        assert "toleration" in text, (
            "removing a recorded toleration must stay allowed during the freeze, or the "
            "freeze halts the very work it was protecting"
        )

    def test_it_forbids_smuggled_deletions(self) -> None:
        text = POLICY.read_text(encoding="utf-8").lower()
        assert "while i am in here" in text or "smuggl" in text


class TestTheDeletionsAreIndividuallyAttributable:
    def test_every_entry_names_an_owning_domain(self) -> None:
        data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
        unattributed = [e["path"] for e in data["deletions"] if not e.get("owner_domain")]
        assert not unattributed, (
            "these deletions have no owner_domain, so no reviewer is accountable for them:\n  "
            + "\n  ".join(unattributed)
        )

    def test_the_domains_used_by_deletions_are_the_ones_codeowners_defines(self) -> None:
        from tests.contract.test_codeowners import DOMAINS

        data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
        used = {e.get("owner_domain") for e in data["deletions"]} - {None}
        assert used <= set(DOMAINS), f"deletions name undefined domains: {used - set(DOMAINS)}"

    def test_no_single_deletion_carries_everything(self) -> None:
        """A log where one change removed 20 things cannot be reviewed per item."""
        data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
        assert len(data["deletions"]) >= 10, "the log should be a list, not a summary"
        for entry in data["deletions"]:
            assert entry["path"].count("/") >= 1, (
                f"{entry['path']}: top-level removals are too coarse to attribute"
            )


class TestTheLedgerAndTheDeletionsAgree:
    def test_a_removed_file_is_not_still_listed_as_live_debt(self) -> None:
        """If a path was deleted, its toleration must have gone with it.

        The two records describe the same tree from opposite directions: the log
        says "this is gone", the ledger says "this is still broken".
        """
        import re

        data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
        deleted = [e["path"] for e in data["deletions"]]
        ledger = LEDGER.read_text(encoding="utf-8")
        stale = [
            path
            for path in deleted
            if re.search(rf"^\s+path:\s*{re.escape(path)}\s*$", ledger, re.MULTILINE)
        ]
        assert not stale, (
            "these paths are logged as deleted but still appear as tolerations:\n  "
            + "\n  ".join(stale)
        )
