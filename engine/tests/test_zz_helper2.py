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
            try:
                importlib.import_module(name)
            except Exception:
                traceback.print_exc()
                raise
    return sys.modules[dotted]


def test_zz_helper_sim():
    print("\n--- helper for simulation.data_cache ---")
    try:
        m = engine_module("engine.hydroma.simulation.data_cache")
        print("  OK:", m.__file__)
    except Exception:
        traceback.print_exc()

    print("\n  sys.path[0:4]:", sys.path[:4])
    import os

    for p in sys.path[:4]:
        if p and os.path.isdir(p):
            try:
                names = sorted(os.listdir(p))[:6]
            except Exception as exc:
                names = f"<err {exc}>"
            print(f"   {p}: {names}")
    assert True
