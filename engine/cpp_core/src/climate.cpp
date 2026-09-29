// HyDroMa C++ core — Climate kernels implementation (FAO-56, Hargreaves-Samani).
#include "hydroma/climate.hpp"

#include <cmath>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

#include <cstddef>
#include <string>
#include <vector>

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

void check_same_size_climate(const std::vector<double>& a, const std::vector<double>& b,
                             const char* what) {
    if (a.size() != b.size()) {
        throw std::invalid_argument(std::string(what) + ": arrays must have equal size");
    }
}
void check_same_size_climate_int(const std::vector<double>& a, const std::vector<int>& b,
                                 const char* what) {
    if (a.size() != b.size()) {
        throw std::invalid_argument(std::string(what) + ": arrays must have equal size");
    }
}

}  // namespace

double hargreaves_et0(double t_min, double t_max, double t_mean, double ra_mj) {
    if (t_max < t_min) throw std::invalid_argument("t_max must be >= t_min");
    if (ra_mj < 0.0) throw std::invalid_argument("radiation cannot be negative");
    // FAO-56 eq. 52, with the published exponent:
    //
    //     ET0 = 0.0023 * (Tmean + 17.8) * (Tmax - Tmin)^0.48 * Ra
    //
    // The exponent is 0.48, not 0.50. std::sqrt is 0.50, which overstated ET0
    // by 3.3 % at a 5 degC diurnal range and 6.6 % at 25 degC. Measured against
    // the Python core, which was corrected to 0.48 in et_calculator.py, this
    // line was 4.71 % high at Tmin 15 / Tmax 25 / Tmean 20 / Ra 15.
    //
    // The array twin below must use the same exponent; the two were the same
    // defect twice and only one of them was noticed.
    if (t_max == t_min) return 0.0;
    return 0.0023 * 0.408 * ra_mj * (t_mean + 17.8) *
           std::pow(t_max - t_min, 0.48);
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

    // FAO-56 eq. 11: es = (e0(Tmax) + e0(Tmin)) / 2. The previous code used
    // e0(Tmean), which is the older Penman form; because es - ea is the vapour
    // pressure deficit and enters ET0 directly, the two differ by tens of
    // percent for the same inputs.
    const double es = (sat_vapor_pressure(t_max) + sat_vapor_pressure(t_min)) / 2.0;
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

    // Two different saturation pressures are required, and conflating them was
    // the source of a large C++/Python divergence in ET0:
    //   es  -- FAO-56 eq. 11: mean of e0(Tmax) and e0(Tmin), used with ea to
    //          form the vapour pressure deficit that drives the second term.
    //   e0  -- FAO-56 eq. 13: e0(Tmean) alone, used for the slope of the curve.
    const double es = (sat_vapor_pressure(t_max) + sat_vapor_pressure(t_min)) / 2.0;
    const double e0_mean = sat_vapor_pressure(t_mean);
    const double ea = es * clamp(rh_mean_pct, 0.0, 100.0) / 100.0;

    // Slope of saturation vapour pressure curve (FAO-56 eq. 13).
    const double delta = 4098.0 * e0_mean / std::pow(t_mean + 237.3, 2);

    // Atmospheric pressure and psychrometric constant (FAO-56 eq. 7-8).
    const double p_atm =
        101.3 * std::pow((293.0 - 0.0065 * elevation_m) / 293.0, 5.26);
    const double gamma = 0.000665 * p_atm;

    const double rn = fao56_net_radiation(t_min, t_max, rh_mean_pct, rs_mj,
                                          elevation_m, lat_deg, doy);

    // FAO-56 eq. 6 uses 273, not 273.16. The constant 273.16 (the more precise
    // form) was used here while the Python fallback used 273, so the two backends
    // differed by ~2e-4 in ET0 for identical inputs.
    const double numerator =
        0.408 * delta * rn +
        gamma * (900.0 / (t_mean + 273.0)) * u2 * (es - ea);
    const double denominator = delta + gamma * (1.0 + 0.34 * u2);

    // A negative numerator means the day loses more energy by radiation than it
    // receives, and the aerodynamic term cannot pay for it: ET0 has no negative
    // meaning. FAO-56 eq. 6 is unclamped on Rn, which is why a polar night keeps
    // a small positive value, but the resulting ET0 is floored here. Without
    // this the two backends returned 0.0 and -0.2241 mm/day for the same day.
    return std::max(0.0, numerator / denominator);
}

