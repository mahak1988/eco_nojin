// HyDroMa C++ core — RUSLE implementation.
#include "hydroma/erosion.hpp"

#include <cmath>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

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

// --- Added by Implementation Plan ---
namespace {
    void check_same_size_erosion(const std::vector<double>& a, const std::vector<double>& b,
                                 const char* what) {
        if (a.size() != b.size()) {
            throw std::invalid_argument(std::string(what) + ": arrays must have equal size");
        }
    }
    void check_same_size_erosion_str(const std::vector<std::string>& a, const std::vector<std::string>& b,
                                 const char* what) {
        if (a.size() != b.size()) {
            throw std::invalid_argument(std::string(what) + ": arrays must have equal size");
        }
    }
}

std::vector<double> rusle_annual_soil_loss_array(const std::vector<double>& R,
                                                 const std::vector<double>& K,
                                                 const std::vector<double>& LS,
                                                 const std::vector<double>& C,
                                                 const std::vector<double>& P) {
    check_same_size_erosion(R, K, "rusle_annual_soil_loss_array");
    check_same_size_erosion(R, LS, "rusle_annual_soil_loss_array");
    check_same_size_erosion(R, C, "rusle_annual_soil_loss_array");
    check_same_size_erosion(R, P, "rusle_annual_soil_loss_array");

    std::vector<double> out(R.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < R.size(); ++i) {
        // Directly implement the calculation to avoid scalar function overhead
        if (R[i] < 0.0 || K[i] < 0.0 || LS[i] < 0.0 || C[i] < 0.0 || P[i] < 0.0) {
            throw std::invalid_argument("RUSLE factors must be non-negative");
        }
        out[i] = R[i] * K[i] * LS[i] * C[i] * P[i];
    }
    return out;
}

std::vector<double> ls_factor_array(const std::vector<double>& slope_length_m,
                                   const std::vector<double>& slope_percent) {
    check_same_size_erosion(slope_length_m, slope_percent, "ls_factor_array");

    std::vector<double> out(slope_length_m.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < slope_length_m.size(); ++i) {
        const double slope_len = slope_length_m[i];
        const double slope_pct = slope_percent[i];

        if (slope_len <= 0.0) { out[i] = 0.0; continue; } // Skip invalid, return 0.0
        if (slope_pct < 0.0) { out[i] = 0.0; continue; } // Skip invalid, return 0.0

        const double slope_fraction = slope_pct / 100.0;
        const double theta = std::atan(slope_fraction);

        double S;
        if (slope_fraction < 0.09) {
            S = 10.8 * std::sin(theta) + 0.03;
        } else {
            S = 16.8 * std::sin(theta) - 0.50;
        }
        if (S < 0.0) S = 0.0;

        const double sin_t = std::sin(theta);
        const double beta = (sin_t / 0.0896) / (3.0 * std::pow(sin_t, 0.8) + 0.56);
        const double m = beta / (1.0 + beta);

        const double L = std::pow(slope_len / 22.13, m);
        out[i] = L * S;
    }
    return out;
}

std::vector<double> estimate_rainfall_erosivity_array(const std::vector<double>& annual_rainfall_mm) {
    std::vector<double> out(annual_rainfall_mm.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < annual_rainfall_mm.size(); ++i) {
        const double rain = annual_rainfall_mm[i];
        if (rain < 0.0) {
             out[i] = 0.0; // Or throw, depending on desired behavior for invalid input
             continue;
        }
        if (rain < 850.0) {
            out[i] = 0.04830 * std::pow(rain, 1.61);
        } else {
            out[i] = 587.8 - 1.219 * rain + 0.004105 * rain * rain;
        }
    }
    return out;
}

std::vector<double> soil_erodibility_k_array(const std::vector<std::string>& textures) {
    std::vector<double> out(textures.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < textures.size(); ++i) {
        const std::string& tex = textures[i];
        if (tex == "sand") out[i] = 0.05;
        else if (tex == "loamy_sand") out[i] = 0.12;
        else if (tex == "sandy_loam") out[i] = 0.24;
        else if (tex == "loam") out[i] = 0.38;
        else if (tex == "silt_loam") out[i] = 0.45;
        else if (tex == "clay_loam") out[i] = 0.32;
        else if (tex == "clay") out[i] = 0.25;
        else {
             out[i] = 0.0; // Or throw, depending on desired behavior for unknown texture
             continue;
        }
    }
    return out;
}

// --- End of Added Section ---

}  // namespace hydroma
