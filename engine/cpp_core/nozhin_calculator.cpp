#include "nojin_calculator.h"
#include <cmath>
#include <vector>
#include <algorithm>
#include <numeric>
#include <iostream>

namespace cpp_core {

double calculate_biofertilizer_efficacy(double soil_nitrogen_ppm, double soil_phosphorus_ppm, double soil_potassium_ppm, double ph, double organic_matter_pct, const std::string& biofert_type) {
    // This is a placeholder implementation.
    // Real implementation would use complex models.
    double efficacy = 0.0;

    if (biofert_type == "nitrogen_fixer") {
        // Efficacy depends on low N, neutral pH, and OM
        efficacy = std::max(0.0, (10.0 - soil_nitrogen_ppm) / 10.0) * std::max(0.0, (1.0 - std::abs(ph - 7.0) / 2.0)) * (0.5 + organic_matter_pct / 10.0);
    } else if (biofert_type == "phosphate_solubilizer") {
        // Efficacy depends on low P and high pH (to solubilize fixed P)
        efficacy = std::max(0.0, (20.0 - soil_phosphorus_ppm) / 20.0) * std::max(0.0, (ph - 6.0) / 2.0);
    } else if (biofert_type == "potash_mobilizer") {
        // Efficacy depends on low K
        efficacy = std::max(0.0, (100.0 - soil_potassium_ppm) / 100.0);
    } else if (biofert_type == "mycorrhiza") {
        // Efficacy depends on low P, low OM
        efficacy = std::max(0.0, (20.0 - soil_phosphorus_ppm) / 20.0) * std::max(0.0, (2.0 - organic_matter_pct) / 2.0);
    } else if (biofert_type == "pgpr") {
        // General purpose, depends on stress factors (pH away from 7, low nutrients)
        double stress_factor = std::abs(ph - 7.0) / 7.0 + (1.0 - std::min({soil_nitrogen_ppm/10.0, soil_phosphorus_ppm/20.0, soil_potassium_ppm/100.0}));
        efficacy = std::min(1.0, stress_factor);
    }

    return std::min(1.0, efficacy); // Clamp between 0 and 1
}

double predict_yield_response(const std::vector<double>& baseline_yield, const std::vector<double>& biofert_efficacy, double baseline_fertilizer_rate, double biofert_dosage) {
    // This is a placeholder for a more complex yield prediction model.
    // It assumes a multiplicative effect of biofertilizer efficacy on potential yield gain.
    double avg_baseline_yield = std::accumulate(baseline_yield.begin(), baseline_yield.end(), 0.0) / baseline_yield.size();
    double avg_efficacy = std::accumulate(biofert_efficacy.begin(), biofert_efficacy.end(), 0.0) / biofert_efficacy.size();

    // Simple model: yield increase is proportional to efficacy and dosage
    double potential_increase = avg_baseline_yield * 0.15 * avg_efficacy * (biofert_dosage / 10.0); // 15% max gain scaled by efficacy and dosage (assuming 10kg/ha as base)
    double predicted_yield = avg_baseline_yield + potential_increase;

    return predicted_yield;
}

} // namespace cpp_core