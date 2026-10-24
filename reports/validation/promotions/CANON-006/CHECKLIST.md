# Promotion checklist (dry-run, no changes applied)

- model: `CANON-006` — registry status `validated`, maturity `S3`
- family: `VAN_GENUCHTEN_THETA_K` — current class `VALIDATED_METHOD_CONFORMANCE`, gap `SOIL_VG_PARAMETERS table provenance withdrawn (G-S6/G-H4); alpha diverges up to 3.8x on the three coarsest textures`
- external-anchor cap today: 10 (raise on apply)

## Required input (the honest gate)
1. A genuine published value for `CANON-006` (published table / measured / worked example), from the source — NOT a re-derivation.
2. A CSV in `tests/reference_data/` carrying the published value(s), with `*.meta.json` (citation + kind + sha256).

## Then run
```
python tools/promote_external.py --apply --model CANON-006 --family VAN_GENUCHTEN_THETA_K --reference <csv> --citation "..." --kind <kind>
```
and hand `engine_patch.md` to the engine owner.
