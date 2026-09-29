// HyDroMa C++ core — Soil physics implementation (van Genuchten).
#include "hydroma/soil.hpp"

#include <cmath>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

#include <cstddef>
#include <string>
#include <vector>

namespace hydroma {

namespace {

// Parameters are generated from engine/data/soil_vg_table.csv, which every
// backend shares. The Carsel & Parrish (1988) attribution formerly quoted here
// is withdrawn: see engine/data/SOIL_TABLE_CONFLICTS.md.
struct TextureEntry {
    const char* key;
    SoilTextureParams params;
};

// GENERATED FILE - do not edit by hand.
// Source of truth: engine/data/soil_vg_table.csv
// Regenerate with: python -m engine.data.generate_cpp_table
//
// Units: Ks is cm/hr here because the compiled kernel has always used it;
// the CSV stores cm/day. That conversion is the only difference for six of the
// seven rows this file carried before consolidation.
//
// Provenance: design assumption, unverified. The former Carsel & Parrish (1988)
// attribution is withdrawn because the Ks column is not monotone in texture
// fineness at two rows. Clay and sandy_clay_loam are marked disputed in the CSV.
// See engine/data/SOIL_TABLE_CONFLICTS.md.
constexpr TextureEntry kTextures[] = {
    {"sand",             {0.045, 0.43, 0.145, 2.68, 29.7}},
    {"loamy_sand",       {0.057, 0.41, 0.124, 2.28, 14.59166667}},
    {"sandy_loam",       {0.065, 0.41, 0.075, 1.89, 4.420833333}},
    {"loam",             {0.078, 0.43, 0.036, 1.56, 1.041666667}},
    {"silt_loam",        {0.067, 0.45, 0.02, 1.41, 0.45}},
    {"silt",             {0.034, 0.46, 0.016, 1.37, 0.25}},
    {"sandy_clay_loam",  {0.1, 0.39, 0.059, 1.48, 1.308333333}},
    {"clay_loam",        {0.095, 0.41, 0.019, 1.31, 0.2583333333}},
    {"silty_clay_loam",  {0.089, 0.43, 0.01, 1.23, 0.1208333333}},
    {"sandy_clay",       {0.1, 0.38, 0.027, 1.23, 0.1208333333}},
    {"silty_clay",       {0.07, 0.36, 0.005, 1.09, 0.08}},
    {"clay",             {0.068, 0.38, 0.008, 1.09, 0.2}},
};

const SoilTextureParams* find_texture(const std::string& texture) {
    for (const auto& entry : kTextures) {
        if (texture == entry.key) return &entry.params;
    }
    return nullptr;
}

}  // namespace

const SoilTextureParams& soil_params(const std::string& texture) {
    const SoilTextureParams* p = find_texture(texture);
    if (p == nullptr) {
        throw std::invalid_argument("Unknown soil texture: " + texture);
    }
    return *p;
}

std::vector<std::string> supported_textures() {
    std::vector<std::string> keys;
    for (const auto& entry : kTextures) keys.emplace_back(entry.key);
    return keys;
}

std::vector<double> soil_water_content(const std::vector<double>& h_matric,
                                       const std::string& soil_texture) {
    const SoilTextureParams& p = soil_params(soil_texture);
    const double m = 1.0 - 1.0 / p.n;
    std::vector<double> result(h_matric.size(), 0.0);

    for (std::size_t i = 0; i < h_matric.size(); ++i) {
        const double h = std::fabs(h_matric[i]);
        if (h < 1e-10) {
            result[i] = p.theta_s;
        } else {
            const double denom =
                std::pow(1.0 + std::pow(p.alpha * h, p.n), m);
            result[i] = p.theta_r + (p.theta_s - p.theta_r) / denom;
        }
    }
    return result;
}

std::vector<double> hydraulic_conductivity(const std::vector<double>& h_matric,
                                           const std::string& soil_texture) {
    const SoilTextureParams& p = soil_params(soil_texture);
    const double m = 1.0 - 1.0 / p.n;
    std::vector<double> result(h_matric.size(), 0.0);

    // Parallelize the loop using OpenMP
    #pragma omp parallel for
    for (std::size_t i = 0; i < h_matric.size(); ++i) {
        const double h = std::fabs(h_matric[i]);
        if (h < 1e-10) {
            result[i] = p.Ks;
        } else {
            const double alpha_h = p.alpha * h; // Pre-compute
            const double alpha_h_n = std::pow(alpha_h, p.n); // pow inside loop, but for a single item
            const double denom = std::pow(1.0 + alpha_h_n, m);
            const double Se = 1.0 / denom;
            if (Se > 0.0 && Se < 1.0) {
                const double Se_inv_m = std::pow(Se, 1.0 / m); // pow inside loop
                const double inner = std::pow(1.0 - Se_inv_m, m); // pow inside loop
                const double one_minus_inner = 1.0 - inner;
                // Final computation
                result[i] = p.Ks * std::sqrt(Se) * one_minus_inner * one_minus_inner;
            } else {
                result[i] = Se >= 1.0 ? p.Ks : 0.0;
            }
        }
    }
    return result;
}

double specific_moisture_capacity(double h_cm, const std::string& texture) {
    const SoilTextureParams& p = soil_params(texture);
    if (h_cm >= -1e-10) return 0.0;  // saturated: retention curve flat
    const double m = 1.0 - 1.0 / p.n;
    const double ha = -h_cm; // |h| for h < 0
    const double ah = p.alpha * ha;
    const double pow_n = std::pow(ah, p.n);
    const double term = 1.0 + pow_n;
    // C(h) = (theta_s - theta_r) * alpha * n * m * (alpha*h)^(n-1) / (term)^(m+1)
    return (p.theta_s - p.theta_r) * p.alpha * p.n * m *
           std::pow(ah, p.n - 1.0) / std::pow(term, m + 1.0);
}

std::vector<double> specific_moisture_capacity_array(const std::vector<double>& h_cm,
                                                     const std::string& texture) {
    const SoilTextureParams& p = soil_params(texture);
    const double m = 1.0 - 1.0 / p.n;
    std::vector<double> result(h_cm.size(), 0.0);

    #pragma omp parallel for
    for (std::size_t i = 0; i < h_cm.size(); ++i) {
        const double h = h_cm[i];
        if (h >= -1e-10) {
            result[i] = 0.0;  // saturated: retention curve flat
        } else {
            const double ha = -h; // |h| for h < 0
            const double ah = p.alpha * ha;
            const double pow_n = std::pow(ah, p.n);
            const double term = 1.0 + pow_n;
            // C(h) = (theta_s - theta_r) * alpha * n * m * (alpha*h)^(n-1) / (term)^(m+1)
            result[i] = (p.theta_s - p.theta_r) * p.alpha * p.n * m *
                        std::pow(ah, p.n - 1.0) / std::pow(term, m + 1.0);
        }
    }
    return result;
}

}  // namespace hydroma
