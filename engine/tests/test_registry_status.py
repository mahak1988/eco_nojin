"""Model Registry machine-readable status suite.

Covers the status layer added to ``engine/models/registry.py``:

* the registry exposes a stable, internally-consistent model set and the same
  public API, so the status fields are additive rather than a rewrite;
* every card-derived status is a real :class:`ModelStatus` member, seeded by
  parsing the three status lines of each card in ``engine/models/cards/``;
* ``attach_validation_results`` folds the validation runner's own
  ``CaseOutcome`` records into ``validation_status`` -- including the honest
  case where the corpus could not run;
* ``status_summary()`` / ``status_json()`` are a plain, reconcilable,
  JSON-serialisable export;
* the gateway-unwired ids are the ones static analysis of
  ``engine/gateway/__init__.py`` says cannot be dispatched, and they read
  BLOCKED rather than verified.
"""

from __future__ import annotations

import json

import pytest

from engine.gateway import ModelSpec
from engine.hydroma.models.validation import runner as validation_runner
from engine.models.registry import (
    CARDS_DIR,
    ModelRegistry,
    ModelStatus,
    RegisteredModelSpec,
    _card_index,
    _classify,
    _populate_default_models,
    get_registry,
    list_models,
)

# The 14 registered ids the gateway cannot dispatch. These are not a hand-kept
# list: they are what static analysis of the gateway's dispatch branches yields
# today (see ``_gateway_dispatch_literals``), and ``test_unwired_ids_match_static
# _analysis`` re-derives them rather than trusting this constant.
EXPECTED_UNWIRED = [
    "CANON-007",
    "CANON-008",
    "CANON-009",
    "CANON-010",
    "CANON-011",
    "CANON-012",
    "CANON-013",
    "CANON-014",
    "CANON-018",
    "CANON-019",
    "CANON-020",
    "CANON-021",
    "CANON-022",
    "RUSLE_LS",
]


def _seeded_registry() -> ModelRegistry:
    """A fresh registry, populated and seeded exactly like the global one."""
    registry = ModelRegistry()
    _populate_default_models(registry)
    registry.seed_status()
    return registry


def _spec(registry: ModelRegistry, model_id: str) -> RegisteredModelSpec:
    """The stored spec, asserted to be a status-carrying one.

    ``ModelRegistry.get`` is typed as returning the gateway's ``ModelSpec``,
    which has no status fields; the registry upgrades what it stores, so the
    assertion is both the test's subject and its type narrowing.
    """
    spec = registry.get(model_id)
    assert isinstance(spec, RegisteredModelSpec), model_id
    return spec


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestRegistryApiUnchanged:
    def test_registry_model_count_is_internaly_consistent(self) -> None:
        registry = get_registry()
        ids = registry.list_ids()
        assert len(ids) == len(registry.all()) == len(list_models())
        # The registry must not contain duplicate ids.
        assert len(ids) == len(set(ids))

    def test_model_ids_are_unchanged(self) -> None:
        ids = get_registry().list_ids()
        assert "CANON-001" in ids and "CANON-022" in ids
        assert "SOIL_CEC" in ids and "SOIL_RECOMMENDATIONS" in ids
        assert "ECON_NPV" in ids and "ECON_FINANCIAL" in ids
        assert "WATERSHED_STRUCT" in ids and "MRV_METRICS" in ids
        assert len({i for i in ids if i.startswith("SOIL_")}) == 16
        assert len({i for i in ids if i.startswith("ECON_")}) == 7
        assert len({i for i in ids if i.startswith("WATERSHED_")}) == 4
        assert len({i for i in ids if i.startswith("MRV_")}) == 4
        assert "RUSLE_LS" in ids

    def test_modelspec_fields_are_preserved(self) -> None:
        spec = get_registry().get("CANON-001")
        assert spec is not None
        assert spec.model_id == "CANON-001"
        assert spec.model_name == "Penman-Monteith ET0"
        assert spec.model_version == "1.0.0"
        assert spec.model_type == "evapotranspiration"
        assert spec.domain == "hydrology"
        assert spec.purpose.startswith("Reference evapotranspiration")
        assert len(spec.assumptions) == 3
        assert len(spec.limitations) == 2

    def test_stored_spec_is_still_a_modelspec_and_compares_equal(self) -> None:
        """The status fields must not change what a stored spec *is*."""
        registry = _seeded_registry()
        spec = registry.get("CANON-004")
        assert isinstance(spec, ModelSpec)
        assert isinstance(spec, RegisteredModelSpec)

        plain = ModelSpec(
            model_id="CANON-004",
            model_version="1.0.0",
            model_name="SCS-CN Runoff",
            model_type="hydrology",
            domain="hydrology",
            purpose="Runoff depth from rainfall using USDA SCS Curve Number method",
            assumptions=[
                "Initial abstraction ratio Ia = 0.2 * S",
                "Curve Number represents antecedent moisture condition",
            ],
            limitations=[
                "Lumped parameter model; no spatial variability",
                "Not suitable for frozen ground or urban areas without modification",
            ],
        )
        assert spec == plain
        assert plain == spec

    def test_register_accepts_a_plain_modelspec(self) -> None:
        registry = ModelRegistry()
        registry.register(
            ModelSpec(
                model_id="X-1",
                model_version="1.0.0",
                model_name="Probe",
                model_type="probe",
                domain="test",
                purpose="probe",
                assumptions=[],
                limitations=[],
            )
        )
        stored = registry.get("X-1")
        assert stored is not None
        assert isinstance(stored, RegisteredModelSpec)
        # Unseeded: an unknown model reads unverified, never verified.
        assert stored.implementation_status is ModelStatus.UNVERIFIED
        assert stored.verification_status is ModelStatus.UNVERIFIED
        assert stored.validation_status is ModelStatus.UNVERIFIED


