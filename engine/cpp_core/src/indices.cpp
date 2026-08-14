// HyDroMa C++ core — Vegetation/water indices implementation.
#include "hydroma/indices.hpp"

#include <stdexcept>

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

std::vector<double> ndvi_array(const std::vector<double>& red,
                               const std::vector<double>& nir) {
    check_same_size(red, nir, "ndvi_array");
    std::vector<double> out(red.size());
    for (std::size_t i = 0; i < red.size(); ++i) out[i] = ndvi(red[i], nir[i]);
    return out;
}

std::vector<double> evi_array(const std::vector<double>& red,
                              const std::vector<double>& nir,
                              const std::vector<double>& blue) {
    check_same_size(red, nir, "evi_array");
    check_same_size(red, blue, "evi_array");
    std::vector<double> out(red.size());
    for (std::size_t i = 0; i < red.size(); ++i) out[i] = evi(red[i], nir[i], blue[i]);
    return out;
}

std::vector<double> savi_array(const std::vector<double>& red,
                               const std::vector<double>& nir, double L) {
    check_same_size(red, nir, "savi_array");
    std::vector<double> out(red.size());
    for (std::size_t i = 0; i < red.size(); ++i) out[i] = savi(red[i], nir[i], L);
    return out;
}

std::vector<double> ndwi_array(const std::vector<double>& green,
                               const std::vector<double>& nir) {
    check_same_size(green, nir, "ndwi_array");
    std::vector<double> out(green.size());
    for (std::size_t i = 0; i < green.size(); ++i) out[i] = ndwi(green[i], nir[i]);
    return out;
}

std::vector<double> nbr_array(const std::vector<double>& nir,
                              const std::vector<double>& swir) {
    check_same_size(nir, swir, "nbr_array");
    std::vector<double> out(nir.size());
    for (std::size_t i = 0; i < nir.size(); ++i) out[i] = nbr(nir[i], swir[i]);
    return out;
}

}  // namespace hydroma
