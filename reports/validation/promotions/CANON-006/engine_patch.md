# Engine patch — DRAFT, apply by the owning agent (NOT auto-applied)

Promoting `CANON-006` to a registry `validated` claim needs four engine
edits, all in-flight STOP-brake surfaces (KN-22/39; SB-03/SB-10). Coordinate with
the engine owner; do not edit out of band.

1. `engine/models/cards/CANON-006_*.md`
   Set the `validation_status` row to claim the model matches its published
   reference (`validated` / `benchmarked` — a whole-word positive the registry
   derivation recognises).

2. `engine/tests/test_machine_evidence_consistency.py`
   Add to `EXTERNALLY_ANCHORED_MODELS`:
       "CANON-006": "VAN_GENUCHTEN_THETA_K",
   And deliberately raise the external-anchor cap in
   `test_corpus_external_anchors_are_reported_distinctly`:
       assert len(external) == <current+1>

3. `engine/validation/test_validation_records.py`
   - Add the independently re-derived `reference` for `CANON-006` (a
     published value, not a re-derivation you typed from the model).
   - If a record already exists, set its `validation_status` to `validated` and
     add `CANON-006` to `CLUSTER_MODELS_MOVED_TO_VALIDATED`.

4. Re-run the gate; the registry then derives `validated` from the card row, and
   `test_no_validated_claim_without_external_anchor` passes with `CANON-006`
   out of `KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR`.
