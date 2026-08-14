// HyDroMa C++ core — Soil physics implementation (van Genuchten).
#include "hydroma/soil.hpp"

#include <cmath>
#include <stdexcept>

namespace hydroma {

namespace {

// Typical parameters from Carsel & Parrish (1988) / Rosetta pedotransfer,
// matching engine/hydroma/cpp_bridge/soil_physics_fast.py exactly.
struct TextureEntry {
    const char* key;
    SoilTextureParams params;
};

constexpr TextureEntry kTextures[] = {
    {"sand",        {0.045, 0.43, 0.145, 2.68, 29.7}},
    {"loamy_sand",  {0.057, 0.41, 0.124, 2.28, 14.6}},
    {"sandy_loam",  {0.065, 0.41, 0.075, 1.89, 4.42}},
    {"loam",        {0.078, 0.43, 0.036, 1.56, 1.05}},
    {"silt_loam",   {0.067, 0.45, 0.020, 1.41, 0.45}},
    {"clay_loam",   {0.095, 0.41, 0.019, 1.31, 0.26}},
    {"clay",        {0.068, 0.38, 0.008, 1.09, 0.12}},
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

    for (std::size_t i = 0; i < h_matric.size(); ++i) {
        const double h = std::fabs(h_matric[i]);
        if (h < 1e-10) {
            result[i] = p.Ks;
        } else {
            const double denom =
                std::pow(1.0 + std::pow(p.alpha * h, p.n), m);
            const double Se = 1.0 / denom;
            if (Se > 0.0 && Se < 1.0) {
                // Mualem-van Genuchten: K = Ks Se^0.5 [1 - (1-Se^{1/m})^m]^2
                const double inner =
                    std::pow(1.0 - std::pow(Se, 1.0 / m), m);
                const double one_minus_inner = 1.0 - inner;
                result[i] = p.Ks * std::sqrt(Se) * one_minus_inner * one_minus_inner;
            } else {
                result[i] = Se >= 1.0 ? p.Ks : 0.0;
            }
        }
    }
    return result;
}

}  // namespace hydroma
