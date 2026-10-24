# EQUATION DIVERGENCE REGISTER

Document id: `ECO-10-EQUATION-DIVERGENCE-REGISTER` · Verified: 2026-10-10 · Source: GAP-REGISTER G-H6 and the formula audit.
Method: code reading. Every `file:line` below was re-read from the live tree on the verification date; where the audit's path no longer resolves, the resolved path is written and the audited name is kept in parentheses so the audit trail survives.

Scope: **internal** divergence — the same equation implemented more than once in this repository, with the copies not agreeing. This is distinct from `DEVIATION-REGISTER.md`, which records where the code disagrees with a *published standard*.

No equation was changed in the course of producing this register. Rows marked *equivalent* are recorded as **not** defects: they are duplicated-but-agreeing implementations, and the only cost is the number of places a future edit has to reach.

---

## 1. Register

| equation | copies (count) | locations (file:line) | canonical | measured divergence |
|---|---|---|---|---|
| RUSLE LS | **3 forms** | `engine/land/erosion_risk.py:125-146` (McCool-1999-labelled set with the `−0.045·cos²θ` term in the steep branch); `engine/cpp_core/src/erosion.cpp:22-46` + `engine/hydroma/wrapper.py:212-226` (AH-703, the canonical pair); `services/_contracts/formula.py:126-155` (Foster & Nearing slope-only polynomial, no length factor) | `engine/cpp_core/src/erosion.cpp:22-46` and `engine/hydroma/wrapper.py:212-226` (USDA AH-703, Renard et al. 1997) — the pair verified externally | **LS differs per input**: the slope-only form carries no `L` factor at all and the Foster/Nearing and Wischmeier–Smith forms disagree by ~3.7× at 3° (documented at `formula.py:139-143`) |
| K factor | **2 forms + a table** | `engine/land/erosion_risk.py:34` (`DEFAULT_K_FACTOR = 0.25`) vs `engine/hydroma/wrapper.py:198` (loam entry in `k_table`) | `engine/hydroma/wrapper.py:198` | **1.52×** (0.25 vs 0.38 for loam); the Williams/Renard K forms are **6.8×** apart on the same input |
| R factor | **2 forms** | `engine/hydroma/wrapper.py:192` (Renard, Fournier-index split at 850 mm) vs `services/_contracts/formula.py:271` (Fournier index, `0.0534·P²`) | unresolved — needs a consolidation mandate | 2 published families; no single number is "the" answer, which is precisely why the row is a decision and not a bug |
| SCS-CN | **5 copies** | `engine/hydroma/models/runoff_model.py:152`; `services/map_engine/pipelines/runoff.py:181`; `services/scientific_motors/swat_plus.py:142`; `services/simulation/adapters/hydrology_adapter.py:33`; `services/_contracts/formula.py:299` | `engine/hydroma/models/runoff_model.py:152` (the copy validated against USDA NEH Sec.4 / TR-55) | **algebraically equivalent** — the mm and inch unit routes (`25400/CN − 254` vs `(1000/CN − 10)·25.4`) agree; cost is 5 edit sites, not wrong numbers |
| Theis | **2** | `engine/hydroma/groundwater/models.py:214` vs `engine/hydroma/models/groundwater_model.py:58` (audit cited `models/groundwater_model.py:58`) | unresolved — two equally canonical modules | **equivalent** — identical drawdown expression `u = r²S/(4Tt)` |
| RothC | **3** | `engine/hydroma/simulation/runners/rothc_runner.py` (the canonical monthly RothC-26.3 port; audit cited `engine/hydroma/carbon/rothc_runner.py`); `services/api_gateway/routers/carbon_engine.py:200-280` (annual step, different initial split, second temperature factor); `services/scientific_motors/rothc.py:134` | `engine/hydroma/simulation/runners/rothc_runner.py` | **structurally divergent** — different time step (annual vs monthly) and different pool initialisation; final-SOC anchors 97.605 / 99.1718 / 97.605 against a live 99.9629 |
| es / Δ / γ / Ra | **6+ copies** | `engine/hydroma/scenario_composite/models_additions.py:147-180`; `engine/hydroma/cpp_bridge/__init__.py:383-390`; `engine/hydroma/climate_adaptation/dynamic_stress_engine.py:26`; `engine/cpp_core/src/climate.cpp:21-131`; `engine/hydroma/models/validation/runner.py:58-106` | `engine/hydroma/scenario_composite/models_additions.py:147-180` (FAO-56 Ch.3 equations 7, 8, 11, 13, 21, each individually cited) | the five copies agree numerically; the divergence is 6+ independent edit sites for the four psychrometric building blocks (D-04 documents the one place where not folding them together produced a wrong result) |
| eq. 52 (Hargreaves ET0) | **5 copies (3 wrong)** | see `DEVIATION-REGISTER.md` **D-06** — the three without the 0.408 conversion were at `services/simulation/adapters/crop_adapter.py:147`, `services/analysis/drought_agent.py:203`, `services/analysis/scenario_agent.py:67` | `engine/hydroma/climate/et_calculator.py` via `services/_gateway_facade.calc_et0_hargreaves` | the 3 wrong copies read **+145 % (2.45×)** high; D-02's uncited `dtr_floor` adds +124 % at ΔT = 0.02 in the canonical copy itself |
| Penman–Monteith ET0 | **2** | `engine/hydroma/cpp_bridge/__init__.py:361-390` vs the FAO-56 Ch.4 implementation reached through the facade | the FAO-56 eq.-19 route reached through `services/_gateway_facade` | see **D-04** — the two copies follow different published routes (eq. 19 vs eq. 17); cause of 6 corpus `inconsistent_case` verdicts |
| NDVI | **4** | `engine/hydroma/satellite/processors/indices.py:47` (audit cited `engine/land/indices.py:47`); `services/scientific_motors/data_repository.py:402`; `services/map_engine/smart_mapper.py:14`; `services/_gateway_facade.py:1064` | `engine/hydroma/satellite/processors/indices.py:47` | same index formula `(NIR − Red)/(NIR + Red)` in four places; the divergence is dtype and divide-by-zero handling, documented at `indices.py:11-19` (uint16 denominator wrap at 65535; `nan_to_num` also zeroing cloud pixels, which `interpret_ndvi` then classifies as bare soil) |

---

## 2. Summary

* **10 equation families** are duplicated; **4 of them** (RUSLE LS, K, RothC, eq. 52) carry divergence that changes a number a reader would act on.
* **3 of them** (SCS-CN, Theis, es/Δ/γ/Ra) are agreement-preserving duplication: the cost is edit surface, not accuracy. They are listed so that nobody has to rediscover the count before changing one of them.
* The consolidation mandate these rows are waiting on is GAP-REGISTER **G-H6**. Until it exists, the correct move is to point new work at the canonical column, not to delete a copy.
