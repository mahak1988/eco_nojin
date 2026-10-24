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

/// Raw-buffer versions. These are the single implementation of the index math:
/// the std::vector overloads below delegate to them, and the pybind11 binding
/// calls them directly so a NumPy input is read and written in place with no
/// intermediate container. `n` is the element count; pointers must be valid for
/// n elements. No aliasing between an input and `out` is assumed.
void ndvi_array_raw(const double* red, const double* nir, double* out, std::size_t n);
void evi_array_raw(const double* red, const double* nir, const double* blue,
                   double* out, std::size_t n);
void savi_array_raw(const double* red, const double* nir, double L, double* out,
                    std::size_t n);
void ndwi_array_raw(const double* green, const double* nir, double* out, std::size_t n);
void nbr_array_raw(const double* nir, const double* swir, double* out, std::size_t n);

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
