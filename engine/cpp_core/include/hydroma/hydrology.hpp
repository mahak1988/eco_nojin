// HyDroMa C++ core — Hydrology kernels
// Muskingum-Cunge flood routing and kinematic wave parameters.
//
// This is the same method used in HEC-HMS, SWMM, and MIKE flood models.
// References:
//  - Cunge, J.A. (1969). "On the subject of a flood propagation computation method"
//  - Chow, V.T., Maidment, D.R., Mays, L.W. (1988). "Applied Hydrology"
//  - USACE HEC-HMS Technical Reference Manual
//
// The Python (Numba) counterpart lives in engine/hydroma/cpp_bridge/hydrology_fast.py.
// Results are numerically identical by design.
#pragma once

#include <cstddef>
#include <vector>

namespace hydroma {

/// Kinematic wave parameters derived from channel geometry (Manning equation).
struct WaveParameters {
    double K;            ///< storage time constant / reach travel time [s]
    double x;            ///< Muskingum weighting factor in [0, 0.5]
    double celerity;     ///< kinematic wave celerity [m/s]
    double normal_depth; ///< normal depth from Manning [m]
    double velocity;     ///< mean flow velocity [m/s]
    double travel_time;  ///< reach travel time [s]
};

/// Full single-reach routing statistics (mirrors Python route_flood_wave).
struct RoutingResult {
    std::vector<double> outflow;  ///< routed outflow hydrograph [m3/s]
    double peak_inflow{0.0};      ///< peak of input hydrograph [m3/s]
    double peak_outflow{0.0};     ///< peak of output hydrograph [m3/s]
    double peak_attenuation{0.0}; ///< peak_inflow - peak_outflow [m3/s]
    double attenuation_ratio{0.0};///< peak_outflow / peak_inflow
    double time_lag{0.0};         ///< time between input and output peaks [s]
    double time_to_peak_out{0.0}; ///< time to output peak [s]
    double travel_time{0.0};      ///< [s]
    double celerity{0.0};         ///< [m/s]
    double normal_depth{0.0};     ///< [m]
    double volume_in{0.0};        ///< [m3]
    double volume_out{0.0};       ///< [m3]
    double mass_balance{0.0};     ///< volume_out / volume_in (conservation check)
};

/// Route an inflow hydrograph with the classic Muskingum-Cunge method.
/// O(t+1) = C0*I(t+1) + C1*I(t) + C2*O(t). Unconditionally stable, O(n) per step.
/// \param inflow  inflow hydrograph [m3/s]
/// \param K       storage time constant [s]
/// \param x       weighting factor [0, 0.5]
/// \param dt      time step [s]
/// \return        routed outflow hydrograph [m3/s]
std::vector<double> muskingum_cunge_route(const std::vector<double>& inflow,
                                          double K, double x, double dt);

/// Compute wave celerity, travel time (K) and normal depth from geometry.
/// Uses the kinematic wave approximation c = (5/3)*v for wide channels.
WaveParameters compute_wave_parameters(double channel_length, double bed_slope,
                                       double manning_n, double channel_width,
                                       double peak_flow);

/// Route a flood wave through a single reach and return routing statistics.
RoutingResult route_flood_wave(const std::vector<double>& inflow_hydrograph,
                               double channel_length, int n_cells,
                               double manning_n, double bed_slope, double dt,
                               double channel_width);

/// Route through multiple reaches; outflow of reach i feeds reach i+1.
RoutingResult route_multi_reach(const std::vector<double>& inflow_hydrograph,
                                double channel_length, int n_reaches,
                                double manning_n, double bed_slope, double dt,
                                double channel_width);

}  // namespace hydroma
