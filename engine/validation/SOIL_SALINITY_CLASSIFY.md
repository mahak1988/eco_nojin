# Validation Evidence — SOIL_SALINITY_CLASSIFY

**Model:** `SOIL_SALINITY_CLASSIFY` — Salinity Class Classification (registry version `1.0.0`)
**Cluster:** soil chemistry / salinity
**Gateway route:** `engine/gateway/model_dispatcher.py::_route_soil_salinity_classify`
**Implementation:** `engine/hydroma/soil/salinity.py::classify_salinity`
**Model card:** `engine/models/cards/SOIL_SALINITY_CLASSIFY_salinity_classes.md`
**Re-verified by:** `engine/validation/test_validation_records.py`

---

## 1. Published reference

**Citation.** U.S. Salinity Laboratory (Richards, L.A., ed.), *Diagnosis and
Improvement of Saline and Alkali Soils*, USDA Agriculture Handbook 60, 1954,
Chapter 3 ("Classification of salt-affected soils"): the saline classes are
defined by the electrical conductivity of the saturation extract, ECe, in
decisiemens per metre (dS/m):

| Class | ECe range (dS/m) |
|---|---|
| non-saline | 0 – 2 |
| slightly saline | 2 – 4 |
| moderately saline | 4 – 8 |
| strongly saline | 8 – 16 |
| very strongly saline | > 16 |

The same five-class scale, with the same four break values, is tabulated as
Table 1 of Ayers, R.S. & Westcot, D.W., *Water Quality for Agriculture*, FAO
Irrigation and Drainage Paper 29 (Rev. 1), 1985, chapter 2.

**How the reference values below were obtained.** The reference column is the
published band selected by comparing the input against the four published break
values written out in the test module (`ec < 2 -> non_saline`, `ec < 4 ->
slightly_saline`, `ec < 8 -> moderately_saline`, `ec < 16 -> strongly_saline`,
otherwise `very_strongly_saline`). No engine module is consulted.

---

## 2. Input range

| Input | Symbol | Unit | Range compared |
|---|---|---|---|
| Electrical conductivity of saturation extract | `ec` | dS/m | 0.5 – 20.0 |

Domain constraints: `ec >= 0`. Every break value of the published table is
included, because a classification model is only trustworthy at its boundaries
and not in the middle of its bands: the cases are 0.5 (inside a band), 2.0 and
4.0 (on the first two break values), 3.0, 6.0, 12.0 (inside bands) and 8.0, 16.0
(the remaining two break values) and 20.0 (inside the top band).

**Boundary convention.** Handbook 60 writes each class as a closed range ending at
the break value (`0 - 2`, `2 - 4`, ...). The implementation assigns an input
sitting exactly on a break value to the *higher* class, so ECe = 2.0 reads
`slightly_saline` and ECe = 16.0 reads `very_strongly_saline`. That is the
reading the published closed ranges give and is asserted below; the alternative
would leave ECe = 2.0 in no class at all.

---

## 3. Tolerance

`tolerance_absolute = 0` — the output is categorical, so the only honest notion of
tolerance is exact equality of the class label. The test asserts string equality.

---

## 4. Comparison table — model output vs reference output

| # | Input `ec` (dS/m) | Model output `classification` | Published class | Verdict |
|---|---|---|---|---|
| 1 | 0.5 | `non_saline` | non-saline | match |
| 2 | 2.0 | `slightly_saline` | slightly saline | match |
| 3 | 3.0 | `slightly_saline` | slightly saline | match |
| 4 | 4.0 | `moderately_saline` | moderately saline | match |
| 5 | 6.0 | `moderately_saline` | moderately saline | match |
| 6 | 8.0 | `strongly_saline` | strongly saline | match |
| 7 | 12.0 | `strongly_saline` | strongly saline | match |
| 8 | 16.0 | `very_strongly_saline` | very strongly saline | match |
| 9 | 20.0 | `very_strongly_saline` | very strongly saline | match |

All four published break values and both interiors of every band agree.

---

## 5. Uncertainty statement

The comparison is **exact, discrete and complete over the published domain**: for
every non-negative input the model returns one of the five published classes, and
the return value is determined by the four published break values alone. Because
the model has no free parameters and no continuous output, there is no
propagated numeric uncertainty at all — the only failure mode available is
choosing the wrong band, and the nine cases above cover every band and every
break value.