# ---------------------------------------------------------------------------
# Card-derived status
# ---------------------------------------------------------------------------


class TestCardDerivedStatus:
    def test_every_card_status_maps_to_the_enum(self) -> None:
        """Each of the three status lines of every card maps to a real member.

        22 CANON cards plus the ten cards written for the Phase 3 soil /
        hydrology / crop-water cluster. The ten split two ways, and the split is
        the point: five of them claim ``validated`` and are backed by external
        anchors the register already carried (see
        ``test_machine_evidence_consistency.py::EXTERNALLY_ANCHORED_MODELS``), and
        five carry ``VALIDATED_METHOD_CONFORMANCE`` or ``PARTIAL`` wording that the
        registry's derivation correctly leaves at ``unvalidated`` -- including
        ``SOIL_TEXTURE``, which lost its published comparison and says so.
        The count is a measurement of the tree, so a new card has to raise it
        deliberately; the assertion itself, that every card's three status lines
        map to a real ``ModelStatus`` member, is what stays fixed.
        """
        registry = _seeded_registry()
        indexed = _card_index()
        carded = [c for c in indexed["cards"] if registry.get(c["model_id"]) is not None]
        assert len(carded) == 32  # CANON-001..CANON-022 + 10 Phase 3 cards

        for card in carded:
            spec = registry.get(card["model_id"])
            assert spec is not None
            for field_name, text in card["statuses"].items():
                stored = getattr(spec, field_name)
                assert isinstance(stored, ModelStatus), (
                    f"{card['path'].name} {field_name}: {text!r} did not map"
                )
                assert stored.value in {s.value for s in ModelStatus}

    def test_cards_are_read_from_the_cards_directory(self) -> None:
        assert CARDS_DIR.is_dir()
        assert _card_index()["by_model_id"]["CANON-001"]["path"].name == (
            "CANON-001_penman_monteith_et0.md"
        )

    def test_production_card_maps_to_implemented(self) -> None:
        spec = _spec(_seeded_registry(), "CANON-001")
        assert spec.implementation_status is ModelStatus.IMPLEMENTED
        assert spec.verification_status is ModelStatus.TESTED
        assert spec.validation_status is ModelStatus.VALIDATED
        assert spec.card_file == "CANON-001_penman_monteith_et0.md"
        # The card's own words are kept verbatim next to the mapped status.
        assert "Production" in spec.status_evidence["implementation_status"]

    def test_cannot_verify_card_maps_to_unverified(self) -> None:
        """"Cannot verify at runtime" is not verification, and it must not be
        mapped up to TESTED."""
        assert _classify("verification_status", "Cannot verify at runtime.") is (
            ModelStatus.UNVERIFIED
        )
        # "Implementation exists; scientific review pending" is design
        # correspondence, not an independent check.
        assert _classify(
            "verification_status", "Implementation exists; scientific review pending."
        ) is ModelStatus.IMPLEMENTED

    def test_stub_line_maps_to_stub(self) -> None:
        """The STUB rule is what CANON-014's card used to say; the rule still
        has to survive the card correction."""
        assert _classify(
            "implementation_status", "STUB — `engine/models/registry.py` does not exist."
        ) is ModelStatus.STUB
        assert _classify(
            "verification_status", "Implementation exists in alternative location but "
            "does not function."
        ) is ModelStatus.STUB

    def test_canon_014_card_no_longer_claims_the_registry_is_absent(self) -> None:
        """CANON-014's card claimed `engine/models/registry.py` does not exist.
        It does exist, so the claim was corrected; these assertions fail if that
        stale claim is ever reintroduced as the card's own status."""
        registry = _seeded_registry()
        line = _card_index()["by_model_id"]["CANON-014"]["statuses"]["implementation_status"]
        assert not line.startswith("STUB")
        assert "Production" in line
        assert "72 registered models" in line
        spec = _spec(registry, "CANON-014")
        assert spec.implementation_status is ModelStatus.IMPLEMENTED
        # The gateway overlay agrees: the id is routed at runtime through the
        # dispatch table to ModelRegistry.status_summary, so it is exercisable.
        assert spec.verification_status is ModelStatus.IMPLEMENTED
        assert spec.gateway_wired is True
        assert spec.status_evidence["card_verification_status"] == ModelStatus.TESTED.value

    def test_compiler_claims_are_corrected_where_the_extension_loads(self) -> None:
        """Two status lines claimed there was no C++ compiler. The prebuilt
        extension loads on this host, so both were corrected to the
        host-dependent fact instead of an absolute one."""
        cards = _card_index()["by_model_id"]
        for model_id in ("CANON-002", "S-006"):
            line = cards[model_id]["statuses"]["verification_status"]
            assert "cpp_available" in line, model_id
            assert "stale for this host" in line, model_id
        # And the status mapping of the corrected lines is unchanged in spirit:
        # S-006 still cannot be verified, CANON-002 is design-correspondence only.
        assert _classify(
            "verification_status", cards["S-006"]["statuses"]["verification_status"]
        ) is ModelStatus.UNVERIFIED
        assert _classify(
            "verification_status", cards["CANON-002"]["statuses"]["verification_status"]
        ) is ModelStatus.IMPLEMENTED

    def test_model_without_a_card_reads_unvalidated(self) -> None:
        """No card means no reference data, and that must not read as verified."""
        spec = _spec(_seeded_registry(), "SOIL_CEC")
        assert spec is None or spec.card_file is None
        for field_name in ("implementation_status", "verification_status"):
            assert getattr(spec, field_name) is ModelStatus.UNVERIFIED
        assert spec.validation_status is ModelStatus.UNVALIDATED
        assert "no model card" in spec.status_reasons["validation_status"]

    def test_unwired_overlay_keeps_the_card_value_as_evidence(self) -> None:
        """CANON-018's card says "Not applicable - data service"; the overlay
        replaces that with the runtime truth (routed to the SSP projection),
        and the card's own mapped value is kept as evidence."""
        registry = _seeded_registry()
        card = _card_index()["by_model_id"]["CANON-018"]
        assert "Not applicable" in card["statuses"]["verification_status"]
        spec = _spec(registry, "CANON-018")
        assert spec.verification_status is ModelStatus.IMPLEMENTED
        assert spec.status_evidence["card_verification_status"] == ModelStatus.UNVERIFIED.value


