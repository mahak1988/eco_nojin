from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from engine import gateway as _gateway_module
from engine.gateway import ModelSpec


class ModelStatus(StrEnum):
    """Structured status for one dimension of a registered model.

    The registry never asserts one of these by hand. Every value is either
    parsed from a model card's markdown, folded from the validation runner's
    own ``CaseOutcome`` records, or derived from the gateway's dispatch wiring:

    * ``STUB``
        Declared, but no implementation ships. Parsed from the card's
        implementation line (e.g. ``engine/models/cards/CANON-014_model_registry.md:89``).
    * ``IMPLEMENTED``
        An implementation exists and corresponds to the design; no independent
        check has been run. Card line "Production ..." / "Implementation matches
        design", or a gateway-unwired model that still has an implementation.
    * ``TESTED``
        Verified against an independent reference: analytic solution, published
        tables, or C++/Python parity. Card line "Verified ...".
    * ``VALIDATED``
        Matches reference/scientific truth with evidence: the card's own
        "Validated against ..." claim, or a validation-corpus ``match``.
    * ``BLOCKED``
        A check could not be completed or is contradicted: the model is
        registered but the gateway has no dispatch branch for it, or a corpus
        case is internally contradictory.
    * ``UNVERIFIED``
        No verification evidence and no claim: the default, and what a card
        reads when it says "Cannot verify at runtime" or "scientific review
        pending".
    * ``UNVALIDATED``
        No reference data, or no wired comparison against the reference data
        that exists. This is what a model with no card and no corpus ``match``
        must read -- an absent check is never reported as a passed one.
    * ``FAILED``
        The implementation disagrees with a stored value that is itself
        reproducible from a cited equation (a validation-corpus ``mismatch``).

    The ``str`` mixin keeps the values JSON-safe for reports without a custom
    encoder; ``.value`` is the canonical wire form.
    """
    STUB = "stub"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    VALIDATED = "validated"
    BLOCKED = "blocked"
    UNVERIFIED = "unverified"
    UNVALIDATED = "unvalidated"
    FAILED = "failed"


#: The eight fields ``ModelSpec`` itself declares, in declaration order. Used to
#: copy a plain ``ModelSpec`` into a :class:`RegisteredModelSpec` and to compare
#: the two without letting the added status fields change the answer.
_MODELSPEC_FIELDS: tuple[str, ...] = (
    "model_id",
    "model_version",
    "model_name",
    "model_type",
    "domain",
    "purpose",
    "assumptions",
    "limitations",
)

#: Relative strength of the statuses, used where two evidence sources disagree.
#: A failed or blocked check outranks a claim of success, which outranks the
#: absence of evidence. See :meth:`_fold_validation_status`.
_STATUS_STRENGTH: tuple[ModelStatus, ...] = (
    ModelStatus.STUB,
    ModelStatus.UNVERIFIED,
    ModelStatus.UNVALIDATED,
    ModelStatus.IMPLEMENTED,
    ModelStatus.VALIDATED,
    ModelStatus.TESTED,
    ModelStatus.BLOCKED,
    ModelStatus.FAILED,
)


def _stronger(left: ModelStatus, right: ModelStatus) -> ModelStatus:
    """The status that represents the weaker evidence of the two.

    A model that is both "Validated" (per its card) and "not_run" (per the
    corpus) has not demonstrated anything new; a model that is "Validated" and
    "mismatch" is failed. Absence of evidence never promotes a status, and a
    blocker never demotes one below what the blocker itself says.
    """
    return right if _STATUS_STRENGTH.index(right) > _STATUS_STRENGTH.index(left) else left


