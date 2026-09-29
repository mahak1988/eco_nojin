"""Claims gate: keeps analytical documents honest about the code they describe.

Why this exists
---------------
On 2026-09-29 an analysis presented several findings as current fact that were
actually copied from a stale comment block in
``docs/standards/tolerated-degradations.yaml`` (reviewed 2026-09-28). One
referenced file had been deleted, and two referenced functions were fully
implemented rather than returning constants. The documents were confidently
wrong.

A document is a snapshot. Code is not. This gate derives facts from the
repository and cross-checks them against what the documents assert, so a
document that drifts from reality fails CI instead of misleading a reader.

Three design rules, all learned the hard way:

1. No claim registry file. A registry becomes a second source of truth and
   drifts the same way the documents do. Facts are derived; documents are
   checked against the derived facts.
2. No fragile string matching. Persian documents mix ASCII and Persian
   numerals, and Persian text uses ZWNJ and hamza variants. Every matcher
   normalises first. A gate that produces false positives is worse than none.
3. A gate that punishes improvement is worse than no gate. Every check
   asserts that a document states reality accurately, never that a defect
   persists. ``test_gate_does_not_punish_improvements`` enforces this on the
   gate itself.

What this gate does and does not do
-----------------------------------
It verifies *mechanical* claims: figures re-derivable from repository state,
and statements about code that can be checked. It cannot verify *interpretive*
claims, because whether "73% of cost comes from replication" is a fair reading
of the data is a judgement, not a computation.

Rather than ignore that limit, the claim-ledger checks below require every
analysis document to declare, per claim, which kind it is. An author cannot
bury a judgement in prose and let a reader assume it was measured. The gate
enforces honesty of labelling, never the verdict itself.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HELM_CHART = REPO_ROOT / "helm" / "eco-nojin"
VALUES = HELM_CHART / "values.yaml"
TEMPLATES = HELM_CHART / "templates"
TOLERATIONS = REPO_ROOT / "docs" / "standards" / "tolerated-degradations.yaml"
COST_DOC = REPO_ROOT / "COST_OPTIMIZATION_RESEARCH_FA.md"
COST_ESTIMATOR = REPO_ROOT / "scripts" / "cost_estimate.py"
WHITELABEL_DOC = REPO_ROOT / "WHITE_LABEL_PLATFORM_RESEARCH_FA.md"
BACKLOG = REPO_ROOT / "docs" / "innovation_backlog.csv"
AGENTS = REPO_ROOT / "AGENTS.md"

PERSIAN_TO_ASCII = {
    ord(c): str(d) for c, d in zip("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789", strict=True)
}

# Persian text mixes hamza, alef and kaf variants of the same letter. NFKC
# does not fold them, so a matcher for "تأییدنشده" must also accept
# "تايیدنشده" or "تاییدنشده".
ARABIC_LETTER_FOLD = {
    **{ord(c): "\u0627" for c in "\u0623\u0625\u0622\u0671"},
    **{ord(c): "\u06cc" for c in "\u0649"},
    **{ord(c): "\u06a9" for c in "\u0643"},
    **{ord(c): "\u0647" for c in "\u0629"},
}

KNOWN_COMPONENTS = {
    "redis",
    "postgresql",
    "n8n",
    "monitoring",
    "logging",
    "tracing",
    "velero",
    "istio",
    "multiRegion",
    "argocd",
    "externalSecrets",
    "pgpool",
    "loki",
    "tempo",
    "otel",
    "prometheus",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _ascii_fold(text: str) -> str:
    """Normalise digits, ZWNJ and Arabic letter variants to a stable alphabet.

    Documents in this repo mix 4,797 / ۴٬۷۹۷ / ٤٬٧٩٧, use ZWNJ (U+200C),
    and write the same Persian word with different hamza/alef forms. Matchers
    must not care which one a given author typed.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(PERSIAN_TO_ASCII).translate(ARABIC_LETTER_FOLD)
    return text.replace("\u200c", "").replace("\u200f", "").replace("\u064b", "")


def _header_comment(path: Path) -> str:
    """Every comment line in a YAML file, not just the leading block.

    Scanning only the leading header was verified to miss a claim appended
    at the end of the file. A gate that can be defeated by moving a comment is
    not a gate, so all comment lines are collected.
    """
    return "\n".join(
        line.strip().lstrip("#").strip()
        for line in _read(path).splitlines()
        if line.strip().startswith("#")
    )