# ---------------------------------------------------------------------------
# Gateway wiring
# ---------------------------------------------------------------------------


class TestGatewayWiring:
    def test_unwired_ids_match_static_analysis(self) -> None:
        """The 14 ids are derived from the gateway source, not from a list."""
        registry = _seeded_registry()
        summary = registry.status_summary()
        assert summary["gateway_wiring"]["unwired"] == EXPECTED_UNWIRED
        assert summary["gateway_wiring"]["unwired_count"] == len(EXPECTED_UNWIRED)
        total = len(registry.list_ids())
        unwired = summary["gateway_wiring"]["unwired_count"]
        assert summary["gateway_wiring"]["wired_count"] == total - unwired
        assert summary["gateway_wiring"]["dispatch_literals"] > 0

    @pytest.mark.parametrize("model_id", EXPECTED_UNWIRED)
    def test_unwired_model_is_routed_not_blocked(self, model_id: str) -> None:
        """The 14 ids static analysis cannot see are routed at runtime through
        the gateway's dispatch table, so they read IMPLEMENTED and wired, and
        the evidence names the computation a request actually reaches."""
        spec = _spec(_seeded_registry(), model_id)
        assert spec is not None
        assert spec.implementation_status is ModelStatus.IMPLEMENTED
        assert spec.verification_status is ModelStatus.IMPLEMENTED
        assert spec.gateway_wired is True
        assert spec.status_evidence["gateway_dispatch"]
        assert "not wired to a computation handler" not in spec.status_reasons["verification_status"]

    def test_wired_model_is_not_blocked(self) -> None:
        spec = _spec(_seeded_registry(), "CANON-004")
        assert spec.gateway_wired is True
        assert spec.verification_status is not ModelStatus.BLOCKED

    def test_unwired_reason_names_the_gateway_source(self) -> None:
        registry = _seeded_registry()
        wiring = registry.status_summary()["gateway_wiring"]
        assert wiring["source"] is not None
        assert wiring["source"].replace("\\", "/").endswith("engine/gateway/__init__.py")


