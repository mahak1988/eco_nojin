import importlib
import sys
import traceback


def test_zz_real_error():

    try:
        m = importlib.import_module("engine.hydroma.eval.benchmark_split_manifest")
        print("\n  import_module OK:", m.__file__)
    except Exception:
        print("\n  import_module traceback:")
        traceback.print_exc()

    print("\n  sys.modules['engine.hydroma']:", sys.modules.get("engine.hydroma"))
    print("  'engine.hydroma.eval' in sys.modules:", "engine.hydroma.eval" in sys.modules)
    print("  'engine.hydroma.eval.benchmark_split_manifest' in sys.modules:",
          "engine.hydroma.eval.benchmark_split_manifest" in sys.modules)
    assert True
