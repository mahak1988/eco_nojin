// C API bridge (Phase 7 — C++20 parity for hot paths).
// Exports a small, stable C surface for ctypes (no pybind11 needed).
// Kernels: ET0 Hargreaves, extraterrestrial radiation, van Genuchten theta.
#include "hydroma/climate.hpp"
#include <cmath>

#if defined(_WIN32) || defined(__CYGWIN__)
#define HYDROMA_API_EXPORT __declspec(dllexport)
#else
#define HYDROMA_API_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {

HYDROMA_API_EXPORT double et0_hargreaves(double t_min, double t_max,
                                          double t_mean, double ra_mj) {
    return hydroma::hargreaves_et0(t_min, t_max, t_mean, ra_mj);
}

HYDROMA_API_EXPORT double extraterrestrial_radiation(double lat_deg,
                                                      int doy) {
    return hydroma::extraterrestrial_radiation(lat_deg, doy);
}

// Single-point van Genuchten retention:
//   m = 1 - 1/n ;  theta(h) = theta_r + (theta_s - theta_r) / (1 + (alpha*|h|)^n)^m
// Matches engine/hydroma/soil/physics.py van_genuchten_theta.
HYDROMA_API_EXPORT double vg_theta(double h, double theta_r,
                                   double theta_s, double alpha, double n) {
    if (n <= 0.0) return 0.0;
    const double m = 1.0 - 1.0 / n;
    const double ah = std::pow(alpha * std::abs(h), n);
    return theta_r + (theta_s - theta_r) / std::pow(1.0 + ah, m);
}

}  // extern "C"
