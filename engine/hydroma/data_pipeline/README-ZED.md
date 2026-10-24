# ZED §2.2ج download gate — operator notes

`pipeline.py` reaches the public internet from every connector. ZED §2.2ج
requires that ingestion be *explicitly gated* (opt-in), never an unconditional
side effect, and that the engine core stay HTTP-framework free (AR-03).
`download_gate.py` is the interim control that makes this observable and
switchable; **ingestion itself is meant to move out of the engine core in
Wave 3+**, at which point this gate becomes a hard, flag-only boundary.

## Three modes

| Mode | How to select | Behaviour |
| --- | --- | --- |
| **permit + warning** (default) | nothing set | fetch proceeds, one warning per target |
| **strict** | `HYDROMA_ALLOW_DOWNLOAD=0` or `--strict` / `--deny-download` | `PermissionError`, no fetch |
| **explicit allow** | `HYDROMA_ALLOW_DOWNLOAD=1` or `--allow-download` | fetch proceeds, no warning |

Precedence: **CLI wins** over the environment for the whole process, then the
environment (re-read at every fetch), then the default (permit). If both
`--allow-download` and `--strict` are supplied, `--strict` wins.

The library default stays permissive on purpose: flipping it would break the 81
existing `engine/hydroma/data_pipeline/tests` tests. The strict flip is deferred
to a Wave-3 decision.

## Source inventory (15 instrumented call sites)

`open_meteo`, `nasa_power`, `soilgrids`, `stac_search`, `stac_oauth2_token`,
`chirps`, `worldclim_chelsa`, `open_meteo_seasonal`, `cgls`, `esa_worldcover`,
`gbif_occurrences`, `gbif_checklist`, `gbif_species`, `gbif_dataset`,
`hydrosheds`. Each is registered at call time in
`download_gate.REGISTERED_SOURCES`; `python pipeline.py --list-sources` prints
both that runtime registry and the static inventory above.

## CLI

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
python engine/hydroma/data_pipeline/pipeline.py --strict          # refuse
python engine/hydroma/data_pipeline/pipeline.py --allow-download  # permit
python engine/hydroma/data_pipeline/pipeline.py --list-sources    # inventory
```

`--help` works without importing `requests` or the connectors (network modules
are imported lazily inside the fetch methods).

## Roadmap

- **Wave 2 (done)** — gate added; behaviour-preserving observability only.
- **Wave 3** — decide whether strict becomes the out-of-the-box default.
- **Wave 3+** — move ingestion into a separate operator-invoked layer outside
  the engine core; the gate then becomes a hard boundary, preferably flag-only.
