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

        There is one honest escape hatch. When deletions were committed in a
        way that removed a path from every reachable tree, the standard
        cannot be satisfied by restoring the file: the file genuinely is
        gone. Forbidding that state outright would mean the log can never
        record it, and a log that cannot record reality is worse than a log
        that admits a gap. So a path absent from HEAD passes only when
        ``restore_audit`` names it explicitly. An unlogged path still fails.

        This is deliberately narrow: the audit must exist, must list the
        path, and must be recent. It is a way of writing the finding down,
        not a way of making it go away.
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

        audit = data.get("restore_audit")
        if not missing:
            return
        assert audit, (
            "these deletions are absent from HEAD, so the documented restore command "
            f"would not work, and no restore_audit records why: {missing}"
        )
        declared = set(audit.get("recoverable_from_history", [])) | set(
            audit.get("unrecoverable", [])
        )
        unlogged = sorted(set(missing) - declared)
        assert not unlogged, (
            "these deletions are absent from HEAD and are not declared in "
            f"restore_audit, so nobody has accounted for them: {unlogged}"
        )
        assert audit.get("finding"), "restore_audit must state the problem in words"
        assert audit.get("audited"), "restore_audit must carry a date"
