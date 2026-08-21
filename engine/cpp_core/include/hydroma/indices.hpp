// HyDroMa C++ core — Vegetation/water index kernels
//
// Standard remote sensing indices, mirroring
// engine/hydroma/cpp_bridge/indices_fast.py.
// References:
//  - NDVI: Rouse et al. (1974)
//  - EVI:  Huete et al. (2002)
//  - SAVI: Huete (1988)
//  - NDWI: McFeeters (1996)
//  - NBR:  Key & Benson (2006)
#pragma once

#include <vector>

namespace hydroma {

/// NDVI = (NIR - Red) / (NIR + Red), clipped to [-1, 1]; 0 on null denominator.
double ndvi(double red, double nir);

/// EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1), clipped to [-1, 1].
double evi(double red, double nir, double blue);

/// SAVI = (NIR - Red) / (NIR + Red + L) * (1 + L), clipped to [-1, 1].
double savi(double red, double nir, double L = 0.5);

/// NDWI = (Green - NIR) / (Green + NIR), clipped to [-1, 1].
double ndwi(double green, double nir);

/// NBR = (NIR - SWIR) / (NIR + SWIR), clipped to [-1, 1].
double nbr(double nir, double swir);

/// Vector versions (element-wise, NaN-free by construction).
std::vector<double> ndvi_array(const std::vector<double>& red,
                               const std::vector<double>& nir);
std::vector<double> evi_array(const std::vector<double>& red,
                              const std::vector<double>& nir,
                              const std::vector<double>& blue);
std::vector<double> savi_array(const std::vector<double>& red,
                               const std::vector<double>& nir, double L = 0.5);
std::vector<double> ndwi_array(const std::vector<double>& green,
                               const std::vector<double>& nir);
std::vector<double> nbr_array(const std::vector<double>& nir,
                              const std::vector<double>& swir);

}  // namespace hydroma
