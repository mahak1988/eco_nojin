"""
Run all HYRUE YAML validation cases independently.
"""
import numpy as np

from engine.hydroma.models.hyrue import HYRUE
from engine.hydroma.models.validation.runner import _coerce, _reduce

# YAML test cases
cases = [
    {
        "name": "mid_season_wheat",
        "inputs": {"par": 20.0, "lai": [2.1, 2.4, 2.6, 2.3, 1.9], "ewsi": [0.45, 0.52, 0.61, 0.58, 0.4], "t_mean": 18.0},
        "expected": 0.04452198,
        "expected_key": "yield_t_ha",
        "reduce": "last",
    },
    {
        "name": "par_at_minimum",
        "inputs": {"par": 0.0, "lai": [2.1, 2.4, 2.6, 2.3, 1.9], "ewsi": [0.45, 0.52, 0.61, 0.58, 0.4], "t_mean": 18.0},
        "expected": 0.0,
        "expected_key": "yield_t_ha",
        "reduce": "last",
    },
    {
        "name": "par_at_maximum",
        "inputs": {"par": 50.0, "lai": [2.1, 2.4, 2.6, 2.3, 1.9], "ewsi": [0.45, 0.52, 0.61, 0.58, 0.4], "t_mean": 18.0},
        "expected": 0.11130496,
        "expected_key": "yield_t_ha",
        "reduce": "last",
    },
    {
        "name": "ewsi_at_minimum",
        "inputs": {"par": 20.0, "lai": [2.1, 2.4, 2.6, 2.3, 1.9], "ewsi": [0.0, 0.0, 0.0, 0.0, 0.0], "t_mean": 18.0},
        "expected": 0.0742033,
        "expected_key": "yield_t_ha",
        "reduce": "last",
    },
    {
        "name": "ewsi_at_maximum",
        "inputs": {"par": 20.0, "lai": [2.1, 2.4, 2.6, 2.3, 1.9], "ewsi": [1.0, 1.0, 1.0, 1.0, 1.0], "t_mean": 18.0},
        "expected": 0.0,
        "expected_key": "yield_t_ha",
        "reduce": "last",
    },
]

print("=== HYRUE YAML Validation Cases (Generic HYRUE()) ===")
m = HYRUE()  # generic params (eps=2.5, t_opt=25, hi=0.45)
print(f"Params: eps={m.params.epsilon}, hi={m.params.hi}, k={m.params.k}, t_opt={m.params.t_opt}")

all_match = True
for case in cases:
    # Coerce inputs like the runner does
    kwargs = {k: _coerce(v) for k, v in case["inputs"].items() if k not in ("expected_key", "reduce")}
    result = m.compute(**kwargs)
    measured = _reduce(result[case["expected_key"]], case["reduce"])
    match = np.isclose(float(measured), case["expected"], rtol=0.01, atol=0.01)
    status = "MATCH" if match else "MISMATCH"
    print(f"  {case['name']}: measured={measured:.8f}, expected={case['expected']}, {status}")
    if not match:
        all_match = False

print(f"\nAll cases match: {all_match}")
