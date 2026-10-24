# Unresolved conflicts in the van Genuchten table

The consolidation commit made one source of truth, and that is settled. What it
did **not** do is decide which value is right where the copies disagreed. Those
conflicts are recorded here rather than adjudicated, because adjudicating them
requires the source publication, which is not available offline.

## Why nothing was changed

The four copies, as they stood:

| Source | Textures | theta_s dataset | Ks for clay |
|---|---|---|---|
| `hydroma/soil/physics.py` | 12 | A | 4.80 cm/day |
| `cpp_bridge/soil_physics_fast.py` | 7 | A | 2.88 cm/day |
| `cpp_core/src/soil.cpp` | 7 | A | 2.88 cm/day |
| `land/integration/soil_integrator.py` | 12 | **B** | absent |

Two facts make adjudication impossible without the source:

1. **The provenance is unverifiable and demonstrably wrong in part.** The Python
   table's Ks column is not monotone in texture fineness in two places
   (`sandy_clay_loam` 31.4 above `silt` 6.0, and `clay` 4.8 above `silty_clay`
   1.92), which hydraulic conductivity cannot be. The `n` column breaks the same
   ordering once, at `sandy_clay_loam`. A table that violates its own defining
   monotonicity cannot be presented as a faithful transcription of a published
   one.
2. **There is no source document in the repository.** No copy of the cited
   publication exists in-tree, and the values appear in no data file. The
   attribution was a comment.

Under the project rule that anything not traceable is either deleted or labelled
a design assumption, the `provenance` column of the CSV reads *design
assumption*, and the Carsel & Parrish attribution is withdrawn. That is the
action taken. Inventing replacement values was not.

## Open conflict 1 — clay conductivity

| Source | Value | Converted |
|---|---|---|
| `soil/physics.py` (canonical, 12 textures) | 4.80 cm/day | 0.200 cm/hr |
| `cpp_bridge/soil_physics_fast.py` | 2.88 cm/day | 0.120 cm/hr |
| `cpp_core/src/soil.cpp` | 0.12 cm/hr | 2.88 cm/day |

Two of the three copies agree at 2.88 cm/day, and the dissenting value is also
the one that breaks fineness monotonicity. That is suggestive, but the C++ table
is provably a derivative of the Python table for the other six rows, so its
clay value may be a rounding of the same wrong number rather than independent
corroboration. **The CSV keeps the Python value** so that nothing moves, and
marks the row `design_assumption_disputed`.

Physical stakes: 0.12 cm/hr is 3.3e-7 m/s and 0.20 cm/hr is 5.8e-5 m/s. The
reference document specifies an aquitard at K < 1e-7 m/s. The two candidates
straddle that threshold by an order of magnitude each way, so a caller gets
either a sealing layer or a draining layer.

## Open conflict 2 — the two theta_s datasets

`soil_integrator.py` carries a second dataset that differs from the Python
table in **every one of the twelve rows**, and is systematically higher:

| Texture | Dataset A | Dataset B |
|---|---|---|
| sand | 0.430 | 0.437 |
| loam | 0.430 | 0.463 |
| silt | 0.460 | 0.479 |
| clay | 0.380 | 0.468 |

Total pore volume rises with clay content, so theta_s should rise with fineness.
Counted along the coarsest-to-finest USDA sequence:

* Dataset A: **6** order inversions, ending with `silty_clay` 0.360 rising to
  `clay` 0.380, and never rising above 0.460.
* Dataset B: **3** inversions, and it rises monotonically from 0.437 at sand to
  0.479 at silt.

Dataset B is the better-behaved of the two, but "better behaved" is not
"verified", and B carries no Ks column at all. The CSV keeps dataset A, so that
`available_water_capacity`, the field-capacity curve and the baseline all stay
bit-identical. Dataset B is preserved in `soil_integrator.py` only in the sense
that its consumer now reads the CSV — its distinct values are recorded here.

## Open conflict 3 — sandy_clay_loam

One row is carried by no other copy: `sandy_clay_loam` with Ks 31.4 cm/day and
n 1.48. It is incoherent on its face — it is finer than silt yet conducts more
than six times as much, and its pore-size index exceeds that of silt. Whatever
assembled the table appears to have placed this row incorrectly.

It is kept, because removing a row is as much a decision as changing one, and
because it is one of the five textures absent from the compiled table, so
nothing cross-checks it.

## How to close these

1. Obtain the source publication and transcribe its table by hand.
2. Compare it against `soil_vg_table.csv` row by row.
3. Replace the disputed rows, change their `status` to `verified`, and set
   `provenance` to the citation in the form the project uses elsewhere: chapter
   and table, not a line number.
4. Regenerate `R18.json` and state the blast radius in the commit message,
   because every AWC in the engine moves with these rows.
