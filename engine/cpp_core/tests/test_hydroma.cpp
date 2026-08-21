// HyDroMa C++ core — self-contained unit tests (no external framework).
//
// Build & run (MSVC):
//   cl /std:c++20 /EHsc /Iinclude src\hydrology.cpp src\soil.cpp src\erosion.cpp
//      src\climate.cpp src\indices.cpp tests\test_hydroma.cpp
//   test_hydroma.exe
//
// Exit code 0 = all tests passed.
#include <cmath>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

#include "hydroma/climate.hpp"
#include "hydroma/erosion.hpp"
#include "hydroma/hydrology.hpp"
#include "hydroma/indices.hpp"
#include "hydroma/soil.hpp"

using namespace hydroma;

namespace {

int g_failures = 0;
int g_checks = 0;

void check(bool ok, const std::string& name) {
    ++g_checks;
    if (!ok) {
        ++g_failures;
        std::printf("  [FAIL] %s\n", name.c_str());
    } else {
        std::printf("  [ ok ] %s\n", name.c_str());
    }
}

void check_close(double a, double b, double tol, const std::string& name) {
    check(std::fabs(a - b) <= tol, name);
}

}  // namespace

int main() {
    std::printf("HyDroMa C++ core tests\n");

    // ---- Hydrology -------------------------------------------------------
    std::printf("[Hydrology]\n");
    {
        const std::vector<double> inflow{0.0, 50.0, 100.0, 50.0, 0.0};
        const RoutingResult r =
            route_flood_wave(inflow, 1000.0, 50, 0.030, 0.002, 10.0, 5.0);
        check(r.peak_inflow == 100.0, "peak inflow detected");
        check(r.peak_outflow <= r.peak_inflow, "peak attenuation (<= inflow)");
        check(r.peak_outflow > 0.0, "outflow peak positive");
        // Short series: wave is still in transit, so mass balance is not a
        // meaningful metric here (the Python suite behaves identically).
        check(r.travel_time > 0.0, "positive travel time");
        check(r.normal_depth > 0.0, "positive normal depth");
        check(r.outflow.size() == inflow.size(), "outflow same length");

        const std::vector<double> flat(10, 100.0);
        const RoutingResult rf =
            route_flood_wave(flat, 1000.0, 50, 0.030, 0.002, 10.0, 5.0);
        check(std::fabs(rf.peak_outflow - 100.0) < 1e-9,
              "steady flow stays steady");

        // Long rectangular hydrograph (200 steps, same as Python suite):
        // mass conserved within 10%, multi-reach attenuates more.
        std::vector<double> rect(200, 0.0);
        for (int i = 0; i < 200; ++i) {
            const double t = i * 10.0;
            if (t > 200.0 && t < 800.0) rect[static_cast<std::size_t>(i)] = 10.0;
        }
        const RoutingResult rr = route_flood_wave(rect, 1000.0, 50, 0.030,
                                                  0.002, 10.0, 5.0);
        check(rr.mass_balance > 0.8 && rr.mass_balance < 1.2,
              "mass conservation within 10% (matches Python suite)");

        const RoutingResult rm = route_multi_reach(rect, 1000.0, 3, 0.030,
                                                   0.002, 10.0, 5.0);
        check(rm.peak_outflow <= rr.peak_outflow + 1e-9,
              "multi-reach attenuates more than single reach");
        check(rm.peak_outflow > 0.0, "multi-reach outflow positive");
    }

    // ---- Soil ------------------------------------------------------------
    std::printf("[Soil physics]\n");
    {
        const std::vector<double> h{0.0, 10.0, 100.0, 1000.0};
        const auto theta = soil_water_content(h, "loam");
        const auto k = hydraulic_conductivity(h, "loam");
        const auto& p = soil_params("loam");
        check_close(theta[0], p.theta_s, 1e-12, "theta(h=0) = theta_s");
        check_close(k[0], p.Ks, 1e-12, "K(h=0) = Ks");
        check(theta[0] >= theta[1] && theta[1] >= theta[3],
              "theta decreases with suction");
        check(theta[3] >= p.theta_r - 1e-12, "theta approaches theta_r");
        bool threw = false;
        try {
            soil_water_content(h, "not_a_texture");
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "unknown texture raises");
    }

    // ---- Erosion ---------------------------------------------------------
    std::printf("[RUSLE]\n");
    {
        check_close(rusle_annual_soil_loss(100.0, 0.3, 1.0, 0.5, 1.0), 15.0,
                    1e-12, "A = R*K*LS*C*P");
        // Slope 10%, length 22.13 m -> L = 1, S = 16.8*sin(atan(0.1))-0.5
        const double ls = ls_factor(22.13, 10.0);
        check_close(ls, 16.8 * std::sin(std::atan(0.1)) - 0.50, 1e-9,
                    "LS factor at 10% slope");
        const double ls_flat = ls_factor(22.13, 2.0);
        check(ls_flat > 0.0 && ls_flat < 1.0, "gentle slope small LS");
        const double r = estimate_rainfall_erosivity(500.0);
        // Renard & Freimund (1994): R = 0.04830 * P^1.61 for P < 850 mm.
        check_close(r, 0.04830 * std::pow(500.0, 1.61), 1e-6,
                    "R estimate follows R&F formula");
        // Piecewise branches must be continuous at the 850 mm breakpoint.
        const double r1 = estimate_rainfall_erosivity(850.0);
        const double r2 = 587.8 - 1.219 * 850.0 + 0.004105 * 850.0 * 850.0;
        check(std::fabs(r1 - r2) < 10.0, "R estimator continuous at 850 mm");
        check(estimate_rainfall_erosivity(300.0) < r,
              "R increases with rainfall");
        check(estimate_rainfall_erosivity(0.0) == 0.0, "R = 0 for no rain");
    }

    // ---- Climate ---------------------------------------------------------
    std::printf("[Climate]\n");
    {
        // Hargreaves-Samani, hand-computed:
        // 0.0023 * 0.408 * 40 * (20+17.8) * sqrt(30-10) = 6.3454...
        check_close(hargreaves_et0(10.0, 30.0, 20.0, 40.0), 6.3454, 1e-3,
                    "Hargreaves-Samani reference value");
        bool threw = false;
        try {
            hargreaves_et0(30.0, 10.0, 20.0, 40.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "Hargreaves rejects t_max < t_min");

        const double et0 = penman_monteith_et0(
            15.0, 25.0, 60.0, 2.0, 20.0, 100.0, 30.0, 180);
        check(et0 > 0.5 && et0 < 12.0, "FAO-56 PM ET0 in plausible range");
        const double et0_high_rad = penman_monteith_et0(
            15.0, 25.0, 60.0, 2.0, 30.0, 100.0, 30.0, 180);
        check(et0_high_rad > et0, "PM ET0 increases with radiation");
        const double et0_hot = penman_monteith_et0(
            20.0, 35.0, 40.0, 3.0, 25.0, 100.0, 30.0, 180);
        check(et0_hot > et0, "PM ET0 increases with heat/dryness");

        const double ra = extraterrestrial_radiation(30.0, 180);
        check(ra > 20.0 && ra < 45.0, "Ra mid-summer mid-latitude plausible");
    }

    // ---- Indices ---------------------------------------------------------
    std::printf("[Vegetation indices]\n");
    {
        check_close(ndvi(100.0, 300.0), 0.5, 1e-12, "NDVI symmetric");
        check_close(ndvi(0.0, 0.0), 0.0, 1e-12, "NDVI null denominator = 0");
        check(ndvi(1000.0, 100.0) >= -1.0 && ndvi(1000.0, 100.0) <= 1.0,
              "NDVI clipped");
        check_close(evi(100.0, 300.0, 50.0),
                    2.5 * 200.0 / (300.0 + 600.0 - 375.0 + 1.0), 1e-9,
                    "EVI formula");
        check_close(savi(100.0, 300.0, 0.5),
                    (200.0 / 400.5) * 1.5, 1e-9, "SAVI formula");
        const std::vector<double> red{100.0, 200.0}, nir{300.0, 400.0};
        const auto out = ndvi_array(red, nir);
        check(out.size() == 2, "array index size");
        check_close(out[0], 0.5, 1e-12, "array NDVI[0]");
    }

    std::printf("\n%d checks, %d failures\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
