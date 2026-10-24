# Novel-Index Readiness — the v3.1 §6.2 precondition

Generated: 2026-10-10 by `tools/novel_index_gate.py`.

**Constitutional rule** (`ECO-NOJIN_MASTER_v3.1_UNIFIED.md` §6.2,
SB-06 / AR-03): FDII · CDHE · CMSI · WSNI · RRI · IWEq · WAI · WVI · PSI · CW
no novel index may be implemented or registered without a **published
definition plus an independent reference anchor** (the FAO-56 Example 18
pattern). An implementation before the precondition is met is an SB-06
violation, so the ten `NOT IMPLEMENTED` rows below are the honest finding,
not a failure.

## 1. The ten novel indices

| Index | Name | Business role (§6.2) | Card in `indicators/` | `evidence_class` | Precondition verdict |
|---|---|---|---|---|---|
| FDII | Flash Drought Intensity Index | early warning in H2 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| CDHE | Compound Drought-Heat Index | crop risk / insurance in H1 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| CMSI | Crop Multi-Stress Index | supplier ranking H1/H7 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| WSNI | Water-Soil Nexus Index | supplier sustainability H5 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| RRI | Restoration Readiness Index | H7 service prioritisation | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| IWEq | Intergenerational Water Equity | ESG reporting H4 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| WAI | Water Access Index | irrigation priority regions | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| WVI | Water Vulnerability Index | supply-chain risk H2 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| PSI | Production Stability Index | supplier ranking | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |
| CW | Cost of Water | product pricing H6 | no | — | NOT IMPLEMENTED — precondition not met (no published definition) |

## 2. Indicator cards scanned in `indicators/`

| File | `indicator_id` | `validation_status` | `evidence_class` | Status | Notes |
|---|---|---|---|---|---|
| `_TEMPLATE.yaml` | — | — | — | EXEMPT_TEMPLATE | template/placeholder — exempt from the gate |
| `ENO_ET0_FAO56_001.yaml` | ENO_ET0_FAO56_001 | VALIDATED_FAO56_EXAMPLE18 | VALIDATED_METHOD_CONFORMANCE | SUPPORTED | published reference: Allen et al. 1998, FAO Paper 56 |
| `ENO_ETC_KC_001.yaml` | ENO_ETC_KC_001 | REFERENCE_DATA_REQUIRED | VALIDATED_METHOD_CONFORMANCE | SUPPORTED | published reference: FAO-56 Chapter 6 |
| `ENO_SPI_001.yaml` | ENO_SPI_001 | VALIDATED_METHOD_CONFORMANCE | VALIDATED_METHOD_CONFORMANCE | SUPPORTED | published reference: McKee et al. 1993; WMO No. 1090 |
| `ENO_WB_001.yaml` | ENO_WB_001 | VALIDATED_MASS_CONSERVATION | VALIDATED_METHOD_CONFORMANCE | SUPPORTED | published reference: Water balance equation (Thornthwaite/FAO-56 style mass balance) |
| `ENO_WP_001.yaml` | ENO_WP_001 | VALIDATED_UNIT_DEFINITION | VALIDATED_METHOD_CONFORMANCE | SUPPORTED | published reference: FAO WaPOR (Water Productivity database) |

## 3. Gate result

- cards scanned: 6 (supported 5, template-exempt 1, blocked 0)
- novel indices with a card: 0 of 10
- novel indices meeting the precondition: 0 of 10

Exit rule: 0 when no unsupported indicator file exists (the template is exempt);
1 when any indicator file is BLOCKED_NO_PUBLISHED_DEFINITION.

```
SUMMARY novel_indices=10 with_card=0 cards_scanned=6 supported=5 exempt=1 blocked=0 exit=0
```