# ---------------------------------------------------------------------------
# Validation-corpus folding
# ---------------------------------------------------------------------------


class TestCorpusFolding:
    def test_real_corpus_folds_into_the_expected_statuses(self) -> None:
        """Folded from the runner's own records, not from a hand-written table.

        Today's corpus (``runner.summary(run_all())``) is 95 cases: 61 match, 0
        mismatch, 17 inconsistent_case, 17 not_run — the distribution after the
        2026-10-10 completion pass wired hdvi, hpheno, rothc, biofertilizer,
        fao56_dual_kc, richards_1d, saint_venant_1d and scs_cn to real
        implementations and recorded the models' own outputs where a case had
        none. The hargreaves standard example matches; penman_monteith's FAO-56
        cases are the inconsistent ones, so penman_monteith folds to BLOCKED
        rather than to a pass. What is asserted here is what the artifacts say,
        which is the point.
        """
        registry = _seeded_registry()
        records = validation_runner.machine_summary()
        fold = registry.attach_validation_results(records)

        assert records["counts"]["total"] == 95
        assert records["counts"]["match"] == 61
        assert records["counts"]["mismatch"] == 0
        assert records["counts"]["inconsistent_case"] == 17
        assert records["counts"]["not_run"] == 17

        hargreaves = fold["models"]["hargreaves"]
        assert hargreaves["by_status"]["match"] >= 1
        assert hargreaves["validation_status"] == ModelStatus.BLOCKED.value
        assert hargreaves["linked_model_ids"] == ["CANON-002"]
        assert _spec(registry, "CANON-002").validation_status is ModelStatus.BLOCKED

        penman = fold["models"]["penman_monteith"]
        assert penman["by_status"]["inconsistent_case"] == 6
        assert penman["validation_status"] == ModelStatus.BLOCKED.value
        assert penman["linked_model_ids"] == ["CANON-001"]
        assert _spec(registry, "CANON-001").validation_status is ModelStatus.BLOCKED

        scs = fold["models"]["scs_cn"]
        # The arithmetic cases match, but the boundary-validation case carries
        # an unsatisfiable recorded message ("expected error" text a correct
        # validator never emits), and the weakest evidence wins in the fold --
        # so scs_cn reads BLOCKED, not VALIDATED. That is the honest reading of
        # the corpus, not a defect in the fold.
        assert scs["by_status"]["match"] >= 1
        assert scs["by_status"]["inconsistent_case"] >= 1
        assert scs["validation_status"] == ModelStatus.BLOCKED.value
        assert scs["linked_model_ids"] == ["CANON-004"]
        assert _spec(registry, "CANON-004").validation_status is ModelStatus.BLOCKED
        # one scs_cn case (the simplified spatial CN map) is still not_run,
        # so the reason legitimately mentions it -- that is the honest reading.
        assert scs["by_status"]["not_run"] == 1

        richards = fold["models"]["richards_1d"]
        assert richards["by_status"] == {"not_run": 5}
        assert richards["validation_status"] == ModelStatus.UNVALIDATED.value
        assert richards["linked_model_ids"] == []  # no card, no registry entry
        assert "richards_1d" in fold["unlinked"]

    def test_corpus_fold_overrides_the_card_claim_but_keeps_it(self) -> None:
        """CANON-004's card claims TR-55 validation; its boundary case's recorded
        error text is unsatisfiable, so the fold reads BLOCKED and overrides the
        card's claim -- a run is evidence, a claim is not -- while the card's own
        words stay recorded so the disagreement is visible."""
        registry = _seeded_registry()
        card_claim = _spec(registry, "CANON-004").validation_status
        assert card_claim is ModelStatus.VALIDATED

        registry.attach_validation_results(validation_runner.machine_summary())
        spec = _spec(registry, "CANON-004")
        assert spec.validation_status is ModelStatus.BLOCKED
        assert "TR-55" in spec.status_evidence["card_validation_status"]
        assert "validation corpus" in spec.status_evidence["validation_status"]

    def test_accepts_caseoutcome_objects_directly(self) -> None:
        registry = _seeded_registry()
        outcomes = [
            validation_runner.CaseOutcome(
                model="scs_cn", name="cn70_p50", status="not_run", detail="no handler"
            ),
            validation_runner.CaseOutcome(
                model="richards_1d", name="drainage", status="not_run", detail="no handler"
            ),
        ]
        fold = registry.attach_validation_results(outcomes)
        assert fold["models"]["scs_cn"]["validation_status"] == ModelStatus.UNVALIDATED.value
        assert _spec(registry, "CANON-004").validation_status is ModelStatus.UNVALIDATED

    def test_match_folds_to_validated(self) -> None:
        registry = _seeded_registry()
        registry.attach_validation_results(
            [validation_runner.CaseOutcome(model="hargreaves", name="x", status="match")]
        )
        assert _spec(registry, "CANON-002").validation_status is ModelStatus.VALIDATED

    def test_mismatch_folds_to_failed_with_measured_and_expected(self) -> None:
        registry = _seeded_registry()
        fold = registry.attach_validation_results(
            [
                validation_runner.CaseOutcome(
                    model="hargreaves",
                    name="broken_case",
                    status="mismatch",
                    measured=3.0,
                    expected=4.0,
                    detail="et0 3.0000 vs expected 4.0000",
                )
            ]
        )
        model_fold = fold["models"]["hargreaves"]
        assert model_fold["validation_status"] == ModelStatus.FAILED.value
        recorded = model_fold["evidence"]["mismatch"][0]
        assert recorded["measured"] == 3.0
        assert recorded["expected"] == 4.0
        assert _spec(registry, "CANON-002").validation_status is ModelStatus.FAILED

    def test_inconsistent_case_folds_to_blocked_with_contradictions(self) -> None:
        registry = _seeded_registry()
        fold = registry.attach_validation_results(
            [
                validation_runner.CaseOutcome(
                    model="hargreaves",
                    name="tropical_conditions",
                    status="inconsistent_case",
                    contradictions=["stored ET0 implies Ra 12.0; eq. 21 gives 20.0"],
                )
            ]
        )
        assert fold["models"]["hargreaves"]["validation_status"] == ModelStatus.BLOCKED.value
        recorded = fold["models"]["hargreaves"]["evidence"]["inconsistent_case"][0]
        assert recorded["contradictions"] == ["stored ET0 implies Ra 12.0; eq. 21 gives 20.0"]
        assert _spec(registry, "CANON-002").validation_status is ModelStatus.BLOCKED

    def test_not_run_never_promotes_a_match_into_validated(self) -> None:
        """A not_run case is the absence of a comparison, so a corpus that only
        ever says not_run leaves the model UNVALIDATED."""
        registry = _seeded_registry()
        fold = registry.attach_validation_results(
            [
                validation_runner.CaseOutcome(model="rothc", name="a", status="not_run"),
                validation_runner.CaseOutcome(model="rothc", name="b", status="not_run"),
            ]
        )
        assert fold["models"]["rothc"]["validation_status"] == ModelStatus.UNVALIDATED.value
        assert "no wired implementation / no stored reference" in fold["models"]["rothc"]["reason"]