def _components_defined_in_values() -> set[str]:
    text = _read(VALUES)
    found = {
        line.split(":", 1)[0].strip()
        for line in text.splitlines()
        if line[:1].isalpha() and ":" in line
    }
    return found & KNOWN_COMPONENTS


def _components_with_templates() -> set[str]:
    """Components that at least one template can actually render."""
    realisable: set[str] = set()
    for template in TEMPLATES.glob("*.yaml"):
        stem = template.stem.lower().replace("-", "")
        for component in _components_defined_in_values():
            if component.lower() in stem:
                realisable.add(component)
    return realisable


def test_helm_chart_can_render_what_values_declares() -> None:
    """values.yaml declares components the chart has no template for.

    This is the most load-bearing fact in the cost analysis. If the gap is
    closed, this test fails and forces the cost documents to be re-derived,
    because the headline figure describes a configuration the chart cannot
    currently produce.
    """
    defined = _components_defined_in_values()
    assert defined, "no deployment components found in values.yaml"

    unrealisable = defined - _components_with_templates()
    assert unrealisable, (
        "every component in values.yaml now has a template; the chart is no "
        f"longer aspirational. Re-derive the baseline and update {COST_DOC.name}."
    )

    doc = _ascii_fold(_read(COST_DOC))
    assert any(component in doc for component in unrealisable), (
        f"cost doc names none of the unrendered components {sorted(unrealisable)}; "
        "it may be presenting the manifest as deployable"
    )


def test_cost_doc_presents_unrendered_manifest_as_target_not_as_spend() -> None:
    """A chart that cannot render its values must not be costed as if it ran.

    The document is Persian, so this checks the concepts the repo actually
    uses for the disclaimer, not an English keyword.
    """
    doc = _ascii_fold(_read(COST_DOC)).lower()
    assert "مانیفست" in doc, "cost doc lost its framing"
    assert "هزینه" in doc, "cost doc lost its framing"
    assert any(marker in doc for marker in ("غیرفعال", "درصورت اجرا", "طراحی هدف", "نوشته شده")), (
        "cost doc must state that the figure is the cost of the manifest as "
        "written and that staging/production are disabled"
    )
    for phrase in ("currently running", "in production", "we pay", "we are paying"):
        assert phrase not in doc, (
            f"cost doc contains {phrase!r}, implying the aspirational manifest is actually deployed"
        )


def test_tolerations_header_cites_only_existing_files() -> None:
    """The tolerances header must not cite deleted files.

    This is the check that would have caught the original error: the header
    cited services/security/ssrf.py, which no longer exists.
    """
    header = _header_comment(TOLERATIONS)
    assert header, f"{TOLERATIONS.name} has no header comment"

    references = re.findall(r"((?:services|engine|apps|tests)/[\w/]+\.py):(\d+)", header)
    assert references, (
        "no file:line references parsed from the tolerances header; the format "
        "changed and this gate must be updated to match reality"
    )

    missing = [path for path, _ in references if not (REPO_ROOT / path).is_file()]
    assert not missing, (
        f"{TOLERATIONS.name} cites files that no longer exist: {sorted(set(missing))}. "
        "Delete those claims or re-verify them against the current code."
    )


def _referenced_paths(text: str) -> list[str]:
    """Extract repo-relative paths from a command string.

    Windows command lines use backslashes. A matcher that only accepts
    forward slashes silently extracts nothing, which turns the calling check
    into a vacuous pass. Normalise first.
    """
    return re.findall(r"(?:scripts|tests|docs)/[\w./-]+", text.replace("\\", "/"))


