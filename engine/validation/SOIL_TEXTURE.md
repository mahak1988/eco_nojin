# Validation Evidence — SOIL_TEXTURE

**Model:** `SOIL_TEXTURE` — USDA Soil Textural Class (registry version `1.0.0`)
**Cluster:** soil texture classification / soil hydrology
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_soil_texture`
**Implementation:** `engine/hydroma/soil/texture.py::classify_texture`
(delegating to `engine/hydroma/soil/taxonomy.py::_determine_texture_class`)
**Model card:** `engine/models/cards/SOIL_TEXTURE_usda_texture_classes.md`
**Re-verified by:** `engine/validation/test_validation_records.py`

> **Outcome: the model does NOT match its published reference and stays
> `unvalidated`.** The engine's texture classifier agrees with the published USDA
> class definitions on **4170 of 5151** compositions across the whole
> sand/silt/clay triangle (**80.96 %**). It answers from a class range at all on
> 4369 of them (**84.82 %**) and falls through to a documented `loam` fallback on
> the remaining **782 (15.18 %)**. This record keeps the disagreement and records
> it; it does not credit the model.

---

## 1. Published reference

**Citation.** United States Department of Agriculture, Natural Resources
Conservation Service, National Soil Survey Handbook, Part 630, *Soil Survey
Manual*, Chapter 3 ("Soil Properties, Qualities, and Interpretations"), the
twelve-class USDA textural triangle. The working transcription held in this
repository is `tests/reference_data/usda_texture_classes.csv`, with
`definition_published` given as machine-readable `clay/silt/sand` bounding
boxes, `source_organization: USDA-NRCS`, `source_document: National Soil Survey
Handbook Part 630 Chapter 3` and `source_url:
https://www.nrcs.usda.gov/resources/guides-and-instructions/soil-survey-manual`;
`meta.json` records `measurement_kind: machine-readable USDA class definitions`,
`attribution: published (not derived)`, `hand_transcribed: true`.

The twelve published classes and their definitions as transcribed:

| Class | Definition (clay / silt / sand, %) |
|---|---|
| sand | sand >= 85 and silt + 1.5 clay <= 15 |
| loamy sand | (85 <= sand <= 90 and silt + 1.5 clay >= 15) or (70 <= sand <= 85 and silt + 2 clay <= 30) |
| sandy loam | (clay <= 20 and sand >= 52 and silt + 2 clay > 30) or (clay < 7 and silt < 50 and 43 <= sand <= 52) |
| loam | 7 <= clay <= 27 and 28 <= silt <= 50 and sand < 52 |
| silt loam | (silt >= 50 and 12 <= clay <= 27) or (50 <= silt <= 80 and clay < 12) |
| silt | silt >= 80 and clay < 12 |
| sandy clay loam | 20 <= clay <= 35 and silt < 28 and sand >= 45 |
| clay loam | 27 <= clay <= 40 and 20 <= sand <= 45 |
| silty clay loam | 27 <= clay <= 40 and sand < 20 |
| sandy clay | clay >= 35 and sand >= 45 |
| silty clay | clay >= 40 and silt >= 40 |
| clay | clay >= 40 and sand < 45 and silt < 40 |

**How the reference values below were obtained.** The reference class for a given
composition is the first class in the published evaluation order
(`sand, loamy_sand, sandy_loam, loam, silt_loam, silt, sandy_clay_loam,
clay_loam, silty_clay_loam, sandy_clay, silty_clay, clay`) whose published
definition the composition satisfies. The order and the definitions are the ones
in `tests/reference_data/usda_texture_classes.csv`, read independently in the
test module. No engine module — in particular not
`engine/hydroma/soil/taxonomy.py::TEXTURE_CLASSES` — is consulted when the
reference class is produced.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Sand content | `sand_pct` | % | 0 – 100 |
| Silt content | `silt_pct` | % | 0 – 100 |
| Clay content | `clay_pct` | % | 0 – 100 |

