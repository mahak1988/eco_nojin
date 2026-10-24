"""Published-reference validation evidence for the engine's registered models.

Phase 3 of the six-phase program (``docs/project/ROADMAP-6-PHASE-2026-10-11.md``)
validates the soil / hydrology / crop-water cluster against published references
first. Each model in that cluster that was validated has one evidence record in
this directory, named ``<MODEL_ID>.md``, carrying

* the published reference and its citation,
* the input range the comparison covers,
* the tolerance and the basis for choosing it,
* a comparison table of model output against independently re-derived reference
  output for at least three cases, and
* an uncertainty statement plus the limitations that bound the claim.

Each record also carries a fenced ``json`` block (schema
``hydroma.validation.record@1``) holding the same comparison as machine-readable
data. ``engine/validation/test_validation_records.py`` re-runs every case through
the engine gateway and asserts the live model still reproduces the recorded
values and still meets the reference within the recorded tolerance, so a record
that no longer describes the code fails the suite.

A model is only credited in the registry's ``validation_status`` when its record
says so, and the derivation that produces that status runs from the model card's
``validation_status`` row (``engine/models/registry.py``). Two kinds of record
exist here and both are re-run on equal terms:

* a record whose model **matches** its published reference. Five of the ten
  cluster models carry the external anchor
  ``engine/tests/test_machine_evidence_consistency.py`` requires and are credited
  ``validated``; the other five are recorded by
  ``reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`` as method-conformance
  evidence, which the registry's derivation does not turn into a ``validated``
  claim, so their cards say ``VALIDATED_METHOD_CONFORMANCE`` and their records
  name the register row that would move them in ``registry_gap``;
* a record whose model **does not** match its published reference. The suite
  asserts that disagreement is still real rather than pretending it drifted, and
  the registry keeps reporting ``unvalidated`` for that model. That is the honest
  reading, and it is the one the registry's own derivation is wired to produce.
"""
