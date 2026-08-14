// HyDroMa C++ core — Soil physics kernels
// van Genuchten (1980) soil water retention curve and unsaturated
// hydraulic conductivity (van Genuchten-Mualem).
//
// Reference: van Genuchten, M.Th. (1980). "A closed-form equation for
// predicting the hydraulic conductivity of unsaturated soils."
// Soil Science Society of America Journal 44:892-898.
//
// The Python (Numba) counterpart lives in engine/hydroma/cpp_bridge/soil_physics_fast.py.
#pragma once

#include <string>
#include <vector>

namespace hydroma {

/// van Genuchten parameters for one soil texture class.
struct SoilTextureParams {
    double theta_r;  ///< residual water content [cm3/cm3]
    double theta_s;  ///< saturated water content [cm3/cm3]
    double alpha;    ///< shape parameter [1/cm]
    double n;        ///< shape parameter [-]
    double Ks;       ///< saturated hydraulic conductivity [cm/day]
};

/// Typical van Genuchten parameters (Carsel & Parrish 1988, Rosetta).
const SoilTextureParams& soil_params(const std::string& texture);

/// List of supported soil texture keys.
std::vector<std::string> supported_textures();

/// theta(h) = theta_r + (theta_s - theta_r) / [1 + |alpha*h|^n]^m,  m = 1 - 1/n
/// \param h_matric  matric potential [cm, positive values]
/// \return          volumetric water content [cm3/cm3]
std::vector<double> soil_water_content(const std::vector<double>& h_matric,
                                       const std::string& soil_texture);

/// Unsaturated hydraulic conductivity, van Genuchten-Mualem model.
/// K(h) = Ks * Se^0.5 * [1 - (1 - Se^(1/m))^m]^2
/// \return hydraulic conductivity [cm/day]
std::vector<double> hydraulic_conductivity(const std::vector<double>& h_matric,
                                           const std::string& soil_texture);

}  // namespace hydroma