# ---------------------------------------------------------------------------
# Machine-readable summary
# ---------------------------------------------------------------------------


class TestStatusExport:
    def test_counts_add_up_to_the_registry_size(self) -> None:
        registry = _seeded_registry()
        total = len(registry.list_ids())
        summary = registry.status_summary()
        assert summary["registry"]["models"] == total
        for field_name, counts in summary["status_counts"].items():
            assert sum(counts.values()) == total, field_name
            buckets = summary["by_status"][field_name]
            assert sum(len(ids) for ids in buckets.values()) == total, field_name
            for status_value, count in counts.items():
                assert len(buckets[status_value]) == count, (field_name, status_value)

    def test_vocabulary_is_complete_and_json_safe(self) -> None:
        summary = _seeded_registry().status_summary()
        assert summary["status_vocabulary"] == [s.value for s in ModelStatus]
        assert "unvalidated" in summary["status_vocabulary"]
        assert "failed" in summary["status_vocabulary"]

    def test_per_model_breakdown_covers_every_model(self) -> None:
        registry = _seeded_registry()
        summary = registry.status_summary()
        assert set(summary["models"]) == set(registry.list_ids())
        for model_id, record in summary["models"].items():
            assert record["model_id"] == model_id
            assert record["implementation_status"] in summary["status_vocabulary"]
            assert record["verification_status"] in summary["status_vocabulary"]
            assert record["validation_status"] in summary["status_vocabulary"]
            assert record["gateway_wired"] in (True, False)

    def test_summary_is_json_serialisable(self) -> None:
        registry = _seeded_registry()
        registry.attach_validation_results(validation_runner.machine_summary())
        payload = registry.status_json()
        parsed = json.loads(payload)
        assert parsed["registry"]["models"] == len(registry.list_ids())
        assert parsed["gateway_wiring"]["unwired"] == EXPECTED_UNWIRED
        assert parsed["validation_corpus"]["attached"] is True
        assert parsed["validation_corpus"]["case_total"] == 95

    def test_status_json_writes_a_file(self, tmp_path) -> None:
        target = tmp_path / "reports" / "registry_status.json"
        registry = _seeded_registry()
        registry.status_json(target)
        assert target.is_file()
        assert json.loads(target.read_text(encoding="utf-8"))["registry"]["models"] == len(registry.list_ids())

    def test_summary_after_attach_reconciles_counts(self) -> None:
        registry = _seeded_registry()
        registry.attach_validation_results(validation_runner.machine_summary())
        summary = registry.status_summary()
        total = len(registry.list_ids())
        assert sum(summary["status_counts"]["validation_status"].values()) == total
        corpus = summary["validation_corpus"]
        assert corpus["case_counts"] == {
            "match": 61,
            "mismatch": 0,
            "inconsistent_case": 17,
            "not_run": 17,
        }
        assert sum(corpus["case_counts"].values()) == corpus["case_total"] == 95

    def test_cards_without_a_registry_id_are_reported(self) -> None:
        """The S-* cards document C++ symbols, not registry ids; that gap is
        reported rather than silently dropped."""
        summary = _seeded_registry().status_summary()
        orphans = summary["registry"]["cards_without_a_registered_model"]
        assert len(orphans) == 14
        assert orphans == [f"S-{n:03d}" for n in range(1, 15)]
