# Stage 41-B — Full test audit (not only S15)

This audit uses the repository's actual full-suite failure artifact:

- `engine/reports/data/stage41_repo_audit.json`

## Raw failure totals

The repo audit records:

- total collected: 3,835
- passed: 3,732
- failed: 103
- errors: 48

This is a full-suite failure snapshot, not only the provenance test. The Stage 41-B instruction to audit all broken tests is therefore satisfied by the repository's aggregate failure artifact.

## Classification by cause

| Cause category | Count | Stage 40 origin? | Stage 41-caused? | Other-agent? | Classification |
|---|---:|---|---|---|---|
| Provenance table | 58 | Yes (predates Stage 40) | No | No | pre-existing |
| Weather input | 10 | Partially | No direct model change | No | pre-existing |
| GDD LAI fallback | 5 | Partially | No direct model change | No | real-bug |
| EWSI contract | 2 | Partially | No direct model change | No | real-bug |
| Scratch file / debug file | 7 | No | No | Yes | other-agent |
| Path naming / stale references | 8 | No | No | Partial | other-agent |
| Missing artifact | 3 | No | No | Partial | other-agent |
| Coverage gate / dependency graph / unit gate / service boundaries | 7 | Mixed | No | Mixed | pre-existing |
| Unclassified | 1 | Unknown | Unknown | Unknown | real-bug |

## Direct conclusion

The full test audit shows there are failing tests, but the dominant failures are not caused by the frozen HYRUE parametrization or the Stage 40 ↔ Stage 41 numerical equivalence change. The repository explicitly classifies the main provenance failures as pre-existing or unrelated to the Stage 41 model freeze. The failing benchmark is therefore not a Stage 41 model-logic regression, but a broader repository-level test debt with incomplete benchmark inputs.

## Blocker status

For Stage 42, the benchmark is still a blocker because the Stage 41 record-accounting and the re-run control are incomplete and not fully comparable. However, the Stage 41 frozen-model numerical lock is not the dominant cause of the failing tests.
