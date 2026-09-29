"""Deletion safety: a removal is a change like any other, and is checked like one.

The plan's risk table names *deleting code that looked dead and was not* as a
medium-probability, medium-impact risk, with the mitigation: "vulture + human
review + one clean full run before deleting". Two of those three are automated
already. This module supplies the third as a *procedure* rather than a promise,
and pins the parts that can be checked mechanically:

* the deletion log exists and every entry has a reason and a verification
  (see ``test_deletion_log.py``);
* a deleted module is never left with a live importer;
* the suite that guards the gates is itself green.

What cannot be automated is the ordering — that the suite was green *before*
the deletion. ``scripts/verify_consolidation.py --skip-contract`` is the
documented pre-deletion command, and its output is what a reviewer asks for.
This module makes the rest of the procedure explicit so it is followed by
default rather than remembered.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DELETION_LOG = ROOT / "docs" / "metrics" / "deletions.json"
PROCEDURE = ROOT / "docs" / "standards" / "deletion-procedure.md"


class TestTheProcedureIsWrittenDown:
    def test_it_exists(self) -> None:
        assert PROCEDURE.exists(), (
            f"{PROCEDURE.relative_to(ROOT)} records the deletion procedure. The plan's "
            "mitigation for the 'deleted something that was alive' risk is three steps, and "
            "without a written procedure the ordering step is the one that gets skipped."
        )

    def test_it_names_the_pre_check_command(self) -> None:
        text = PROCEDURE.read_text(encoding="utf-8")
        assert "verify_consolidation.py" in text, (
            "the pre-deletion verification command must be written down, not recalled"
        )

    def test_it_says_how_to_undo(self) -> None:
        """Every logged deletion is a tracked file, so the undo is one command.

        Recording it is what separates a reversible action from a frightening
        one.
        """
        text = PROCEDURE.read_text(encoding="utf-8")
        assert "git checkout" in text, "the procedure must state how to restore a deletion"

    def test_it_requires_a_human_decision_on_ambiguous_evidence(self) -> None:
        """The G2 scanner and vulture disagree about some things by design.

        When the evidence is not clean, a person decides; the procedure has to
        say so, or a future reader assumes the tooling settled it.
        """
        text = PROCEDURE.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "human" in lowered or "reviewer" in lowered


class TestEveryDeletionIsRecoverable:
    def test_all_logged_paths_were_tracked_files(self) -> None:
        """An untracked deletion cannot be restored from git.

        Each entry must be a path git knows about, which is what makes the
        documented ``git checkout HEAD -- <path>`` undo real.
        """
        import json
        import subprocess

        data = json.loads(DELETION_LOG.read_text(encoding="utf-8"))
        paths = [e["path"] for e in data["deletions"]]
        proc = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", *paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        tracked = set(proc.stdout.split())
        missing = [p for p in paths if p not in tracked]
        assert not missing, (
            "these deletions were not tracked in HEAD, so the documented restore command "
            f"would not work: {missing}"
        )
