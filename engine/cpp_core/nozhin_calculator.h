#ifndef NOJJIN_CALCULATOR_H
#define NOJJIN_CALCULATOR_H

#include <string>
#include <vector>

namespace cpp_core {

/**
 * @brief Calculates the theoretical efficacy of a biofertilizer type based on soil conditions.
 *
 * @param soil_nitrogen_ppm Soil nitrogen content in parts per million.
 * @param soil_phosphorus_ppm Soil phosphorus content in parts per million.
 * @param soil_potassium_ppm Soil potassium content in parts per million.
 * @param ph Soil pH value.
 * @param organic_matter_pct Organic matter percentage in soil.
 * @param biofert_type Type of biofertilizer ('nitrogen_fixer', 'phosphate_solubilizer', etc.).
 * @return A double between 0.0 (no efficacy) and 1.0 (maximum efficacy).
 */
double calculate_biofertilizer_efficacy(double soil_nitrogen_ppm, double soil_phosphorus_ppm, double soil_potassium_ppm, double ph, double organic_matter_pct, const std::string& biofert_type);

/**
 * @brief Predicts potential yield response based on biofertilizer application.
 *
 * @param baseline_yield Vector of historical/predicted baseline yields.
 * @param biofert_efficacy Vector of efficacy values from calculate_biofertilizer_efficacy.
 * @param baseline_fertilizer_rate Rate of conventional fertilizer applied.
 * @param biofert_dosage Dosage of biofertilizer applied.
 * @return Predicted yield after applying biofertilizer.
 */
double predict_yield_response(const std::vector<double>& baseline_yield, const std::vector<double>& biofert_efficacy, double baseline_fertilizer_rate, double biofert_dosage);

} // namespace cpp_core

#endif // NOJJIN_CALCULATOR_H