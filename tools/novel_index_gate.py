#!/usr/bin/env python3
"""Novel-index readiness gate — the v3.1 §6.2 precondition (SB-06 / AR-03).

``docs/specs/ECO-NOJIN_MASTER_v3.1_UNIFIED.md`` §6.2 requires ten novel indices — FDII,
CDHE, CMSI, WSNI, RRI, IWEq, WAI, WVI, PSI, CW — none of which is implemented,
and states the precondition: *no index may be implemented or registered without
a published definition plus an independent reference anchor* (the FAO-56
Example 18 pattern). Implementing one earlier is an SB-06 violation.

This tool builds that gate, not the science. It

1. keeps the registry of the ten indices with their business roles (the roles
   are the ones recorded for the §6.2 requirement in
   ``reports/eco-nojin/SPEC-V3-CONFORMANCE-REPORT.md`` §3);
2. scans ``indicators/*.yaml`` and reports every file that declares a real
   ``indicator_id`` yet cannot demonstrate the precondition as
   ``BLOCKED_NO_PUBLISHED_DEFINITION`` — the template file (``_TEMPLATE.yaml``)
   and any file without a real ``indicator_id`` are exempt;
3. writes ``reports/eco-nojin/NOVEL-INDEX-READINESS.md``.

The precondition, checked per indicator card:

* ``reference`` must cite a published, independent source. A citation that is
  empty, or composed only of tautological self-references (``methodology``,
  ``project composite``, ``none``, the project's own name), fails.
* The card's evidence class must come from the honesty vocabulary in
  ``engine/honesty/statuses.py``. That module is the single source of truth and
  is read with :mod:`ast`, so this tool stays inside the standard library while
  still failing loudly if the vocabulary ever moves.
* ``validation_status: VALIDATED_EXTERNAL`` is only accepted when the reference
  cites a published source.

The gate derives a card's evidence class, it never invents one: an explicit
``evidence_class`` wins; otherwise the card's own ``validation_status`` is used
when it already is a vocabulary term; otherwise a published, non-tautological
reference anchors the conservative ``VALIDATED_METHOD_CONFORMANCE`` class. A
card whose evidence chain cannot be classified at all is unsupported.

Exit codes: 0 = no unsupported indicator file (the honest "nothing implemented
yet" state), 1 = at least one indicator file violates the precondition.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
INDICATOR_GLOB = "*.yaml"
TEMPLATE_PREFIX = "_"
REPORT_RELPATH = Path("reports") / "eco-nojin" / "NOVEL-INDEX-READINESS.md"

VIOLATION_CODE = "BLOCKED_NO_PUBLISHED_DEFINITION"
STATUS_SUPPORTED = "SUPPORTED"
STATUS_EXEMPT = "EXEMPT_TEMPLATE"
STATUS_BLOCKED = "BLOCKED"

METHOD_CONFORMANCE = "VALIDATED_METHOD_CONFORMANCE"
EXTERNAL_STATUS = "VALIDATED_EXTERNAL"

NOT_IMPLEMENTED_VERDICT = "NOT IMPLEMENTED — precondition not met (no published definition)"
PRECONDITION_MET_VERDICT = (
    "IMPLEMENTED — precondition met (published definition + independent reference anchor)"
)


@dataclass(frozen=True)
class NovelIndex:
    """One of the ten novel indices required by v3.1 §6.2."""

    code: str
    name: str
    role: str


#: The ten indices required by v3.1 §6.2, in the document's own order, each
#: with the business role recorded for it in the tree's §6.2 requirement audit
#: (``reports/eco-nojin/SPEC-V3-CONFORMANCE-REPORT.md`` §3, "v3.0 role" column).
NOVEL_INDICES: tuple[NovelIndex, ...] = (
    NovelIndex("FDII", "Flash Drought Intensity Index", "early warning in H2"),
    NovelIndex("CDHE", "Compound Drought-Heat Index", "crop risk / insurance in H1"),
    NovelIndex("CMSI", "Crop Multi-Stress Index", "supplier ranking H1/H7"),
    NovelIndex("WSNI", "Water-Soil Nexus Index", "supplier sustainability H5"),
    NovelIndex("RRI", "Restoration Readiness Index", "H7 service prioritisation"),
    NovelIndex("IWEq", "Intergenerational Water Equity", "ESG reporting H4"),
    NovelIndex("WAI", "Water Access Index", "irrigation priority regions"),
    NovelIndex("WVI", "Water Vulnerability Index", "supply-chain risk H2"),
    NovelIndex("PSI", "Production Stability Index", "supplier ranking"),
    NovelIndex("CW", "Cost of Water", "product pricing H6"),
)


@dataclass
class CardVerdict:
    """The §6.2 precondition verdict for one file in ``indicators/``."""

    path: Path
    indicator_id: str | None
    status: str
    violation: str | None
    evidence_class: str | None
    reasons: list[str] = field(default_factory=list)
    validation_status: str = ""
    reference: str = ""


@dataclass
class ScanResult:
    """Every card found under ``indicators/`` with its verdict."""

    directory: Path
    cards: list[CardVerdict]

    @property
    def violations(self) -> list[CardVerdict]:
        """The cards that violate the precondition (the gate's exit condition)."""
        return [card for card in self.cards if card.status == STATUS_BLOCKED]


# --------------------------------------------------------------------------
# A restricted YAML reader (stdlib only; the card contract is a small subset)
# --------------------------------------------------------------------------


class _Token(NamedTuple):
    indent: int
    text: str


_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*\s*:")


def _strip_comment(raw: str) -> str:
    """Drop a ``#`` comment that sits outside quotes."""
    quote: str | None = None
    for index, char in enumerate(raw):
        if quote is not None:
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            continue
        if char == "#" and (index == 0 or raw[index - 1] in " \t"):
            return raw[:index]
    return raw


def _tokenise(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip() or line.strip() in {"---", "..."}:
            continue
        leading = line[: len(line) - len(line.lstrip())]
        if "\t" in leading:
            raise ValueError("tab indentation is not valid YAML")
        tokens.append(_Token(len(leading), line.strip()))
    return tokens


def _scalar(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def parse_indicator_yaml(text: str) -> dict[str, Any]:
    """Parse the YAML subset used by the indicator cards.

    Supports block mappings, nested mappings, block sequences of scalars and of
    mappings (``- key: value`` with indented continuation lines), quoted and
    plain scalars, comments and blank lines. Anything outside the card contract
    (anchors, flow mappings, multi-line block scalars) raises ``ValueError``
    rather than being silently misread — an unreadable card cannot demonstrate
    the precondition.
    """
    tokens = _tokenise(text)
    if not tokens:
        return {}
    value, position = _parse_block(tokens, 0, tokens[0].indent)
    if position != len(tokens):
        raise ValueError(f"unparsed content near {tokens[position].text!r}")
    if not isinstance(value, dict):
        raise ValueError("an indicator card must be a YAML mapping")
    return value


def _parse_block(tokens: list[_Token], position: int, indent: int) -> tuple[Any, int]:
    if tokens[position].text.startswith("-"):
        return _parse_sequence(tokens, position, indent)
    return _parse_mapping(tokens, position, indent)


def _parse_mapping(tokens: list[_Token], position: int, indent: int) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while position < len(tokens) and tokens[position].indent == indent:
        text = tokens[position].text
        if text.startswith("- "):
            break
        key, separator, rest = text.partition(":")
        if not separator:
            raise ValueError(f"expected 'key: value', found {text!r}")
        key_text = _scalar(key)
        rest = rest.strip()
        position += 1
        if rest:
            mapping[key_text] = _scalar(rest)
        elif position < len(tokens) and tokens[position].indent > indent:
            mapping[key_text], position = _parse_block(tokens, position, tokens[position].indent)
        else:
            mapping[key_text] = None
    return mapping, position


def _parse_sequence(tokens: list[_Token], position: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    while position < len(tokens) and tokens[position].indent == indent:
        text = tokens[position].text
        if not text.startswith("-"):
            break
        after = text[1:].strip()
        position += 1
        if not after:
            if position < len(tokens) and tokens[position].indent > indent:
                value, position = _parse_block(tokens, position, tokens[position].indent)
                items.append(value)
            else:
                items.append(None)
            continue
        if _KEY_PATTERN.match(after):
            # "- key: value": the dash line is the first line of a mapping item,
            # so it is rewritten as a line of the item's own mapping block.
            tokens[position - 1] = _Token(indent + 2, after)
            value, position = _parse_block(tokens, position - 1, indent + 2)
            items.append(value)
        else:
            items.append(_scalar(after))
    return items, position


# --------------------------------------------------------------------------
# The precondition rules
# --------------------------------------------------------------------------

#: Words that never make a citation independent. A reference composed only of
#: these (plus a date or a filler word) points back at the project, or at
#: nothing — which is what the §6.2 "independent reference anchor" forbids.
TAUTOLOGY_TOKENS = frozenset(
    {
        "a",
        "an",
        "and",
        "composite",
        "eco",
        "house",
        "in",
        "internal",
        "methodology",
        "n/a",
        "nojin",
        "none",
        "of",
        "project",
        "reference",
        "referenced",
        "self",
        "tbd",
        "the",
        "todo",
        "اکو",
        "نوژین",
    }
)

_PUNCTUATION_PATTERN = re.compile(r"[^a-z0-9\u0600-\u06ff ]+")

PUBLISHED_SOURCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"https?://"),
    re.compile(r"\bdoi\.org/", re.IGNORECASE),
    re.compile(r"\b10\.\d{4,9}/"),
    re.compile(r"\b(?:1[5-9]\d{2}|20[0-2]\d)\b"),
    re.compile(r"\bNo\.\s*\d+"),
    re.compile(r"\b\d{1,3}:\d{2,}\b"),
    re.compile(
        r"\b(?:FAO|WMO|USDA|ISO|IPCC|NEH|AGU|AMS|Copernicus|WorldClim|CHIRPS|ERA5"
        r"|SoilGrids|WaPOR|SRTM|FABDEM)\b",
        re.IGNORECASE,
    ),
)

PLACEHOLDER_IDS = frozenset(
    {"", "-", "--", "example", "n/a", "none", "null", "placeholder", "tbd", "template", "todo"}
)


def _normalised_words(text: str) -> list[str]:
    return _PUNCTUATION_PATTERN.sub(" ", text.lower()).split()


def is_tautological_reference(citation: str) -> bool:
    """True when *citation* carries no independent published content.

    Empty citations fail, and so do citations composed only of self-referential
    boilerplate — the project's own ``methodology`` or ``composite``, the
    project's own name, or ``none``.
    """
    words = _normalised_words(citation)
    return not words or all(word in TAUTOLOGY_TOKENS for word in words)


def cites_published_source(citation: str, url: str = "") -> bool:
    """True when the citation (or its URL) names a published, external source.

    A heuristic on purpose: it recognises URLs, DOIs, author-year citations,
    standard designations (FAO-56, WMO No. 1090, ...) and the open-data
    programmes of the §6.3 catalogue. It is only consulted to decide whether a
    claimed ``VALIDATED_EXTERNAL`` status has an anchor; the primary rule is the
    non-tautology check above.
    """
    text = f"{citation} {url}".strip()
    return any(pattern.search(text) for pattern in PUBLISHED_SOURCE_PATTERNS)


def load_evidence_vocabulary(root: Path | None = None) -> tuple[str, ...]:
    """Read ``VOCABULARY`` from ``engine/honesty/statuses.py`` without importing it.

    The statuses module is the single source of truth for the evidence-class
    vocabulary; parsing it with :mod:`ast` keeps this tool stdlib-only while
    still failing loudly when the vocabulary moves or changes shape.
    """
    base = REPO_ROOT if root is None else root
    path = base / "engine" / "honesty" / "statuses.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if "VOCABULARY" in targets:
            return tuple(ast.literal_eval(node.value))
    raise ValueError(f"VOCABULARY not found in {path}")


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _is_real_indicator_id(value: str | None) -> bool:
    return bool(value) and value.strip().lower() not in PLACEHOLDER_IDS


def _citation_and_url(reference: Any) -> tuple[str, str]:
    if isinstance(reference, dict):
        return _text(reference.get("source")), _text(reference.get("url"))
    return _text(reference), ""


def check_indicator_card(path: Path, vocabulary: Sequence[str] | None = None) -> CardVerdict:
    """Check one indicator file against the §6.2 precondition."""
    terms = tuple(vocabulary) if vocabulary is not None else load_evidence_vocabulary()
    try:
        data = parse_indicator_yaml(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return CardVerdict(
            path=path,
            indicator_id=None,
            status=STATUS_BLOCKED,
            violation=VIOLATION_CODE,
            evidence_class=None,
            reasons=[f"unreadable or unparseable indicator card: {exc}"],
        )
    return _evaluate_card(path, data, terms)


def _evaluate_card(path: Path, data: dict[str, Any], vocabulary: tuple[str, ...]) -> CardVerdict:
    indicator_id = _text(data.get("indicator_id")) or None
    declared_class = _text(data.get("evidence_class"))
    validation_status = _text(data.get("validation_status"))
    citation, url = _citation_and_url(data.get("reference"))

    if path.name.startswith(TEMPLATE_PREFIX) or not _is_real_indicator_id(indicator_id):
        return CardVerdict(
            path=path,
            indicator_id=indicator_id,
            status=STATUS_EXEMPT,
            violation=None,
            evidence_class=declared_class or None,
            validation_status=validation_status,
            reference=citation,
            reasons=["template or placeholder file: carries no real indicator_id"],
        )

    reasons: list[str] = []
    if is_tautological_reference(citation):
        reasons.append(f"reference {citation!r} is not a published, independent citation")
    if validation_status == EXTERNAL_STATUS and not cites_published_source(citation, url):
        reasons.append("validation_status VALIDATED_EXTERNAL without a published reference")

    evidence_class: str | None = None
    if declared_class:
        if declared_class in vocabulary:
            evidence_class = declared_class
        else:
            reasons.append(f"evidence_class {declared_class!r} is outside the honesty vocabulary")
    elif validation_status in vocabulary:
        evidence_class = validation_status
    elif cites_published_source(citation, url):
        evidence_class = METHOD_CONFORMANCE
    else:
        reasons.append(
            "no evidence class can be established: declare evidence_class from the "
            "engine/honesty/statuses.py vocabulary, or cite a published reference"
        )

    return CardVerdict(
        path=path,
        indicator_id=indicator_id,
        status=STATUS_BLOCKED if reasons else STATUS_SUPPORTED,
        violation=VIOLATION_CODE if reasons else None,
        evidence_class=evidence_class,
        reasons=reasons,
        validation_status=validation_status,
        reference=citation,
    )


def scan_indicators(directory: Path, vocabulary: Sequence[str] | None = None) -> ScanResult:
    """Scan ``indicators/*.yaml`` and check every card with a real indicator_id."""
    terms = tuple(vocabulary) if vocabulary is not None else load_evidence_vocabulary()
    cards = [check_indicator_card(path, terms) for path in sorted(directory.glob(INDICATOR_GLOB))]
    return ScanResult(directory=directory, cards=cards)


# --------------------------------------------------------------------------
# The readiness report
# --------------------------------------------------------------------------


def _declares_index(indicator_id: str, code: str) -> bool:
    parts = re.split(r"[^A-Za-z0-9]+", indicator_id.lower())
    return code.lower() in parts


def find_novel_cards(result: ScanResult) -> dict[str, CardVerdict]:
    """Map each novel-index code to the card that declares it, if any."""
    found: dict[str, CardVerdict] = {}
    for index in NOVEL_INDICES:
        for card in result.cards:
            if card.indicator_id and _declares_index(card.indicator_id, index.code):
                found[index.code] = card
                break
    return found


def _count(result: ScanResult, status: str) -> int:
    return sum(1 for card in result.cards if card.status == status)


def summary_line(result: ScanResult, novel_cards: dict[str, CardVerdict] | None = None) -> str:
    """The one-line machine-readable verdict printed by the CLI and the report."""
    cards = novel_cards if novel_cards is not None else find_novel_cards(result)
    blocked = len(result.violations)
    return (
        f"SUMMARY novel_indices={len(NOVEL_INDICES)}"
        f" with_card={len(cards)}"
        f" cards_scanned={len(result.cards)}"
        f" supported={_count(result, STATUS_SUPPORTED)}"
        f" exempt={_count(result, STATUS_EXEMPT)}"
        f" blocked={blocked}"
        f" exit={1 if blocked else 0}"
    )


def render_readiness_report(result: ScanResult, as_of: date) -> str:
    """Render ``NOVEL-INDEX-READINESS.md`` for the scan in *result*."""
    novel_cards = find_novel_cards(result)
    lines: list[str] = []
    lines.append("# Novel-Index Readiness — the v3.1 §6.2 precondition")
    lines.append("")
    lines.append(f"Generated: {as_of.isoformat()} by `tools/novel_index_gate.py`.")
    lines.append("")
    lines.append("**Constitutional rule** (`docs/specs/ECO-NOJIN_MASTER_v3.1_UNIFIED.md` §6.2,")
    lines.append("SB-06 / AR-03): FDII · CDHE · CMSI · WSNI · RRI · IWEq · WAI · WVI · PSI · CW")
    lines.append("no novel index may be implemented or registered without a **published")
    lines.append("definition plus an independent reference anchor** (the FAO-56 Example 18")
    lines.append("pattern). An implementation before the precondition is met is an SB-06")
    lines.append("violation, so the ten `NOT IMPLEMENTED` rows below are the honest finding,")
    lines.append("not a failure.")
    lines.append("")
    lines.append("## 1. The ten novel indices")
    lines.append("")
    lines.append(
        "| Index | Name | Business role (§6.2) | Card in `indicators/` "
        "| `evidence_class` | Precondition verdict |"
    )
    lines.append("|---|---|---|---|---|---|")
    for index in NOVEL_INDICES:
        card = novel_cards.get(index.code)
        if card is None:
            has_card = "no"
            evidence_class = "—"
            verdict = NOT_IMPLEMENTED_VERDICT
        else:
            has_card = f"yes (`{card.path.name}`)"
            evidence_class = card.evidence_class or "—"
            verdict = (
                f"{VIOLATION_CODE} — {'; '.join(card.reasons)}"
                if card.status == STATUS_BLOCKED
                else PRECONDITION_MET_VERDICT
            )
        lines.append(
            f"| {index.code} | {index.name} | {index.role} | {has_card} "
            f"| {evidence_class} | {verdict} |"
        )
    lines.append("")
    lines.append("## 2. Indicator cards scanned in `indicators/`")
    lines.append("")
    lines.append(
        "| File | `indicator_id` | `validation_status` | `evidence_class` | Status | Notes |"
    )
    lines.append("|---|---|---|---|---|---|")
    for card in result.cards:
        if card.status == STATUS_BLOCKED:
            notes = "; ".join(card.reasons)
        elif card.status == STATUS_EXEMPT:
            notes = "template/placeholder — exempt from the gate"
        else:
            notes = f"published reference: {card.reference}" if card.reference else ""
        lines.append(
            f"| `{card.path.name}` | {card.indicator_id or '—'} "
            f"| {card.validation_status or '—'} | {card.evidence_class or '—'} "
            f"| {card.status} | {notes} |"
        )
    lines.append("")
    lines.append("## 3. Gate result")
    lines.append("")
    lines.append(
        f"- cards scanned: {len(result.cards)} "
        f"(supported {_count(result, STATUS_SUPPORTED)}, "
        f"template-exempt {_count(result, STATUS_EXEMPT)}, "
        f"blocked {len(result.violations)})"
    )
    lines.append(f"- novel indices with a card: {len(novel_cards)} of {len(NOVEL_INDICES)}")
    met = sum(
        1
        for index in NOVEL_INDICES
        if index.code in novel_cards and novel_cards[index.code].status == STATUS_SUPPORTED
    )
    lines.append(f"- novel indices meeting the precondition: {met} of {len(NOVEL_INDICES)}")
    lines.append("")
    lines.append("Exit rule: 0 when no unsupported indicator file exists (the template is exempt);")
    lines.append(f"1 when any indicator file is {VIOLATION_CODE}.")
    lines.append("")
    lines.append("```")
    lines.append(summary_line(result, novel_cards))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to gate")
    parser.add_argument(
        "--report",
        default=None,
        help="readiness report path (default: <root>/reports/eco-nojin/NOVEL-INDEX-READINESS.md)",
    )
    parser.add_argument("--date", default=None, help="report date as YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)

    root = Path(args.root)
    as_of = date.today() if args.date is None else date.fromisoformat(args.date)
    report_path = Path(args.report) if args.report else root / REPORT_RELPATH

    vocabulary = load_evidence_vocabulary(root)
    result = scan_indicators(root / "indicators", vocabulary)
    novel_cards = find_novel_cards(result)

    report = render_readiness_report(result, as_of)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    for card in result.cards:
        print(
            f"{card.status:<15} {card.path.name:<28} "
            f"{card.indicator_id or '-':<20} {card.evidence_class or '-'}"
        )
    for index in NOVEL_INDICES:
        card = novel_cards.get(index.code)
        if card is None:
            print(f"NOVEL    {index.code:<6} {NOT_IMPLEMENTED_VERDICT}")
        elif card.status == STATUS_BLOCKED:
            print(f"NOVEL    {index.code:<6} {VIOLATION_CODE}: {'; '.join(card.reasons)}")
        else:
            print(f"NOVEL    {index.code:<6} {PRECONDITION_MET_VERDICT} ({card.path.name})")
    print(summary_line(result, novel_cards))
    print(f"report: {report_path}")
    return 1 if result.violations else 0


if __name__ == "__main__":
    sys.exit(main())
