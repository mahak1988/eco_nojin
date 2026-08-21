# 20 — Phase 8 Kickoff: Token Economy & Carbon (weeks 18-22)

> Status: **phase 8 started** — carbon verification + credit issuance +
> persistent ECO wallet. 360 backend tests green.

## 1. Goal
A legal, credible economic layer: carbon projects registered -> verified
(VM0042-aligned methodology) -> credits issued -> shown in the wallet.

## 2. Shipped (kickoff)
- **`services/carbon/verification.py`** — honest methodology checks:
  baseline / additionality / leakage / permanence. A project passes ONLY
  when every check passes; failing checks are returned verbatim.
- **`POST /api/v1/carbon/projects/{id}/verify`** — runs the checks; sets
  verification_status (verified|failed) + detail (JSON). Never rubber-stamps.
- **`POST /api/v1/carbon/projects/{id}/issue`** — only for VERIFIED projects;
  issues credits and credits the **persistent ECO wallet**
  (rate: carbon_credit = 100 ECO/unit).
- **`GET /api/v1/carbon/wallet`** — DB-backed wallet state (survives
  restarts; the old ecowallet router stays in-memory for its legacy tests).
- Migration `f7a3b4c5d6e7` — carbon_projects += verification_status,
  verification_detail, issued_at.
- Ownership enforced (403) + 404 for unknown projects.
- Tests: `tests/integration/test_carbon_phase8.py` (5).

## 3. Acceptance criterion — status
| Step | Status |
|---|---|
| پروژه کربن ثبت (register) | ✅ (existing) |
| تأیید متدولوژی (verify) | ✅ honest checks |
| صدور اعتبار (issue) | ✅ verified-only |
| نمایش در کیف پول | ✅ persistent wallet |

## 4. Next (Phase 8 remainder)
1. EcoCoin 70/15/10/5 distribution engine + wallet UI (frontend + bot).
2. Marketplace (orders + traceability).
3. Blockchain ledger hooks (honest gates; legal advice before any launch).
4. VerificationOracle migration from econojin.com.