// --- Added by Implementation Plan ---
std::vector<double> hargreaves_et0_array(const std::vector<double>& t_min,
                                          const std::vector<double>& t_max,
                                          const std::vector<double>& t_mean,
                                          const std::vector<double>& ra_mj) {
    check_same_size_climate(t_min, t_max, "hargreaves_et0_array");
    check_same_size_climate(t_min, t_mean, "hargreaves_et0_array");
    check_same_size_climate(t_min, ra_mj, "hargreaves_et0_array");

    std::vector<double> out(t_min.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < t_min.size(); ++i) {
        const double tmin = t_min[i];
        const double tmax = t_max[i];
        const double tmean = t_mean[i];
        const double ra = ra_mj[i];

        if (tmax < tmin) {
            throw std::invalid_argument("t_max must be >= t_min at index " + std::to_string(i));
        }
        if (ra < 0.0) {
            throw std::invalid_argument("radiation cannot be negative at index " + std::to_string(i));
        }
        // Same exponent as the scalar form: 0.48 per FAO-56 eq. 52, not the 0.50
        // that std::sqrt gives. test_climate_unit.cpp already cross-checks the
        // two at 1e-10, which is why this drifted for as long as it did.
        out[i] = (tmax == tmin)
                     ? 0.0
                     : 0.0023 * 0.408 * ra * (tmean + 17.8) *
                           std::pow(tmax - tmin, 0.48);
    }
    return out;
}

std::vector<double> extraterrestrial_radiation_array(const std::vector<double>& lat_deg,
                                                     const std::vector<int>& doy) {
    check_same_size_climate_int(lat_deg, doy, "extraterrestrial_radiation_array");

    std::vector<double> out(lat_deg.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < lat_deg.size(); ++i) {
        const double lat = lat_deg[i];
        const int day = doy[i];

        if (day < 1 || day > 366) {
            throw std::invalid_argument("doy must be in [1, 366] at index " + std::to_string(i));
        }

        const double phi = lat * kPi / 180.0;
        const double dr = 1.0 + 0.033 * std::cos(2.0 * kPi * day / 365.0);
        const double decl = 0.409 * std::sin(2.0 * kPi * day / 365.0 - 1.39);
        const double cos_ws = -std::tan(phi) * std::tan(decl);
        const double ws = std::acos(clamp(cos_ws, -1.0, 1.0));
        out[i] = (24.0 * 60.0 / kPi) * kGsc * dr *
                 (ws * std::sin(phi) * std::sin(decl) +
                  std::cos(phi) * std::cos(decl) * std::sin(ws));
    }
    return out;
}


std::vector<double> penman_monteith_et0_array(const std::vector<double>& t_min,
                                              const std::vector<double>& t_max,
                                              const std::vector<double>& rh_mean_pct,
                                              const std::vector<double>& u2,
                                              const std::vector<double>& rs_mj,
                                              const std::vector<double>& elevation_m,
                                              const std::vector<double>& lat_deg,
                                              const std::vector<int>& doy) {
    check_same_size_climate(t_min, t_max, "penman_monteith_et0_array");
    check_same_size_climate(t_min, rh_mean_pct, "penman_monteith_et0_array");
    check_same_size_climate(t_min, u2, "penman_monteith_et0_array");
    check_same_size_climate(t_min, rs_mj, "penman_monteith_et0_array");
    check_same_size_climate(t_min, elevation_m, "penman_monteith_et0_array");
    check_same_size_climate(t_min, lat_deg, "penman_monteith_et0_array");
    check_same_size_climate_int(t_min, doy, "penman_monteith_et0_array");

    std::vector<double> out(t_min.size());
    #pragma omp parallel for
    for (std::size_t i = 0; i < t_min.size(); ++i) {
        const double tmin = t_min[i];
        const double tmax = t_max[i];
        double rh_pct = rh_mean_pct[i];
        const double wind = u2[i];
        const double rs = rs_mj[i];
        const double elev = elevation_m[i];
        const double lat = lat_deg[i];
        const int day = doy[i];

        if (tmax < tmin) {
            throw std::invalid_argument("t_max must be >= t_min at index " + std::to_string(i));
        }
        if (wind < 0.0) {
            throw std::invalid_argument("wind speed cannot be negative at index " + std::to_string(i));
        }
        if (rs < 0.0) {
            throw std::invalid_argument("radiation cannot be negative at index " + std::to_string(i));
        }
        if (day < 1 || day > 366) {
            throw std::invalid_argument("doy must be in [1, 366] at index " + std::to_string(i));
        }

        // Mirror of the scalar function, term for term. This loop was a
        // re-derivation and had drifted from penman_monteith_et0 in four
        // places: es used e0(Tmean) instead of the mean of the two endpoints,
        // ea was built from that same e0, the psychrometric term used 273.16
        // where eq. 6 says 273, and the result was not floored at zero. Call the
        // scalar function instead of keeping a second copy to fall out of date.
        out[i] = penman_monteith_et0(tmin, tmax, rh_mean_pct[i], wind, rs, elev,
                                      lat, day);
    }
    return out;
}

// --- End of Added Section ---

}  // namespace hydroma
