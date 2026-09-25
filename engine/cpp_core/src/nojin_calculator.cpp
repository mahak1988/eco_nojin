#include "nojin_calculator.h"
#include <cmath>
#include <vector>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <iostream>

namespace hydroma {

double calculate_biofertilizer_efficacy(double soil_nitrogen_ppm, double soil_phosphorus_ppm, double soil_potassium_ppm, double ph, double organic_matter_pct, const std::string& biofert_type) {
    if (biofert_type.empty()) {
        throw std::invalid_argument("biofert_type must not be empty");
    }
    if (ph < 0.0 || ph > 14.0) {
        throw std::invalid_argument("pH must be in [0, 14]");
    }
    if (organic_matter_pct < 0.0 || organic_matter_pct > 100.0) {
        throw std::invalid_argument("organic_matter_pct must be in [0, 100]");
    }

    double efficacy = 0.0;

    if (biofert_type == "nitrogen_fixer") {
        efficacy = std::max(0.0, (10.0 - soil_nitrogen_ppm) / 10.0) *
                   std::max(0.0, (1.0 - std::abs(ph - 7.0) / 2.0)) *
                   (0.5 + organic_matter_pct / 10.0);
    } else if (biofert_type == "phosphate_solubilizer") {
        efficacy = std::max(0.0, (20.0 - soil_phosphorus_ppm) / 20.0) *
                   std::max(0.0, (ph - 6.0) / 2.0);
    } else if (biofert_type == "potash_mobilizer") {
        efficacy = std::max(0.0, (100.0 - soil_potassium_ppm) / 100.0);
    } else if (biofert_type == "mycorrhiza") {
        efficacy = std::max(0.0, (20.0 - soil_phosphorus_ppm) / 20.0) *
                   std::max(0.0, (2.0 - organic_matter_pct) / 2.0);
    } else if (biofert_type == "pgpr") {
        double stress_factor = std::abs(ph - 7.0) / 7.0 +
                               (1.0 - std::min({soil_nitrogen_ppm / 10.0,
                                                soil_phosphorus_ppm / 20.0,
                                                soil_potassium_ppm / 100.0}));
        efficacy = std::min(1.0, stress_factor);
    } else {
        throw std::invalid_argument("Unknown biofert_type: " + biofert_type);
    }

    return std::clamp(efficacy, 0.0, 1.0);
}

double predict_yield_response(const std::vector<double>& baseline_yield,
                              const std::vector<double>& biofert_efficacy,
                              double baseline_fertilizer_rate,
                              double biofert_dosage) {
    if (baseline_yield.empty() || biofert_efficacy.empty()) {
        throw std::invalid_argument("Input vectors must not be empty");
    }
    if (baseline_yield.size() != biofert_efficacy.size()) {
        throw std::invalid_argument("baseline_yield and biofert_efficacy must have equal size");
    }
    if (baseline_fertilizer_rate < 0.0 || biofert_dosage < 0.0) {
        throw std::invalid_argument("Fertilizer rate and dosage must be non-negative");
    }

    const double avg_baseline_yield =
        std::accumulate(baseline_yield.begin(), baseline_yield.end(), 0.0) /
        baseline_yield.size();
    const double avg_efficacy =
        std::accumulate(biofert_efficacy.begin(), biofert_efficacy.end(), 0.0) /
        biofert_efficacy.size();

    const double potential_increase =
        avg_baseline_yield * 0.15 * avg_efficacy * (biofert_dosage / 10.0);

    return avg_baseline_yield + potential_increase;
}

} // namespace hydroma