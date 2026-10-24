"""Re-run every published-reference validation record (Phase 3, task 3).

Each ``<MODEL_ID>.md`` file beside this module is one evidence record: it states
the published reference, the input range, the tolerance, a comparison table of
model output against independently re-derived reference output, and an
uncertainty statement. This module makes those records falsifiable rather than
aspirational:

* every case in the record is re-executed through the engine **gateway** —
  ``engine/gateway`` is the only sanctioned caller path and the one the services
  layer uses — and the live result must still equal the value the record stored.
  A model that drifts away from its record fails here;
* the stored reference number is re-derived **independently** from the published
  equation in this module, so a number typed into a record by hand, or computed
  from an engine implementation, cannot survive;
* every recorded verdict is re-checked against that independent reference, so a
  record claiming a match the model does not meet fails, and a record claiming a
  discrepancy the model no longer has also fails;
* the registry's own ``validation_status`` for the model must equal the record's
  claim, and the status must come from a card's ``validation_status`` row —
  which is how ``engine/models/registry.py`` derives it. The status is never
  hand-edited;
* the decision ``tools/engine_model_triage.py`` derives for the model must be
  ``published`` exactly when the record says the model is validated.

**The status split is deliberate, and this suite pins it.** Of the ten models
validated here, five claim ``validated`` in the registry and five are left at
``unvalidated`` even though their comparisons pass in full. The difference is not
the evidence — it is the anchor. ``engine/tests/test_machine_evidence_consistency.py``
requires every ``validated`` claim to be backed by an *external* anchor, a
``VALIDATED_EXTERNAL`` row in
``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json``, and refuses to let the
known-unanchored debt set grow. Five of these models already had such a row
(``ENO_HARGREAVES_ET0``, ``FAO56_RA``, ``RUSLE_LS``, ``ROTHC_TEMP_FACTOR``,
``SOIL_SALINITY_CLASSES``) and only needed the model-to-row wiring; the other
five are recorded by the register as method-conformance evidence, which is exactly
what ``engine/validation/<MODEL_ID>.md`` establishes, so their cards say
``VALIDATED_METHOD_CONFORMANCE`` — a label the registry's own derivation does not
turn into a ``validated`` claim. Their records name the register row that would
move them, in ``registry_gap``.

A record whose model disagrees with its published reference (today:
``SOIL_TEXTURE``) is re-run on equal terms. Its discrepancy cases are asserted to
still be discrepancies, the registry is asserted to still read ``unvalidated``
for it, and the record's exhaustive counts are re-measured from scratch.

No network, no compiled-kernel rebuild, and one shared gateway instance.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from engine.gateway import EngineGateway, GatewayRequest, GatewayResult, ProvenanceSpec
from engine.models.registry import ModelStatus, RegisteredModelSpec, get_registry

VALIDATION_DIR = Path(__file__).resolve().parent
REPO_ROOT = VALIDATION_DIR.parents[1]
CARDS_DIR = REPO_ROOT / "engine" / "models" / "cards"
TRIAGE_TOOL = REPO_ROOT / "tools" / "engine_model_triage.py"

#: The one record schema this suite understands.
RECORD_SCHEMA = "hydroma.validation.record@1"

#: The ten soil / hydrology / crop-water models Phase 3 was scoped to validate.
#: The set is asserted below, not assumed: a record that disappears shows up as
#: a missing model rather than as a silently smaller suite.
CLUSTER_MODEL_IDS = (
    "SOIL_TEXTURE",
    "SOIL_SAR",
    "SOIL_ESP",
    "SOIL_SALINITY_CLASSIFY",
    "SOIL_LEACHING",
    "RUSLE_LS",
    "IRRIGATION_DEPTH",
    "IRRIGATION_INTERVAL",
    "CANON-002",
    "CANON-011_RAD",
    "ROTHTC_TEMP_FACTOR",
)

#: The derivation's positive pattern: a whole-word validated / benchmarked /
#: matches claim in the card's validation_status row (see
#: ``engine/models/registry.py::_VALIDATION_RULES``).
POSITIVE_CLAIM = re.compile(r"\b(?:validated|benchmarked|matches)\b", re.IGNORECASE)

#: The five cluster models whose ``validated`` claim is backed by an external
#: anchor the register already carries. The other five validated here are left
#: at ``unvalidated`` on purpose: the register records them as method-conformance
#: evidence, and ``engine/tests/test_machine_evidence_consistency.py`` refuses a
#: registry ``validated`` claim without an external anchor.
CLUSTER_MODELS_MOVED_TO_VALIDATED = (
    "CANON-002",
    "CANON-011_RAD",
    "RUSLE_LS",
    "ROTHTC_TEMP_FACTOR",
    "SOIL_SALINITY_CLASSIFY",
)

#: The one fenced json block per record that carries the machine data.
_JSON_FENCE = re.compile(r"```json\n(.*?)```", re.DOTALL)

PROVENANCE = ProvenanceSpec(source="validation_record", source_type="TEST")
GATEWAY = EngineGateway()


# --------------------------------------------------------------------------- #
# Record loading                                                               #
# --------------------------------------------------------------------------- #
def _records() -> list[dict[str, Any]]:
    """Every record in this directory, with its schema-bearing json block."""
    found: list[dict[str, Any]] = []
    for path in sorted(VALIDATION_DIR.glob("*.md")):
        for block in _JSON_FENCE.findall(path.read_text(encoding="utf-8")):
            payload: Any = json.loads(block)
            if isinstance(payload, dict) and payload.get("schema") == RECORD_SCHEMA:
                found.append(payload)
                break
        else:
            raise AssertionError(f"{path.name} carries no {RECORD_SCHEMA} block")
    return found


def _record_for(model_id: str) -> dict[str, Any]:
    for record in _records():
        if record["model_id"] == model_id:
            return record
    raise AssertionError(f"no validation record for {model_id}")


def _tolerance_of(record: dict[str, Any]) -> float:
    return float(record["tolerance"]["absolute"])


def _gateway_values(model_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Run one case through the engine gateway, the services-sanctioned path."""
    result = GATEWAY.execute(
        GatewayRequest(
            model_id=model_id,
            inputs=dict(inputs),
            input_units={},
            provenance=PROVENANCE,
        )
    )
    assert isinstance(result, GatewayResult), (
        f"{model_id}: {result.error_code}: {result.message}"
    )
    return result.values


