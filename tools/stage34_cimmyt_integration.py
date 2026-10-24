"""Stage 34 — CIMMYT integration run.

Runs the EWSI → HYRUE pipeline on a sample of CIMMYT records using
synthetic EWSI inputs (real satellite NIR/SWIR, VPD, and soil moisture
data are not available from configured sources — see limitations).

Synthetic EWSI inputs are used ONLY to verify pipeline structure.
Results are NOT validation-grade and must not be reported as benchmark
metrics.
"""

from __future__ import annotations

import sys
from datetime import datetime

import numpy as np
import pandas as pd

from engine.hydroma.eval.seasonal_predictor import (
    EWSIInputs,
    InputSourcePolicy,
    SeasonalPredictionRequest,
    compute_seasonal_prediction,
)


def load_cimmyt_sample(n_records: int = 5) -> list[dict]:
    """Load a sample of CIMMYT records for integration testing."""
    df = pd.read_excel(
        "data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx"
    )
    # Take records from different districts for spatial diversity
    sample = df.sample(n=n_records, random_state=42)
    records = []
    for _, row in sample.iterrows():
        records.append(
            {
                "field_id": str(row["Field_ID"]),
                "district": str(row["District"]),
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
                "planting_date": str(row["SowingDate"])[:10],
                "harvest_date": str(row["HarvestDate"])[:10],
                "observed_yield": float(row["GrainYield"]),
                "observed_yield_unit": "t/ha",
            }
        )
    return records


def run_cimmyt_integration(n_records: int = 5) -> dict:
    """Run EWSI → HYRUE pipeline on CIMMYT sample records."""
    results = []
    records = load_cimmyt_sample(n_records)

    for rec in records:
        site_id = f"CIMMYT_{rec['field_id']}"
        season_id = f"wheat_{rec['district']}"

        print(f"\n=== {site_id} ({rec['district']}) ===")
        print(f"  Coordinates: {rec['latitude']}, {rec['longitude']}")
        print(f"  Season: {rec['planting_date']} to {rec['harvest_date']}")
        print(f"  Observed yield: {rec['observed_yield']} t/ha")

        # Create EWSI inputs with synthetic values (clearly labeled)
        n_days = (
            datetime.strptime(rec["harvest_date"], "%Y-%m-%d")
            - datetime.strptime(rec["planting_date"], "%Y-%m-%d")
        ).days + 1

        # Synthetic EWSI inputs - NOT real observations
        nir = np.full(n_days, 0.5)
        swir = np.full(n_days, 0.2)
        vpd = np.full(n_days, 1.5)
        soil_moisture = np.full(n_days, 0.30)

        ewsi_inputs = EWSIInputs(
            nir=nir,
            swir=swir,
            vpd=vpd,
            soil_moisture=soil_moisture,
            soil_field_capacity=0.35,
        )

        request = SeasonalPredictionRequest(
            site_id=site_id,
            season_id=season_id,
            crop="wheat",
            planting_date=rec["planting_date"],
            harvest_date=rec["harvest_date"],
            latitude=rec["latitude"],
            longitude=rec["longitude"],
            input_source_policy=InputSourcePolicy.ALLOW_ESTIMATED,
            ewsi_inputs=ewsi_inputs,
            data_label="cimmyt_integration_synthetic_ewsi",
        )

        try:
            prediction, report = compute_seasonal_prediction(request)
            print(f"  Computation status: {prediction.computation_status}")
            print(f"  Predicted yield: {prediction.value:.3f} t/ha")
            print(f"  Observed yield: {rec['observed_yield']} t/ha")
            print(f"  Input quality: {prediction.input_quality}")
            print(f"  EWSI provenance: {prediction.ewsi_provenance}")

            results.append(
                {
                    "site_id": site_id,
                    "district": rec["district"],
                    "predicted_yield_t_ha": prediction.value,
                    "observed_yield_t_ha": rec["observed_yield"],
                    "computation_status": prediction.computation_status,
                    "input_quality": prediction.input_quality,
                    "ewsi_provenance": prediction.ewsi_provenance,
                    "errors": report.errors,
                    "warnings": report.warnings,
                }
            )
        except Exception as exc:
            print(f"  FAILED: {exc}")
            results.append(
                {
                    "site_id": site_id,
                    "district": rec["district"],
                    "predicted_yield_t_ha": None,
                    "observed_yield_t_ha": rec["observed_yield"],
                    "computation_status": "failed",
                    "error": str(exc),
                }
            )

    return {
        "n_records": n_records,
        "n_successful": sum(1 for r in results if r.get("predicted_yield_t_ha") is not None),
        "results": results,
        "note": "Synthetic EWSI inputs used — results are NOT validation-grade.",
    }


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    summary = run_cimmyt_integration(n_records=n)
    print(f"\n{'=' * 50}")
    print("CIMMYT Integration Summary")
    print(f"{'=' * 50}")
    print(f"Records: {summary['n_records']}")
    print(f"Successful: {summary['n_successful']}")
    print(f"Note: {summary['note']}")
