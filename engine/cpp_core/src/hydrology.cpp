// HyDroMa C++ core — Hydrology kernels implementation.
#include "hydroma/hydrology.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
// Add OpenMP header for potential parallel loops in other functions
#include <omp.h>

namespace hydroma {

namespace {

double safe_positive(double value, double fallback) {
    return (std::isfinite(value) && value > 0.0) ? value : fallback;
}

}  // namespace

std::vector<double> muskingum_cunge_route(const std::vector<double>& inflow,
                                          double K, double x, double dt) {
    if (inflow.empty()) return {};
    if (dt <= 0.0) throw std::invalid_argument("dt must be positive");
    if (x < 0.0 || x > 0.5) throw std::invalid_argument("x must be in [0, 0.5]");

    const double denom = K - K * x + 0.5 * dt;
    if (denom <= 0.0) {
        // K too small: pass through unchanged (matches Python fallback).
        return inflow;
    }

    const double C0 = (-K * x + 0.5 * dt) / denom;
    const double C1 = (K * x + 0.5 * dt) / denom;
    const double C2 = (K - K * x - 0.5 * dt) / denom;

    std::vector<double> outflow(inflow.size(), 0.0);
    outflow[0] = inflow[0];

    // The core loop is inherently serial, but we can hint at vectorization for the math inside.
    // Modern compilers often auto-vectorize simple arithmetic like this.
    // We use restrict-like semantics (though not standard C++) by assuming no overlap.
    const double* restrict inflow_ptr = inflow.data();
    double* restrict outflow_ptr = outflow.data();
    const std::size_t n = inflow.size();

    for (std::size_t t = 1; t < n; ++t) {
        const double temp_val = C0 * inflow_ptr[t] + C1 * inflow_ptr[t - 1] + C2 * outflow_ptr[t - 1];
        outflow_ptr[t] = temp_val < 0.0 ? 0.0 : temp_val;
    }
    return outflow;
}

WaveParameters compute_wave_parameters(double channel_length, double bed_slope,
                                       double manning_n, double channel_width,
                                       double peak_flow) {
    const double q = channel_width > 0.0 ? peak_flow / channel_width : 0.0;
    double h_normal = 0.1;
    if (q > 0.0 && bed_slope > 0.0 && manning_n > 0.0) {
        h_normal = std::pow(q * manning_n / std::sqrt(bed_slope), 0.6);
    }
    const double v = h_normal > 0.0 ? q / h_normal : 0.1;
    const double celerity = (5.0 / 3.0) * v;
    const double K = celerity > 0.0 ? channel_length / celerity : 100.0;
    return WaveParameters{K, 0.2, celerity, h_normal, v, K};
}

RoutingResult route_flood_wave(const std::vector<double>& inflow_hydrograph,
                               double channel_length, int /*n_cells*/,
                               double manning_n, double bed_slope, double dt,
                               double channel_width) {
    if (inflow_hydrograph.empty()) {
        return RoutingResult{};
    }
    const double peak_in =
        *std::max_element(inflow_hydrograph.begin(), inflow_hydrograph.end());

    const WaveParameters params = compute_wave_parameters(
        channel_length, bed_slope, manning_n, channel_width, peak_in);

    const std::vector<double> outflow =
        muskingum_cunge_route(inflow_hydrograph, params.K, params.x, dt);

    const double peak_out =
        *std::max_element(outflow.begin(), outflow.end());
    const std::size_t peak_in_idx =
        std::distance(inflow_hydrograph.begin(),
                      std::max_element(inflow_hydrograph.begin(),
                                       inflow_hydrograph.end()));
    const std::size_t peak_out_idx =
        std::distance(outflow.begin(),
                      std::max_element(outflow.begin(), outflow.end()));

    double volume_in = 0.0, volume_out = 0.0;
    for (std::size_t i = 0; i < inflow_hydrograph.size(); ++i) {
        volume_in += inflow_hydrograph[i] * dt;
        volume_out += outflow[i] * dt;
    }

    RoutingResult r;
    r.outflow = outflow;
    r.peak_inflow = peak_in;
    r.peak_outflow = peak_out;
    r.peak_attenuation = peak_in - peak_out;
    r.attenuation_ratio = peak_in > 0.0 ? peak_out / peak_in : 0.0;
    r.time_lag = static_cast<double>(static_cast<long long>(peak_out_idx) -
                                     static_cast<long long>(peak_in_idx)) * dt;
    r.time_to_peak_out = static_cast<double>(peak_out_idx) * dt;
    r.travel_time = params.travel_time;
    r.celerity = params.celerity;
    r.normal_depth = params.normal_depth;
    r.volume_in = volume_in;
    r.volume_out = volume_out;
    r.mass_balance = volume_in > 0.0 ? volume_out / volume_in : 0.0;
    r.converged = true; // Always true for this method
    return r;
}

RoutingResult route_multi_reach(const std::vector<double>& inflow_hydrograph,
                                double channel_length, int n_reaches,
                                double manning_n, double bed_slope, double dt,
                                double channel_width) {
    if (inflow_hydrograph.empty() || n_reaches < 1) {
        return RoutingResult{};
    }

    std::vector<double> current_inflow = inflow_hydrograph;

    for (int r = 0; r < n_reaches; ++r) {
        // Route through one reach
        RoutingResult step_result = route_flood_wave(current_inflow, channel_length, 1,
                                                    manning_n, bed_slope, dt, channel_width);
        // Output of this reach becomes input for the next
        current_inflow = step_result.outflow;
    }

    // Return the result of the last reach
    RoutingResult final_result = route_flood_wave(current_inflow, channel_length, 1,
                                                 manning_n, bed_slope, dt, channel_width);
    // Note: Some statistics might need aggregation over all reaches.
    // This simplified version returns stats for the final reach.
    return final_result;
}

}  // namespace hydroma
