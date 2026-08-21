// HyDroMa C++ core — FAO-56 dual crop coefficient water balance.
#include "hydroma/crop_water.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

namespace hydroma {

namespace {

// Stage progression helper: returns Kcb for a given day of the season.
double kcb_for_day(int day, const CropWaterParams& p) {
    const int t_ini = p.l_ini;
    const int t_dev = p.l_ini + p.l_dev;
    const int t_mid = p.l_ini + p.l_dev + p.l_mid;
    const int t_late = p.l_ini + p.l_dev + p.l_mid + p.l_late;
    if (day < 0) return p.kcb_ini;
    if (day <= t_ini) return p.kcb_ini;
    if (day < t_dev) {
        // linear growth during development
        const double frac = static_cast<double>(day - t_ini) / p.l_dev;
        return p.kcb_ini + frac * (p.kcb_mid - p.kcb_ini);
    }
    if (day < t_mid) return p.kcb_mid;
    if (day < t_late) {
        const double frac = static_cast<double>(day - t_mid) / p.l_mid;
        return p.kcb_mid + frac * (p.kcb_end - p.kcb_mid);
    }
    return p.kcb_end;
}

double kc_max_for_height(const CropWaterParams& p) {
    // FAO-56 eq. 72: Kc_max = 1.2 + (0.04*(u2-2) - 0.004*(RHmin-45))*(h/3)^0.3
    // Simplified for typical conditions (u2=2 m/s, RHmin=45%): 1.20.
    return p.kc_max;
}

}  // namespace

CropWaterResult simulate_crop_water(const std::vector<double>& et0_mm,
                                    const std::vector<double>& rain_mm,
                                    bool auto_irrigate,
                                    const CropWaterParams& p) {
    const std::size_t nd = et0_mm.size();
    if (nd == 0) throw std::invalid_argument("empty ET0 series");
    if (rain_mm.size() != nd) throw std::invalid_argument("rain/ET0 length mismatch");
    if (p.theta_fc <= p.theta_wp) throw std::invalid_argument("theta_fc must exceed theta_wp");

    CropWaterResult r;
    r.et0_mm = et0_mm;
    r.etc_mm.assign(nd, 0.0);
    r.kc_effective.assign(nd, 0.0);
    r.stress_factor.assign(nd, 1.0);
    r.depletion_mm.assign(nd, 0.0);
    r.deep_percolation_mm.assign(nd, 0.0);
    r.irrigation_mm.assign(nd, 0.0);

    const double taw_mm = 1000.0 * (p.theta_fc - p.theta_wp) * p.root_depth_m;
    const double raw_mm = p.p_fraction * taw_mm;
    const double kc_max = kc_max_for_height(p);
    const double few = p.fraction_wetted;  // fraction of soil surface wetted+exposed

    double dr = 0.0;        // root zone depletion [mm]
    double de = 0.0;        // surface layer depletion [mm]
    double de_final = 0.0;
    double runoff_total = 0.0;

    for (std::size_t d = 0; d < nd; ++d) {
        const double et0 = std::max(et0_mm[d], 0.0);
        const double rain = std::max(rain_mm[d], 0.0);

        // --- Rainfall partition (USDA-SCS CN=65 style) ---
        const double cn = 65.0;
        const double s_mm = 25400.0 / cn - 254.0;
        double runoff = 0.0;
        if (rain > 0.2 * s_mm) {
            runoff = (rain - 0.2 * s_mm) * (rain - 0.2 * s_mm) /
                     (rain + 0.8 * s_mm);
        }
        runoff = std::min(runoff, rain);
        runoff_total += runoff;
        const double infil = rain - runoff;

        // Infiltration first fills the surface layer; excess reaches the root zone.
        const double fill = std::min(infil, de);
        de -= fill;
        const double excess = infil - fill;
        // Recharge limited by remaining storage; surplus above field capacity
        // becomes deep percolation (tracked later).
        const double recharge = std::min(excess, dr);
        dr -= recharge;
        const double surplus = excess - recharge;

        // --- Crop coefficients ---
        const double kcb = kcb_for_day(static_cast<int>(d), p);
        // Stress coefficient Ks (FAO-56 eq. 84).
        double ks = 1.0;
        if (dr > raw_mm && taw_mm > 0.0) {
            ks = std::max(0.0, (taw_mm - dr) / (taw_mm - raw_mm));
        }
        // Evaporation coefficient Ke (FAO-56 eq. 71-76).
        double kr = 1.0;
        if (de > p.rew_mm) {
            kr = (p.tew_mm - de) / (p.tew_mm - p.rew_mm);
            kr = std::clamp(kr, 0.0, 1.0);
        }
        double ke = kr * (kc_max - kcb);
        ke = std::clamp(ke, 0.0, few * kc_max);
        // Evaporation is limited by the water remaining in the surface layer
        // (TEW): this keeps the water balance exact.
        const double de_capacity = std::max(0.0, p.tew_mm - de);
        const double ke_avail = et0 > 0.0 ? de_capacity / et0 : 0.0;
        const double ke_actual = std::min(ke, ke_avail);

        const double kc_eff = kcb * ks + ke_actual;
        const double etc_actual = std::max(0.0, kc_eff * et0);

        // --- Depletion updates (FAO-56 dual-Kc water balance) ---
        dr += kcb * ks * et0;   // root zone uptake
        de += ke_actual * et0;  // surface evaporation (<= remaining TEW)
        de = std::min(de, p.tew_mm);

        // Deep percolation: recharge surplus + overflow beyond field capacity.
        double dp = surplus;
        if (dr > taw_mm) {
            dp += dr - taw_mm;
            dr = taw_mm;
        }

        // --- Irrigation ---
        double irr = 0.0;
        if (auto_irrigate && dr > raw_mm) {
            irr = dr;  // refill to field capacity
            dr = 0.0;
        }

        de_final = de;
        r.etc_mm[d] = etc_actual;
        r.kc_effective[d] = kc_eff;
        r.stress_factor[d] = ks;
        r.depletion_mm[d] = dr;
        r.deep_percolation_mm[d] = dp;
        r.irrigation_mm[d] = irr;
    }

    for (std::size_t d = 0; d < nd; ++d) {
        r.total_etc_mm += r.etc_mm[d];
        r.total_rain_mm += std::max(rain_mm[d], 0.0);
        r.total_irrigation_mm += r.irrigation_mm[d];
        r.total_dp_mm += r.deep_percolation_mm[d];
    }
    // Closure incl. storage change (depletion = negative storage):
    // P + I = ETc + DP + runoff - Delta(dr + de).
    const double storage_change = r.depletion_mm.back() + de_final;
    r.water_balance_error_mm =
        (r.total_rain_mm + r.total_irrigation_mm) -
        (r.total_etc_mm + r.total_dp_mm + runoff_total) + storage_change;
    return r;
}

std::vector<CropWaterResult> simulate_crop_water_batch(
    const std::vector<std::vector<double>>& et0_mm_list,
    const std::vector<std::vector<double>>& rain_mm_list,
    const std::vector<bool>& auto_irrigate_list,
    const std::vector<CropWaterParams>& params_list) {

    if (et0_mm_list.size() != rain_mm_list.size() ||
        et0_mm_list.size() != auto_irrigate_list.size() ||
        et0_mm_list.size() != params_list.size()) {
        throw std::invalid_argument("Input list sizes for batch simulation must match.");
    }

    const size_t num_simulations = et0_mm_list.size();
    std::vector<CropWaterResult> results(num_simulations);

    #pragma omp parallel for
    for (size_t i = 0; i < num_simulations; ++i) {
        // Each simulation is independent and can run in parallel
        results[i] = simulate_crop_water(et0_mm_list[i], rain_mm_list[i],
                                        auto_irrigate_list[i], params_list[i]);
    }
    return results;
}

}  // namespace hydroma
