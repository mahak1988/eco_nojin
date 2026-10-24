import sys


def test_zz_diagnostic_import_env():
    """Print the import environment as pytest sees it (diagnostic)."""
    print("\n--- pytest import environment ---")
    print("sys.path[0:6]:", sys.path[:6])
    print("'engine' in sys.modules:", "engine" in sys.modules)
    if "engine" in sys.modules:
        e = sys.modules["engine"]
        print("engine.__file__:", getattr(e, "__file__", None))
        print("engine.__path__:", list(getattr(e, "__path__", [])))
    print("__name__ of this test module:", __name__)

    import os

    print("os.listdir(engine.__path__[0]):", sorted(os.listdir("D:/HyDroMA/engine"))[:12])
    print("'hydrama' in that listing:", "hydrama" in os.listdir("D:/HyDroMA/engine"))

    import importlib.util

    spec = importlib.util.find_spec("engine.hydroma")
    print("find_spec('engine.hydroma'):", spec)

    try:
        m = importlib.import_module("engine.hydroma")
        print("import_module OK:", m.__file__)
    except Exception as exc:
        print(f"import_module FAILED: {type(exc).__name__}: {exc}")

    try:

        print("from-import OK")
    except Exception as exc:
        print(f"from-import FAILED: {type(exc).__name__}: {exc}")
    print("--- end diagnostic ---")
    assert True
