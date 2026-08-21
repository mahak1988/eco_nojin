// HyDroMa C++ core — 1D Saint-Venant (shallow water) solver.
//
// Solves the 1D Saint-Venant equations for open-channel flow:
//     dA/dt + dQ/dx = 0
//     dQ/dt + d(Q^2/A)/dx + g A dh/dx = g A (S0 - Sf)
// with rectangular cross-section (A = B h), explicit first-order
// finite volumes with the Rusanov (local Lax-Friedrichs) flux and
// Manning friction. Intended for flash-flood routing where the
// kinematic/diffusion approximations are insufficient.
//
// References:
//  - de Saint-Venant, A.J.C.B. (1871). "Theorie du mouvement non
//    permanent des eaux." C.R. Acad. Sci. Paris 73.
//  - Toro, E.F. (2001). "Shock-Capturing Methods for Free-Surface
//    Shallow Flows." Wiley.
//  - Chow, V.T. (1959). "Open-Channel Hydraulics." McGraw-Hill.
#pragma once

#include <vector>

namespace hydroma {

struct SaintVenantOptions {
    double length_m{1000.0};   ///< channel length [m]
    int n_cells{200};          ///< number of cells
    double width_m{5.0};       ///< rectangular width [m]
    double bed_slope{0.002};   ///< S0 [m/m]
    double manning_n{0.030};   ///< Manning roughness
    double t_end_s{600.0};     ///< simulation horizon [s]
    double cfl{0.5};           ///< CFL number
    double dry_tolerance{1e-4};///< depth below this treated as dry [m]
    int output_every{20};      ///< save every N steps
};

struct SaintVenantResult {
    std::vector<std::vector<double>> depth_m;  ///< per saved step per cell [m]
    std::vector<std::vector<double>> discharge_m3s; ///< [m3/s]
    std::vector<double> time_s;
    double total_volume_initial_m3{0.0};
    double total_volume_final_m3{0.0};
    double mass_balance{};     ///< final/initial volume
    bool stable{true};
};

/// Run the Saint-Venant simulation.
/// \param initial_depth_m  initial depth profile (length n_cells; empty => zero)
/// \param inflow_m3s       upstream inflow [m3/s] (constant during run)
/// \param opts             simulation options
SaintVenantResult simulate_saint_venant(const std::vector<double>& initial_depth_m,
                                        double inflow_m3s,
                                        const SaintVenantOptions& opts);

/// Normal depth from Manning's equation for a wide rectangular channel.
double manning_normal_depth(double discharge_m3s, double width_m,
                            double bed_slope, double manning_n);

}  // namespace hydroma
