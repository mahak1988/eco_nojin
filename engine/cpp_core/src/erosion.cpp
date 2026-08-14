// HyDroMa C++ core — RUSLE implementation.
#include "hydroma/erosion.hpp"

#include <cmath>
#include <stdexcept>

namespace hydroma {

double rusle_annual_soil_loss(double R, double K, double LS, double C, double P) {
    if (R < 0.0 || K < 0.0 || LS < 0.0 || C < 0.0 || P < 0.0) {
        throw std::invalid_argument("RUSLE factors must be non-negative");
    }
    return R * K * LS * C * P;
}

double ls_factor(double slope_length_m, double slope_percent) {
    if (slope_length_m <= 0.0) throw std::invalid_argument("slope length must be positive");
    if (slope_percent < 0.0) throw std::invalid_argument("slope cannot be negative");

    const double slope_fraction = slope_percent / 100.0;
    const double theta = std::atan(slope_fraction);

    // Slope steepness factor S (McCool et al. 1987).
    double S;
    if (slope_fraction < 0.09) {
        S = 10.8 * std::sin(theta) + 0.03;
    } else {
        S = 16.8 * std::sin(theta) - 0.50;
    }
    if (S < 0.0) S = 0.0;

    // Slope length exponent m (RUSLE handbook).
    const double sin_t = std::sin(theta);
    const double beta =
        (sin_t / 0.0896) / (3.0 * std::pow(sin_t, 0.8) + 0.56);
    const double m = beta / (1.0 + beta);

    const double L = std::pow(slope_length_m / 22.13, m);
    return L * S;
}

double estimate_rainfall_erosivity(double annual_rainfall_mm) {
    if (annual_rainfall_mm < 0.0) {
        throw std::invalid_argument("annual rainfall cannot be negative");
    }
    // Renard & Freimund (1994) piecewise relation.
    if (annual_rainfall_mm < 850.0) {
        return 0.04830 * std::pow(annual_rainfall_mm, 1.61);
    }
    return 587.8 - 1.219 * annual_rainfall_mm +
           0.004105 * annual_rainfall_mm * annual_rainfall_mm;
}

double soil_erodibility_k(const std::string& texture) {
    // Typical K values (USDA NRCS/RUSLE tables), t ha h / (ha MJ mm).
    if (texture == "sand") return 0.05;
    if (texture == "loamy_sand") return 0.12;
    if (texture == "sandy_loam") return 0.24;
    if (texture == "loam") return 0.38;
    if (texture == "silt_loam") return 0.45;
    if (texture == "clay_loam") return 0.32;
    if (texture == "clay") return 0.25;
    throw std::invalid_argument("Unknown soil texture: " + texture);
}

}  // namespace hydroma
