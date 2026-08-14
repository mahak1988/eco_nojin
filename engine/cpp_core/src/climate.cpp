// HyDroMa C++ core — Climate kernels implementation (FAO-56, Hargreaves-Samani).
#include "hydroma/climate.hpp"

#include <cmath>
#include <stdexcept>

namespace hydroma {

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kGsc = 0.0820;        // solar constant [MJ/m2/min]
constexpr double kSigma = 4.903e-9;    // Stefan-Boltzmann [MJ/K4/m2/day]
constexpr double kAlbedo = 0.23;       // grass reference albedo (FAO-56)

double sat_vapor_pressure(double t_c) {
    return 0.6108 * std::exp(17.27 * t_c / (t_c + 237.3));
}

double clamp(double v, double lo, double hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

}  // namespace

double hargreaves_et0(double t_min, double t_max, double t_mean, double ra_mj) {
    if (t_max < t_min) throw std::invalid_argument("t_max must be >= t_min");
    if (ra_mj < 0.0) throw std::invalid_argument("radiation cannot be negative");
    return 0.0023 * 0.408 * ra_mj * (t_mean + 17.8) *
           std::sqrt(t_max - t_min);
}

double extraterrestrial_radiation(double lat_deg, int doy) {
    if (doy < 1 || doy > 366) throw std::invalid_argument("doy must be in [1, 366]");
    const double phi = lat_deg * kPi / 180.0;
    const double dr = 1.0 + 0.033 * std::cos(2.0 * kPi * doy / 365.0);
    const double decl = 0.409 * std::sin(2.0 * kPi * doy / 365.0 - 1.39);
    const double cos_ws = -std::tan(phi) * std::tan(decl);
    const double ws = std::acos(clamp(cos_ws, -1.0, 1.0));
    return (24.0 * 60.0 / kPi) * kGsc * dr *
           (ws * std::sin(phi) * std::sin(decl) +
            std::cos(phi) * std::cos(decl) * std::sin(ws));
}

double fao56_net_radiation(double t_min, double t_max, double rh_mean_pct,
                           double rs_mj, double elevation_m, double lat_deg,
                           int doy) {
    if (t_max < t_min) throw std::invalid_argument("t_max must be >= t_min");
    rh_mean_pct = clamp(rh_mean_pct, 0.0, 100.0);
    if (rs_mj < 0.0) throw std::invalid_argument("radiation cannot be negative");

    const double t_mean = (t_min + t_max) / 2.0;
    const double es = sat_vapor_pressure(t_mean);
    const double ea = es * rh_mean_pct / 100.0;

    const double ra = extraterrestrial_radiation(lat_deg, doy);
    const double rso = (0.75 + 2e-5 * elevation_m) * ra;
    const double rns = (1.0 - kAlbedo) * rs_mj;

    // Clear-sky ratio limited to [0.3, 1.0] per FAO-56 recommendation.
    double rs_rso = rso > 0.0 ? rs_mj / rso : 1.0;
    rs_rso = clamp(rs_rso, 0.3, 1.0);

    const double t_max_k = t_max + 273.16;
    const double t_min_k = t_min + 273.16;
    const double rnl =
        kSigma * (std::pow(t_max_k, 4) + std::pow(t_min_k, 4)) / 2.0 *
        (0.34 - 0.14 * std::sqrt(ea)) * (1.35 * rs_rso - 0.35);

    return rns - rnl;
}

double penman_monteith_et0(double t_min, double t_max, double rh_mean_pct,
                           double u2, double rs_mj, double elevation_m,
                           double lat_deg, int doy) {
    if (u2 < 0.0) throw std::invalid_argument("wind speed cannot be negative");

    const double t_mean = (t_min + t_max) / 2.0;
    const double es = sat_vapor_pressure(t_mean);
    const double ea = es * clamp(rh_mean_pct, 0.0, 100.0) / 100.0;

    // Slope of saturation vapour pressure curve (FAO-56 eq. 13).
    const double delta = 4098.0 * es / std::pow(t_mean + 237.3, 2);

    // Atmospheric pressure and psychrometric constant (FAO-56 eq. 7-8).
    const double p_atm =
        101.3 * std::pow((293.0 - 0.0065 * elevation_m) / 293.0, 5.26);
    const double gamma = 0.000665 * p_atm;

    const double rn = fao56_net_radiation(t_min, t_max, rh_mean_pct, rs_mj,
                                          elevation_m, lat_deg, doy);

    const double numerator =
        0.408 * delta * rn +
        gamma * (900.0 / (t_mean + 273.16)) * u2 * (es - ea);
    const double denominator = delta + gamma * (1.0 + 0.34 * u2);

    return numerator / denominator;
}

}  // namespace hydroma
