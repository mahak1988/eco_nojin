import numpy as np

from engine.hydroma.models.hyrue import HYRUE

model = HYRUE(crop="wheat")
print(f"Params: epsilon={model.params.epsilon}, hi={model.params.hi}, t_opt={model.params.t_opt}")

# Test seasonal mode
par = np.array([10.0]*120, dtype=float)
lai = np.linspace(0.1, 4.0, 120, dtype=float)
ewsi = np.array([0.2]*120, dtype=float)
t_mean = np.array([15.0]*120, dtype=float)
result = model.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t_mean)
print(f"Mode: {result['computation_mode']}")
print(f"Yield t/ha: {result['yield_t_ha']}")
print(f"Yield type: {type(result['yield_t_ha'])}")

# Test the seasonal prediction pipeline with a real record
from engine.hydroma.eval.seasonal_predictor import (
    InputSourcePolicy,
    SeasonalPredictionRequest,
    compute_seasonal_prediction,
)

# Fetch real weather for a sample record
from engine.hydroma.simulation.weather_source import fetch_daily_weather

request = SeasonalPredictionRequest(
    site_id="District_Begusarai",
    season_id="wheat_2017",
    crop="wheat",
    planting_date="2016-11-15",
    harvest_date="2017-04-15",
    latitude=25.2648,  # approximate for Begusarai
    longitude=85.1348,
    input_source_policy=InputSourcePolicy.DIAGNOSTIC,
)

try:
    weather_df = fetch_daily_weather(
        latitude=25.2648,
        longitude=85.1348,
        start="2016-11-15",
        end="2017-04-15",
    )
    print(f"\nWeather fetched: {len(weather_df)} days")
    print(f"Columns: {list(weather_df.columns)}")
    print(f"Shortwave attrs: source={weather_df.attrs.get('shortwave_source')}")
    print(f"PAR attrs: source={weather_df.attrs.get('par_source')}")

    # Try with DIAGNOSTIC policy (allows legacy fallback for missing EWSI)
    prediction, report = compute_seasonal_prediction(request)
    print(f"\nPrediction yield: {prediction.value}")
    print(f"Computation status: {prediction.computation_status}")
    print(f"Scientific support: {prediction.scientific_support_status}")
    print(f"External validation: {prediction.external_validation_status}")
    print(f"Input quality: {prediction.input_quality}")
    print(f"PAR provenance: {prediction.par_provenance}")
    print(f"Missing fields: {prediction.missing_fields}")
    print(f"LAI provenance: {prediction.lai_provenance}")
    print(f"EWSI provenance: {prediction.ewsi_provenance}")
except Exception as e:
    print(f"\nError: {type(e).__name__}: {e}")
