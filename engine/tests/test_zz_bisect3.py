import sys


def test_zz_a_import_eval_pkg():

    h = sys.modules["engine.hydroma"]
    print("\n  engine.hydroma.__path__:", list(getattr(h, "__path__", [])))
    print("  engine.hydroma.__spec__:", getattr(h, "__spec__", None))
    print("  engine.hydroma.__file__:", getattr(h, "__file__", None))
    e = sys.modules["engine.hydroma.eval"]
    print("  engine.hydroma.eval.__path__:", list(getattr(e, "__path__", [])))
    print("  engine.hydroma.eval.__spec__:", getattr(e, "__spec__", None))
    assert True


def test_zz_b_import_submodule():

    h = sys.modules["engine.hydroma"]
    print("\n  engine.hydroma.__path__:", list(getattr(h, "__path__", [])))
    print("  engine.hydroma.__spec__:", getattr(h, "__spec__", None))
    import os

    p = list(getattr(h, "__path__", []))[0]
    print("  listdir:", sorted(os.listdir(p))[:8])
    try:

        print("  import OK")
    except Exception as exc:
        print(f"  import FAILED: {type(exc).__name__}: {exc}")
        import importlib.util

        print(
            "  find_spec:",
            importlib.util.find_spec("engine.hydroma.eval.benchmark_split_manifest"),
        )
    assert True