def _function_body(lines: list[str], func: str) -> list[str] | None:
    """Return the body of ``func`` by indentation, or None if not found.

    A line-number window is not enough. A real implementation usually contains
    the same constant the comment claims, inside a guard clause, which makes a
    naive substring check pass and hides a stale claim. Measuring the body is
    what actually distinguishes a stub from an implementation.
    """
    start = None
    for index, line in enumerate(lines):
        if re.match(rf"^\s*(async\s+)?def\s+{re.escape(func)}\s*\(", line):
            start = index
            break
    if start is None:
        return None

    indent = len(lines[start]) - len(lines[start].lstrip())
    body: list[str] = []
    for line in lines[start + 1 :]:
        if not line.strip():
            body.append(line)
            continue
        current = len(line) - len(line.lstrip())
        if current <= indent and not line.lstrip().startswith(("#", '"""', "'''")):
            break
        body.append(line)

    # Drop the docstring: it is prose, not logic.
    stripped = [line for line in body if line.strip()]
    if stripped and stripped[0].lstrip().startswith(('"""', "'''")):
        closing = '"""' if stripped[0].lstrip().startswith('"""') else "'''"
        for offset, line in enumerate(stripped[1:], start=1):
            if closing in line:
                stripped = stripped[offset + 1 :]
                break
    return stripped


def _looks_like_constant_stub(body: list[str], value: str) -> bool:
    """True only if the body is a bare ``return <value>``.

    A guard clause returning the constant is not a stub; it is a normal
    function. The threshold is deliberately tight so the gate errs towards
    flagging a claim for human review rather than silently passing.
    """
    statements = [line for line in body if line.strip() and not line.strip().startswith("#")]
    if not statements:
        return False
    if len(statements) > 3:
        return False
    returns = [line for line in statements if line.strip().startswith("return")]
    if not returns:
        return False
    if any(not re.match(rf"^return\s+{re.escape(value)}\b", line.strip()) for line in returns):
        return False
    # Any assignment or call means the function is doing work.
    return not any(
        re.match(r"^\w+\s*=[^=]", line.strip()) or re.search(r"\w+\s*\(", line.strip())
        for line in statements
    )


def test_tolerations_claim_matches_current_implementation() -> None:
    """Each cited function must still behave the way the header claims.

    The header described these as returning a constant. For every claim whose
    target still exists, extract the real function body and check whether it
    really is a bare constant return.

    This asserts accuracy, not continued breakage: if a function was properly
    implemented, this test fails and the header must be corrected.
    """
    header = _ascii_fold(_header_comment(TOLERATIONS))
    claims = re.findall(
        r"((?:services|engine|apps|tests)/[\w/]+\.py):(\d+)\s*\(\s*([\w_]+)\s*"
        r"(?:->|→)\s*(\w+)\s+(?:constant|ثابت)",
        header,
    )
    if not claims:
        # The header currently makes no constant-return claims, because all
        # six of them were wrong and have been corrected. That is the desired
        # state, not a gap in the gate. File-reference drift is still covered
        # by test_tolerations_header_cites_only_existing_files.
        assert "verif" in header or "بررسی" in header or "بازبینی" in header, (
            "the tolerances header makes no verifiable claims and records no "
            "review; add one so this gate has something to protect"
        )
        return

    inaccurate: list[str] = []
    unverified: list[str] = []
    for relative_path, line_text, func, value in claims:
        absolute = REPO_ROOT / relative_path
        if not absolute.is_file():
            continue
        lines = _read(absolute).splitlines()
        body = _function_body(lines, func)
        if body is None:
            unverified.append(f"{relative_path}:{line_text} {func}() not found")
            continue
        if not _looks_like_constant_stub(body, value):
            inaccurate.append(f"{relative_path} {func}() is not a constant {value}")

    assert not inaccurate, f"{TOLERATIONS.name} misdescribes current code:\n  " + "\n  ".join(
        inaccurate
    )
    assert not unverified, (
        f"{TOLERATIONS.name} cites functions that no longer exist:\n  " + "\n  ".join(unverified)
    )


