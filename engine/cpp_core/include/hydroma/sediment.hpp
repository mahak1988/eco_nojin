// HyDroMa C++ core — Distributed erosion (RUSLE) and sediment delivery.
//
// Cell-based RUSLE (A = R*K*LS*C*P per cell), empirical sediment
// delivery ratio, and check-dam trap efficiency for watershed planning.
//
// References:
//  - Renard, K.G. et al. (1997). USDA Agriculture Handbook No. 703.
//  - Boyce, R.C. (1975). "Sediment routing with sediment-delivery
//    ratios." In: Present and Prospective Technology for Predicting
//    Sediment Yields and Sources. USDA-ARS.
//  - Brune, G.M. (1953). "Trap efficiency of reservoirs." Trans. Am.
//    Geophys. Union 34(3):407-418.
//  - Verstraeten, G., Poesen, J. (2000). "Estimating trap efficiency of
//    small reservoirs and ponds." Earth Surf. Process. Landf. 25.
#pragma once

#include <string>
#include <vector>

namespace hydroma {

struct RusleCell {
    double k{0.32};            ///< erodibility [t ha h / (ha MJ mm)]
    double c{0.5};             ///< cover-management [-]
    double p{1.0};             ///< support practice [-]
    double slope_percent{5.0}; ///< slope [%]
    double slope_length_m{50.0};///< slope length [m]
};

struct SedimentOptions {
    double r_factor{300.0};    ///< rainfall erosivity [MJ mm/(ha h yr)]
    double cell_area_ha{1.0};  ///< cell area [ha]
    double watershed_area_km2{10.0}; ///< contributing area for SDR [km2]
    double sdr_coefficient{0.41};    ///< SDR = a * A^b
    double sdr_exponent{-0.3};
};

/// Grid-based annual soil loss [t/(ha yr)] per cell.
/// \return per-cell A values (same length as cells)
std::vector<double> rusle_grid(const std::vector<RusleCell>& cells,
                               double r_factor);

/// Total annual erosion on the grid [t/yr].
double rusle_grid_total(const std::vector<RusleCell>& cells,
                        double r_factor, double cell_area_ha);

/// Empirical sediment delivery ratio SDR = a * A^b.
double sediment_delivery_ratio(double watershed_area_km2,
                               double coefficient = 0.41,
                               double exponent = -0.3);

/// Sediment yield reaching the outlet [t/yr] = erosion * SDR.
double sediment_yield(const std::vector<RusleCell>& cells, double r_factor,
                      double cell_area_ha, double watershed_area_km2);

/// Check-dam / reservoir trap efficiency.
/// Explicit approximation of the Brune (1953) median curve:
///     TE = (C/I) / (C/I + k),  k ~ 0.15
/// Calibrate k locally; the value is documented as an empirical fit.
/// \param capacity_inflow_ratio  reservoir capacity / mean annual inflow [-]
/// \param k                      fitted coefficient (default 0.15)
/// \return trap efficiency in (0, 1)
double trap_efficiency_brune(double capacity_inflow_ratio, double k = 0.15);

/// Annual sediment trapped by a check dam [t/yr].
double sediment_trapped(const std::vector<RusleCell>& cells, double r_factor,
                        double cell_area_ha, double watershed_area_km2,
                        double capacity_inflow_ratio);

}  // namespace hydroma
