# Stage 33: Bootstrap Uncertainty Report

## Method

Cluster bootstrap at the spatial unit of independence (district level),
following the design in `validation_uncertainty.py`. This resamples districts
with replacement (not individual records), which correctly accounts for the
clustered structure of the data.

- **Confidence level:** 95%
- **Bootstrap resamples:** 1,000
- **Independence unit:** district (site)
- **Random seed:** 42
- **Minimum units required:** 2

## A. STRICT Policy Uncertainty

| Metric | Status |
|---|---|
| Status | not_assessed |
| Note | No successful predictions; bootstrap cannot be computed. |

No uncertainty can be computed — no predictions were produced (all blocked).

## B. ALLOW_ESTIMATED_INPUTS Policy Uncertainty

| Metric | Status |
|---|---|
| Status | not_assessed |
| Note | No successful predictions; bootstrap cannot be computed. |

No uncertainty can be computed — no predictions were produced (all blocked).

## C. DIAGNOSTIC Policy Uncertainty (Supplementary Only)

| Metric | Status | Value |
|---|---|---|
| N independent units | | 3 |
| Unit of independence | | site |
| Bootstrap method | | cluster_bootstrap |

| rmse | assessed | point=1.8572, CI95%=[1.6443, 2.0075] |
| mae | assessed | point=1.6364, CI95%=[1.3814, 1.8604] |
| bias | assessed | point=1.5004, CI95%=[1.0029, 1.8499] |

**WARNING:** These CIs are computed from legacy_constant mode predictions
and overstate seasonal totals. They are NOT suitable for validation inference.

## D. Uncertainty Status Interpretation

| Condition | Result |
|---|---|
| >= 2 independent districts with predictions | CI computed |
| < 2 independent districts | NOT_ASSESSED |
| 0 successful predictions | NOT_ASSESSED (insufficient data) |

For the STRICT and ALLOW_ESTIMATED evaluations, 0 predictions were produced,
so uncertainty is NOT_ASSESSED. The blockage is due to unavailable EWSI inputs,
not statistical insufficiency.
