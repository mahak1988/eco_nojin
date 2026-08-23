# services/models/__init__.py

# All major DB models have been moved to database/models.py for centralized management by Alembic.
# This package can be removed or used for service-specific models not managed by the main Alembic revision.

# Import models that are now in the central database.models module
# This is for compatibility if other parts of the codebase expect them here.
# In the future, imports should come directly from database.models.

# Note: The Base used by these models is defined in database.config.Base
# and is shared across the application.

# from .land_models import LandProfileDB, TerrainAnalysisDB, LandCapabilityAssessmentDB
# from .soil_climate_models import SoilProfileDB, ClimateDataDB
# from .water_models import SurfaceWaterSourceDB, GroundwaterDataDB, WatershedDataDB

# Since they are now in database.models, we could potentially import them from there if needed here.
# But the recommended place to import them is directly from database.models.

__all__ = [] # Models are now in database.models