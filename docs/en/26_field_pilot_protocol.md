# Field Pilot Protocol — 3 Villages (Phase 10, star 15)

**Status:** protocol (ready for field season) · **Owner:** Eco Nojin + university partner (TBD)

## 1. Objective
Validate real Sentinel-2 NDVI products against on-ground truth and measure farmer
adoption of the advisory loop (NDVI → irrigation/drought advice → action).

## 2. Site Selection (criteria)
- 3 villages across distinct agro-climatic zones (e.g., semiarid rainfed, irrigated plain, cold highland).
- Each village: ≥ 10 consenting farms with ≥ 1 ha wheat or barley fields.
- Access to field for 2 ground visits per season.

## 3. Data Protocol

| Layer | Source | Frequency | Use |
|---|---|---|---|
| NDVI (10 m) | Sentinel-2 via CDSE (Phase 4 pipeline) | 5-day (cloud-masked) | Index + advice |
| Ground NDVI | handheld NDVI meter / phone app | biweekly, 5 points/field | Validation |
| Biomass/yield | crop-cut at harvest | end of season | Ground truth |
| Soil moisture | portable probe | biweekly | Correlate NDVI |
| Farmer log | app/paper | weekly | Adoption metric |

## 4. Validation Metrics
- R² and RMSE of satellite NDVI vs ground NDVI (target R² ≥ 0.7).
- Yield prediction error (target MAPE ≤ 20% at village level).
- Adoption: % farmers following ≥ 60% of advice items; qualitative interviews.

## 5. Ethics & Consent
- Written informed consent (plain Persian), data ownership stays with farmers;
  anonymized aggregate only in publications. No incentive beyond free advice.

## 6. University Collaboration (joint paper)
- Joint protocol sign-off; shared dataset w/ DOI via Zenodo (Phase 9 ⭐9);
  co-authorship matrix agreed before data collection.

## 7. Deliverables
- Pilot report (fa + en), validation stats, farmer feedback summary, paper draft.

## 8. Go/No-Go for wider rollout
- R² ≥ 0.7 AND MAPE ≤ 20% AND ≥ 60% adoption in ≥ 2 villages → scale to province.
