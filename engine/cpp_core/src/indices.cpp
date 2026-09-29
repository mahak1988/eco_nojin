// HyDroMa C++ core — Vegetation/water indices implementation.
#include "hydroma/indices.hpp"

#include <stdexcept>
// Add OpenMP header
#include <omp.h>

#include <cstddef>
#include <string>
#include <vector>

namespace hydroma {

namespace {

double clip(double v) { return v < -1.0 ? -1.0 : (v > 1.0 ? 1.0 : v); }

double safe_ratio(double numerator, double denominator) {
    if (denominator == 0.0) return 0.0;
    return numerator / denominator;
}

void check_same_size(const std::vector<double>& a, const std::vector<double>& b,
                     const char* what) {
    if (a.size() != b.size()) {
        throw std::invalid_argument(std::string(what) + ": arrays must have equal size");
    }
}

}  // namespace

double ndvi(double red, double nir) { return clip(safe_ratio(nir - red, nir + red)); }

double evi(double red, double nir, double blue) {
    return clip(safe_ratio(2.5 * (nir - red), nir + 6.0 * red - 7.5 * blue + 1.0));
}

double savi(double red, double nir, double L) {
    return clip(safe_ratio((nir - red) * (1.0 + L), nir + red + L));
}

double ndwi(double green, double nir) { return clip(safe_ratio(green - nir, green + nir)); }

double nbr(double nir, double swir) { return clip(safe_ratio(nir - swir, nir + swir)); }

// ---------------------------------------------------------------------------
// Raw-buffer kernels: the single implementation of the index math.
// The std::vector overloads below delegate here, and the pybind11 binding calls
// these directly so a NumPy array is read and written in place.
// The index type is signed because MSVC's /openmp is OpenMP 2.0, which rejects
// unsigned loop indices; /openmp:llvm (OpenMP 3.1) is used instead, but the
// signed type keeps the source portable to the plain flag as well.
// ---------------------------------------------------------------------------
void ndvi_array_raw(const double* red, const double* nir, double* out, std::size_t n) {
    const long long count = static_cast<long long>(n);
    #pragma omp parallel for
    for (long long i = 0; i < count; ++i) {
        out[i] = ndvi(red[i], nir[i]);
    }
}

void evi_array_raw(const double* red, const double* nir, const double* blue,
                   double* out, std::size_t n) {
    const long long count = static_cast<long long>(n);
    #pragma omp parallel for
    for (long long i = 0; i < count; ++i) {
        out[i] = evi(red[i], nir[i], blue[i]);
    }
}

void savi_array_raw(const double* red, const double* nir, double L, double* out,
                    std::size_t n) {
    const long long count = static_cast<long long>(n);
    #pragma omp parallel for
    for (long long i = 0; i < count; ++i) {
        out[i] = savi(red[i], nir[i], L);
    }
}

void ndwi_array_raw(const double* green, const double* nir, double* out, std::size_t n) {
    const long long count = static_cast<long long>(n);
    #pragma omp parallel for
    for (long long i = 0; i < count; ++i) {
        out[i] = ndwi(green[i], nir[i]);
    }
}

void nbr_array_raw(const double* nir, const double* swir, double* out, std::size_t n) {
    const long long count = static_cast<long long>(n);
    #pragma omp parallel for
    for (long long i = 0; i < count; ++i) {
        out[i] = nbr(nir[i], swir[i]);
    }
}

// --- Vector overloads: delegate to the raw kernels -------------------------
std::vector<double> ndvi_array(const std::vector<double>& red,
                               const std::vector<double>& nir) {
    check_same_size(red, nir, "ndvi_array");
    std::vector<double> out(red.size());
    ndvi_array_raw(red.data(), nir.data(), out.data(), out.size());
    return out;
}

std::vector<double> evi_array(const std::vector<double>& red,
                              const std::vector<double>& nir,
                              const std::vector<double>& blue) {
    check_same_size(red, nir, "evi_array");
    check_same_size(red, blue, "evi_array");
    std::vector<double> out(red.size());
    evi_array_raw(red.data(), nir.data(), blue.data(), out.data(), out.size());
    return out;
}

std::vector<double> savi_array(const std::vector<double>& red,
                               const std::vector<double>& nir, double L) {
    check_same_size(red, nir, "savi_array");
    std::vector<double> out(red.size());
    savi_array_raw(red.data(), nir.data(), L, out.data(), out.size());
    return out;
}

std::vector<double> ndwi_array(const std::vector<double>& green,
                               const std::vector<double>& nir) {
    check_same_size(green, nir, "ndwi_array");
    std::vector<double> out(green.size());
    ndwi_array_raw(green.data(), nir.data(), out.data(), out.size());
    return out;
}

std::vector<double> nbr_array(const std::vector<double>& nir,
                              const std::vector<double>& swir) {
    check_same_size(nir, swir, "nbr_array");
    std::vector<double> out(nir.size());
    nbr_array_raw(nir.data(), swir.data(), out.data(), out.size());
    return out;
}

}  // namespace hydroma