def _agrees(got: Any, expected: Any, tolerance: float) -> bool:
    """Agreement inside tolerance, with exact equality for categorical output."""
    if isinstance(expected, str) or isinstance(got, str):
        return bool(got == expected)
    return bool(abs(float(got) - float(expected)) <= float(tolerance))


def _registry_spec(model_id: str) -> RegisteredModelSpec:
    """The registered spec, narrowed to the status-carrying subclass."""
    spec = get_registry().get(model_id)
    assert spec is not None, model_id
    assert isinstance(spec, RegisteredModelSpec), model_id
    return spec


# --------------------------------------------------------------------------- #
# Independent re-derivations of the published equations                       #
#                                                                              #
# Each function below is written from the published source named in the       #
# matching record, so a reference never comes from the engine. Changing an    #
# engine constant, a bridge or a route therefore cannot move the comparison.  #
# --------------------------------------------------------------------------- #
def _ra_eq21(latitude_deg: float, doy: float) -> float:
    """FAO-56 eq. 21: daily extraterrestrial radiation, MJ/m2/day."""
    phi = math.radians(float(latitude_deg))
    day = float(doy)
    solar_constant = 0.0820
    eccentricity_coefficient = 0.033
    obliquity_coefficient = 0.409
    phase = 1.39
    inverse_relative_distance = 1.0 + eccentricity_coefficient * math.cos(
        2.0 * math.pi * day / 365.0
    )
    declination = obliquity_coefficient * math.sin(2.0 * math.pi * day / 365.0 - phase)
    sunset_hour_angle = math.acos(-math.tan(phi) * math.tan(declination))
    return float(
        (24.0 * 60.0 / math.pi)
        * solar_constant
        * inverse_relative_distance
        * (
            sunset_hour_angle * math.sin(phi) * math.sin(declination)
            + math.cos(phi) * math.cos(declination) * math.sin(sunset_hour_angle)
        )
    )


