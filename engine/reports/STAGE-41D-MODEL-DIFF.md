# Stage 41-D — Model-file diff proof

## Git evidence and exact hashes

`git tag --list stage40-frozen` returned no output. `git log --oneline --all -- <file>` showed only checkpoint commits dated after the frozen manifest timestamp (2026-10-20T05:12:03Z). None is established as the Stage 40 freeze commit.

The current `identifiability_calibration.py` and `seasonal_predictor.py` are untracked in the current Git worktree. The attempted `git diff e700f39..HEAD -- <file>` showed them as deleted at HEAD; this is not a valid comparison with the live untracked files. A no-index comparison against `e700f39` is not a comparison against the Stage 40 frozen state.

## Hash evidence from the Stage 41 frozen manifest

| File | Stage 40 recorded SHA256 | Current SHA256 in manifest | Match |
|---|---|---|---|
| `engine/hydroma/eval/identifiability_calibration.py` | `999465b119477c2397351f6bde48dab4143f709d7d7f1c5d1f86fbf12668817b` | `6b2e76e31cc301243f0d3b5c0e4a11bb65c82527cbd722040f94e9fa6ff2d580` | no |
| `engine/hydroma/eval/seasonal_predictor.py` | `68c7da0e490b0da724a4cd308614259b1a9919592dacbca60100e3c8d70966ef` | `322374c4b3afa10f79c487d1dac2428d74b06b69bd8925cef386772576f2dc80` | no |

The independently recomputed worktree hashes match the manifest's `current` hashes. No Git-history revision for either file matches the Stage 40 `recorded` hash:

| File | Candidate Git blob SHA256 in available path history | Matches Stage 40 hash? |
|---|---|---|
| `identifiability_calibration.py` | `f9505f1a4e375073427fe5a854da76c263314b40ca78009ab1093f35a5ebc030` | No |
| `seasonal_predictor.py` | `322374c4b3afa10f79c487d1dac2428d74b06b69bd8925cef386772576f2dc80` | No |

The available commits are later checkpoint commits, not a verified freeze revision. The manifest describes the changes as additive `data_source` provenance metadata; that description is not a line-by-line diff against Stage 40. Hash differences confirm the files differ, but do not establish whether numeric constants, thresholds, or operators changed.

## Conclusion

**`scientific_change = UNPROVEN`**. The requested line-by-line diff against the Stage 40 frozen revision cannot be established from the available Git history. The metadata-only claim remains an assertion in the Stage 41 manifest, not a verified diff proof.
