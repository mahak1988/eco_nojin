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
Contains sample data files (e.g., DEMs) used for testing the `land` and `hydroma` modules.

### `cpp_core/`
*(Orphaned)* Contains C++ source code for performance-critical computations. This module is currently not connected to the main Python application.

## Architecture

- **Models:** The canonical SQLAlchemy models are defined in `database/models.py`. Any legacy model definitions within `engine` (e.g., older `hydroma` models) have been deprecated in favor of the central definition.
- **Dependencies:** The `engine` layer is designed to be independent of the `services` layer. The `services` layer interacts with `engine` through defined interfaces and adapters (located in `adapters/`).
- **State:** Modules within `engine` should ideally be stateless or have minimal, well-defined state for a given input.

## Interaction with Other Layers

- **Services:** The `services` layer uses adapters (e.g., `adapters/engine_adapter.py`, `adapters/hydroma_adapter.py`) to interact with the `engine` layer, promoting loose coupling.
- **Database:** Direct database interaction within `engine` should be avoided. The `services` layer is responsible for persisting data using models from `database/models.py`.