What is *not* established is that the ECe supplied to the model is the ECe of the
soil. The published classes are defined on the saturation extract, which has to
be measured (or estimated from a field bulk-EC measurement with a saturation
estimate); the model cannot detect an input that is a 1:5 extract reading or a
salient soil-water EC instead. The record therefore credits the classification
rule, not the soil.

---

## 6. Limitations

1. The record validates the *classification rule* only. It does not validate that
   a given `ec` input is a saturation-extract conductivity.
2. Handbook 60's classification of salt-affected soils also uses ESP, which this
   model does not take. A soil with ECe in the non-saline band can still be sodic,
   and this model will say nothing about that.
3. The upper class is unbounded: Handbook 60 does not cap "very strongly saline",
   and neither does the implementation. Very high ECe values are therefore
   reported exactly, with the same label as ECe = 16.1.

---

## 7. Machine-readable comparison

Schema `hydroma.validation.record@1`. `reference` and `recorded` are class labels;
the tolerance is exact equality.

```json
{
  "schema": "hydroma.validation.record@1",
  "model_id": "SOIL_SALINITY_CLASSIFY",
  "model_name": "Salinity Class Classification",
  "model_version": "1.0.0",
  "gateway_route": "engine/gateway/model_dispatcher.py::_route_soil_salinity_classify",
  "reference": {
    "citation": "U.S. Salinity Laboratory (Richards, L.A., ed.), Diagnosis and Improvement of Saline and Alkali Soils, USDA Agriculture Handbook 60, 1954, ch. 3; restated as Table 1 of Ayers & Westcot, Water Quality for Agriculture, FAO Irrigation and Drainage Paper 29 (Rev. 1), 1985, ch. 2.",
    "equation": "non_saline: ECe < 2; slightly_saline: 2 <= ECe < 4; moderately_saline: 4 <= ECe < 8; strongly_saline: 8 <= ECe < 16; very_strongly_saline: ECe >= 16, ECe in dS/m"
  },
  "input_range": {
    "ec_ds_per_m": [0.5, 20.0]
  },
  "output_key": "classification",
  "tolerance": {
    "absolute": 0.0,
    "basis": "the output is categorical; the only honest notion of tolerance is exact equality of the class label"
  },
  "cases": [
    {
      "name": "inside_the_lowest_band",
      "inputs": {"ec": 0.5},
      "reference": "non_saline",
      "recorded": "non_saline",
      "verdict": "match"
    },
    {
      "name": "on_the_first_break_value",
      "inputs": {"ec": 2.0},
      "reference": "slightly_saline",
      "recorded": "slightly_saline",
      "verdict": "match"
    },
    {
      "name": "inside_the_slightly_saline_band",
      "inputs": {"ec": 3.0},
      "reference": "slightly_saline",
      "recorded": "slightly_saline",
      "verdict": "match"
    },
    {
      "name": "on_the_second_break_value",
      "inputs": {"ec": 4.0},
      "reference": "moderately_saline",
      "recorded": "moderately_saline",
      "verdict": "match"
    },
    {
      "name": "inside_the_moderately_saline_band",
      "inputs": {"ec": 6.0},
      "reference": "moderately_saline",
      "recorded": "moderately_saline",
      "verdict": "match"
    },
    {
      "name": "on_the_third_break_value",
      "inputs": {"ec": 8.0},
      "reference": "strongly_saline",
      "recorded": "strongly_saline",
      "verdict": "match"
    },
    {
      "name": "inside_the_strongly_saline_band",
      "inputs": {"ec": 12.0},
      "reference": "strongly_saline",
      "recorded": "strongly_saline",
      "verdict": "match"
    },
    {
      "name": "on_the_fourth_break_value",
      "inputs": {"ec": 16.0},
      "reference": "very_strongly_saline",
      "recorded": "very_strongly_saline",
      "verdict": "match"
    },
    {
      "name": "inside_the_top_band",
      "inputs": {"ec": 20.0},
      "reference": "very_strongly_saline",
      "recorded": "very_strongly_saline",
      "verdict": "match"
    }
  ],
  "validation_status": "validated",
  "status_vocabulary_label": "VALIDATED_METHOD",
  "uncertainty": "No propagated numeric uncertainty: the model has no free parameters and no continuous output. The only failure mode available is choosing the wrong published band, and every band and every break value is compared above.",
  "limitations": [
    "The classification rule is validated, not that the supplied ec is a saturation-extract conductivity.",
    "The published classification of salt-affected soils also uses ESP, which this model does not take.",
    "The top class is unbounded, as in the published table."
  ]
}
```