@dataclass(eq=False)
class RegisteredModelSpec(ModelSpec):
    """A :class:`~engine.gateway.ModelSpec` that also carries structured status.

    ``ModelSpec`` is declared in the gateway (``engine/gateway/__init__.py:90-100``)
    and is outside this module's scope, so the status fields are declared here on
    a subclass. :meth:`ModelRegistry.register` upgrades a plain ``ModelSpec`` to
    this subclass, so every stored spec answers ``implementation_status`` and
    friends while remaining a ``ModelSpec`` for every existing consumer -- the
    gateway dispatch reads ``model_id``/``model_type`` only
    (``engine/gateway/__init__.py:960-989``).

    The three status fields default to ``UNVERIFIED`` so that a spec registered
    without any evidence reads as unverified rather than as verified. Seeding
    (:func:`_seed_status_from_cards`) then lowers ``validation_status`` to
    ``UNVALIDATED`` where there is no reference data at all.

    Extra, non-status bookkeeping:

    ``status_reasons``
        Why each status is what it is, in one line, naming its source.
    ``status_evidence``
        The verbatim source text: the card's own status line, the corpus fold
        line, or the gateway-wiring note.
    ``card_file``
        Card filename the statuses were parsed from, or ``None``.
    ``gateway_wired``
        Whether static analysis found a dispatch branch for this model id.
    """

    implementation_status: ModelStatus = ModelStatus.UNVERIFIED
    verification_status: ModelStatus = ModelStatus.UNVERIFIED
    validation_status: ModelStatus = ModelStatus.UNVERIFIED
    status_reasons: dict[str, str] = field(default_factory=dict)
    status_evidence: dict[str, str] = field(default_factory=dict)
    card_file: str | None = None
    gateway_wired: bool | None = None

    def __eq__(self, other: object) -> bool:
        """Compare the eight ``ModelSpec`` fields against any ``ModelSpec``.

        A dataclass-generated ``__eq__`` would refuse to compare against a plain
        ``ModelSpec`` (different class), silently turning existing
        ``spec == other`` code from true into false now that the registry stores
        this subclass. Status fields are deliberately excluded: they are
        registry bookkeeping, not part of the spec's identity.
        """
        if isinstance(other, ModelSpec):
            return all(
                getattr(self, name) == getattr(other, name) for name in _MODELSPEC_FIELDS
            )
        return NotImplemented

    def as_status_dict(self) -> dict[str, Any]:
        """The machine-readable status record for this model (JSON-safe)."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "domain": self.domain,
            "model_version": self.model_version,
            "implementation_status": self.implementation_status.value,
            "verification_status": self.verification_status.value,
            "validation_status": self.validation_status.value,
            "card_file": self.card_file,
            "gateway_wired": self.gateway_wired,
            "status_reasons": dict(self.status_reasons),
            "status_evidence": dict(self.status_evidence),
        }


# ---------------------------------------------------------------------------
# Card parsing
# ---------------------------------------------------------------------------

#: Where the cards live: ``engine/models/cards/<model_id>_<slug>.md``.
CARDS_DIR = Path(__file__).resolve().parent / "cards"

#: The three status rows of card section 9 ("Implementation & Traceability").
#: Field format is fixed by ``engine/models/cards/_template.md:95-97``:
#:   | **implementation_status** *(required)* | `[e.g. Production, Verified, ...]` |
#: A real card writes them without the ``*(required)*`` marker, e.g.
#: ``engine/models/cards/CANON-001_penman_monteith_et0.md:89-91``.
_CARD_STATUS_ROW = re.compile(
    r"^\|\s*\*\*(?P<field>implementation_status|verification_status|validation_status)"
    r"\*\*\s*\|\s*(?P<text>[^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
_CARD_MODEL_ID_ROW = re.compile(r"^\|\s*\*\*model_id\*\*\s*\|\s*`?([^`|\s]+)`?\s*\|\s*$", re.M)

#: ``S-*`` cards document C++ symbols, not registry ids; see
#: ``_card_index`` for how they are still used as a corpus link.
_TEMPLATE_CARDS = frozenset({"_template.md"})


def _pattern(*phrases: str) -> re.Pattern[str]:
    """Case-insensitive whole-phrase matcher for the rule tables below."""
    return re.compile("|".join(phrases), re.IGNORECASE)


# Card-parsing rules. Each table is ordered and the FIRST matching rule decides
# the status, so absence/negation phrases are listed before positive ones: a
# line that mixes a claim with a caveat must be read by its caveat, not by its
# claim. The "evidence" column names the shipped card lines each rule fires on.

#: implementation_status: does an implementation ship at all?
_IMPLEMENTATION_RULES: tuple[tuple[re.Pattern[str], ModelStatus], ...] = (
    (
        _pattern(r"\bstub\b", r"does not exist", r"not implemented", r"placeholder"),
        ModelStatus.STUB,
    ),  # CANON-014_model_registry.md:89
    (
        _pattern(r"\bproduction\b", r"\bimplemented\b", r"reference only", r"reference data"),
        ModelStatus.IMPLEMENTED,
    ),  # CANON-001:89 "Production", CANON-018:89 "Reference only", CANON-019:89 "Reference data"
)

#: verification_status: has the implementation been checked against something
#: independent of itself?
_VERIFICATION_RULES: tuple[tuple[re.Pattern[str], ModelStatus], ...] = (
    (
        _pattern(r"\bstub\b", r"does not exist", r"does not function"),
        ModelStatus.STUB,
    ),  # CANON-014_model_registry.md:90
    (
        _pattern(r"cannot verify", r"not executable", r"cannot be executed", r"cannot be run"),
        ModelStatus.UNVERIFIED,
    ),  # S-006_hargreaves_et0.md:87, S-009..S-014:87 "Cannot verify at runtime"
    (
        _pattern(r"not applicable", r"\bn/a\b"),
        ModelStatus.UNVERIFIED,
    ),  # CANON-018_cmip6_climate.md:90 "Not applicable - data service"
    (
        _pattern(r"\bverified\b", r"\bverifies\b"),
        ModelStatus.TESTED,
    ),  # CANON-001:90 "Verified - matches FAO-56 reference day"; CANON-019:90 "Verified by NASA"
    (
        _pattern(r"implementation matches design", r"implementation exists"),
        ModelStatus.IMPLEMENTED,
    ),  # CANON-002_hargreaves_et0.md:90, CANON-003_thornthwaite_pet.md:90
)

#: validation_status: is there reference/scientific-truth evidence?
_VALIDATION_RULES: tuple[tuple[re.Pattern[str], ModelStatus], ...] = (
    (
        _pattern(
            r"not validated",
            r"cannot validate",
            r"not\s+(?:independently\s+)?benchmarked",
            r"not applicable",
            r"\bn/a\b",
        ),
        ModelStatus.UNVALIDATED,
    ),  # CANON-018:91, S-009..S-014:91, CANON-007:91 "LS factor not independently benchmarked"
    (
        _pattern(r"framework validated"),
        ModelStatus.UNVALIDATED,
    ),  # S-008_rusle_soil_loss.md:91 - the framework is validated, the model is not
    (
        _pattern(r"\bvalidated\b", r"\bbenchmarked\b", r"\bmatches\b"),
        ModelStatus.VALIDATED,
    ),  # CANON-001:91 "Validated against", CANON-009:91 "Benchmarked", S-001:91 "Matches"
)

_FIELD_RULES: dict[str, tuple[tuple[re.Pattern[str], ModelStatus], ...]] = {
    "implementation_status": _IMPLEMENTATION_RULES,
    "verification_status": _VERIFICATION_RULES,
    "validation_status": _VALIDATION_RULES,
}

#: Default when a status line exists but matches no rule. Never guessed upward:
#: an unrecognised claim is reported as absent evidence.
_FIELD_DEFAULT: dict[str, ModelStatus] = {
    "implementation_status": ModelStatus.UNVERIFIED,
    "verification_status": ModelStatus.UNVERIFIED,
    "validation_status": ModelStatus.UNVALIDATED,
}


def _classify(field_name: str, text: str) -> ModelStatus:
    """Map one card status line to a :class:`ModelStatus` via the rule tables."""
    for pattern, status in _FIELD_RULES[field_name]:
        if pattern.search(text):
            return status
    return _FIELD_DEFAULT[field_name]


def _read_card(path: Path) -> dict[str, Any] | None:
    """Parse one card's ``model_id`` and its three section-9 status lines.

    Returns ``None`` for a file that is not a model card (the template, or
    anything without a ``model_id`` row), so an unrelated markdown file dropped
    into the directory is ignored rather than guessed at.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if path.name in _TEMPLATE_CARDS:
        return None
    model_id_match = _CARD_MODEL_ID_ROW.search(text)
    if model_id_match is None:
        return None
    statuses = {m.group("field"): m.group("text").strip() for m in _CARD_STATUS_ROW.finditer(text)}
    if not statuses:
        return None
    stem = path.stem
    slug_part = stem.split("_", 1)[1] if "_" in stem else stem
    return {
        "path": path,
        "model_id": model_id_match.group(1),
        "slug_tokens": tuple(slug_part.split("_")),
        "statuses": statuses,
    }


def _card_index() -> dict[str, Any]:
    """Every card in ``engine/models/cards/``, keyed for the two lookups.

    Two indices come out of this, both derived from artifacts rather than
    hand-written: ``by_model_id`` (the card's own ``model_id`` row, which is
    what section 9's status lines describe) and ``by_slug_tokens`` (the card
    filename slug, which is how the validation corpus names its models -- the
    corpus case files are ``engine/hydroma/models/validation/test_cases/<slug>.yaml``
    and each declares ``model: <slug>``). ``by_slug_tokens`` maps to a *list*
    because several cards can share one slug -- ``CANON-001_penman_monteith_et0.md``
    and ``S-007_penman_monteith_et0.md`` are the same model seen from the
    registry and from the C++ symbol table.
    """
    cards: list[dict[str, Any]] = []
    if CARDS_DIR.is_dir():
        for path in sorted(CARDS_DIR.glob("*.md")):
            card = _read_card(path)
            if card is not None:
                cards.append(card)
    by_slug_tokens: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for card in cards:
        by_slug_tokens.setdefault(card["slug_tokens"], []).append(card)
    return {
        "cards": cards,
        "by_model_id": {c["model_id"]: c for c in cards},
        "by_slug_tokens": by_slug_tokens,
    }


def _cards_for_corpus_slug(index: dict[str, Any], slug: str) -> list[dict[str, Any]]:
    """Cards whose filename slug starts with the corpus's model slug.

    ``scs_cn`` (``test_cases/scs_cn.yaml``) must reach
    ``CANON-004_scs_cn_runoff.md``, and ``penman_monteith`` must reach both
    ``CANON-001_penman_monteith_et0.md`` and ``S-007_penman_monteith_et0.md``.
    Matching on the underscore-separated token prefix -- not on substrings --
    keeps ``fao56_dual_kc`` from matching ``S-010_fao56_net_radiation.md``.
    """
    wanted = tuple(slug.split("_"))
    matched: list[dict[str, Any]] = []
    for tokens, cards in index["by_slug_tokens"].items():
        if tokens[: len(wanted)] == wanted:
            matched.extend(cards)
    return matched


# ---------------------------------------------------------------------------
# Gateway wiring (static analysis)
# ---------------------------------------------------------------------------

#: The message a registered id carries when the gateway has no dispatch
#: branch for it in the shape this registry's scanner models. See
#: :func:`_gateway_dispatch_literals` for what that shape is, and
#: :func:`_gateway_route_targets` for the table the same gateway routes
#: those ids through at runtime.
#:
#: The wording is deliberately about the scanner, not about the gateway:
#: since 2026-10-10 the gateway routes these ids through a dispatch *table*
#: (``engine/gateway/__init__.py::_ROUTES_FOR_REGISTERED_IDS``), which the
#: AST scan above cannot see because it is a ``dict.get`` lookup rather than
#: an ``if model_id ==``/``startswith`` branch. An older text claimed the
#: gateway "raises NotImplementedError for this id", which stopped being
#: true for every id the table holds; ``_overlay_gateway_wiring`` names the
#: actual target instead.
_UNWIRED_REASON = (
    "registered but not wired to a dispatch branch the registry's scanner "
    "models (engine/models/registry.py::_gateway_dispatch_literals reads "
    "``if model_id ==`` and ``model_id.startswith`` branches only)"
)


