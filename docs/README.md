# HyDroMA documentation tree

This directory holds the **specifications**, **audits** and **architecture
decisions**. The program record-of-resolution (handoffs, gap registers, lint and
quality measurements, release plans) lives separately in
[`../reports/`](../reports/) and is maintained by the implementation agents.

Every specification document carries an **"Implementation status (verified
2026-10-11)"** block at its top. That block maps the document's claims and gaps
to the live code, with file references, and marks each item **resolved** /
**open** / **superseded / knowingly deferred**. It does not change the
document's requirements — these documents remain the source of truth for what
the system must do.

## `specs/` — the specification set

| Document | Role |
|---|---|
| [`ECO-NOJIN_MASTER_v3.1_UNIFIED.md`](specs/ECO-NOJIN_MASTER_v3.1_UNIFIED.md) | The live v3.1 constitution: ZED contract, safety brakes, architecture rules, model catalogue, KPI baselines, 90-day roadmap |
| [`ECO_NOJIN_HYDROMA_MASTER_v3.0.html`](specs/ECO_NOJIN_HYDROMA_MASTER_v3.0.html) | **Superseded** temporary v3.0 HTML — its 13 registered patches were folded into v3.1 (see `../reports/eco-nojin/SPEC-V3.1-PATCH.md`) |
| [`ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`](specs/ECO-NOJIN%20MASTER%20EXECUTION%20SPECIFICATION.md) | ECO-MASTER-v2.0-ZED-UNIFIED — the master execution spec and the ECO-01…17 phase plan |
| [`ECO-01.md`](specs/ECO-01.md) | Phase 01 — knowledge, scientific & technology forensics |
| [`ECO-02.md`](specs/ECO-02.md) | Phase 02 — canonical architecture & core contracts |
| [`ECO-03.md`](specs/ECO-03.md) | Phase 03 — architecture hardening, reconciliation & implementation specification |
| [`ECO-03.1.md`](specs/ECO-03.1.md) | Phase 03.1 — blocker reconciliation & minimal architecture hardening |
| [`ECO-04.md`](specs/ECO-04.md) | Phase 04 — controlled implementation |
| [`ECO-04.1.md`](specs/ECO-04.1.md) | Phase 04.1 — architecture completion, enforcement, verification & final gate |
| [`HYDROMA-MASTER.md`](specs/HYDROMA-MASTER.md) | Master development & completion directive (honesty contract, capability chain) |
| [`HYDROMA-MASTER-TESTING.md`](specs/HYDROMA-MASTER-TESTING.md) | HYDROMA-QA-001 — rigorous testing, scientific validation & evidence-driven development |

## `audits/`

| Document | Role |
|---|---|
| [`ECO-00-ENGINE-SERVICES-FORENSIC-AUDIT-REPAIR.md`](audits/ECO-00-ENGINE-SERVICES-FORENSIC-AUDIT-REPAIR.md) | ECO-00 engine & services forensic audit, repair and canonicalization. Its status block reconciles the G-Z gap register (G-Z1…G-Z6) and the Track C2 service→Gateway migration debt against the live tree, with evidence per item |

## `adr/`

| Document | Role |
|---|---|
| [`014-import-guard-policy.md`](adr/014-import-guard-policy.md) | ADR-014 — the import-guard policy as a versioned data file (`../tools/import_guard_policy.json`) |

## Where the specs came from

All twelve of these documents were `git mv`-d from the repository root into this
tree on **2026-10-11**, preserving git history. Before that they lived at the
top level of `D:\HyDroMA` next to `pyproject.toml`.
