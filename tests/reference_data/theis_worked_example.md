# Theis reference — what could and could not be verified (2026-10-10)

## Status: **no published drawdown value for this input set was obtainable offline**

Sources attempted (all fetched live today):

| Source | Result |
|---|---|
| USGS WSP 1541 (classic worked Theis tables) | HTTP 404 — not reachable |
| EPA Theis equation note | HTTP 403 — blocked |
| KGS Ground Water Series 3 (THEISFIT worked run) | reachable — gives a *fitted* dataset (S=1e-5, KB=2000 gal/day/ft, Q=316 800 gal/day, R=824 ft) and rms errors in **feet**, not a single published drawdown for our inputs |
| TWDB analytical model page | reachable — publishes the **formulae** (u, w(u) series, s) but no worked numeric table |
| AQTESOLV Theis page | reachable — publishes the equation and the **series expansion** of w(u) |
| OpenGeoSys Theis benchmark | reachable — a *published benchmark parameter set* (Pinder & Frind / Kolditz: Q=1223.3 m³/d, T=9.2903e-4 m/s, S=1e-3) used for *numerical* comparison, not an analytical drawdown value for our inputs |

**Therefore no drawdown number is recorded in this file.** Per the honesty contract (never invent a reference) and CANON-005's earlier defect (a card printed a wrong value, 0.018 m, against a measured 0.3062 m), the anchor for this model is built from **published formulae instead of a published table**, which is reproducible and independently checkable:

1. the published **well-function series** `w(u) = -0.5772 - ln(u) + u - u²/(2·2!) + u³/(3·3!) - …` — compared against the engine's `scipy.special.expi` evaluation in `engine/tests/test_theis_reference.py`;
2. the published **Cooper–Jacob approximation** `s = (Q/4πT)·ln(2.25Tt/(r²S))` for `u < 0.05` — the same relation the engine's own Cooper–Jacob branch uses, cross-checked against the exact branch.

The remaining gap is recorded as **G-V3-05**: a published *numeric* Theis benchmark (e.g. a USGS WSP table) is still needed before CANON-005 can be labelled `VALIDATED_EXTERNAL` rather than `VALIDATED_METHOD_CONFORMANCE`.

Engine inputs used throughout (from `engine/strict_tests/conftest.py`): T = 2000 m²/day, S = 2e-4, Q = 760 m³/day, r = 30 m, t = 1 day → the engine returns **0.3062 m** (not the 0.018 m the old card claimed).