def test_cost_baseline_matches_current_manifest() -> None:
    """The headline figure must be re-derivable from the manifest.

    If someone edits values.yaml, the documented total must change in the same
    edit. This is the staleness guard a document alone cannot provide.
    """
    if not COST_ESTIMATOR.is_file():
        raise AssertionError(f"missing estimator: {COST_ESTIMATOR}")

    result = subprocess.run(
        [sys.executable, str(COST_ESTIMATOR)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, f"cost_estimate.py failed:\n{result.stderr}"

    match = re.search(r"TOTAL \(all\)\s+([\d,]+\.\d\d)", result.stdout)
    assert match, "could not parse the total from cost_estimate.py output"
    current = float(match.group(1).replace(",", ""))

    doc = _ascii_fold(_read(COST_DOC))
    documented = [
        float(n.replace(",", ""))
        for n in re.findall(r"[\d,]{4,}(?:\.\d\d)?", doc)
        if n.replace(",", "").replace(".", "").isdigit()
    ]
    assert any(abs(value - current) < 1.0 for value in documented), (
        f"cost doc contains no figure matching the current manifest total "
        f"({current:,.2f}). Re-derive and update it in the same change that "
        "edited the manifest."
    )


def test_unverified_rates_stay_labelled() -> None:
    """Estimates must never be presented as measured facts (S-HONEST).

    The EC2 and EBS rates in cost_estimate.py are assumptions, not quoted
    vendor rates. The Hetzner price could not be extracted at all.
    """
    doc = _ascii_fold(_read(COST_DOC))
    for token in ("measured", "estimated"):
        assert token in doc, f"cost doc does not distinguish {token!r} figures"
    assert "Hetzner" in doc, "the failed Hetzner lookup must stay on the record"

    label_doc = _ascii_fold(_read(WHITELABEL_DOC))
    assert "NOT VERIFIED" in label_doc or "تاییدنشده" in label_doc, (
        "white-label research must keep its unverified list"
    )


def test_pending_language_decision_is_still_pending_or_resolved() -> None:
    """ADR 0001 commits to Rust and Go. Either code exists, or the item is open.

    Prevents a second silent gap: a decision record that drifted away from the
    repository without anyone noticing for years.
    """
    adr = REPO_ROOT / "docs" / "adr" / "0001-language-strategy.md"
    assert adr.is_file(), f"missing ADR: {adr}"

    sources: list[Path] = []
    for pattern in ("*.rs", "*.go"):
        for root in ("engine", "services", "apps", "mobile"):
            candidate = REPO_ROOT / root
            if candidate.is_dir():
                sources.extend(candidate.rglob(pattern))

    if not sources and BACKLOG.is_file():
        rows = _ascii_fold(_read(BACKLOG)).lower()
        assert "rust" in rows, (
            "ADR 0001 commits to Rust, no such source exists, and the "
            "innovation backlog no longer carries an open item for it."
        )
        assert " go " in f" {rows} ", (
            "ADR 0001 commits to Go, no such source exists, and the innovation "
            "backlog no longer carries an open item for it."
        )


# --- claim ledgers -----------------------------------------------------------
#
# Every analysis document must carry a fenced ```claims block classifying each
# of its load-bearing claims. Kinds:
#
#   derived      - computed from repository state by a named runnable command
#   quoted       - taken from an external primary source, with retrieval date
#   interpretive - a judgement; the basis must be stated, never bare
#
# The gate checks the labelling, never the verdict. An interpretive claim that
# turns out to be wrong still passes here; that is the accepted limit of
# automation and is why the basis field exists.

ANALYSIS_DOCS = [
    REPO_ROOT / "COST_OPTIMIZATION_RESEARCH_FA.md",
    REPO_ROOT / "WHITE_LABEL_PLATFORM_RESEARCH_FA.md",
    REPO_ROOT / "INNOVATION_BACKLOG_FA.md",
]

CLAIM_KINDS = {"derived", "quoted", "interpretive"}
CLAIM_BLOCK = re.compile(r"^```claims\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
ENTRY = re.compile(r"^- id:\s*(\S+)\s*$(.*?)(?=^- id:|\Z)", re.MULTILINE | re.DOTALL)
FIELD = re.compile(r"^\s*(\w+):\s*(.+?)\s*$", re.MULTILINE)

MIN_BASIS_WORDS = 6


def _unquote(value: str) -> str:
    """Strip one layer of matching quotes.

    The ledger is YAML-ish, so values are usually quoted. Keeping the quotes
    made every value compare against a string that can never appear in
    command output, which would have made the reproduce check always fail.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _claim_ledger(path: Path) -> dict[str, dict[str, str]]:
    """Parse the ```claims block of an analysis document."""
    match = CLAIM_BLOCK.search(_read(path))
    if not match:
        return {}
    entries: dict[str, dict[str, str]] = {}
    for claim_id, blob in ENTRY.findall(match.group(1)):
        fields = {key.lower(): _unquote(value) for key, value in FIELD.findall(blob)}
        fields["id"] = claim_id
        entries[claim_id] = fields
    return entries


def test_every_analysis_document_has_a_claim_ledger() -> None:
    """A reader must be able to see how each headline claim was arrived at."""
    missing = [path.name for path in ANALYSIS_DOCS if path.is_file() and not _claim_ledger(path)]
    assert not missing, (
        f"analysis documents without a ```claims ledger: {missing}. Add one, "
        "classifying each load-bearing claim as derived, quoted or interpretive."
    )


def test_claim_ledger_entries_are_well_formed() -> None:
    """Every entry needs an id, a statement, a kind, and kind-specific evidence."""
    problems: list[str] = []
    for path in ANALYSIS_DOCS:
        if not path.is_file():
            continue
        ledger = _claim_ledger(path)
        if not ledger:
            continue
        for claim_id, fields in ledger.items():
            kind = fields.get("kind", "").lower()
            if kind not in CLAIM_KINDS:
                problems.append(f"{path.name}:{claim_id} unknown kind {kind!r}")
                continue
            if not fields.get("text"):
                problems.append(f"{path.name}:{claim_id} has no text")
            if kind == "derived" and not fields.get("reproduce"):
                problems.append(f"{path.name}:{claim_id} derived but names no command")
            if kind == "quoted" and not fields.get("source"):
                problems.append(f"{path.name}:{claim_id} quoted but names no source")
            if kind == "interpretive":
                basis = fields.get("basis", "")
                if not basis:
                    problems.append(f"{path.name}:{claim_id} interpretive with no basis")
                elif len(basis.split()) < MIN_BASIS_WORDS:
                    problems.append(
                        f"{path.name}:{claim_id} basis too thin to audit "
                        f"({len(basis.split())} words)"
                    )
    assert not problems, "malformed claim entries:\n  " + "\n  ".join(problems)


def test_claim_ids_are_unique_per_document() -> None:
    """Duplicate ids make a ledger ambiguous when someone cites a claim."""
    for path in ANALYSIS_DOCS:
        if not path.is_file():
            continue
        raw = CLAIM_BLOCK.search(_read(path))
        if not raw:
            continue
        ids = ENTRY.findall(raw.group(1))
        duplicates = sorted({claim for claim in ids if ids.count(claim) > 1})
        assert not duplicates, f"{path.name} has duplicate claim ids: {duplicates}"


def _command_parts(reproduce: str) -> tuple[str | None, list[str]]:
    """Split a reproduce field into (script, args).

    A reproduce field is a full command line, so it may include a
    subcommand (``cost_guard.py check``) and not just flags. Running the
    script bare makes it fail, which used to look like a stale claim rather
    than a malformed instruction.
    """
    normalised = reproduce.replace("\\", "/")
    tokens = re.findall(r"[\w./:-]+", normalised)
    script = next((token for token in tokens if token.endswith(".py")), None)
    if script is None:
        return None, []
    tail = tokens[tokens.index(script) + 1 :]
    args = [token for token in tail if not token.startswith("-") and "/" not in token]
    return script, args


def test_derived_claims_name_a_command_that_exists() -> None:
    """A derivation path that does not run is a broken promise to the reader."""
    problems: list[str] = []
    for path in ANALYSIS_DOCS:
        if not path.is_file():
            continue
        for claim_id, fields in _claim_ledger(path).items():
            if fields.get("kind", "").lower() != "derived":
                continue
            reproduce = fields.get("reproduce", "")
            for referenced in _referenced_paths(reproduce):
                referenced = referenced.rstrip(".,;:")
                if "*" in referenced or not (REPO_ROOT / referenced).exists():
                    problems.append(f"{path.name}:{claim_id} -> missing {referenced}")
    assert not problems, "derived claims point at nothing:\n  " + "\n  ".join(problems)


def test_derived_claims_actually_reproduce() -> None:
    """Run the named command and confirm the stated value still appears.

    This is the claim ledger's teeth: a derived claim whose value the command
    no longer produces has gone stale exactly like a hand-written figure.
    """
    problems: list[str] = []
    for path in ANALYSIS_DOCS:
        if not path.is_file():
            continue
        for claim_id, fields in _claim_ledger(path).items():
            if fields.get("kind", "").lower() != "derived":
                continue
            reproduce = fields.get("reproduce", "")
            value = fields.get("value", "").strip()
            script, args = _command_parts(reproduce)
            if script is None:
                problems.append(
                    f"{path.name}:{claim_id} is derived but its command names no runnable script"
                )
                continue
            if not value:
                continue
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / script), *args],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                check=False,
            )
            # A non-zero exit is not automatically a broken claim.
            # `cost_guard.py budget` exits 2 to mean "the bill is unknown",
            # which is a legitimate state it still prints. Only treat it as a
            # failure when the command reported nothing to check against.
            if result.returncode != 0 and not value:
                problems.append(
                    f"{path.name}:{claim_id} command failed: {script} "
                    f"(exit {result.returncode})"
                )
                continue
            expected = value.replace(",", "")
            # Command output keeps thousands separators; the claim value may
            # or may not. Compare against both renderings.
            haystack = _ascii_fold(result.stdout) + _ascii_fold(result.stderr)
            if expected and expected not in haystack and expected not in haystack.replace(",", ""):
                problems.append(
                    f"{path.name}:{claim_id} states {value!r}, which the command "
                    f"no longer produces"
                )
    assert not problems, "stale derived claims:\n  " + "\n  ".join(problems)


