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


def test_zz_helper_debug():
    print("\n--- helper debug ---")
    for dotted in (
        "engine",
        "engine.hydroma",
        "engine.hydroma.eval",
        "engine.hydroma.eval.data_cache",
    ):
        try:
            m = engine_module(dotted)
            print(f"  OK  {dotted} -> {getattr(m, '__file__', None)}")
        except Exception:
            print(f"  FAIL {dotted}:")
            traceback.print_exc()
            break
    assert True
