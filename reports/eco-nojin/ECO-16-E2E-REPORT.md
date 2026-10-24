{
  "document_id": "ECO-16",
  "status": "BLOCKED_ENVIRONMENT",
  "generated_at": "2026-10-10T02:53:45.474639+00:00",
  "generator_version": "ECO-16-runner/1.0.0",
  "gate": {
    "data_root": "data\\raw",
    "categories": {
      "climate": {
        "expected_files": [
          "chirps_daily_precipitation.csv",
          "era5_land_daily.csv"
        ],
        "present_files": [],
        "problems": []
      },
      "satellite": {
        "expected_files": [
          "sentinel2_sr_monthly.csv"
        ],
        "present_files": [],
        "problems": []
      },
      "soil": {
        "expected_files": [
          "soilgrids_phh2o.csv"
        ],
        "present_files": [],
        "problems": []
      }
    },
    "problems": [],
    "missing": [
      "data\\raw/climate/ (one of: chirps_daily_precipitation.csv, era5_land_daily.csv)",
      "data\\raw/satellite/ (one of: sentinel2_sr_monthly.csv)",
      "data\\raw/soil/ (one of: soilgrids_phh2o.csv)"
    ],
    "ok": false,
    "blocked_reason": "local raw mirror incomplete — ZED §2.2ج forbids live download, so the chain cannot run. Provide the files listed below, each with a .meta.json sidecar that passes engine.data.meta_contract."
  },
  "missing": [
    "data\\raw/climate/ (one of: chirps_daily_precipitation.csv, era5_land_daily.csv)",
    "data\\raw/satellite/ (one of: sentinel2_sr_monthly.csv)",
    "data\\raw/soil/ (one of: soilgrids_phh2o.csv)"
  ],
  "required_categories": {
    "climate": [
      "chirps_daily_precipitation.csv",
      "era5_land_daily.csv"
    ],
    "satellite": [
      "sentinel2_sr_monthly.csv"
    ],
    "soil": [
      "soilgrids_phh2o.csv"
    ]
  },
  "meta_contract": "Each raw file needs <file>.meta.json with the required fields of spec §4.6 (dataset_id, dataset_version, source_id, variable, unit, content_hash); see engine/data/meta_contract.py and tests/reference_data/README.md.",
  "steps_to_unblock": [
    "Mirror the source files locally (no runtime download).",
    "Write a validating .meta.json sidecar next to each file.",
    "Re-run: python tools/run_e2e_demo.py --data-root data/raw"
  ],
  "scientific_claim": "None. The chain has not executed, so no indicator value exists; this report claims nothing about model accuracy."
}