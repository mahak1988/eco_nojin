# Engine Directory

The `engine` directory houses the computational core of the Eco Nojin platform. It contains specialized modules for land analysis, hydrological modeling, climate data processing, and related scientific calculations.

## Subsystems

### `land/`
Responsible for topographical analysis, including:
- Digital Elevation Model (DEM) processing
- Slope and aspect calculation
- Terrain classification
- Drainage analysis
- Land capability assessment

### `hydroma/`
An integrated suite for hydro-meteorological and agricultural modeling, including:
- Soil analysis and fertility models
- Climate data processing and ET₀ calculation
- Groundwater and hydrology models
- Crop water requirement calculations
- Watershed analysis and structure design
- Calibration and optimization tools

### `data/`
Load-bearing shared data, not sample rasters: `soil_vg_table.csv` is the single
source of the van Genuchten parameter table that the whole engine reads, with
the meta-contract, physics-guard and table-projection tools that keep the C++,
Numba and Python copies agreeing. See `data/README.md`.

### `cpp_core/`
C++20 source of the performance-critical kernels. It is **not** orphaned: the
compiled `hydroma_core` extension is loaded by `engine/hydroma/cpp_bridge`
(which falls back to pure-Python kernels when the extension is absent) and is
consumed from the engine tests, the API gateway (`/health` backend status) and
the services. Build instructions live in `cpp_core/README.md`.

## Architecture

- **Models:** The canonical SQLAlchemy models are defined in `database/models.py`. Engine-local ORM models that predate that centralisation still exist and are documented in place (`engine/hydroma/core/models.py`, `engine/hydroma/biofertilizer/models.py`); everything added since uses the central definition.
- **Dependencies:** The `engine` layer is designed to be independent of the `services` layer. The `services` layer interacts with `engine` through defined interfaces and adapters (located in `adapters/`).
- **State:** Modules within `engine` should ideally be stateless or have minimal, well-defined state for a given input.

## Interaction with Other Layers

- **Services:** The `services` layer uses adapters (e.g., `adapters/engine_adapter.py`, `adapters/hydroma_adapter.py`) to interact with the `engine` layer, promoting loose coupling.
- **Database:** Direct database interaction within `engine` should be avoided. The `services` layer is responsible for persisting data using models from `database/models.py`.