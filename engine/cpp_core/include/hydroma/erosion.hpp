// HyDroMa C++ core — Soil erosion kernels (RUSLE)
//
// Revised Universal Soil Loss Equation: A = R * K * LS * C * P
// References:
//  - Renard, K.G. et al. (1997). "Predicting Soil Erosion by Water:
//    A Guide to Conservation Planning With the Revised Universal Soil Loss
//    Equation (RUSLE)." USDA Agriculture Handbook No. 703.
//  - McCool, D.K. et al. (1987). "Revised slope steepness factor for the
//    Universal Soil Loss Equation." Trans. ASAE 30:1387-1396.
//  - Renard, K.G., Freimund, J.R. (1994). "Using monthly precipitation data
//    to estimate the R-factor in the revised USLE." J. Hydrology 157:287-306.
#pragma once

#include <string>

namespace hydroma {

/// Annual average soil loss from RUSLE.
/// A = R * K * LS * C * P
/// \param R  rainfall-runoff erosivity factor [MJ mm / (ha h yr)]
/// \param K  soil erodibility factor [t ha h / (ha MJ mm)]
/// \param LS slope length and steepness factor [-]
/// \param C  cover-management factor [-]
/// \param P  support practice factor [-]
/// \return   average annual soil loss [t / (ha yr)]
double rusle_annual_soil_loss(double R, double K, double LS, double C, double P);

/// Slope length and steepness (LS) factor for RUSLE.
/// L = (lambda / 22.13)^m with m = beta / (1 + beta);
/// S per McCool et al. (1987): 10.8*sin(theta)+0.03 (slope < 9%),
/// 16.8*sin(theta)-0.50 (slope >= 9%).
/// \param slope_length_m  slope length [m]
/// \param slope_percent   slope steepness [%]
/// \return LS factor [-]
double ls_factor(double slope_length_m, double slope_percent);

/// Simple R-factor estimator from mean annual precipitation
/// (Renard & Freimund 1994). Coarse estimate; measured R is preferred.
/// \param annual_rainfall_mm  mean annual precipitation [mm]
/// \return R factor [MJ mm / (ha h yr)]
double estimate_rainfall_erosivity(double annual_rainfall_mm);

/// Typical K (soil erodibility) values for common texture classes [t ha h/(ha MJ mm)].
double soil_erodibility_k(const std::string& texture);

}  // namespace hydroma
