# HyDroMa Validation System
==========================

This directory contains the validation infrastructure for HyDroMa computational models.

## Structure

```
engine/hydroma/models/validation/
├── test_cases/              # YAML test case definitions per model
│   ├── richards_1d.yaml
│   ├── saint_venant_1d.yaml
│   ├── scs_cn.yaml
│   ├── rothc.yaml
│   └── penman_monteith.yaml
├── reference_profiles/      # NumPy .npy reference data for comparison
└── README.md               # This file
```

## Test Case Format

Each model has a YAML file defining test cases:

```yaml
model: richards_1d
reference: "Celia et al. 1990"
category: hydrology
language: cpp
status: validated

tolerances:
  rtol: 1e-4
  atol: 1e-6
  mass_balance_max: 1e-3

cases:
  - name: infiltration_sandy_loam_constant_flux
    description: "Constant flux infiltration into initially dry sandy loam"
    inputs:
      soil_type: "sandy_loam"
      nz: 100
      ...
    expected:
      pressure_head_profile: "reference_profiles/richards_sandy_loam_24h.npy"
      mass_balance_error: "< 1e-3"
```

## Running Validation Locally

```bash
# Run the whole corpus and print a per-case report
python -c "from engine.hydroma.models.validation import report; print(report())"

# Machine-readable counts
python -c "from engine.hydroma.models.validation import summary; print(summary())"
```

There is no per-model CLI flag. `runner.py` loads every case in `test_cases/`
and dispatches on `case.model`; filter in Python, e.g.
`[o for o in run_all() if o.model == "richards_1d"]`.

Each case is reported as one of four statuses, and the distinction matters:

| status | meaning |
|--------|---------|
| `match` | the implementation agrees with the stored value |
| `mismatch` | the implementation disagrees with a reproducible stored value — **the code is wrong** |
| `inconsistent_case` | the case's own inputs and expected intermediates contradict each other — **the case is wrong** |
| `not_run` | no implementation is wired for this case |

`inconsistent_case` exists so that a red corpus does not invite "fixing" a
correct implementation to match an expectation no correct implementation can
satisfy. Do not collapse these into a single pass/fail.

## CI Pipeline

The slaughterhouse pipeline runs on every PR:

1. **Discover** - Find all models with test cases
2. **Build** - Compile C++ core (if needed)
3. **Validate** - Run test cases for each model × backend
4. **Gate** - Block PR merge if any failures
5. **Badges** - Generate and deploy shields.io badges

## Adding a New Model

1. Create test case YAML in `test_cases/`
2. Add reference data to `reference_profiles/` if needed
3. Add a handler to `_DISPATCH` in `runner.py`, and return `not_run` with a
   reason for any model you do not wire. Do not invent a fallback number.
4. Add to CI matrix in `.github/workflows/hydroma-slaughterhouse.yml`
5. Run locally to verify
6. Push - CI will validate automatically

## Tolerance Guidelines

| Model Type | rtol | atol | Mass Balance |
|------------|------|------|--------------|
| PDE (Richards, St-Venant) | 1e-4 | 1e-6 | < 1e-3 |
| Algebraic (SCS-CN, Rational) | 1e-6 | 1e-9 | Exact |
| Empirical (RUSLE, ET0) | 1e-3 | 1e-4 | N/A |
| Carbon (RothC, ECSI) | 1e-3 | 1e-5 | < 1e-2 tC/ha/yr |
| Optimization | 1e-3 | 1e-5 | Constraint satisfaction |

## Reference Data

Reference profiles are stored as `.npy` files in `reference_profiles/`. To generate new reference data:

```python
import numpy as np

# Run model with known inputs
output = run_model(...)
np.save("engine/hydroma/models/validation/reference_profiles/my_reference.npy", output)
```