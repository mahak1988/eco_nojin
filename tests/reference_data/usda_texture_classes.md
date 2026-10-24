# USDA texture classes — published defining ranges

## What this table is

`usda_texture_classes.csv` holds the **twelve USDA texture classes** with their
published defining ranges, in the form they are actually published: the verbatim
class definitions of the USDA soil texture triangle (`definition_published`
column), together with the percentage bounds each definition states for clay,
silt and sand (`clay_percent_as_published`, `silt_percent_as_published`,
`sand_percent_as_published`).

The publication defines the classes by *inequalities over the whole 100 percent
fine-earth fraction*, not by per-axis ranges, so six extra integer columns are
provided: `clay_min`/`clay_max`, `silt_min`/`silt_max`, `sand_min`/`sand_max`
(`region_size` completes the set). These are the **bounding box of each class's
published defining region over the integer texture triangle** (`sand + silt +
clay == 100`, the same 5151-composition grid the audit tool uses), obtained by
evaluating the published definition itself at every integer composition and
keeping the min/max of each fraction. No boundary is invented: the boxes are a
mechanical evaluation of the published definition, they are recomputed from the
CSV by `engine/tests/test_usda_texture_reference.py`, and the test fails if the
two ever disagree. The boxes deliberately do *not* reproduce the triangle's
polygon edges; they are the smallest axis-aligned boxes that contain each
published region.

File layout, matching `tests/reference_data/fao56_examples.{csv,md,meta.json}`
and `tests/reference_data/mckee_spi_classification.{csv,meta.json}`:

- `usda_texture_classes.csv` — the data
- `usda_texture_classes.meta.json` — the §4.6 sidecar (provenance, licence, hash)
- `usda_texture_classes.md` — this file
- `tests/reference_data/README.md` — the index of the reference-data directory

## Source

**Primary transcription source (what was fetched):**

`https://websites.umich.edu/~nre430/PDF/Soil_Profile_Descriptions.pdf`
— *A GUIDE FOR PREPARING SOIL PROFILE DESCRIPTIONS* (Soils Properties and
Processes NRE 430/EEB 489, University of Michigan, 2003, 18 pp.), section
"Soil Texture and Rock Fragments". The document states the twelve USDA texture
class definitions ("Definitions of the soil texture classes according to
distribution of size classes of mineral particles less than 2 mm in diameter")
and its textural-triangle figure is credited there to *Soil Survey Staff, 1962,
1975*, which is the USDA publication the definitions come from.

**Corroborating source (USDA government domain):**

`https://efotg.sc.egov.usda.gov/references/Delete/2007-12-15/soilpropqual.htm`
— USDA-NRCS eFOTG archived National Cooperative Soil Survey soil-properties
guide. It independently names the twelve USDA texture classes and states the
`loam` bounds exactly as the transcription does: *"Loam, for example, is soil
that is 7 to 27 percent clay, 28 to 50 percent silt, and less than 52 percent
sand."* It publishes numeric bounds for `loam` only and defers the rest to the
survey glossary, so it corroborates the class list and one definition, not the
whole table — the per-row `corroboration_note` column records that distinction
truthfully.

**Retrieval date:** 2026-10-10. Both URLs were fetched on that date with the
`webfetch` tool; the .pdf was read through a text-extraction proxy
(`r.jina.ai`) because the fetch tool does not convert PDFs, and the .htm was
fetched directly.

## Retrieval failure, recorded honestly

Every USDA/NRCS publication host was **unreachable from this environment**. Each
of these was attempted repeatedly on 2026-10-10 and returned a transport error
or a timeout (directly and through a text-extraction proxy):

- `https://www.nrcs.usda.gov/` — the whole host, including
  `/resources/education-and-teaching-materials/soil-texture-calculator`
  (the "Soil Texture Calculator" the engine's own docstring cites) and
  `/resources/education-and-teaching-materials/glossary-of-landforms-and-soil-science-terms`
- `https://nrcs.usda.gov/`, `https://www2.nrcs.usda.gov/`,
  `https://soils.usda.gov/`
- `https://web.archive.org/` snapshots of the above

Other US-government mirrors of the USDA publication were tried and could not be
read either: `https://www.govinfo.gov/content/pkg/GOVPUB-A-PURL-gpo82564/pdf/GOVPUB-A-PURL-gpo82564.pdf`
(Soil Survey Manual 2017, US Government Publishing Office) serves a 639-page
PDF whose text could not be extracted from this environment, and
`https://directives.nrcs.usda.gov/...` serves NRCS engineering-handbook PDFs
whose texture content is the triangle *diagram*, not numeric class definitions.

The consequence is recorded here rather than hidden: **this CSV is a
transcription of USDA's published definitions obtained through a secondary
carrier** (a university course document that reproduces them verbatim), **not a
direct transcription fetched from a USDA domain**. No value in the CSV was
produced by this repository. `engine/tests/test_usda_texture_reference.py`
asserts that the CSV, the .meta.json and the audit report remain consistent with
each other; it does not assert that the USDA primary publication was reached.

Re-running the acquisition against a USDA host, and re-checking the two rows
where secondary transcriptions of the USDA definitions disagree with each other
(`loamy_sand` is stated in the fetched source as an upper-limit/lower-limit
pair, whereas other transcriptions of the same USDA definition state it as a
single conjunction over 70-91 percent sand), is the follow-up this file does
not close.

## Licence and attribution

This is **public-domain USDA material transcribed for citation**. The USDA
texture class definitions are US Government work, published by the USDA Soil
Survey Staff / NRCS; they are reproduced here verbatim, one row per class, each
row naming the URL it was transcribed from, for the purpose of enabling an
independent check of the engine's own classifier
(`engine/hydroma/soil/taxonomy.py`) without depending on any restricted
package.

**It is NOT the GPL `soiltexture` package.** Nothing here is derived from, or
copied from, that package or any other third-party texture-classifier code; the
only code in this repository that reads this table is the test named above.

The van Genuchten parameter table carried in earlier drafts of this project is
**not** part of this table and is not reintroduced by it: no van Genuchten
parameter, no `Carsel`/`Parrish` attribution and no residual moisture /
saturated conductivity / alpha / n columns appear anywhere in this directory.

## How the table is used

`engine/tests/test_usda_texture_reference.py`:

1. checks the table is complete and sourced and that the sidecar validates;
2. runs the engine's own classifier over the same 5151-composition integer grid
   the audit tool uses and reports its agreement rate against the transcribed
   table;
3. checks that `reports/eco-nojin/TEXTURE-CLASSIFIER-AUDIT.md` still exists and
   still records the 782 fallback count that this reference data is meant to
   measure;
4. checks that no GPL package token and no van Genuchten parameter table
   appear in the sources and data files this task created.

Gaps addressed: G-V3-02, the texture half of G-V3-09, and the texture half of
G-S6. The hydraulic-parameter half of G-V3-09 stays open: it needs a van
Genuchten parameter table, which this task deliberately does not supply.
