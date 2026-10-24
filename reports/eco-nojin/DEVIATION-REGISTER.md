# DEVIATION REGISTER — engine vs. published standard

Document id: `ECO-10-DEVIATION-REGISTER` · Verified: 2026-10-10 · Source: formula-audit findings recorded in `reports/eco-nojin/FORMULA-VALIDATION-REGISTER.md` (§4, §5) and `GAP-REGISTER.md` (G-H8, G-H6).
Method: code reading + live execution (venv `D:\eco_nojin\.venv`, `$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"`). Every `file:line` below was re-read from the live tree on the verification date; where the tree has moved since the audit, the audited location is named alongside the current one and the **status** column says so.

Scope: these are **engine-versus-standard** deviations — places where this repository's code does something other than what the cited standard says. They are *not* internal inconsistencies between two copies in this repo; those are in `EQUATION-DIVERGENCE-REGISTER.md`.

Nothing here was changed to make the table shorter. No equation was modified in the course of producing this register.

---

## 1. Register

| id | what the code does | what the standard says | file:line | measured effect | status |
|---|---|---|---|---|---|
| D-01 | clamps `Rs/Rso` into `[0.3, 1.0]` before feeding FAO-56 eq. 40's cloudiness term, and attributes the clamp to FAO | FAO-56 eq. 40 caps `Rs/Rso` at **1.0** only; the 0.3 floor is this repo's addition, and the eq.-40 factor is clamped separately to its physical band | `engine/hydroma/climate/et_calculator.py:222` | `Rn` −1.44 MJ/m²/day (≈ −0.35 mm/day ET0) at ratio 0.14 | **open** — docstring/card correction (no equation change without mandate), owner HONESTY2; attribution recorded in GAP-REGISTER G-H8 |
| D-02 | injects an uncited `dtr_floor=0.1 degC` into the Hargreaves diurnal range, so a range below 0.1 °C is clamped *up* instead of returning the eq.-52 value | FAO-56 / Hargreaves & Samani (1985) publish no floor on `Tmax − Tmin`; the floor is a consolidation artefact of two of four copies | `engine/hydroma/climate/et_calculator.py:127` (used at `:161`, `:174-175`) | +124 % ET0 at ΔT = 0.02 | **open** — docstring/card correction, owner HONESTY2; attribution recorded in GAP-REGISTER G-H8 |
| D-03 | the shipped `hydroma_core.pyd` is built from source using Hargreaves exponent 0.48 | FAO-56 eq. 52 and Hargreaves & Samani (1985) use exponent **0.5** (square root of the diurnal range) | `engine/cpp_core/src/climate.cpp:44-59` (source now correct; the shipped binary is stale — no MSVC/cmake toolchain on the review host) | −4.5 % (−4.5 % ET0, ~−5 % until rebuilt) | **open** — rebuild the extension on a host with a toolchain; pinned as a strict xfail (S11) so the divergence is visible rather than hidden |
| D-04 | the second published PM route computes actual vapour pressure as `ea = es_mean × rh_mean / 100` | FAO-56 gives two published routes: eq. 17 (`ea` from dewpoint) and eq. 19 (`ea = es(Tmin)·RHmax/100 + es(Tmax)·RHmin/100`) — the mean-of-saturation-times-mean-RH product is neither | `engine/hydroma/cpp_bridge/__init__.py:387` (route defined at `:361`, cited by audit as `:361`) | different published route (eq. 19 vs eq. 17); cause of 6 corpus `inconsistent_case` verdicts | **open** — docstring/card correction; the two routes must be named, not merged, owner HONESTY2 |
| D-05 | invents missing-data defaults `rh_max=80`, `rh_min=30`, `rh_mean=55` derived from them, and `solar_radiation=20.0` when the caller omits them | only `u2 = 2.0 m/s` is FAO-56's own default (Annex 2); the humidity and radiation defaults are this repo's | `services/api_gateway/routers/hydroma_climate.py:166-170` | silently substituted climate, no flag that the caller sent nothing | **open** — docstring/card correction; defaults must be labelled as this repo's, owner HONESTY2 |
| D-06 | three inline copies of eq. 52 were shipped without the 0.408 MJ/m²/day → mm/day conversion (2 of them also used surface radiation `Rs` in the `Ra` slot) | FAO-56 eq. 52 requires `0.408 × Ra_mj` when `Ra` is in MJ/m²/day, and `Ra` is extraterrestrial radiation derived from latitude and day of year, not surface radiation | audited: `services/simulation/adapters/crop_adapter.py:147`, `services/analysis/drought_agent.py:203`, `services/analysis/scenario_agent.py:67`; current: `services/simulation/adapters/crop_adapter.py:148-163`, `services/analysis/drought_agent.py:178-204`, `services/analysis/scenario_agent.py:139-145` | +145 % ET0 (2.45×); scenario SPEI computed against a PET 2.45× high | **owner: PHASES agent** — the live tree now delegates to `services/_gateway_facade.calc_et0_hargreaves` in all three sites; the 2.45× history is preserved in each replacement's docstring. Re-verify that no fourth copy is reintroduced |
| D-07 | a duplicate Kirpich time-of-concentration fed slope in **percent** (`tan(deg)×100`) and returned the minute-scale value under an **hours** label | canonical Kirpich (USDA, `engine/hydroma/watershed/calculator.calculate_kirpich_tc`, card CANON-015) takes slope in m/m and returns minutes | audited: `engine/land/drainage.py:143-156`; current: `engine/land/drainage.py:122-156` (wrapper `_calculate_time_of_concentration`), delegating at `:175-183` | 3.98 "hours" where the canonical returns 23.44 minutes (0.39 h) for a 1000 m / 1 % catchment — the percent-for-m/m substitution alone is worth 100^−0.385 = 0.098 | **owner: PHASES agent** — the duplicate is gone from the live tree; one implementation, one place (`drainage.py:7-11`, `:146-152`, `:174-183`) |

---

## 2. Reading the register

* **D-01, D-02, D-05** are attribution defects, not arithmetic defects: the code runs the numbers, but it names the wrong author. They are cheapest to fix and they are the ones a reader of the card would be misled by, because the card's citation is what transfers trust.
* **D-03** is a build-state defect. The source is right; the shipped artefact is not. Until it is rebuilt, any Windows user of the extension gets a different ET0 than the Python core in the same process — which is exactly why S11 pins it as a strict xfail instead of deleting the test.
* **D-04** is a genuine identity-of-method defect: two of the six corpus `inconsistent_case` families disagree because two published routes were folded into one expression that is neither of them.
* **D-06 and D-07** carry `PHASES agent` in the status column: the live tree no longer contains the defect. They stay in the register because the 2.45× and 3.98 "hours" numbers are the evidence any future re-introduction must be compared against, and because the docstrings that replaced the inline copies are the only remaining record of what was wrong.

### Cross-references

* Internal duplicates and shared-formula divergence: `EQUATION-DIVERGENCE-REGISTER.md`.
* The claim-status vocabulary that prevents these from being filed as "validated": `engine/honesty/statuses.py`.
* The citation-existence check that keeps phantom evidence out of the evidence chain: `tools/phantom_path_check.py`, gated in CI as *Phantom-path check (honesty contract 3)*.
