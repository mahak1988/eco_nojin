// HyDroMa C++ core — Distributed erosion and sediment delivery.
#include "hydroma/sediment.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include "hydroma/erosion.hpp"
// Add OpenMP header
#include <omp.h>

namespace hydroma {

std::vector<double> rusle_grid(const std::vector<RusleCell>& cells,
                               double r_factor) {
    if (r_factor < 0.0) throw std::invalid_argument("R factor must be non-negative");
    std::vector<double> out(cells.size());

    #pragma omp parallel for
    for (std::size_t i = 0; i < cells.size(); ++i) {
        const RusleCell& c = cells[i];
        // Assuming ls_factor is thread-safe or inlined safely
        const double ls = ls_factor(c.slope_length_m, c.slope_percent);
        out[i] = r_factor * c.k * ls * c.c * c.p;
    }
    return out;
}

// ... rest of the functions remain the same ...

double rusle_grid_total(const std::vector<RusleCell>& cells, double r_factor,
                        double cell_area_ha) {
    const auto per_ha = rusle_grid(cells, r_factor); // This now calls the parallel version
    double total = 0.0;
    for (double a : per_ha) total += a * cell_area_ha;
    return total;
}

double sediment_delivery_ratio(double watershed_area_km2,
                               double coefficient, double exponent) {
    if (watershed_area_km2 <= 0.0) throw std::invalid_argument("area must be positive");
    // SDR = a * A^b  (Boyce 1975 style power law; calibrate locally).
    return coefficient * std::pow(watershed_area_km2, exponent);
}

double sediment_yield(const std::vector<RusleCell>& cells, double r_factor,
                      double cell_area_ha, double watershed_area_km2) {
    const double erosion = rusle_grid_total(cells, r_factor, cell_area_ha);
    const double sdr = sediment_delivery_ratio(watershed_area_km2);
    return erosion * sdr;
}

double trap_efficiency_brune(double capacity_inflow_ratio, double k) {
    if (capacity_inflow_ratio < 0.0) {
        throw std::invalid_argument("capacity/inflow ratio must be non-negative");
    }
    // Explicit empirical fit to the Brune (1953) median curve:
    //   TE = C/I / (C/I + k), k ~ 0.15  (passes near C/I=1 -> TE~0.87).
    if (capacity_inflow_ratio <= 0.0) return 0.0;
    return capacity_inflow_ratio / (capacity_inflow_ratio + k);
}

double sediment_trapped(const std::vector<RusleCell>& cells, double r_factor,
                        double cell_area_ha, double watershed_area_km2,
                        double capacity_inflow_ratio) {
    return sediment_yield(cells, r_factor, cell_area_ha, watershed_area_km2) *
           trap_efficiency_brune(capacity_inflow_ratio);
}

}  // namespace hydroma
