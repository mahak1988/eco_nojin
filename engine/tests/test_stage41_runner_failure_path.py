"""Regression tests for Stage 41 resumable-runner failure handling."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from engine.hydroma.eval import resumable_benchmark_runner as runner_module
from engine.hydroma.eval.resumable_benchmark_runner import (
    ResumableBenchmarkRunner,
)


def test_prediction_failure_returns_failed_record_without_unbound_baseline(
    monkeypatch,
) -> None:
    weather = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2024-01-01"]),
            "VapourPressureDeficit": [1.0],
            "SoilMoisture_0_7cm": [0.2],
            "ShortwaveRadiation": [10.0],
        }
    )
    weather.attrs["source"] = "test"
    monkeypatch.setattr(runner_module, "fetch_daily_weather", lambda *args: weather)
    monkeypatch.setattr(
        runner_module,
        "Sentinel2Source",
        lambda: SimpleNamespace(
            fetch_reflectance=lambda *args: (_ for _ in ()).throw(
                RuntimeError("satellite unavailable")
            )
        ),
    )
    monkeypatch.setattr(
        runner_module,
        "compute_daily_ewsi",
        lambda *args, **kwargs: SimpleNamespace(
            ewsi=np.array([0.5]),
            missing_fields=[],
            quality_status="complete",
            scientific_status="estimated",
            method="test",
            weights={},
            computation_policy="test",
        ),
    )
    def fail_after_input_capture(*args, input_sink=None, **kwargs):
        assert input_sink is not None
        input_sink.append({"par": np.array([1.0]), "dates": ["2024-01-01"]})
        raise RuntimeError("prediction failed")

    monkeypatch.setattr(
        runner_module, "compute_seasonal_prediction", fail_after_input_capture
    )

    runner = object.__new__(ResumableBenchmarkRunner)
    runner.hyrue_params = object()
    runner.baseline_params = object()
    runner.data_label = "test"
    runner.input_sink = []
    runner.model_code_hash = None

    result = runner.process_record(
        pd.Series(
            {
                "Latitude": 25.0,
                "Longitude": 85.0,
                "SowingDate": "2023-11-01",
                "HarvestDate": "2024-01-01",
                "Field_ID": 1533,
                "District": "test-district",
                "Year": 2024,
                "GrainYield": 2.0,
            }
        )
    )

    assert result.execution_status == "FAILED"
    assert result.failure_reason == "HYRUE computation failed: prediction failed"
    assert result.predicted_yield is None
    assert result.baseline_predicted_yield is None
    assert runner.input_sink == [
        {
            "record_id": "1533",
            "par": np.array([1.0]),
            "dates": ["2024-01-01"],
        }
    ]
