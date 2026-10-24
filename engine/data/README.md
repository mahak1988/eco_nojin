# Engine Shared Data

Shared, load-bearing data for the `engine` modules, plus the generators that
project it into the other backends. This directory holds no DEM rasters and no
sample fixtures: what lives here is read at run time by the numerical kernels.

## Contents

| File | Role |
|---|---|
| `soil_vg_table.csv` | Single source of the van Genuchten parameter table the whole engine reads. Loaded by `engine.hydroma.soil.parameters`, and declared in `package-data` because it is load-bearing rather than incidental. |
| `soil_table.py` | The loader for that CSV: fineness order, unit conversion (`ks_cm_per_day` is canonical), provenance flags and `disputed_textures()`. |
| `physics_guard.py` | `warn_if_disputed` — a disputed conductivity row fails loudly instead of silently. |
| `meta_contract.py` | The raw-data sidecar contract: every raw file ships a `*.meta.json`. |
| `generate_cpp_table.py` | Projects the CSV into `engine/cpp_core/src/soil.cpp`, because the C++ kernel cannot read a CSV at run time. `python -m engine.data.generate_cpp_table --check` is the CI guard that a hand edit to the generated block never becomes a second copy of the table. |
| `apply_published_table.py` | The one command that closes the four unresolved rows once the publication is in hand. |
| `SOIL_TABLE_CONFLICTS.md` | The unresolved conflicts, per row. |

## Why one file

The table used to exist in four places with three different answers
(`soil/physics.py`, `cpp_bridge/soil_physics_fast.py`, `cpp_core/src/soil.cpp`
and `land/integration/soil_integrator.py`). `soil_table.py`'s docstring records
that history and what the single source does **not** settle — the unresolved
conflicts stay flagged rather than being averaged away.

## Usage

Nothing here is a fixture for `engine/land` tests. The Python backends read the
CSV through `soil_table.py`; the C++ table is regenerated from the same CSV with
`python -m engine.data.generate_cpp_table`; and the sidecar contract is enforced
by `engine.data.meta_contract.validate_meta` from the tests
(`engine/tests/test_meta_contract.py`).