Domain constraints: the three fractions must sum to 100 and be non-negative,
which the published triangle itself requires. The comparison is exhaustive
rather than sampled: **all 5151 integer compositions** (every `(clay, silt, sand)`
with `clay + silt + sand = 100` and each component between 0 and 100) were run
through the gateway and compared against the published definitions. That is a
complete comparison over the discrete triangle at 1 % resolution, which is the
resolution at which a soil laboratory reports particle-size fractions.

---

## 3. Tolerance

`tolerance_absolute = 0` — the output is a class label, so the only honest notion
of tolerance is exact equality of the label. The test asserts string equality and
counts the mismatches.

---

## 4. Comparison table — model output vs published reference

Twelve cases, chosen to include both the agreements and the disagreements the
exhaustive comparison finds. The last column gives the exhaustive verdict for
that composition.

| # | clay / silt / sand (%) | Model output | Published class | Verdict |
|---|---|---|---|---|
| 1 | 5 / 90 / 5 | silt | silt | match |
| 2 | 20 / 40 / 40 | loam | loam | match |
| 3 | 15 / 25 / 60 | sandy_loam | sandy_loam | match |
| 4 | 30 / 35 / 35 | clay_loam | clay_loam | match |
| 5 | 40 / 10 / 50 | sandy_clay | sandy_clay | match |
| 6 | 42 / 48 / 10 | silty_clay | silty_clay | match |
| 7 | 25 / 15 / 60 | sandy_clay_loam | sandy_clay_loam | match |
| 8 | 60 / 30 / 10 | clay | clay | match |
| 9 | 5 / 10 / 85 | **sand** | **loamy sand** | **discrepancy** |
| 10 | 15 / 55 / 30 | **loam** | **silt loam** | **discrepancy** |
| 11 | 5 / 45 / 50 | **loam** | **sandy loam** | **discrepancy** |
| 12 | 10 / 45 / 45 | loam | loam | match |

Case 9 is the clearest failure: at sand 85, silt 10, clay 5 the published
definition requires `silt + 1.5 clay = 17.5 > 15`, so the composition is **loamy
sand**; the engine returns **sand** because its class box starts at `sand >= 85`
and its condition is evaluated differently. Cases 10 and 11 are fallback
failures: compositions that satisfy no class range and fall through to the
documented `loam` default, which is not what the published table assigns.

### 4a. Exhaustive comparison over the whole triangle

| Population | Count | Share |
|---|---|---|
| Integer compositions on the triangle | 5151 | 100.00 % |
| Compositions the engine answers from a class range | 4369 | 84.82 % |
| Compositions answered by the documented `loam` fallback | 782 | 15.18 % |
| Model agrees with the published class | 4170 | 80.96 % |
| Model disagrees with the published class | 981 | 19.04 % |
| Disagreements among the answered population | 199 of 4369 | 4.55 % |

The five commonest disagreement pairs (engine label vs published label) are

| Engine | Published | Occurrences |
|---|---|---|
| loamy_sand | sandy_loam | 114 |
| sand | loamy_sand | 30 |
| loam | sandy_loam | 13 |
| silt | silt_loam | 12 |
| silty_clay_loam | clay_loam | 7 |

The dominant mode is a systematic one-class shift along the
`sand -> loamy_sand -> sandy_loam -> loam` sequence and, separately, the
`loam` fallback swallowing the silt-bearing sandy loams. Those are the classes
that select texture-dependent parameters for every downstream soil-water and
PTF model in the registry, so the misclassification is not cosmetic.

---

## 5. Uncertainty statement

**No credit is claimed.** The comparison is exhaustive over the discrete triangle
at 1 % resolution and finds the model wrong on 981 of 5151 compositions (19.04 %),
wrong on 199 of the 4369 compositions it answers at all (4.55 %), and falling back
to a default label on 782 (15.18 %). A model that is wrong on one composition in
five against its own published table is not validated, and the registry is left
to report it as `unvalidated`.

The measured quantity has no sampling uncertainty: every integer composition on
the triangle is compared, so the counts above are exact rather than estimates.
If a caller works at finer resolution than 1 % the rate will differ by however
much the boundary errors smear, but nothing in the exhaustive comparison suggests
it improves — the disagreements concentrate at the class boundaries, where finer
resolution produces more of them, not fewer.