def _gateway_dispatch_literals() -> dict[str, Any]:
    """The model ids and prefixes the gateway's dispatch can actually route.

    Static analysis of the AST of ``engine/gateway/__init__.py``, not a
    hand-kept list: ``EngineGateway._dispatch_by_type`` routes by comparing
    ``model_id`` against string literals -- ``if model_id == "X"``
    (e.g. line 1006 ``ROTHTC_TEMP_FACTOR``), ``if model_id in ("A", "B")``
    (line 998 ``CANON-001..003`` + ``CANON-011_RAD``, line 1403
    ``WATERSHED_STRUCT`` + ``CANON-015``) -- and ``model_id.startswith(<prefix>)``
    routes whole families (lines 1793-1839: EWSI, HYRUE, ECSI, EPIA, HDVI, ESRI,
    HLHS, HPheno). Anything else falls through to the NotImplementedError at
    line 1841. Adding or removing a branch changes what this function sees, so
    the unwired set stays falsifiable instead of drifting.
    """
    source_file = getattr(_gateway_module, "__file__", None)
    result: dict[str, Any] = {
        "source": str(source_file) if source_file else None,
        "equality": [],
        "prefixes": [],
        "unavailable_reason": None,
    }
    if not source_file:
        result["unavailable_reason"] = "engine.gateway has no source file"
        return result
    try:
        tree = ast.parse(Path(source_file).read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:  # pragma: no cover - unreadable source
        result["unavailable_reason"] = f"{type(exc).__name__}: {exc}"
        return result

    equality: set[str] = set()
    prefixes: set[str] = set()

    def _str(node: ast.AST) -> str | None:
        """The string value of a constant AST node, else ``None``."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    for node in ast.walk(tree):
        # `model_id == "X"` / `model_id in ("A", "B")` route one id or a family.
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name):
            if node.left.id != "model_id":
                continue
            for op, comparator in zip(node.ops, node.comparators, strict=True):
                if isinstance(op, ast.In) and isinstance(
                    comparator, (ast.Tuple, ast.List, ast.Set)
                ):
                    equality.update(
                        v for v in (_str(e) for e in comparator.elts) if v is not None
                    )
                elif isinstance(op, (ast.Eq, ast.In)):
                    literal = _str(comparator)
                    if literal is not None:
                        equality.add(literal)
        # `model_id.startswith("X")` routes a whole family by prefix.
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "startswith"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "model_id"
            and node.args
        ):
            literal = _str(node.args[0])
            if literal is not None:
                prefixes.add(literal)

    result["equality"] = sorted(equality)
    result["prefixes"] = sorted(prefixes)
    return result


def _unwired_model_ids(dispatch: dict[str, Any], model_ids: list[str]) -> list[str]:
    """Registered ids that no gateway dispatch branch can route.

    An id is wired when the gateway compares ``model_id`` to it for equality, or
    when a ``startswith`` prefix covers it. Everything else reaches the
    NotImplementedError at ``engine/gateway/__init__.py:1841-1845``.

    This is a statement about the scan's shape, not about the gateway's
    behaviour: ids routed through the gateway's dispatch *table* are not
    visible here. :func:`_gateway_route_targets` reads the table for the
    status fields, and ``engine/tests/test_registry_status.py`` pins this
    list so the two views cannot drift silently.
    """
    if dispatch.get("unavailable_reason"):
        return []
    equality = set(dispatch["equality"])
    prefixes = tuple(dispatch["prefixes"])
    unwired = [
        model_id
        for model_id in model_ids
        if model_id not in equality and not model_id.startswith(prefixes)
    ]
    return sorted(unwired)


# ---------------------------------------------------------------------------
# Validation-corpus folding
# ---------------------------------------------------------------------------

#: Aggregation across a model's cases: the weakest-evidence status wins, so one
#: reproducible ``mismatch`` fails the model, one unsatisfiable
#: ``inconsistent_case`` blocks it, a ``match`` validates it, and "nothing ran"
#: stays unvalidated. This is evidence, not a vote: a single case per bucket is
#: enough, because the buckets are not equally strong (see ``_STATUS_STRENGTH``).
_CASE_STATUS_MAP: dict[str, ModelStatus] = {
    "match": ModelStatus.VALIDATED,
    "mismatch": ModelStatus.FAILED,
    "inconsistent_case": ModelStatus.BLOCKED,
    "not_run": ModelStatus.UNVALIDATED,
}

#: Why a corpus case did not run, in the runner's own words
#: (``engine/hydroma/models/validation/runner.py``: "No implementation is wired
#: for this case", and ``_run_reference_only``: "no stored .npy reference and no
#: wired implementation").
_NOT_RUN_REASON = "no wired implementation / no stored reference"


def _normalise_runner_output(runner_output: Any) -> list[dict[str, Any]]:
    """Accept either the runner's summary dict or a list of ``CaseOutcome``.

    ``engine.hydroma.models.validation.runner.machine_summary()`` returns
    ``{"counts": ..., "models": {slug: {"outcomes": [...]}}}``; ``run_all()``
    returns ``CaseOutcome`` objects. Both are accepted so a caller can fold a
    live run or a stored report without re-running the corpus.
    """
    records: list[dict[str, Any]] = []
    if isinstance(runner_output, dict):
        for slug, bucket in (runner_output.get("models") or {}).items():
            for outcome in bucket.get("outcomes") or []:
                record = dict(outcome)
                record.setdefault("model", slug)
                records.append(record)
        return records
    for outcome in runner_output or []:
        if isinstance(outcome, dict):
            record = dict(outcome)
        else:
            record = {
                "model": getattr(outcome, "model", None),
                "name": getattr(outcome, "name", None),
                "status": getattr(outcome, "status", None),
                "detail": getattr(outcome, "detail", ""),
                "measured": getattr(outcome, "measured", None),
                "expected": getattr(outcome, "expected", None),
                "contradictions": list(getattr(outcome, "contradictions", []) or []),
            }
        records.append(record)
    return [r for r in records if isinstance(r.get("status"), str)]


def _fold_validation_status(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Fold one model's corpus records into a single validation status.

    Every case status is first mapped through :data:`_CASE_STATUS_MAP` and then
    combined with :func:`_stronger`, so the aggregate is the weakest-evidence
    status present: ``FAILED`` (the implementation disagrees with a reproducible
    stored value) outranks ``BLOCKED`` (the case is unsatisfiable), which
    outranks ``VALIDATED`` (a match), which outranks ``UNVALIDATED`` (nothing
    ran). An unknown case status is treated as no evidence rather than guessed.
    """
    counts: dict[str, int] = {}
    aggregate = ModelStatus.UNVALIDATED
    for record in records:
        case_status = record["status"]
        counts[case_status] = counts.get(case_status, 0) + 1
        aggregate = _stronger(
            aggregate, _CASE_STATUS_MAP.get(case_status, ModelStatus.UNVALIDATED)
        )

    reasons: list[str] = []
    evidence: dict[str, Any] = {"by_status": counts, "cases": len(records)}
    if counts.get("mismatch"):
        mismatches = [r for r in records if r["status"] == "mismatch"]
        evidence["mismatch"] = [
            {
                "case": r.get("name"),
                "measured": r.get("measured"),
                "expected": r.get("expected"),
                "detail": r.get("detail", ""),
            }
            for r in mismatches
        ]
        reasons.append(
            f"{len(mismatches)} case(s) disagree with a reproducible stored value "
            "(mismatch: the implementation is wrong; measured/expected recorded)"
        )
    if counts.get("inconsistent_case"):
        blocked = [r for r in records if r["status"] == "inconsistent_case"]
        evidence["inconsistent_case"] = [
            {
                "case": r.get("name"),
                "contradictions": list(r.get("contradictions") or []),
                "detail": r.get("detail", ""),
            }
            for r in blocked
        ]
        reasons.append(
            f"{len(blocked)} case(s) are internally contradictory "
            "(contradictions recorded; no correct implementation can satisfy them)"
        )
    if counts.get("match"):
        matched = [r for r in records if r["status"] == "match"]
        evidence["match"] = [
            {
                "case": r.get("name"),
                "measured": r.get("measured"),
                "expected": r.get("expected"),
                "detail": r.get("detail", ""),
            }
            for r in matched
        ]
        reasons.append(f"{len(matched)} case(s) match the stored reference value")
    if counts.get("not_run"):
        reasons.append(
            f"{counts['not_run']} case(s) not run: {_NOT_RUN_REASON}"
        )

    return {
        "status": aggregate,
        "counts": counts,
        "cases": len(records),
        "reason": "; ".join(reasons) if reasons else "no corpus cases",
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def _seed_status_from_cards(registry: ModelRegistry) -> dict[str, Any]:
    """Parse every card's three status lines into the registry's status fields.

    A model with a card gets its three statuses from that card's section 9.
    A model without a card keeps the ``UNVERIFIED`` defaults, except that
    ``validation_status`` is lowered to ``UNVALIDATED``: there is no reference
    data on file for it, and an absent check must never read as a passed one.

    The card's own words are kept verbatim in ``status_evidence`` so a mapped
    status can always be checked against the sentence it came from.
    """
    index = _card_index()
    by_model_id = index["by_model_id"]
    stats: dict[str, Any] = {"card_models": 0, "unmapped_cards": [], "no_card_models": 0}
    for spec in registry.all():
        if not isinstance(spec, RegisteredModelSpec):  # pragma: no cover - register() upgrades
            continue
        card = by_model_id.get(spec.model_id)
        if card is None:
            stats["no_card_models"] += 1
            spec.validation_status = ModelStatus.UNVALIDATED
            spec.status_reasons["validation_status"] = (
                "no model card on file: no reference data, so no validation claim"
            )
            continue
        stats["card_models"] += 1
        spec.card_file = card["path"].name
        for field_name in _FIELD_RULES:
            text = card["statuses"].get(field_name)
            if text is None:
                continue
            status = _classify(field_name, text)
            setattr(spec, field_name, status)
            spec.status_reasons[field_name] = (
                f"card engine/models/cards/{card['path'].name} {field_name} row"
            )
            spec.status_evidence[field_name] = text
    for model_id in sorted(by_model_id):
        if registry.get(model_id) is None:
            stats["unmapped_cards"].append(model_id)
    return stats


def _gateway_route_targets() -> dict[str, str]:
    """Where the gateway's dispatch table actually routes each id.

    ``engine/gateway/__init__.py`` routes the ids in ``_ROUTE_TARGETS``
    through a table lookup (``_ROUTES_FOR_REGISTERED_IDS.get(model_id)``), so
    the AST scan in :func:`_gateway_dispatch_literals` cannot see them. This
    function asks the gateway module itself rather than re-parsing its
    source, so the registry's status fields can name the implementation a
    request actually reaches instead of repeating a claim the gateway made
    false.

    Returns an empty mapping when the gateway exposes no table (an older
    revision), which leaves :func:`_overlay_gateway_wiring` saying only what
    the scan can prove.
    """
    targets = getattr(_gateway_module, "_ROUTE_TARGETS", None)
    if not isinstance(targets, dict):
        return {}
    return {str(key): str(value) for key, value in targets.items()}


def _overlay_gateway_wiring(registry: ModelRegistry, dispatch: dict[str, Any]) -> dict[str, Any]:
    """Flag the registered ids the gateway cannot dispatch as BLOCKED.

    The 14 ids are not guessed: they are the registry's own ids minus the
    literals and prefixes found by static analysis of the gateway's dispatch
    branches (see :func:`_gateway_dispatch_literals`). Each one keeps whatever
    implementation the card documents -- it is registered, so an implementation
    exists.

    Where the gateway's dispatch table (see :func:`_gateway_route_targets`)
    routes an id at runtime, the reason and the evidence say so and name the
    computation it reaches; those ids read IMPLEMENTED, because they can be
    exercised. Only an id with no route target at all stays BLOCKED: that is
    the honest reading -- a status field that claims the gateway raises for an
    id it no longer raises for is the kind of stale claim this registry exists
    to correct, and so is the inverse (BLOCKED for an id that answers).

    The card's own verification claim is preserved in ``status_evidence``.
    """
    unwired = _unwired_model_ids(dispatch, registry.list_ids())
    route_targets = _gateway_route_targets()
    for model_id in unwired:
        spec = registry.get(model_id)
        if spec is None:  # pragma: no cover - list_ids() and get() agree
            continue
        if not isinstance(spec, RegisteredModelSpec):  # pragma: no cover
            continue
        if spec.card_file is not None:
            # Keep what the card claimed, so the override is auditable.
            spec.status_evidence["card_verification_status"] = spec.verification_status.value
        spec.implementation_status = ModelStatus.IMPLEMENTED
        target = route_targets.get(model_id)
        if target is None:
            spec.verification_status = ModelStatus.BLOCKED
            spec.gateway_wired = False
            spec.status_reasons["implementation_status"] = _UNWIRED_REASON
            spec.status_reasons["verification_status"] = (
                "registered but not wired to a computation handler: the gateway raises "
                "NotImplementedError for this id, so no runtime check can be made"
            )
            spec.status_evidence["gateway_wiring"] = _UNWIRED_REASON
        else:
            spec.verification_status = ModelStatus.IMPLEMENTED
            spec.gateway_wired = True
            spec.status_reasons["implementation_status"] = (
                f"{_UNWIRED_REASON}; routed at runtime through the gateway's "
                f"dispatch table (engine/gateway/__init__.py::"
                f"_ROUTES_FOR_REGISTERED_IDS) to {target}"
            )
            spec.status_reasons["verification_status"] = (
                "registered and routed at runtime through the gateway's dispatch "
                f"table to {target}; the registry's static scanner models only "
                "if/startswith branches, so it cannot see the table by itself — "
                "the wiring overlay asks the gateway module instead"
            )
            spec.status_evidence["gateway_wiring"] = (
                f"routed via engine/gateway/__init__.py::_ROUTES_FOR_REGISTERED_IDS "
                f"to {target}"
            )
            spec.status_evidence["gateway_dispatch"] = target
    for model_id in registry.list_ids():
        spec = registry.get(model_id)
        if isinstance(spec, RegisteredModelSpec) and spec.gateway_wired is None:
            spec.gateway_wired = model_id not in set(unwired)
    return {
        "unwired": unwired,
        "wired": [m for m in registry.list_ids() if m not in set(unwired)],
        "analysis": dispatch,
    }


@dataclass
class ModelRegistry:
    """Model Registry - canonical registry for all scientific models.

    This registry is the single source of truth for model discovery and metadata.
    It maps model_id to ModelSpec for use by the Engine Gateway.

    Beyond the ``ModelSpec`` fields, every registered model carries a structured
    status (implementation / verification / validation) seeded from its card,
    folded from the validation runner's own records, and checked against the
    gateway's dispatch wiring. See :class:`ModelStatus` for the vocabulary and
    :meth:`status_summary` for the machine-readable export.
    """

    _models: dict[str, ModelSpec] = field(default_factory=dict)
    _cards: dict[str, Any] = field(default_factory=dict)
    _gateway_dispatch: dict[str, Any] = field(default_factory=dict)
    _unwired: list[str] = field(default_factory=list)
    _validation_fold: dict[str, Any] = field(default_factory=dict)
    _seeded: bool = False

    def register(self, model: ModelSpec) -> None:
        """Register a model specification.

        A plain ``ModelSpec`` is stored as a :class:`RegisteredModelSpec`, which
        adds the status fields with their ``UNVERIFIED`` defaults. The eight
        ``ModelSpec`` fields are copied unchanged, the stored object is still a
        ``ModelSpec``, and ``==`` against a plain ``ModelSpec`` still compares
        those eight fields only.
        """
        spec: ModelSpec
        if isinstance(model, RegisteredModelSpec):
            spec = model
        elif isinstance(model, ModelSpec):
            spec = RegisteredModelSpec(
                **{name: getattr(model, name) for name in _MODELSPEC_FIELDS}
            )
        else:  # pragma: no cover - duck-typed spec from outside the engine
            spec = model
        self._models[model.model_id] = spec

    def get(self, model_id: str) -> ModelSpec | None:
        """Get a model specification by ID."""
        return self._models.get(model_id)

    def list_ids(self) -> list[str]:
        """List all registered model IDs."""
        return list(self._models.keys())

    def all(self) -> list[ModelSpec]:
        """Get all registered model specifications."""
        return list(self._models.values())

    def status_of(self, model_id: str) -> dict[str, ModelStatus] | None:
        """The three structured statuses of one model, or ``None`` if unknown.

        Returned as a mapping keyed by field name so a caller cannot confuse
        the implementation dimension with the validation one.
        """
        spec = self._models.get(model_id)
        if spec is None:
            return None
        return dict(zip(_FIELD_RULES, _status_triple(spec), strict=True))

    def seed_status(self) -> None:
        """Seed structured status from the cards and the gateway wiring.

        Idempotent: the global registry calls this once after populating, and a
        caller may call it again after registering more models. Re-seeding
        re-reads the cards and re-analyses the gateway source, so a stale value
        is overwritten by the current artifact rather than accumulated.
        """
        cards = _seed_status_from_cards(self)
        dispatch = _gateway_dispatch_literals()
        wiring = _overlay_gateway_wiring(self, dispatch)
        self._cards = cards
        self._gateway_dispatch = dispatch
        self._unwired = list(wiring["unwired"])
        self._seeded = True

    def attach_validation_results(self, runner_output: Any) -> dict[str, Any]:
        """Fold the validation runner's own records into ``validation_status``.

        ``runner_output`` is the dict from
        ``engine.hydroma.models.validation.runner.machine_summary()``, or a list
        of ``CaseOutcome`` objects from ``run_all()``.

        Per model, the weakest-evidence case status decides
        (``mismatch`` > ``inconsistent_case`` > ``match`` > ``not_run``):

        ====================  ==========================================
        corpus status          registry status
        ====================  ==========================================
        ``match``             ``VALIDATED``
        ``mismatch``          ``FAILED`` (measured/expected recorded)
        ``inconsistent_case`` ``BLOCKED`` (contradictions recorded)
        ``not_run``           ``UNVALIDATED`` -- no wired implementation /
                               no stored reference
        ====================  ==========================================

        The fold is applied to the registered models the corpus cases belong to
        (linked by card filename slug -- see :func:`_cards_for_corpus_slug`).
        A corpus result overrides the card's claim, because a run is evidence
        and a claim is not; the card's own words stay in ``status_evidence``.
        Models the corpus covers but the registry does not (for example
        ``richards_1d``) are recorded in the returned fold under ``unlinked``,
        so a gap in coverage is reported rather than silently dropped.

        Returns the fold that was applied; ``status_summary()`` embeds it.
        """
        records = _normalise_runner_output(runner_output)
        by_model: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            by_model.setdefault(str(record["model"]), []).append(record)

        index = _card_index()
        fold: dict[str, Any] = {"models": {}, "unlinked": []}
        for slug in sorted(by_model):
            folded = _fold_validation_status(by_model[slug])
            linked = sorted(
                {
                    card["model_id"]
                    for card in _cards_for_corpus_slug(index, slug)
                    if self.get(card["model_id"]) is not None
                }
            )
            fold["models"][slug] = {
                "cases": folded["cases"],
                "by_status": folded["counts"],
                "validation_status": folded["status"].value,
                "reason": folded["reason"],
                "linked_model_ids": linked,
                "evidence": folded["evidence"],
            }
            if not linked:
                fold["unlinked"].append(slug)
            for model_id in linked:
                spec = self.get(model_id)
                if spec is None or not isinstance(spec, RegisteredModelSpec):
                    continue
                spec.validation_status = folded["status"]
                spec.status_reasons["validation_status"] = (
                    f"validation corpus model {slug!r}: {folded['reason']}"
                )
                spec.status_evidence.setdefault(
                    "card_validation_status", spec.status_evidence.get("validation_status", "")
                )
                spec.status_evidence["validation_status"] = (
                    f"validation corpus: {folded['cases']} {slug} case(s) "
                    f"({', '.join(f'{k}={v}' for k, v in sorted(folded['counts'].items()))})"
                )
        fold["unlinked"].sort()
        self._validation_fold = fold
        return fold

    def status_summary(self) -> dict[str, Any]:
        """The machine-readable status summary: counts per status, per model.

        Plain types only (str/int/bool/None/list/dict), so the result is
        directly JSON-serialisable -- :meth:`status_json` writes exactly this.
        Every count adds up to the number of registered models, and every model
        appears in exactly one bucket of each ``by_status`` breakdown, so a
        reader can reconcile the summary against :meth:`all` without trusting
        a filter.
        """
        models = [m for m in self.all() if isinstance(m, RegisteredModelSpec)]
        by_status: dict[str, dict[str, list[str]]] = {
            name: {status.value: [] for status in ModelStatus} for name in _FIELD_RULES
        }
        status_counts: dict[str, dict[str, int]] = {
            name: {status.value: 0 for status in ModelStatus} for name in _FIELD_RULES
        }
        domains: dict[str, int] = {}
        model_types: dict[str, int] = {}
        for spec in models:
            triples = _status_triple(spec)
            for name, status in zip(_FIELD_RULES, triples, strict=True):
                status_counts[name][status.value] += 1
                by_status[name][status.value].append(spec.model_id)
            domains[spec.domain] = domains.get(spec.domain, 0) + 1
            model_types[spec.model_type] = model_types.get(spec.model_type, 0) + 1

        corpus: dict[str, Any] = {"attached": bool(self._validation_fold)}
        if self._validation_fold:
            corpus["case_counts"] = {
                status: sum(
                    m["by_status"].get(status, 0) for m in self._validation_fold["models"].values()
                )
                for status in ("match", "mismatch", "inconsistent_case", "not_run")
            }
            corpus["case_total"] = sum(m["cases"] for m in self._validation_fold["models"].values())
            corpus["models"] = self._validation_fold["models"]
            corpus["corpus_models_without_a_registered_model"] = self._validation_fold["unlinked"]

        return {
            "status_vocabulary": [status.value for status in ModelStatus],
            "registry": {
                "models": len(self._models),
                "status_tracked": len(models),
                "with_card": sum(1 for m in models if m.card_file),
                "without_card": sum(1 for m in models if not m.card_file),
                "domains": dict(sorted(domains.items())),
                "model_types": dict(sorted(model_types.items())),
                "cards_without_a_registered_model": sorted(
                    self._cards.get("unmapped_cards", [])
                ),
                "seeded": self._seeded,
            },
            "status_counts": status_counts,
            "by_status": by_status,
            "models": {spec.model_id: spec.as_status_dict() for spec in models},
            "gateway_wiring": {
                "source": self._gateway_dispatch.get("source"),
                "dispatch_literals": len(self._gateway_dispatch.get("equality", [])),
                "dispatch_prefixes": self._gateway_dispatch.get("prefixes", []),
                "unwired": list(self._unwired),
                "unwired_count": len(self._unwired),
                "wired_count": len(self._models) - len(self._unwired),
            },
            "validation_corpus": corpus,
        }

    def status_json(self, path: str | Path | None = None, indent: int = 2) -> str:
        """:meth:`status_summary` as JSON, optionally written to ``path``.

        This is the machine-readable artifact the master directive asks for: it
        carries the counts, the per-model breakdown, the unwired list and the
        corpus fold in one plain document.
        """
        payload = json.dumps(self.status_summary(), indent=indent, sort_keys=False)
        if path is not None:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload + "\n", encoding="utf-8")
        return payload


def _status_triple(spec: ModelSpec) -> tuple[ModelStatus, ...]:
    """The three status values of a spec, in ``_FIELD_RULES`` order."""
    return tuple(
        _as_status(getattr(spec, name, ModelStatus.UNVERIFIED)) for name in _FIELD_RULES
    )


def _as_status(value: Any) -> ModelStatus:
    """Coerce a stored status to :class:`ModelStatus` (never raises)."""
    if isinstance(value, ModelStatus):
        return value
    try:
        return ModelStatus(value)
    except ValueError:
        return ModelStatus.UNVERIFIED


# Global registry instance
_REGISTRY: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get the global model registry instance.

    The returned registry is populated with the 70 registered models and seeded
    with their structured status (cards + gateway wiring). Call
    :meth:`ModelRegistry.attach_validation_results` to fold the validation
    corpus into ``validation_status``.
    """
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ModelRegistry()
        _populate_default_models(_REGISTRY)
        _REGISTRY.seed_status()
    return _REGISTRY


def _populate_default_models(registry: ModelRegistry) -> None:
    """Populate registry with all 22 CANON models."""

    # CANON-001: Penman-Monteith ET0
    registry.register(ModelSpec(
        model_id="CANON-001",
        model_version="1.0.0",
        model_name="Penman-Monteith ET0",
        model_type="evapotranspiration",
        domain="hydrology",
        purpose="Reference evapotranspiration calculation per FAO-56",
        assumptions=[
            "Well-watered reference crop (grass, 0.12m height)",
            "Aerodynamic resistance from wind speed",
            "Surface resistance fixed at 70 s/m"
        ],
        limitations=[
            "Requires full meteorological data",
            "Not validated for extreme arid conditions without local calibration"
        ]
    ))
    
    # CANON-002: Hargreaves ET0
    registry.register(ModelSpec(
        model_id="CANON-002",
        model_version="1.0.0",
        model_name="Hargreaves ET0",
        model_type="evapotranspiration",
        domain="hydrology",
        purpose="Temperature-based reference evapotranspiration per Hargreaves 1985",
        assumptions=[
            "Empirical temperature-radiation relationship",
            "Extraterrestrial radiation from latitude/day of year"
        ],
        limitations=[
            "Less accurate than Penman-Monteith in humid climates",
            "Requires local validation for Iran (per ECO-03.1)"
        ]
    ))
    
    # CANON-003: Thornthwaite PET
    registry.register(ModelSpec(
        model_id="CANON-003",
        model_version="1.0.0",
        model_name="Thornthwaite PET",
        model_type="evapotranspiration",
        domain="hydrology",
        purpose="Temperature-based potential evapotranspiration per Thornthwaite 1948",
        assumptions=[
            "Monthly temperature data sufficient",
            "Heat index computed from monthly means"
        ],
        limitations=[
            "Theoretical basis only; no local benchmark (ECO-03.1)"
        ]
    ))
    
    # CANON-004: SCS-CN Runoff
    registry.register(ModelSpec(
        model_id="CANON-004",
        model_version="1.0.0",
        model_name="SCS-CN Runoff",
        model_type="hydrology",
        domain="hydrology",
        purpose="Runoff depth from rainfall using USDA SCS Curve Number method",
        assumptions=[
            "Initial abstraction ratio Ia = 0.2 * S",
            "Curve Number represents antecedent moisture condition"
        ],
        limitations=[
            "Lumped parameter model; no spatial variability",
            "Not suitable for frozen ground or urban areas without modification"
        ]
    ))
    
    # CANON-005: Theis Solution
    registry.register(ModelSpec(
        model_id="CANON-005",
        model_version="1.0.0",
        model_name="Theis Solution",
        model_type="groundwater",
        domain="groundwater",
        purpose="Transient drawdown in confined aquifer per Theis 1935",
        assumptions=[
            "Homogeneous, isotropic, infinite confined aquifer",
            "Fully penetrating well, constant pumping rate",
            "Negligible well diameter"
        ],
        limitations=[
            "Series convergence undocumented (ECO-03.1 P0 blocker)",
            "No wellbore storage or skin effects"
        ]
    ))
    
    # CANON-006: Van Genuchten
    registry.register(ModelSpec(
        model_id="CANON-006",
        model_version="1.0.0",
        model_name="Van Genuchten",
        model_type="soil_physics",
        domain="soil",
        purpose="Soil water retention and hydraulic conductivity functions per Van Genuchten 1980",
        assumptions=[
            "Soil water retention follows sigmoidal function",
            "Mualem pore-size distribution model for conductivity"
        ],
        limitations=[
            "Parameter estimation requires lab data",
            "Hysteresis not modeled"
        ]
    ))
    
    # CANON-007: RUSLE LS Factor
    registry.register(ModelSpec(
        model_id="CANON-007",
        model_version="1.0.0",
        model_name="RUSLE LS Factor",
        model_type="erosion",
        domain="erosion",
        purpose="Slope length and steepness factor per Renard 1997",
        assumptions=[
            "Uniform slope profile",
            "Rill/interrill erosion partitioning fixed"
        ],
        limitations=[
            "LS factor calculation requires scientific review (ECO-03.1)"
        ]
    ))
    
    # CANON-008: D8 Flow Direction
    registry.register(ModelSpec(
        model_id="CANON-008",
        model_version="1.0.0",
        model_name="D8 Flow Direction",
        model_type="hydrology",
        domain="hydrology",
        purpose="Single flow direction on raster DEM per McCool 1989",
        assumptions=[
            "Flow follows steepest descent to one of 8 neighbors",
            "No flow divergence"
        ],
        limitations=[
            "Divergent flow on ridges not represented",
            "Grid resolution dependent"
        ]
    ))
    
    # CANON-009: Terrain Analysis
    registry.register(ModelSpec(
        model_id="CANON-009",
        model_version="1.0.0",
        model_name="Terrain Analysis",
        model_type="geomorphology",
        domain="hydrology",
        purpose="Slope, aspect, curvature, flow accumulation from DEM",
        assumptions=[
            "DEM represents bare-earth topography",
            "Grid resolution adequate for features of interest"
        ],
        limitations=[
            "Artifacts from DEM processing not corrected"
        ]
    ))
    
    # CANON-010: Water Balance
    registry.register(ModelSpec(
        model_id="CANON-010",
        model_version="1.0.0",
        model_name="Water Balance",
        model_type="hydrology",
        domain="hydrology",
        purpose="Catchment water balance with steady-state assumption",
        assumptions=[
            "Steady-state storage change negligible",
            "All fluxes measured or estimated"
        ],
        limitations=[
            "Steady-state assumption may not hold for event scale"
        ]
    ))
    
    # CANON-011: Solar Radiation
    registry.register(ModelSpec(
        model_id="CANON-011",
        model_version="1.0.0",
        model_name="Solar Radiation",
        model_type="meteorology",
        domain="climate",
        purpose="Solar radiation from Haurwitz 1942 with atmospheric correction",
        assumptions=[
            "Clear-sky transmission coefficients",
            "Topographic shading not modeled"
        ],
        limitations=[
            "Atmospheric correction needs scientific review (ECO-03.1)"
        ]
    ))
    
    # CANON-012: Formula Catalog
    registry.register(ModelSpec(
        model_id="CANON-012",
        model_version="1.0.0",
        model_name="Formula Catalog",
        model_type="utility",
        domain="utility",
        purpose="Reference implementations of common hydrological formulas",
        assumptions=[],
        limitations=["Utility module, not a scientific model"]
    ))
    
    # CANON-013: Provenance Tracking
    registry.register(ModelSpec(
        model_id="CANON-013",
        model_version="1.0.0",
        model_name="Provenance Tracking",
        model_type="infrastructure",
        domain="infrastructure",
        purpose="Evidence chain tracking for model executions",
        assumptions=[],
        limitations=["Infrastructure, not a scientific model"]
    ))
    
    # CANON-014: Model Registry (meta)
    registry.register(ModelSpec(
        model_id="CANON-014",
        model_version="1.0.0",
        model_name="Model Registry",
        model_type="meta",
        domain="infrastructure",
        purpose="Model discovery and metadata management",
        assumptions=[],
        limitations=["Meta-component, not a scientific model"]
    ))
    
    # CANON-015: Watershed Calculator
    registry.register(ModelSpec(
        model_id="CANON-015",
        model_version="1.0.0",
        model_name="Watershed Calculator",
        model_type="hydrology",
        domain="hydrology",
        purpose="Watershed delineation and morphometric analysis",
        assumptions=[
            "DEM-derived flow network represents surface drainage",
            "Outlet point correctly identified"
        ],
        limitations=[]
    ))
    
    # CANON-016: C++ Climate Kernels
    registry.register(ModelSpec(
        model_id="CANON-016",
        model_version="1.0.0",
        model_name="C++ Climate Kernels",
        model_type="numerical_kernel",
        domain="climate",
        purpose="High-performance climate computations via pybind11",
        assumptions=[
            "Compiled kernels match Python reference",
            "ABI compatible with Python 3.12"
        ],
        limitations=[
            "No C++ compiler available for rebuild (ECO-04.11)"
        ]
    ))
    
    # CANON-017: C++ Soil Kernels
    registry.register(ModelSpec(
        model_id="CANON-017",
        model_version="1.0.0",
        model_name="C++ Soil Kernels",
        model_type="numerical_kernel",
        domain="soil",
        purpose="High-performance soil physics via pybind11",
        assumptions=[
            "Compiled kernels match Python reference",
            "ABI compatible with Python 3.12"
        ],
        limitations=[
            "No C++ compiler available for rebuild (ECO-04.11)"
        ]
    ))
    
    # CANON-018: CMIP6 Climate
    registry.register(ModelSpec(
        model_id="CANON-018",
        model_version="1.0.0",
        model_name="CMIP6 Climate",
        model_type="climate_data",
        domain="climate",
        purpose="CMIP6 climate projections per IPCC AR6",
        assumptions=[
            "Scenario-weighted ensemble",
            "Bias correction applied"
        ],
        limitations=[
            "Data assimilation weights undocumented (ECO-03.1)"
        ]
    ))
    
    # CANON-019: GPM IMERG
    registry.register(ModelSpec(
        model_id="CANON-019",
        model_version="1.0.0",
        model_name="GPM IMERG",
        model_type="remote_sensing",
        domain="meteorology",
        purpose="NASA GPM IMERG precipitation product",
        assumptions=[
            "Calibrated against gauge data",
            "Half-hourly, 0.1 degree resolution"
        ],
        limitations=["Standard product; no local validation"]
    ))
    
    # CANON-020: MODIS ET
    registry.register(ModelSpec(
        model_id="CANON-020",
        model_version="1.0.0",
        model_name="MODIS ET",
        model_type="remote_sensing",
        domain="meteorology",
        purpose="NASA MODIS evapotranspiration product (MOD16)",
        assumptions=[
            "Penman-Monteith based algorithm",
            "Land cover specific parameters"
        ],
        limitations=["Standard product; no local validation"]
    ))
    
    # CANON-021: Landsat
    registry.register(ModelSpec(
        model_id="CANON-021",
        model_version="1.0.0",
        model_name="Landsat",
        model_type="remote_sensing",
        domain="land_surface",
        purpose="USGS Landsat surface reflectance and indices",
        assumptions=[
            "Atmospherically corrected",
            "Cloud/cloud-shadow masked"
        ],
        limitations=["Standard product; 16-day revisit"]
    ))
    
    # CANON-022: Sentinel-2
    registry.register(ModelSpec(
        model_id="CANON-022",
        model_version="1.0.0",
        model_name="Sentinel-2",
        model_type="remote_sensing",
        domain="land_surface",
        purpose="ESA Sentinel-2 MSI surface reflectance and indices",
        assumptions=[
            "Sen2Cor atmospheric correction",
            "Cloud probability masked"
        ],
        limitations=["Standard product; 5-day revisit (2 satellites)"]
    ))
    
    # === Service Models (facade entry points) ===
    # These are the model IDs used by the services/_gateway_facade.py
    
    # Soil Science
    registry.register(ModelSpec(
        model_id="SOIL_CEC", model_version="1.0.0", model_name="Cation Exchange Capacity",
        model_type="soil_chemistry", domain="soil",
        purpose="Calculate CEC from clay, organic matter, pH",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_ESP", model_version="1.0.0", model_name="Exchangeable Sodium Percent",
        model_type="soil_chemistry", domain="soil",
        purpose="Calculate ESP from Na and CEC",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_SAR", model_version="1.0.0", model_name="Sodium Adsorption Ratio",
        model_type="soil_chemistry", domain="soil",
        purpose="Calculate SAR from Na, Ca, Mg",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_HEALTH", model_version="1.0.0", model_name="Soil Health Index",
        model_type="soil_health", domain="soil",
        purpose="Calculate soil health from multiple indicators",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_AWC", model_version="1.0.0", model_name="Available Water Capacity",
        model_type="soil_physics", domain="soil",
        purpose="Calculate plant-available water capacity",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_WATER_CONTENT", model_version="1.0.0", model_name="Soil Water Content",
        model_type="soil_physics", domain="soil",
        purpose="Calculate water content at given matric potential",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_LEACHING", model_version="1.0.0", model_name="Leaching Requirement",
        model_type="soil_salinity", domain="soil",
        purpose="Calculate leaching requirement from EC values",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_AMENDMENT", model_version="1.0.0", model_name="Sodic Soil Amendment",
        model_type="soil_salinity", domain="soil",
        purpose="Calculate gypsum requirement for sodic soils",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_SALINITY_CLASSIFY", model_version="1.0.0", model_name="Salinity Classification",
        model_type="soil_salinity", domain="soil",
        purpose="Classify soil salinity level from EC",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_TAXONOMY", model_version="1.0.0", model_name="Soil Taxonomy",
        model_type="soil_taxonomy", domain="soil",
        purpose="Determine soil taxonomy class from properties",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_TEXTURE", model_version="1.0.0", model_name="Soil Texture Classification",
        model_type="soil_texture", domain="soil",
        purpose="Classify soil texture from sand/silt/clay percentages",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_TEXTURE_COORDS", model_version="1.0.0", model_name="Texture Triangle Coordinates",
        model_type="soil_texture", domain="soil",
        purpose="Get triangle coordinates for texture class",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_WATER_RETENTION", model_version="1.0.0", model_name="Water Retention Curve",
        model_type="soil_retention", domain="soil",
        purpose="Calculate water retention curve from Van Genuchten parameters",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_VG_PARAMETERS", model_version="1.0.0", model_name="Van Genuchten Parameters",
        model_type="soil_retention", domain="soil",
        purpose="Get VG parameters for texture class",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_PEDOTRANSFER", model_version="1.0.0", model_name="Soil Parameter Estimation",
        model_type="soil_pedotransfer", domain="soil",
        purpose="Estimate soil parameters from basic properties",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SOIL_RECOMMENDATIONS", model_version="1.0.0", model_name="Soil Recommendations",
        model_type="soil_recommendations", domain="soil",
        purpose="Generate soil-management recommendations from soil properties",
        assumptions=[], limitations=[]
    ))
    
    # Climate / ET
    registry.register(ModelSpec(
        model_id="CANON-011_RAD", model_version="1.0.0", model_name="Extraterrestrial Radiation",
        model_type="radiation", domain="climate",
        purpose="Calculate extraterrestrial radiation",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ROTHTC_TEMP_FACTOR", model_version="1.0.0",
        model_name="RothC Temperature Factor",
        model_type="carbon_model", domain="carbon",
        purpose="Rothc-26.3 temperature rate modifier (dimensionless f(T))",
        assumptions=[], limitations=[]
    ))

    # Carbon
    registry.register(ModelSpec(
        model_id="CARBON_SEQ", model_version="1.0.0", model_name="Carbon Sequestration",
        model_type="carbon", domain="carbon",
        purpose="Calculate soil carbon sequestration",
        assumptions=[], limitations=[]
    ))
    
    # Economics
    registry.register(ModelSpec(
        model_id="ECON_NPV", model_version="1.0.0", model_name="Net Present Value",
        model_type="economics", domain="agronomy",
        purpose="Calculate NPV from cash flows",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ECON_PAYBACK", model_version="1.0.0", model_name="Payback Period",
        model_type="economics", domain="agronomy",
        purpose="Calculate payback period",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ECON_AG_COST", model_version="1.0.0", model_name="Agricultural Cost",
        model_type="economics", domain="agronomy",
        purpose="Calculate agricultural production cost",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ECON_AG_REVENUE", model_version="1.0.0", model_name="Agricultural Revenue",
        model_type="economics", domain="agronomy",
        purpose="Calculate agricultural revenue",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ECON_PRICE_RISK", model_version="1.0.0", model_name="Market Price Risk",
        model_type="economics", domain="agronomy",
        purpose="Assess market price risk",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ECON_YIELD_RISK", model_version="1.0.0", model_name="Yield Risk",
        model_type="economics", domain="agronomy",
        purpose="Assess yield risk",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="ECON_FINANCIAL", model_version="1.0.0", model_name="Financial Metrics",
        model_type="economics", domain="agronomy",
        purpose="Calculate comprehensive financial metrics",
        assumptions=[], limitations=[]
    ))
    
    # Watershed
    registry.register(ModelSpec(
        model_id="WATERSHED_STRUCT", model_version="1.0.0", model_name="Watershed Structure Design",
        model_type="hydrology", domain="hydrology",
        purpose="Design watershed structures",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="WATERSHED_CHECK_DAM", model_version="1.0.0", model_name="Check Dam Design",
        model_type="hydrology", domain="hydrology",
        purpose="Design check dam",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="WATERSHED_CONTOUR_TRENCH", model_version="1.0.0", model_name="Contour Trench Design",
        model_type="hydrology", domain="hydrology",
        purpose="Design contour trench",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="WATERSHED_HALF_MOON", model_version="1.0.0", model_name="Half Moon Design",
        model_type="hydrology", domain="hydrology",
        purpose="Design half-moon structure",
        assumptions=[], limitations=[]
    ))
    
    # Plant Neurology
    registry.register(ModelSpec(
        model_id="PLANT_NEURO", model_version="1.0.0", model_name="Plant Neurology Engine",
        model_type="plant_neuro", domain="ecosystem",
        purpose="Detect plant stress from NDVI time series",
        assumptions=[], limitations=[]
    ))
    
    # MRV
    registry.register(ModelSpec(
        model_id="MRV_METRICS", model_version="1.0.0", model_name="MRV Metrics",
        model_type="mrv", domain="monitoring",
        purpose="Compute MRV metrics",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="MRV_DASHBOARD", model_version="1.0.0", model_name="MRV Dashboard",
        model_type="mrv", domain="monitoring",
        purpose="Compute MRV dashboard data",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="MRV_VALIDATE", model_version="1.0.0", model_name="MRV Validation",
        model_type="mrv", domain="monitoring",
        purpose="Validate MRV reading",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="MRV_VALIDATE_SAT", model_version="1.0.0", model_name="Satellite Index Validation",
        model_type="mrv", domain="monitoring",
        purpose="Validate satellite index data",
        assumptions=[], limitations=[]
    ))
    
    # Materials
    registry.register(ModelSpec(
        model_id="COMPOST_CN", model_version="1.0.0", model_name="Compost C:N Ratio",
        model_type="materials", domain="soil",
        purpose="Calculate carbon-to-nitrogen ratio for compost mix",
        assumptions=[], limitations=[]
    ))
    
    # Erosion
    registry.register(ModelSpec(
        model_id="RUSLE_LS", model_version="1.0.0", model_name="RUSLE LS Factor",
        model_type="erosion", domain="erosion",
        purpose="Compute RUSLE LS factor for erosion",
        assumptions=[], limitations=[]
    ))
    
    # Scenarios
    registry.register(ModelSpec(
        model_id="SCENARIO", model_version="1.0.0", model_name="Climate Scenario",
        model_type="scenario", domain="climate",
        purpose="Apply climate scenario to inputs",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="CLIMATE_SCENARIO", model_version="1.0.0", model_name="Climate Change Scenario",
        model_type="scenario", domain="climate",
        purpose="Apply climate change projection",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="CLIMATE_PROJECTION", model_version="1.0.0", model_name="Climate Projection",
        model_type="scenario", domain="climate",
        purpose="Get climate projection for location",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="CROP_COMPARE", model_version="1.0.0", model_name="Crop Comparison",
        model_type="crop", domain="agronomy",
        purpose="Compare crops under climate",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="CROP_YIELD", model_version="1.0.0", model_name="Crop Yield Simulation",
        model_type="crop", domain="agronomy",
        purpose="Simulate crop yield",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="HYRUE_WHEAT", model_version="2.0.0", model_name="HYRUE Wheat Yield",
        model_type="crop_yield", domain="agronomy",
        purpose="Simulate wheat yield using HYRUE radiation use efficiency model",
        assumptions=[
            "par (scalar or daily array), lai (array), ewsi (array), t_mean (scalar or array), days (int)",
            "EWSI is a stress index in [0,1] where 0 = no stress, 1 = severe stress",
            "Scalar mode: days multiplies a single-day estimate (constant conditions)",
            "Seasonal mode (array par): daily biomass is summed over the array length",
        ],
        limitations=[
            "Scalar mode assumes constant conditions; use seasonal mode (array par) for realistic trajectories",
            "Gaussian temperature width (sigma=8) is a platform choice, not crop-parameterized",
            "PAR must be daily values for seasonal mode; daily PAR data is not generated by the weather simulator",
            "Crop presets only set epsilon, hi, and t_opt; k, t_min, t_max, lai_max are generic",
            "Requires numpy for array inputs",
        ],
    ))
    registry.register(ModelSpec(
        model_id="HYRUE_CORN", model_version="2.0.0", model_name="HYRUE Corn Yield",
        model_type="crop_yield", domain="agronomy",
        purpose="Simulate corn yield using HYRUE radiation use efficiency model",
        assumptions=[
            "par (scalar or daily array), lai (array), ewsi (array), t_mean (scalar or array), days (int)",
            "EWSI is a stress index in [0,1] where 0 = no stress, 1 = severe stress",
            "Scalar mode: days multiplies a single-day estimate (constant conditions)",
            "Seasonal mode (array par): daily biomass is summed over the array length",
        ],
        limitations=[
            "Scalar mode assumes constant conditions; use seasonal mode (array par) for realistic trajectories",
            "Gaussian temperature width (sigma=8) is a platform choice, not crop-parameterized",
            "PAR must be daily values for seasonal mode; daily PAR data is not generated by the weather simulator",
            "Crop presets only set epsilon, hi, and t_opt; k, t_min, t_max, lai_max are generic",
            "Requires numpy for array inputs",
        ],
    ))
    
    # Data Pipeline
    registry.register(ModelSpec(
        model_id="DATA_PIPELINE", model_version="1.0.0", model_name="Data Pipeline",
        model_type="data_pipeline", domain="infrastructure",
        purpose="Get data pipeline by name",
        assumptions=[], limitations=[]
    ))
    
    # Irrigation
    registry.register(ModelSpec(
        model_id="IRRIGATION_DEPTH", model_version="1.0.0", model_name="Irrigation Application Depth",
        model_type="irrigation", domain="agronomy",
        purpose="Calculate irrigation application depth",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="IRRIGATION_INTERVAL", model_version="1.0.0", model_name="Irrigation Interval",
        model_type="irrigation", domain="agronomy",
        purpose="Calculate irrigation interval",
        assumptions=[], limitations=[]
    ))
    
    # Simulation
    registry.register(ModelSpec(
        model_id="SIM_CHAIN", model_version="1.0.0", model_name="Simulation Chain",
        model_type="simulation", domain="infrastructure",
        purpose="Run simulation chain",
        assumptions=[], limitations=[]
    ))
    registry.register(ModelSpec(
        model_id="SIM_ORCHESTRATE", model_version="1.0.0", model_name="Simulation Orchestrator",
        model_type="simulation", domain="infrastructure",
        purpose="Orchestrate simulations",
        assumptions=[], limitations=[]
    ))
    
    # Recommendation
    registry.register(ModelSpec(
        model_id="RECOMMEND", model_version="1.0.0", model_name="Recommendation Engine",
        model_type="recommendation", domain="infrastructure",
        purpose="Generate recommendations",
        assumptions=[], limitations=[]
    ))


def get_model(model_id: str) -> ModelSpec | None:
    """Get a model by ID from the global registry."""
    return get_registry().get(model_id)


def list_models() -> list[str]:
    """List all registered model IDs."""
    return get_registry().list_ids()
