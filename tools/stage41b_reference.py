import sys
sys.path.insert(0, 'D:/HyDroMA')
sys.path.insert(0, 'D:/eco_nojin')
import numpy as np
from engine.hydroma.models.hyrue import HYRUE, HYRUEParams

# Fixed scalar input: a single representative day (Stage 40 frozen model input)
par = 6.0      # MJ/m^2/day
lai = 3.0
ewsi = 0.05
t_mean = 24.0  # deg C
days = 1

# Stage 40 frozen params: epsilon=2.63, HI=0.45
params = HYRUEParams(epsilon=2.63, hi=0.45, k=0.65, lai_max=6.0, t_opt=25.0)
model = HYRUE(params)
result = model.compute(par, lai, ewsi, t_mean)
print('REF_CAL_YIELD_T_HA=' + repr(float(result['yield_t_ha'])))
print('REF_TOTAL_BIOMASS=' + repr(float(result['total_biomass_g_m2'])))
print('REF_KEYS=' + repr(sorted(result.keys())))

# Baseline (epsilon=2.2) linearity check
params_base = HYRUEParams(epsilon=2.2, hi=0.45, k=0.65, lai_max=6.0, t_opt=25.0)
model_base = HYRUE(params_base)
result_base = model_base.compute(par, lai, ewsi, t_mean)
print('REF_BASE_YIELD_T_HA=' + repr(float(result_base['yield_t_ha'])))
print('RATIO_CAL_BASE=' + repr(float(result['yield_t_ha'] / result_base['yield_t_ha'])))
print('2.63/2.2=' + repr(2.63 / 2.2))
print('LINEARITY_OK=' + repr(abs(result['yield_t_ha'] - result_base['yield_t_ha'] * (2.63 / 2.2)) < 1e-12))