Two further measurements, both independent of the engine's own class boxes:

* **the published definitions cover the whole grid.** All 5151 integer
  compositions satisfy at least one published class. The engine's own fallback is
  therefore not a hole in the published table, it is a hole in the engine's
  boxes;
* the published table does contain overlapping conditions (several classes'
  definitions are satisfied by the same composition, which is why an evaluation
  order is needed). The order applied here is the one the repository's own
  transcription states. A different order moves the reference class for boundary
  compositions and can only change *which* compositions are counted as
  disagreements, not whether disagreements exist.

---

## 6. Limitations / findings for whoever fixes this

1. **`loam` fallback.** `_determine_texture_class` ends with a documented
   `Textures that do not fit any class range (fallback) = "loam"`. 782
   compositions reach it, while the published definitions cover all 5151 — so
   the gap is the engine's, not the table's. A fallback to the single
   most-common soil class is not a classification; it silently converts a gap in
   the class boxes into a confident answer that then feeds texture-keyed
   parameter lookups.
2. **The `sand` boundary condition.** The engine's `sand` box appears to accept
   sand >= 85 without the published `silt + 1.5 clay <= 15` conjunction, which is
   the source of at least the 30 `sand` vs `loamy_sand` disagreements.
3. **`loamy_sand` / `sandy_loam` adjacency.** 114 compositions are assigned
   `loamy_sand` where the published definition says `sandy_loam`. The two
   published definitions are not nested, so a single range-box representation
   cannot express both; a definition-order evaluator rather than a
   range lookup would.
4. **Existing guards are rate guards, not agreement guards.** The internal
   check quoted in `engine/hydroma/soil/taxonomy.py` sets
   `AGREEMENT_FLOOR = 0.848`, but it compares the engine against *itself*
   (`_turtle_class` vs `_turtle_from_range_boxes` over compositions the boxes
   cover). It therefore passes at 100 % while saying nothing about agreement with
   the published table, which the exhaustive comparison above measures at
   80.96 %. The internal consistency check and the external comparison are
   different measurements and conflating them is the trap.
5. **Not validated, deliberately.** Per the program's rule, a model that cannot
   be validated honestly stays `unvalidated`. `engine/validation/
   test_validation_records.py` still re-runs these cases, so any fix is verified
   by the same route, and the record's exhaustive figures are the number to beat.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`. `validation_status` is `unvalidated` and the
