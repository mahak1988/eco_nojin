// HyDroMa C++ core — Sampling engines: Monte Carlo and Latin Hypercube.
//
// Uncertainty quantification for scenario ensembles. Latin Hypercube
// Sampling (LHS) stratifies each dimension, reducing estimator variance
// versus plain Monte Carlo for the same sample count (a measurable
// innovation for the scenario engine).
//
// References:
//  - McKay, M.D., Beckman, R.J., Conover, W.J. (1979). "A comparison of
//    three methods for selecting values of input variables in the
//    analysis of output from a computer code." Technometrics 21:239-245.
//  - Iman, R.L. (2008). "Latin hypercube sampling." Encyclopedia of
//    Quantitative Risk Analysis and Assessment. Wiley.
#pragma once

#include <cstddef>
#include <functional>
#include <vector>

namespace hydroma {

/// Draw n standard-LHS samples in `dims` dimensions over [0,1]^dims.
/// Each dimension is stratified into n equal strata (one sample each).
/// \param n     number of samples
/// \param dims  number of dimensions
/// \param seed  RNG seed (deterministic)
std::vector<std::vector<double>> latin_hypercube(std::size_t n,
                                                 std::size_t dims,
                                                 unsigned long long seed);

/// Plain Monte Carlo samples (independent uniform draws).
std::vector<std::vector<double>> monte_carlo_uniform(std::size_t n,
                                                     std::size_t dims,
                                                     unsigned long long seed);

/// Map unit-cube samples to [lo, hi] bounds (independent per dimension).
std::vector<std::vector<double>> scale_samples(
    const std::vector<std::vector<double>>& unit_samples,
    const std::vector<double>& lo, const std::vector<double>& hi);

/// Estimate the mean of f over uniform inputs with standard MC.
/// \return {estimate, standard_error}
std::pair<double, double> estimate_mean_mc(
    const std::function<double(const std::vector<double>&)>& f,
    std::size_t dims, std::size_t n, unsigned long long seed);

/// Estimate the mean of f over uniform inputs with LHS.
std::pair<double, double> estimate_mean_lhs(
    const std::function<double(const std::vector<double>&)>& f,
    std::size_t dims, std::size_t n, unsigned long long seed);

/// Simple water-productivity yield model (mirrors the Python crop
/// scenario engine): yield [kg/ha] from available water [mm] and
/// mean temperature [degC] for a given crop.
double simplified_yield(double available_water_mm, double mean_temp_c,
                        const std::string& crop);

/// Yield ensemble statistics {mean, std, p5, p50, p95} over water/temp
/// uncertainty using LHS.
struct YieldStats {
    double mean_kg_ha{0.0};
    double std_kg_ha{0.0};
    double p5_kg_ha{0.0};
    double p50_kg_ha{0.0};
    double p95_kg_ha{0.0};
    double failure_probability{0.0}; ///< P(yield < 500 kg/ha)
    std::size_t n_samples{0};
};

YieldStats yield_ensemble_lhs(double mean_water_mm, double water_std_mm,
                              double mean_temp_c, double temp_std_c,
                              const std::string& crop, std::size_t n_samples,
                              unsigned long long seed);

}  // namespace hydroma
