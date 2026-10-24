# ECO-03.1: Scientific Blockers — Report 14

## P0 scientific items requiring review

---

## 1. Theis Solution (CANON-005)

| Field | Value |
|-------|-------|
| Model ID | CANON-005 |
| Name | Theis Solution (Groundwater drawdown) |
| P0 Reason | Series convergence undocumented |
| ECO-04 Blocking? | NO — not in ECO-04 sprint plan |
| Status | REQUIRES_SCIENTIFIC_REVIEW |

### Investigation

**Equation**: Theis (1935) groundwater flow equation:

$$s = \frac{Q}{4\pi T} W(u)$$

where $W(u)$ is the exponential integral (Well function).

**Series implementation**:
```
W(u) = -γ - ln(u) + Σ_{n=1}^{∞} (-1)^n * u^n / (n * n!
```

**Convergence**: The series converges for small `u` (typically `u < 0.01`), but diverges for `u > 1`. For large `u`, an asymptotic expansion must be used instead.

**Finding**: The implementation exists (`engine/hydroma/hydrology/theis.py`) but convergence criteria are **not documented** in the source code. No test validates the series convergence behavior.

**Action required**: Scientific review of the Theis series implementation. This is NOT blocking ECO-04 since the next sprint does not use Theis.

---

## 2. Climate Data Assimilation (CANON-018)

| Field | Value |
|-------|-------|
| Model ID | CANON-018 |
| Name | CMIP6 Climate Data Assimilation |
| P0 Reason | Data assimilation weights undocumented |
| ECO-04 Blocking? | NO — not in ECO-04 sprint plan |
| Status | REQUIRES_SCIENTIFIC_REVIEW |

### Investigation

**Implementation**: `services/satellite/nasa_power.py` and `services/satellite/monitoring_service.py` reference climate data assimilation.

**Evidence**: ECO-01 report §119: "Climate Data Assimilation - Issues found" — weight assignment methodology undocumented.

**Finding**: No weight assignment documented in source code. The assimilation uses default weights without justification.

**Action required**: Scientific review of climate data assimilation methodology. NOT blocking ECO-04.

---

## 3. Other Review Items (LOWER PRIORITY)

| Model | Issue | ECO-04 Blocking? |
|-------|-------|-----------------|
| CANON-002 (Hargreaves ET0) | Needs local Iranian validation | NO |
| CANON-003 (Thornthwaite PET) | Needs arid climate validation | NO |
| CANON-007 (RUSLE LS Factor) | LS factor calculation needs review | NO |
| CANON-011 (Solar Radiation) | Atmospheric correction for Iran altitude | NO |

---

## 4. ECO-04 Impact Assessment

| Scientific Review Item | In ECO-04 Sprint Plan? | ECO-04 Impact |
|------------------------|----------------------|---------------|
| Theis Solution (CANON-005) | NO | None |
| Climate Data Assimilation (CANON-018) | NO | None |
| Hargreaves ET0 (CANON-002) | YES (used in ET0 calculator) | Use as IMPLEMENTATION_VERIFIED, note for future review |
| RUSLE LS Factor (CANON-007) | NO | None |

---

## 5. Conclusion

Two P0 scientific items were investigated:

1. **Theis Solution**: Series convergence is undocumented. **NOT blocking ECO-04**.
2. **Climate Data Assimilation**: Weight methodology undocumented. **NOT blocking ECO-04**.

Both items are deferred to post-ECO-04 scientific review. Neither blocks the ECO-04 start.

---

*Report generated: 2026-10-08*
*Status: 0 scientific blockers for ECO-04 — all require review but not immediate*