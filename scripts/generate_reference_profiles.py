"""Generate reference profiles for model validation.

Creates .npy files with expected outputs for test cases.
These reference values serve as the "ground truth" for validation.
"""

from pathlib import Path

import numpy as np

REF_DIR = Path("engine/hydroma/models/validation/reference_profiles")
REF_DIR.mkdir(parents=True, exist_ok=True)


def save_reference(name: str, data: np.ndarray):
    """Save a reference profile as .npy file."""
    path = REF_DIR / f"{name}.npy"
    np.save(path, data)
    print(f"Saved {name}: shape={data.shape}, dtype={data.dtype}")


# SCS-CN reference profiles
save_reference("scs_cn_cn70_p50", np.array([5.813]))
save_reference("scs_cn_cn95_p30", np.array([18.35]))
save_reference("scs_cn_cn40_p10", np.array([0.0]))
save_reference("scs_cn_cn100_p25", np.array([25.0]))

# Penman-Monteith reference profiles
save_reference("penman_monteith_fao56_ch3", np.array([6.5989]))
save_reference("penman_monteith_tropical", np.array([5.4272]))
save_reference("penman_monteith_arid", np.array([13.8463]))

# Hargreaves reference profiles
save_reference("hargreaves_standard", np.array([5.37]))
save_reference("hargreaves_tropical", np.array([4.85]))

# RothC reference profiles
save_reference("rothc_standard_run", np.array([97.1718]))
save_reference("rothc_clay_23", np.array([97.605]))

# Kirpich reference profiles
save_reference("kirpich_1000m_1pct", np.array([23.444]))

# Rational method reference profiles
save_reference("rational_1ha_100mm", np.array([500.0]))

# RUSLE reference profiles
save_reference("rusle_loam_100m_5pct", np.array([12.5]))

# HDVI reference profiles
save_reference("hdvi_standard", np.array([0.45]))
save_reference("hdvi_drought", np.array([0.15]))

# Check dam reference profiles
save_reference("check_dam_standard", np.array([1.8, 12.5, 1500.0, 3.5, 225000.0, 0.75]))

# Biofertilizer reference profiles
save_reference("biofertilizer_standard", np.array([500.0, 200.0, 400.0, 30.0]))

print("\nAll reference profiles generated successfully!")
