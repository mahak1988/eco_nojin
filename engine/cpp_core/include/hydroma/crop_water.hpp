// HyDroMa C++ core — FAO-56 dual crop coefficient soil water balance.
//
// Daily soil water balance of the crop root zone with the dual
// crop-coefficient approach (basal crop coefficient Kcb + soil
// evaporation coefficient Ke) and water stress (Ks):
//     Dr,i = Dr,i-1 - (P - RO)i - Ii + ETc,i + DPi
//     ETc = (Kcb * Ks + Ke) * ET0
//
// References:
//  - Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998).
//    "Crop evapotranspiration." FAO Irrigation and Drainage Paper 56.
//  - Allen, R.G. et al. (2005). "The FAO-56 dual crop coefficient
//    method and its use in irrigation scheduling." Agric. Water
//    Manage. 70:3-24.
#pragma once

#include <vector>

namespace hydroma {

struct CropWaterParams {
    // Crop stage lengths [days]
    int l_ini{25};
    int l_dev{35};
    int l_mid{45};
    int l_late{30};
    // Basal crop coefficients [-]
    double kcb_ini{0.15};
    double kcb_mid{1.10};
    double kcb_end{0.35};
    // Root zone and soil water
    double root_depth_m{0.6};   ///< effective root zone depth [m]
    double theta_fc{0.32};      ///< field capacity [m3/m3]
    double theta_wp{0.15};      ///< wilting point [m3/m3]
    double p_fraction{0.55};    ///< depletion fraction for no stress
    // Evaporation parameters
    double rew_mm{9.0};         ///< readily evaporable water [mm]
    double tew_mm{20.0};        ///< total evaporable water [mm]
    double fraction_wetted{0.4};///< f_w (drip) [-]
    double crop_height_m{0.6};  ///< for Kc_max computation
    double kc_max{1.20};        ///< upper bound on Kc after full cover
};

struct CropWaterResult {
    std::vector<double> et0_mm;
    std::vector<double> etc_mm;      ///< actual ETc [mm/day]
    std::vector<double> kc_effective;///< Kcb*Ks + Ke [-]
    std::vector<double> stress_factor;///< Ks [-]
    std::vector<double> depletion_mm;///< root zone depletion Dr [mm]
    std::vector<double> deep_percolation_mm;///< DP [mm/day]
    std::vector<double> irrigation_mm;///< applied irrigation [mm/day]
    double total_etc_mm{0.0};
    double total_rain_mm{0.0};
    double total_irrigation_mm{0.0};
    double total_dp_mm{0.0};
    double water_balance_error_mm{0.0}; ///< closure check
};

/// Run the daily dual-Kc water balance.
/// \param et0_mm      daily reference ET0 [mm]
/// \param rain_mm     daily rainfall [mm]
/// \param auto_irrigate  when true, irrigate to field capacity whenever
///                       depletion exceeds RAW (root zone)
/// \param p           crop/soil parameters
CropWaterResult simulate_crop_water(const std::vector<double>& et0_mm,
                                    const std::vector<double>& rain_mm,
                                    bool auto_irrigate,
                                    const CropWaterParams& p);

/// Run multiple independent crop water simulations in parallel.
/// Each element in the input vectors represents one simulation run.
std::vector<CropWaterResult> simulate_crop_water_batch(
    const std::vector<std::vector<double>>& et0_mm_list,
    const std::vector<std::vector<double>>& rain_mm_list,
    const std::vector<bool>& auto_irrigate_list,
    const std::vector<CropWaterParams>& params_list);

}  // namespace hydroma
