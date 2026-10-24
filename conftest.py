"""Repository-root pytest configuration.

Makes the HYDROMA engine importable in environments where the import
machinery's directory scan intermittently fails to find package
directories.

The sandbox filesystem caches path resolutions, and a path that was
resolved while the tree was in a particular state stays cached as
"missing" even after the directory becomes visible to other tools.  The
symptom is a confusing ``ModuleNotFoundError: No module named
'engine.hydroma'`` raised for a module that demonstrably exists.

``engine/hydroma/eval/runtime_bootstrap.py`` works around this: it
registers the engine package hierarchy with explicit search paths and
loads modules straight from their file paths, bypassing the failing
directory scan.

Installing the bootstrap here — before any test module is collected —
means every test module resolves the engine the same way, instead of
depending on which import order happens to work.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_BOOTSTRAP_PATH = _ROOT / "engine" / "hydroma" / "eval" / "runtime_bootstrap.py"

if "engine" in sys.modules:
    # Another conftest already installed it.
    pass
elif _BOOTSTRAP_PATH.exists():
    _spec = importlib.util.spec_from_file_location(
        "_hydroma_runtime_bootstrap", _BOOTSTRAP_PATH
    )
    if _spec is not None and _spec.loader is not None:
        _module = importlib.util.module_from_spec(_spec)
        sys.modules["_hydroma_runtime_bootstrap"] = _module
        _spec.loader.exec_module(_module)
        _module.ensure_engine_importable()

        # Load the modules the test-suite imports directly, so that a
        # later ``from engine.hydroma.<pkg>.<mod> import ...`` in a test
        # module finds a fully initialised module in ``sys.modules``
        # instead of re-running the failing directory scan.  The import
        # cycle between ``weather_source`` and ``par_pipeline`` is
        # resolved by the bootstrap's documented load order.
        for _name in (
            "engine.hydroma.simulation.radiation_units",
            "engine.hydroma.simulation.weather_source",
            "engine.hydroma.simulation.par_pipeline",
            "engine.hydroma.simulation.ewsi_pipeline",
            "engine.hydroma.simulation.lai_model",
            "engine.hydroma.simulation.vpd_model",
            "engine.hydroma.simulation.soil_moisture_model",
            "engine.hydroma.simulation.data_cache",
            "engine.hydroma.models.hyrue",
            "engine.hydroma.models.ewsi",
            "engine.hydroma.eval.prediction",
            "engine.hydroma.eval.seasonal_predictor",
        ):
            try:
                _module.load_module(_name)
            except Exception:  # pragma: no cover - best effort preload
                pass
