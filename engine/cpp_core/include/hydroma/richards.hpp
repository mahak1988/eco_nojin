// HyDroMa C++ core — 1D vertical Richards equation solver (mixed form).
//
// Solves the mixed-form Richards equation for unsaturated/saturated flow:
//     C(h) dh/dt = d/dz [ K(h) (dh/dz + 1) ]
// with z positive upward, using cell-centered finite volumes,
// backward (implicit) Euler in time and the modified Picard iteration
// of Celia et al. (1990) for mass-conservative solution.
//
// References:
//  - Richards, L.A. (1931). "Capillary conduction of liquids through
//    porous mediums." Physics 1:318-333.
//  - Celia, M.A., Bouloutas, E.T., Zarba, R.L. (1990). "A general
//    mass-conservative numerical solution for the unsaturated flow
//    equation." Water Resour. Res. 26(7):1483-1496.
//  - van Genuchten, M.Th. (1980). Soil Sci. Soc. Am. J. 44:892-898.
#pragma once

#include <string>
#include <vector>

namespace hydroma {

/// Boundary condition at the top of the column.
enum class TopBoundary {
    Flux,       ///< prescribed infiltration/evaporation flux [cm/day]
    Head,       ///< prescribed pressure head [cm] (0 = ponded saturated)
};

/// Boundary condition at the bottom of the column.
enum class BottomBoundary {
    FreeDrainage,  ///< unit-gradient outflow (gravity drainage)
    Head,          ///< prescribed pressure head [cm]
};

struct RichardsOptions {
    int n_cells{100};             ///< number of cells
    double column_depth_cm{200.0};///< total depth [cm]
    double dt_days{0.05};         ///< time step [days]
    int n_steps{200};             ///< number of time steps
    double tolerance_cm{1e-4};    ///< Picard iteration tolerance [cm]
    int max_iter{50};             ///< max Picard iterations per step
    TopBoundary top{TopBoundary::Flux};
    double top_value_cm_day{1.0}; ///< flux [cm/day] or head [cm]
    BottomBoundary bottom{BottomBoundary::FreeDrainage};
    double bottom_head_cm{-100.0};///< used when bottom == Head
};

struct RichardsResult {
    std::vector<std::vector<double>> head_cm;    ///< pressure head per step per cell
    std::vector<std::vector<double>> theta;      ///< water content per step per cell
    std::vector<double> storage_cm;              ///< total column storage per step [cm]
    std::vector<double> cumulative_top_flux_cm;  ///< [cm]
    std::vector<double> cumulative_bottom_flux_cm;///< [cm]
    bool converged{true};
    int iterations_last_step{0};
};

/// Run the 1D vertical Richards simulation.
/// \param texture     soil texture key (see soil.hpp)
/// \param initial_head_cm  initial pressure head profile (length n_cells or empty => hydrostatic -z)
/// \param opts        simulation options
RichardsResult simulate_richards(const std::string& texture,
                                 const std::vector<double>& initial_head_cm,
                                 const RichardsOptions& opts);

/// Specific moisture capacity C(h) = d(theta)/dh for van Genuchten soil.
double specific_moisture_capacity(double h_cm, const std::string& texture);

}  // namespace hydroma