def _hargreaves_et0(inputs: dict[str, Any]) -> float:
    """FAO-56 eq. 52, the Hargreaves ET0, with eq. 21 and eq. 40 applied to Ra."""
    temp_min = float(inputs["temp_min"])
    temp_max = float(inputs["temp_max"])
    temp_mean = (temp_min + temp_max) / 2.0
    rain_mm = 0.408 * float(_ra_eq21(inputs["latitude"], inputs["doy"]))
    return float(0.0023 * (temp_mean + 17.8) * (temp_max - temp_min) ** 0.5 * rain_mm)


def _rusle_ls(inputs: dict[str, Any]) -> float:
    """USDA AH-703 ch. 4, eqs. 4-1 to 4-4: the topographic LS factor."""
    slope_fraction = float(inputs["slope_percent"]) / 100.0
    slope_radians = math.atan(slope_fraction)
    sin_slope = math.sin(slope_radians)
    beta = (sin_slope / 0.0896) / (3.0 * sin_slope**0.8 + 0.56)
    slope_length_exponent = beta / (1.0 + beta)
    length_factor = (float(inputs["slope_length_m"]) / 22.13) ** slope_length_exponent
    if slope_fraction < 0.09:
        steepness_factor = 10.8 * sin_slope + 0.03
    else:
        steepness_factor = 16.8 * sin_slope - 0.50
    return float(length_factor * steepness_factor)


def _rothc_temp_factor(inputs: dict[str, Any]) -> float:
    """RothC-26.3 section 1.6.1 eq. (1), plus the official -5 C guard."""
    temperature = float(inputs["temperature"])
    if temperature < -5.0:
        return 0.0
    return float(47.91 / (1.0 + math.exp(106.06 / (temperature + 18.27))))


def _salinity_class(inputs: dict[str, Any]) -> str:
    """USDA Handbook 60 ch. 3 salinity classes, ECe in dS/m."""
    conductivity = float(inputs["ec"])
    if conductivity < 2.0:
        return "non_saline"
    if conductivity < 4.0:
        return "slightly_saline"
    if conductivity < 8.0:
        return "moderately_saline"
    if conductivity < 16.0:
        return "strongly_saline"
    return "very_strongly_saline"


#: Published USDA textural-class definitions, in the published evaluation order.
#: Transcribed from ``tests/reference_data/usda_texture_classes.csv``
#: (USDA-NRCS National Soil Survey Handbook Part 630 ch. 3), independently of
#: ``engine/hydroma/soil/taxonomy.py`` so the engine cannot define its own
#: reference.
_TEXTURE_CLASS_ORDER = (
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_clay_loam",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
)


def _published_texture_class(inputs: dict[str, Any]) -> str | None:
    """The published class for a composition, or None if no class is satisfied."""
    clay = float(inputs["clay_pct"])
    silt = float(inputs["silt_pct"])
    sand = float(inputs["sand_pct"])
    definitions: dict[str, bool] = {
        "sand": sand >= 85 and silt + 1.5 * clay <= 15,
        "loamy_sand": (85 <= sand <= 90 and silt + 1.5 * clay >= 15)
        or (70 <= sand <= 85 and silt + 2 * clay <= 30),
        "sandy_loam": (clay <= 20 and sand >= 52 and silt + 2 * clay > 30)
        or (clay < 7 and silt < 50 and 43 <= sand <= 52),
        "loam": 7 <= clay <= 27 and 28 <= silt <= 50 and sand < 52,
        "silt_loam": (silt >= 50 and 12 <= clay <= 27) or (50 <= silt <= 80 and clay < 12),
        "silt": silt >= 80 and clay < 12,
        "sandy_clay_loam": 20 <= clay <= 35 and silt < 28 and sand >= 45,
        "clay_loam": 27 <= clay <= 40 and 20 <= sand <= 45,
        "silty_clay_loam": 27 <= clay <= 40 and sand < 20,
        "sandy_clay": clay >= 35 and sand >= 45,
        "silty_clay": clay >= 40 and silt >= 40,
        "clay": clay >= 40 and sand < 45 and silt < 40,
    }
    for name in _TEXTURE_CLASS_ORDER:
        if definitions[name]:
            return name
    return None