record carries `verdict: "discrepancy"` cases, so the test asserts that the
disagreement is still real rather than treating it as drift.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "SOIL_TEXTURE",
  "model_name": "USDA Soil Textural Class",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_soil_texture",
  "reference": {
    "citation": "USDA-NRCS, National Soil Survey Handbook Part 630, Soil Survey Manual, ch. 3 (twelve-class USDA textural triangle); machine-readable transcription held at tests/reference_data/usda_texture_classes.csv (source_url https://www.nrcs.usda.gov/resources/guides-and-instructions/soil-survey-manual).",
    "equation": "first matching class in the published evaluation order whose clay/silt/sand defining conditions the composition satisfies"
  },
  "input_range": {
    "clay_pct": [0.0, 100.0],
    "silt_pct": [0.0, 100.0],
    "sand_pct": [0.0, 100.0],
    "note": "the three fractions must sum to 100; the comparison is exhaustive over all 5151 integer compositions on the triangle"
  },
  "output_key": "texture_class",
  "tolerance": {
    "absolute": 0.0,
    "basis": "the output is a class label; the only honest notion of tolerance is exact equality"
  },
  "cases": [
    {
      "name": "silt_exact_match",
      "inputs": {"clay_pct": 5.0, "silt_pct": 90.0, "sand_pct": 5.0},
      "reference": "silt",
      "recorded": "silt",
      "verdict": "match"
    },
    {
      "name": "loam_exact_match",
      "inputs": {"clay_pct": 20.0, "silt_pct": 40.0, "sand_pct": 40.0},
      "reference": "loam",
      "recorded": "loam",
      "verdict": "match"
    },
    {
      "name": "sandy_loam_exact_match",
      "inputs": {"clay_pct": 15.0, "silt_pct": 25.0, "sand_pct": 60.0},
      "reference": "sandy_loam",
      "recorded": "sandy_loam",
      "verdict": "match"
    },
    {
      "name": "clay_loam_exact_match",
      "inputs": {"clay_pct": 30.0, "silt_pct": 35.0, "sand_pct": 35.0},
      "reference": "clay_loam",
      "recorded": "clay_loam",
      "verdict": "match"
    },
    {
      "name": "sandy_clay_exact_match",
      "inputs": {"clay_pct": 40.0, "silt_pct": 10.0, "sand_pct": 50.0},
      "reference": "sandy_clay",
      "recorded": "sandy_clay",
      "verdict": "match"
    },
    {
      "name": "silty_clay_exact_match",
      "inputs": {"clay_pct": 42.0, "silt_pct": 48.0, "sand_pct": 10.0},
      "reference": "silty_clay",
      "recorded": "silty_clay",
      "verdict": "match"
    },
    {
      "name": "sandy_clay_loam_exact_match",
      "inputs": {"clay_pct": 25.0, "silt_pct": 15.0, "sand_pct": 60.0},
      "reference": "sandy_clay_loam",
      "recorded": "sandy_clay_loam",
      "verdict": "match"
    },
    {
      "name": "clay_exact_match",
      "inputs": {"clay_pct": 60.0, "silt_pct": 30.0, "sand_pct": 10.0},
      "reference": "clay",
      "recorded": "clay",
      "verdict": "match"
    },
    {
      "name": "sand_vs_loamy_sand_boundary",
      "inputs": {"clay_pct": 5.0, "silt_pct": 10.0, "sand_pct": 85.0},
      "reference": "loamy_sand",
      "recorded": "sand",
      "verdict": "discrepancy"
    },
    {
      "name": "loam_fallback_vs_silt_loam",
      "inputs": {"clay_pct": 15.0, "silt_pct": 55.0, "sand_pct": 30.0},
      "reference": "silt_loam",
      "recorded": "loam",
      "verdict": "discrepancy"
    },
    {
      "name": "loam_fallback_vs_sandy_loam",
      "inputs": {"clay_pct": 5.0, "silt_pct": 45.0, "sand_pct": 50.0},
      "reference": "sandy_loam",
      "recorded": "loam",
      "verdict": "discrepancy"
    },
    {
      "name": "loam_exact_match_second",
      "inputs": {"clay_pct": 10.0, "silt_pct": 45.0, "sand_pct": 45.0},
      "reference": "loam",
      "recorded": "loam",
      "verdict": "match"
    }
  ],
  "measurement": {
    "grid": "all integer compositions with clay + silt + sand = 100 and each component in 0..100",
    "grid_size": 5151,
    "answered_from_a_class_range": 4369,
    "answered_by_the_loam_fallback": 782,
    "published_definitions_cover_the_whole_grid": true,
    "published_side_unclassified": 0,
    "agreements": 4170,
    "disagreements": 981,
    "agreement_rate_full_grid": 0.8095521,
    "agreement_rate_among_answered": 0.9544516
  },
  "validation_status": "unvalidated",
  "status_vocabulary_label": "PARTIAL",
  "uncertainty": "The counts are exact, not estimates: every integer composition on the triangle is compared, so there is no sampling uncertainty. The published table itself overlaps, so the reference class depends on the documented evaluation order, but the 15.18 % fallback population is order-independent because those compositions satisfy no published class box.",
  "limitations": [
    "The model disagrees with the published USDA definitions on 981 of 5151 integer compositions (19.04 %), including 199 of the 4369 it answers at all (4.55 %).",
    "782 compositions (15.18 %) fall through to the documented loam fallback, which is not a classification.",
    "The internal AGREEMENT_FLOOR check compares the engine against its own range boxes and passes at 100 %; it is not an external comparison.",
    "The registry is deliberately left reporting unvalidated for this model."
  ]
}
```