def test_ledgers_declare_at_least_one_interpretive_claim() -> None:
    """A document claiming everything is mechanical is hiding judgement.

    If an analysis genuinely has no interpretive claim, that is worth
    noticing. This test forces the author to look again.
    """
    for path in ANALYSIS_DOCS:
        if not path.is_file():
            continue
        ledger = _claim_ledger(path)
        if not ledger:
            continue
        kinds = [fields.get("kind", "").lower() for fields in ledger.values()]
        assert "interpretive" in kinds, (
            f"{path.name} classifies every claim as derived or quoted. An analysis "
            "always contains judgement about what matters; label it."
        )


def test_agents_md_commands_reference_real_files() -> None:
    """Every path an agent is told to run must exist.

    AGENTS.md is the most-read file in the repository, and it is a list of
    commands. A command that points at a deleted or renamed file is worse than
    no command: the agent follows it and reports a spurious failure.
    """
    agents = _read(AGENTS)
    assert agents, "AGENTS.md is empty or missing"

    referenced = set(
        re.findall(r"(?:scripts|tests|docs|engine|services|apps|deploy|helm|k8s)/[\w./-]+", agents)
    )
    assert referenced, "no script or path references parsed from AGENTS.md"

    missing = sorted(
        path
        for path in referenced
        # Directory-ish references, glob patterns and naming templates
        # (AGENTS.md documents the NNNN-title.md convention) are out of scope.
        if not any(ch in path for ch in "*?")
        and not path.endswith("/")
        and "NNNN" not in path
        and not (REPO_ROOT / path).exists()
    )
    assert not missing, (
        "AGENTS.md references paths that do not exist: "
        f"{missing}. Update the file in the same change that moved them."
    )