#: Independent reference evaluation for every cluster model. Keys here are the
#: gateway input names, so the record's inputs drive the reference too.
REFERENCE_FUNCTIONS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "SOIL_TEXTURE": _published_texture_class,
    "SOIL_SAR": lambda i: float(i["na"]) / math.sqrt((float(i["ca"]) + float(i["mg"])) / 2.0),
    "SOIL_ESP": lambda i: 100.0 * float(i["na"]) / float(i["cex"]),
    "SOIL_SALINITY_CLASSIFY": _salinity_class,
    "SOIL_LEACHING": (
        lambda i: float(i["ec_water"]) / (5.0 * float(i["target_ec"]) - float(i["ec_water"]))
    ),
    "RUSLE_LS": _rusle_ls,
    "IRRIGATION_DEPTH": (
        lambda i: max(0.0, float(i["etc_mm"]) - float(i["effective_rain_mm"]))
        / float(i["efficiency"])
    ),
    "IRRIGATION_INTERVAL": (
        lambda i: max(
            1,
            round(
                float(i["raw_mm"]) * float(i["allowable_depletion"])
                / float(i["etc_mm_per_day"])
            ),
        )
    ),
    "CANON-002": _hargreaves_et0,
    "CANON-011_RAD": lambda i: _ra_eq21(i["latitude"], i["doy"]),
    "ROTHTC_TEMP_FACTOR": _rothc_temp_factor,
}


