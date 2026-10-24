import importlib
import sys
import traceback

_PROJECT_ROOT = "D:/HyDroMA"


def engine_module(dotted: str):
    if _PROJECT_ROOT not in sys.path:
        sys.path.append(_PROJECT_ROOT)
    parts = dotted.split(".")
    for i in range(1, len(parts) + 1):
        name = ".".join(parts[:i])
        if name not in sys.modules:
            importlib.import_module(name)
    return sys.modules[dotted]


def test_zz_step1_engine_only():
    print("\n--- step 1: engine only ---")
    m = engine_module("engine")
    print("  OK:", m.__file__)


def test_zz_step2_hydrama_only():
    print("\n--- step 2: engine.hydroma only ---")
    try:
        m = engine_module("engine.hydroma")
        print("  OK:", m.__file__)
    except Exception:
        traceback.print_exc()


def test_zz_step3_deep():
    print("\n--- step 3: deep module ---")
    try:
        m = engine_module("engine.hydroma.simulation.data_cache")
        print("  OK:", m.__file__)
    except Exception:
        traceback.print_exc()