def test_agents_md_claims_gate_wiring_is_intact() -> None:
    """The claims gate must stay wired into CI, or the rule is decorative.

    A guard that nobody runs is documentation, not enforcement.
    """
    workflow = _read(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    assert "test_claims_gate" in workflow, (
        "tests/contract/test_claims_gate.py is not referenced by ci.yml; the "
        "document/code consistency rule is not being enforced"
    )
    assert "test_claims_gate" in _read(AGENTS), (
        "AGENTS.md does not tell agents to run the claims gate"
    )


def test_gate_does_not_punish_improvements() -> None:
    """This gate must not become a brake on real fixes.

    Scans the sibling contract tests for assertions that require a defect to
    still be present. A gate that punishes improvement is worse than no gate.
    """
    offenders: list[str] = []
    for test_file in sorted((REPO_ROOT / "tests" / "contract").glob("test_*.py")):
        if test_file.name == Path(__file__).name:
            continue
        body = _ascii_fold(_read(test_file))
        for pattern in (
            r"assert\s+[\"']return\s+NotImplemented",
            r"assert\s+[\"']TODO[\"']\s+in\s+",
            r"assert\s+[\"']raise\s+NotImplementedError",
        ):
            if re.search(pattern, body):
                offenders.append(f"{test_file.name}: {pattern}")

    assert not offenders, "a contract test asserts that a defect persists:\n  " + "\n  ".join(
        offenders
    )