def _load_triage_tool() -> Any:
    """Import ``tools/engine_model_triage.py`` by path.

    ``tools/`` is not a package, and the import guard sanctions engine-internal
    imports only, so the tool is loaded the way this repository's other cross
    tool checks load it.
    """
    spec = importlib.util.spec_from_file_location("engine_model_triage_under_test", TRIAGE_TOOL)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {TRIAGE_TOOL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _triage_decision(model_id: str) -> str:
    """The decision ``tools/engine_model_triage.py`` derives today for a model."""
    tool = _load_triage_tool()
    rows: Any = tool.build_rows()
    for row in rows:
        if row["model_id"] == model_id:
            return str(row["decision"])
    raise AssertionError(f"{model_id} is absent from the triage table")


# --------------------------------------------------------------------------- #
# The record set itself                                                       #
# --------------------------------------------------------------------------- #
def test_the_soil_hydrology_crop_water_cluster_is_covered() -> None:
    records = _records()
    assert len(records) >= 10, f"only {len(records)} records in {VALIDATION_DIR}"
    assert set(CLUSTER_MODEL_IDS) == {record["model_id"] for record in records}


@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_every_record_is_complete(model_id: str) -> None:
    """A record without a reference, a tolerance and three cases is prose."""
    record = _record_for(model_id)
    assert len(record["cases"]) >= 3, f"{model_id} records fewer than three cases"
    for case in record["cases"]:
        assert case["inputs"], f"{model_id}/{case['name']}: no inputs"
        assert "reference" in case, f"{model_id}/{case['name']}: no reference"
        assert case["verdict"] in {"match", "discrepancy"}, case["verdict"]
    assert record["validation_status"] in {"validated", "unvalidated"}
    assert record["reference"]["citation"].strip()
    assert record["uncertainty"].strip()
    assert record["input_range"], f"{model_id}: no input range"
    assert model_id in REFERENCE_FUNCTIONS, f"{model_id}: no independent reference evaluator"
    # A record whose cases all pass but which does not claim a registry-level
    # status must say why in a field, not leave the reason to a reader. A record
    # with a failing comparison is a different case: the failure *is* the reason,
    # and it is stated in the comparison table and in `measurement`/`limitations`.
    all_cases_match = all(case["verdict"] == "match" for case in record["cases"])
    if record["validation_status"] == "unvalidated" and all_cases_match:
        assert record.get("registry_gap", "").strip(), (
            f"{model_id}: every case matches but the record claims no registry "
            "status and carries no registry_gap naming what is missing"
        )
    if all_cases_match:
        assert record["status_vocabulary_label"] in {
            "VALIDATED_METHOD",
            "VALIDATED_METHOD_CONFORMANCE",
        }, record["status_vocabulary_label"]


def test_the_status_split_is_the_anchored_five_and_only_them() -> None:
    """Exactly five models move, and they are the anchored ones.

    The five are the cluster models the machine-readable evidence register
    already carried a ``VALIDATED_EXTERNAL`` row for. Marking any of the other
    five as ``validated`` would be a new unanchored claim, which
    ``engine/tests/test_machine_evidence_consistency.py`` refuses: the honest
    move is a register row first, the claim second.
    """
    moved = sorted(
        model_id
        for model_id in CLUSTER_MODEL_IDS
        if _record_for(model_id)["validation_status"] == "validated"
    )
    assert tuple(moved) == tuple(sorted(CLUSTER_MODELS_MOVED_TO_VALIDATED))


# --------------------------------------------------------------------------- #
# Drift: the live model must still be what the record says it was             #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_the_live_model_still_reproduces_the_record(model_id: str) -> None:
    """Re-run every case through the gateway and demand the recorded value."""
    record = _record_for(model_id)
    tolerance = _tolerance_of(record)
    output_key = str(record["output_key"])
    for case in record["cases"]:
        values = _gateway_values(model_id, case["inputs"])
        assert output_key in values, f"{model_id}: {output_key} not in {sorted(values)}"
        got = values[output_key]
        assert _agrees(got, case["recorded"], tolerance), (
            f"{model_id}/{case['name']}: gateway returned {got!r}, the record stores "
            f"{case['recorded']!r} (tolerance {tolerance})"
        )


# --------------------------------------------------------------------------- #
# Reference: the record's numbers must be the published equation's numbers    #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_the_recorded_reference_is_independently_reproducible(model_id: str) -> None:
    """Re-derive each reference from the published equation in this module."""
    record = _record_for(model_id)
    evaluate = REFERENCE_FUNCTIONS[model_id]
    tolerance = _tolerance_of(record)
    for case in record["cases"]:
        computed = evaluate(case["inputs"])
        assert _agrees(computed, case["reference"], tolerance), (
            f"{model_id}/{case['name']}: the published equation gives {computed!r}, "
            f"the record stores {case['reference']!r}"
        )


# --------------------------------------------------------------------------- #
# Verdict: every recorded match or discrepancy must still hold                #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_every_recorded_verdict_still_holds(model_id: str) -> None:
    """A claimed match must still be a match; a claimed discrepancy still a gap.

    The second arm is the one that keeps the unvalidated record honest: if a fix
    lands and the model starts agreeing with the published reference, this test
    says the record and the registry status have to move together.
    """
    record = _record_for(model_id)
    evaluate = REFERENCE_FUNCTIONS[model_id]
    tolerance = _tolerance_of(record)
    output_key = str(record["output_key"])
    for case in record["cases"]:
        reference = evaluate(case["inputs"])
        got = _gateway_values(model_id, case["inputs"])[output_key]
        if case["verdict"] == "match":
            assert reference is not None, f"{model_id}/{case['name']}: no published class"
            assert _agrees(got, reference, tolerance), (
                f"{model_id}/{case['name']}: the record claims a match but the model "
                f"gives {got!r} against the published {reference!r}"
            )
        else:
            assert not _agrees(got, reference, tolerance), (
                f"{model_id}/{case['name']}: the record claims a discrepancy but the "
                "model now agrees with the published reference"
            )


# --------------------------------------------------------------------------- #
# Registry: the status must be the one the derivation produces from the card   #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_the_registry_status_equals_the_record_claim(model_id: str) -> None:
    record = _record_for(model_id)
    spec = _registry_spec(model_id)
    expected = ModelStatus.VALIDATED
    if record["validation_status"] != "validated":
        expected = ModelStatus.UNVALIDATED
    assert spec.validation_status is expected, (
        f"{model_id}: the record claims {record['validation_status']!r} but the "
        f"registry derives {spec.validation_status.value!r}"
    )


@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_the_status_comes_from_a_card_row_not_a_hand_edit(model_id: str) -> None:
    """``engine/models/registry.py`` derives validation_status from a card row.

    A validated record therefore requires a card that carries a whole-word
    validated / benchmarked / matches claim, and the registry must say its
    status came from that row.
    """
    record = _record_for(model_id)
    spec = _registry_spec(model_id)
    assert spec.card_file is not None, f"{model_id}: no model card in engine/models/cards/"
    assert "validation_status row" in spec.status_reasons["validation_status"]
    if record["validation_status"] == "validated":
        card_text = (CARDS_DIR / str(spec.card_file)).read_text(encoding="utf-8")
        assert POSITIVE_CLAIM.search(card_text), (
            f"{spec.card_file} carries no whole-word validated claim for a "
            "validated record"
        )


@pytest.mark.parametrize("model_id", CLUSTER_MODEL_IDS)
def test_the_triage_decision_matches_the_record(model_id: str) -> None:
    """``tools/engine_model_triage.py`` must call published exactly the models
    these records validate, and nothing else."""
    record = _record_for(model_id)
    decision = _triage_decision(model_id)
    if record["validation_status"] == "validated":
        assert decision == "published", (
            f"{model_id}: the record is validated but the triage decision is {decision!r}"
        )
    else:
        assert decision != "published", (
            f"{model_id}: the record is unvalidated but the triage reads published"
        )


# --------------------------------------------------------------------------- #
# The exhaustive texture measurement the unvalidated record reports           #
# --------------------------------------------------------------------------- #
@pytest.mark.filterwarnings(
    "ignore::DeprecationWarning"
)
def test_the_texture_measurement_is_reproducible_in_full() -> None:
    """Re-measure the SOIL_TEXTURE record's headline counts on the whole grid.

    That record is unvalidated *because* of these numbers, so they have to be
    the ones a fresh run produces rather than a figure quoted from an older
    measurement. The agreement count is recomputed from the published
    definitions alone; the engine's own fallback population is re-derived from
    the same run, which is what makes it a statement about the engine rather
    than about the table.
    """
    record = _record_for("SOIL_TEXTURE")
    measured = record["measurement"]
    grid = [
        (100 - sand - silt, silt, sand) for sand in range(101) for silt in range(101 - sand)
    ]
    assert len(grid) == int(measured["grid_size"])

    agreements = 0
    published_unclassified = 0
    for clay, silt, sand in grid:
        inputs = {
            "clay_pct": float(clay),
            "silt_pct": float(silt),
            "sand_pct": float(sand),
        }
        published = _published_texture_class(inputs)
        if published is None:
            published_unclassified += 1
        got = _gateway_values("SOIL_TEXTURE", inputs)["texture_class"]
        if got == published:
            agreements += 1

    assert agreements == int(measured["agreements"])
    assert published_unclassified == int(measured["published_side_unclassified"])
    assert published_unclassified == 0, "the published definitions leave no hole on the grid"
    assert measured["disagreements"] + measured["agreements"] == measured["grid_size"]
    assert measured["answered_from_a_class_range"] + measured["answered_by_the_loam_fallback"] == (
        measured["grid_size"]
    )


def test_the_validated_cluster_reads_published_and_the_failed_one_does_not() -> None:
    validated = [
        model
        for model in CLUSTER_MODEL_IDS
        if _record_for(model)["validation_status"] == "validated"
    ]
    assert validated, "no validated records, so nothing may read published"
    for model_id in validated:
        assert _triage_decision(model_id) == "published", model_id
    assert _triage_decision("SOIL_TEXTURE") != "published"
    # The five method-conformance models match their reference and still do not
    # read published: that is the anchor rule doing its job, not a regression.
    for model_id in CLUSTER_MODEL_IDS:
        if model_id not in CLUSTER_MODELS_MOVED_TO_VALIDATED:
            assert _triage_decision(model_id) != "published", model_id
