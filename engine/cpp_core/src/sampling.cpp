// HyDroMa C++ core — Sampling engines (MC and LHS).
#include "hydroma/sampling.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>
#include <random>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

namespace hydroma {

std::vector<std::vector<double>> latin_hypercube(std::size_t n,
                                                 std::size_t dims,
                                                 unsigned long long seed) {
    if (n == 0 || dims == 0) return {};
    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> unit(0.0, 1.0);

    std::vector<std::vector<double>> samples(n, std::vector<double>(dims));
    for (std::size_t j = 0; j < dims; ++j) {
        // Stratify dimension j: one sample per stratum.
        std::vector<std::size_t> perm(n);
        std::iota(perm.begin(), perm.end(), 0);
        std::shuffle(perm.begin(), perm.end(), rng);
        for (std::size_t i = 0; i < n; ++i) {
            const double stratum = static_cast<double>(perm[i]) / n;
            const double within = unit(rng) / n;
            samples[i][j] = stratum + within;  // in (0,1)
        }
    }
    return samples;
}

std::vector<std::vector<double>> monte_carlo_uniform(std::size_t n,
                                                     std::size_t dims,
                                                     unsigned long long seed) {
    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    std::vector<std::vector<double>> samples(n, std::vector<double>(dims));
    for (std::size_t i = 0; i < n; ++i)
        for (std::size_t j = 0; j < dims; ++j) samples[i][j] = unit(rng);
    return samples;
}

std::vector<std::vector<double>> scale_samples(
    const std::vector<std::vector<double>>& unit_samples,
    const std::vector<double>& lo, const std::vector<double>& hi) {
    if (lo.size() != hi.size()) throw std::invalid_argument("lo/hi size mismatch");
    std::vector<std::vector<double>> out = unit_samples;
    for (auto& s : out) {
        if (s.size() != lo.size()) throw std::invalid_argument("sample dim mismatch");
        for (std::size_t j = 0; j < s.size(); ++j) {
            s[j] = lo[j] + s[j] * (hi[j] - lo[j]);
        }
    }
    return out;
}

std::pair<double, double> estimate_mean_mc(
    const std::function<double(const std::vector<double>&)>& f,
    std::size_t dims, std::size_t n, unsigned long long seed) {
    const auto samples = monte_carlo_uniform(n, dims, seed);
    std::vector<double> vals;
    vals.reserve(n);
    for (const auto& s : samples) vals.push_back(f(s));
    const double mean = std::accumulate(vals.begin(), vals.end(), 0.0) / n;
    double var = 0.0;
    for (double v : vals) var += (v - mean) * (v - mean);
    var /= (n > 1 ? n - 1 : 1);
    return {mean, std::sqrt(var / n)};
}

std::pair<double, double> estimate_mean_lhs(
    const std::function<double(const std::vector<double>&)>& f,
    std::size_t dims, std::size_t n, unsigned long long seed) {
    const auto samples = latin_hypercube(n, dims, seed);
    std::vector<double> vals;
    vals.reserve(n);
    #pragma omp parallel for
    for (std::size_t i = 0; i < n; ++i) {
        // Each thread needs its own RNG instance for parallel safety
        std::mt19937_64 rng(seed + static_cast<unsigned long long>(i));
        vals[i] = f(samples[i]);
    }
    const double mean = std::accumulate(vals.begin(), vals.end(), 0.0) / n;
    double var = 0.0;
    for (double v : vals) var += (v - mean) * (v - mean);
    var /= (n > 1 ? n - 1 : 1);
    return {mean, std::sqrt(var / n)};
}

double simplified_yield(double available_water_mm, double mean_temp_c,
                        const std::string& crop) {
    // Mirrors engine/hydroma/scenarios/crop_scenarios.py (wheat-like default).
    struct Crop { double wp; double kc; int days; double tbase; double topt; double tmax; double ds; };
    Crop c{1.2, 1.1, 180, 0.0, 20.0, 35.0, 0.6};  // wheat
    if (crop == "barley") c = Crop{1.0, 1.0, 150, 0.0, 18.0, 32.0, 0.5};
    else if (crop == "corn") c = Crop{1.8, 1.2, 140, 8.0, 25.0, 38.0, 0.7};
    else if (crop == "millet") c = Crop{0.8, 0.9, 100, 10.0, 28.0, 42.0, 0.2};
    else if (crop == "sorghum") c = Crop{1.0, 1.0, 120, 10.0, 27.0, 40.0, 0.3};
    else if (crop == "chickpea") c = Crop{0.9, 1.0, 120, 5.0, 22.0, 35.0, 0.5};

    double temp_factor;
    if (mean_temp_c < c.tbase) temp_factor = 0.0;
    else if (mean_temp_c <= c.topt) temp_factor = (mean_temp_c - c.tbase) / (c.topt - c.tbase);
    else if (mean_temp_c <= c.tmax) temp_factor = 1.0 - 0.5 * (mean_temp_c - c.topt) / (c.tmax - c.topt);
    else temp_factor = std::max(0.0, 0.5 - (mean_temp_c - c.tmax) / 10.0);

    const double req = c.kc * c.days * 3.0;
    double water_factor = 1.0;
    if (available_water_mm < req) {
        water_factor = 1.0 - c.ds * (1.0 - available_water_mm / req);
        water_factor = std::max(0.0, water_factor);
    }
    const double transpiration = std::min(available_water_mm, req) * 0.6;
    const double potential = c.wp * transpiration;
    const double actual = potential * temp_factor * water_factor;
    return actual * 10.0;  // kg/ha
}

YieldStats yield_ensemble_lhs(double mean_water_mm, double water_std_mm,
                              double mean_temp_c, double temp_std_c,
                              const std::string& crop, std::size_t n_samples,
                              unsigned long long seed) {
    const auto unit = latin_hypercube(n_samples, 2, seed);
    std::vector<double> yields(n_samples);
    
    // Parallelize the loop that evaluates the yield function for each sample.
    #pragma omp parallel for
    for (std::size_t i = 0; i < n_samples; ++i) {
        const auto& s = unit[i];
        // Each thread needs its own RNG instance seeded differently to ensure independence
        // and reproducibility. Using the sample index and base seed is a common approach.
        std::mt19937_64 rng(seed + static_cast<unsigned long long>(i));
        std::normal_distribution<double> nw(mean_water_mm, water_std_mm);
        std::normal_distribution<double> nt(mean_temp_c, temp_std_c);
        const double water = std::max(50.0, nw(rng));
        const double temp = nt(rng);
        yields[i] = simplified_yield(water, temp, crop);
    }

    // Sequential part: sorting and statistics calculation
    std::sort(yields.begin(), yields.end());
    const double mean = std::accumulate(yields.begin(), yields.end(), 0.0) / n_samples;
    double var = 0.0;
    for (double v : yields) var += (v - mean) * (v - mean);
    var /= n_samples > 1 ? n_samples - 1 : 1;
    auto pct = [&](double q) {
        const std::size_t idx = static_cast<std::size_t>(q * (n_samples - 1));
        return yields[idx];
    };
    YieldStats st;
    st.mean_kg_ha = mean;
    st.std_kg_ha = std::sqrt(var);
    st.p5_kg_ha = pct(0.05);
    st.p50_kg_ha = pct(0.50);
    st.p95_kg_ha = pct(0.95);
    st.failure_probability = static_cast<double>(
        std::count_if(yields.begin(), yields.end(), [](double v) { return v < 500.0; })) /
        n_samples;
    st.n_samples = n_samples;
    return st;
}

}  // namespace hydroma
