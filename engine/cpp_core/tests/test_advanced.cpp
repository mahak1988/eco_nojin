// HyDroMa C++ core — tests for advanced kernels:
// Richards, Saint-Venant, crop water balance, sediment, sampling.
//
// Build (MSVC):
//   cl /std:c++20 /EHsc /Iinclude src\richards.cpp src\saint_venant.cpp
//      src\crop_water.cpp src\sediment.cpp src\sampling.cpp
//      src\soil.cpp src\erosion.cpp tests\test_advanced.cpp
// Exit code 0 = all tests passed.
#include <cmath>
#include <cstdio>
#include <functional>
#include <numeric>
#include <string>
#include <vector>

#include "hydroma/crop_water.hpp"
#include "hydroma/richards.hpp"
#include "hydroma/saint_venant.hpp"
#include "hydroma/sampling.hpp"
#include "hydroma/sediment.hpp"
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
    std::printf("HyDroMa advanced kernel tests\n");

    // ================= Richards ===========================================
    std::printf("[Richards 1D]\n");
    {
        // Hydrostatic equilibrium: heads = -z, no flow -> state persists.
        RichardsOptions opts;
        opts.n_cells = 40;
        opts.column_depth_cm = 100.0;
        opts.dt_days = 0.1;
        opts.n_steps = 20;
        opts.top = TopBoundary::Head;
        opts.top_value_cm_day = -50.0;  // water table 50 cm below surface
        opts.bottom = BottomBoundary::Head;
        opts.bottom_head_cm = 50.0;     // h(-100) = +50 cm

        // Hydrostatic profile h = -z - 50: unsaturated near top, saturated below.
        std::vector<double> h0(40);
        for (int i = 0; i < 40; ++i) h0[i] = (i + 0.5) * 2.5 - 50.0;

        const RichardsResult r = simulate_richards("loam", h0, opts);
        check(r.converged, "hydrostatic: converges");
        double max_drift = 0.0;
        for (int i = 0; i < 40; ++i)
            max_drift = std::max(max_drift, std::fabs(r.head_cm.back()[i] - h0[i]));
        check(max_drift < 1e-3, "hydrostatic: heads do not drift");

        // Infiltration into dry sandy loam with constant flux: wetting front.
        // Initially unsaturated everywhere (water table 160 cm below surface,
        // column is 150 cm) so the system is well posed (C > 0 in every cell).
        RichardsOptions inf;
        inf.n_cells = 60;
        inf.column_depth_cm = 150.0;
        inf.dt_days = 0.05;
        inf.n_steps = 120;
        inf.top = TopBoundary::Flux;
        inf.top_value_cm_day = 1.0;
        inf.bottom = BottomBoundary::FreeDrainage;
        std::vector<double> h_dry(60);
        for (int i = 0; i < 60; ++i) h_dry[i] = (i + 0.5) * 2.5 - 160.0;
        const RichardsResult r2 = simulate_richards("sandy_loam", h_dry, inf);
        check(r2.converged, "infiltration: converges");
        // Surface should wet: theta at top cell increases.
        const double theta_top0 = r2.theta.front()[0];
        const double theta_top1 = r2.theta.back()[0];
        check(theta_top1 > theta_top0 + 1e-4, "infiltration: top wets");
        // Mass balance: storage change = top flux - bottom flux (cm).
        const double ds = r2.storage_cm.back() - r2.storage_cm.front();
        const double flux_net = r2.cumulative_top_flux_cm.back() -
                                r2.cumulative_bottom_flux_cm.back();
        check(std::fabs(ds - flux_net) < 1.0,
              "infiltration: mass balance closes within 1 cm");
    }

    // ================= Saint-Venant =======================================
    std::printf("[Saint-Venant 1D]\n");
    {
        // Dam break on flat frictionless bed: symmetric expansion, volume kept.
        SaintVenantOptions sv;
        sv.length_m = 1000.0;
        sv.n_cells = 400;
        sv.width_m = 1.0;
        sv.bed_slope = 0.0;
        sv.manning_n = 0.0;
        sv.t_end_s = 30.0;
        sv.cfl = 0.5;
        sv.output_every = 1000000;  // only final state saved

        std::vector<double> h0(400, 0.05);
        for (int i = 0; i < 200; ++i) h0[i] = 1.0;  // left reservoir
        const SaintVenantResult r = simulate_saint_venant(h0, 0.0, sv);
        check(r.stable, "dam break: stable");
        check(std::fabs(r.mass_balance - 1.0) < 0.02,
              "dam break: mass conserved within 2%");
        check(r.depth_m.back().size() == 400, "dam break: output size");
        // Wave must have propagated: some cells right of the dam now wet.
        double wet_right = 0.0;
        for (int i = 250; i < 400; ++i) wet_right += r.depth_m.back()[i];
        check(wet_right > 0.05, "dam break: wave propagates right");

        // Steady uniform flow sanity: normal depth from Manning.
        const double hn = manning_normal_depth(10.0, 5.0, 0.002, 0.03);
        check(hn > 0.5 && hn < 2.0, "Manning normal depth plausible");
    }

    // ================= Crop water balance =================================
    std::printf("[Crop water (FAO-56 dual Kc)]\n");
    {
        const int nd = 120;
        std::vector<double> et0(nd, 5.0), rain(nd, 0.0);
        for (int i = 20; i < 25; ++i) rain[i] = 15.0;  // one wet spell
        CropWaterParams p;
        const CropWaterResult r = simulate_crop_water(et0, rain, false, p);
        check(r.total_etc_mm > 0.0, "ETc positive");
        check(r.total_etc_mm < 5.0 * nd * 1.3, "ETc bounded by Kc_max*ET0");
        // Water balance closure.
        check(std::fabs(r.water_balance_error_mm) < 0.01 * r.total_rain_mm + 1.0,
              "water balance closes");
        // Well-watered start: no stress early season.
        check(r.stress_factor[0] == 1.0, "no stress at start");
        // Depletion grows under drought (no rain, no irrigation).
        check(r.depletion_mm.back() > r.depletion_mm[10],
              "depletion increases under drought");

        // Auto-irrigation keeps depletion near zero.
        const CropWaterResult r2 = simulate_crop_water(et0, rain, true, p);
        check(r2.depletion_mm.back() < p.p_fraction * 1000.0 *
                                           (p.theta_fc - p.theta_wp) * p.root_depth_m,
              "auto-irrigation controls depletion");
        check(r2.total_irrigation_mm > 0.0, "auto-irrigation applied");
    }

    // ================= Sediment ===========================================
    std::printf("[Sediment / RUSLE grid]\n");
    {
        std::vector<RusleCell> cells(4);
        cells[0] = RusleCell{0.32, 0.5, 1.0, 10.0, 50.0};
        cells[1] = RusleCell{0.32, 0.5, 1.0, 10.0, 50.0};
        cells[2] = RusleCell{0.32, 0.2, 1.0, 5.0, 30.0};
        cells[3] = RusleCell{0.32, 0.1, 1.0, 2.0, 20.0};
        const auto per_cell = rusle_grid(cells, 300.0);
        check(per_cell.size() == 4, "grid output size");
        check(per_cell[0] > per_cell[3], "erosion higher on steeper bare cell");
        const double total = rusle_grid_total(cells, 300.0, 1.0);
        check(total > 0.0, "grid total positive");
        const double sdr = sediment_delivery_ratio(10.0);
        check(sdr > 0.0 && sdr < 1.0, "SDR in (0,1)");
        const double yield = sediment_yield(cells, 300.0, 1.0, 10.0);
        check(yield > 0.0 && yield < total, "yield <= erosion");
        // Brune trap efficiency monotone + bounded.
        check(trap_efficiency_brune(0.0) == 0.0, "TE=0 at C/I=0");
        check(trap_efficiency_brune(1.0) > 0.8 && trap_efficiency_brune(1.0) < 0.95,
              "TE at C/I=1 near median curve");
        check(trap_efficiency_brune(5.0) > trap_efficiency_brune(0.5),
              "TE increases with C/I");
        const double trapped = sediment_trapped(cells, 300.0, 1.0, 10.0, 1.0);
        check(trapped > 0.0 && trapped < yield, "trapped <= yield");
    }

    // ================= Sampling ===========================================
    std::printf("[Sampling (MC vs LHS)]\n");
    {
        // Stratification: each of n LHS samples lies in its own stratum.
        const auto lhs = latin_hypercube(10, 3, 42);
        check(lhs.size() == 10 && lhs[0].size() == 3, "LHS shape");
        std::vector<int> strata(10, 0);
        bool stratified = true;
        for (std::size_t j = 0; j < 3; ++j) {
            std::fill(strata.begin(), strata.end(), 0);
            for (const auto& s : lhs) {
                const int k = static_cast<int>(s[j] * 10.0);
                if (k >= 0 && k < 10) strata[k] = 1;
            }
            for (int k = 0; k < 10; ++k)
                if (strata[k] == 0) stratified = false;
        }
        check(stratified, "LHS: one sample per stratum per dimension");

        // Variance reduction: f(x,y) = x + y, true mean = 1.0 on [0,1]^2.
        // Honest comparison: empirical SE of the 40 replicate means.
        const auto f = [](const std::vector<double>& x) { return x[0] + x[1]; };
        std::vector<double> mc_means, lhs_means;
        mc_means.reserve(40);
        lhs_means.reserve(40);
        constexpr int reps = 40;
        for (int rep = 0; rep < reps; ++rep) {
            const auto m = estimate_mean_mc(f, 2, 100, 1000 + rep);
            const auto l = estimate_mean_lhs(f, 2, 100, 1000 + rep);
            mc_means.push_back(m.first);
            lhs_means.push_back(l.first);
        }
        auto mean_of = [](const std::vector<double>& v) {
            return std::accumulate(v.begin(), v.end(), 0.0) / v.size();
        };
        auto se_of = [&](const std::vector<double>& v) {
            const double mu = mean_of(v);
            double s = 0.0;
            for (double x : v) s += (x - mu) * (x - mu);
            return std::sqrt(s / (v.size() - 1));
        };
        const double mean_mc = mean_of(mc_means);
        const double mean_lhs = mean_of(lhs_means);
        const double se_mc = se_of(mc_means);
        const double se_lhs = se_of(lhs_means);
        check(std::fabs(mean_mc - 1.0) < 0.05, "MC mean accurate");
        check(std::fabs(mean_lhs - 1.0) < 0.05, "LHS mean accurate");
        std::printf("      [info] empirical SE: MC = %.5f, LHS = %.5f, ratio = %.1fx\n",
                    se_mc, se_lhs, se_mc / std::max(se_lhs, 1e-12));
        check(se_lhs < 0.5 * se_mc,
              "LHS reduces standard error >=2x (innovation evidence)");

        // Yield ensemble.
        const YieldStats ys = yield_ensemble_lhs(400.0, 80.0, 20.0, 3.0,
                                                 "wheat", 2000, 7);
        check(ys.mean_kg_ha > 0.0 && ys.p5_kg_ha <= ys.p50_kg_ha &&
                  ys.p50_kg_ha <= ys.p95_kg_ha,
              "yield ensemble order statistics");
        check(ys.failure_probability >= 0.0 && ys.failure_probability <= 1.0,
              "failure probability bounded");
        std::printf("      [info] yield mean=%.0f kg/ha, p5=%.0f, p95=%.0f\n",
                    ys.mean_kg_ha, ys.p5_kg_ha, ys.p95_kg_ha);
    }

    // ================= Regression vs Python Numba ======================
    std::printf("[Regression: C++ vs Python Numba (van Genuchten)]\n");
    {
        // Reference values from engine/hydroma/cpp_bridge/soil_physics_fast.py
        // (correct Mualem-van Genuchten form) for sandy_loam.
        const std::vector<double> h_ref = {-100.0, -158.75, -10.0};
        const std::vector<double> k_ref = {1.89612882e-4, 2.74975225e-5, 5.61044425e-1};
        const std::vector<double> th_ref = {0.12182329, 0.10288729, 0.34309673};
        const auto K = hydraulic_conductivity(h_ref, "sandy_loam");
        const auto th = soil_water_content(h_ref, "sandy_loam");
        bool k_ok = true, th_ok = true;
        for (std::size_t i = 0; i < h_ref.size(); ++i) {
            if (std::fabs(K[i] - k_ref[i]) > 1e-6 * std::max(k_ref[i], 1e-12) + 1e-9)
                k_ok = false;
            if (std::fabs(th[i] - th_ref[i]) > 1e-6)
                th_ok = false;
        }
        check(k_ok, "K matches Python Numba reference (bugfix regression)");
        check(th_ok, "theta matches Python Numba reference");
        std::printf("      [info] K(-100)=%.6e K(-158.75)=%.6e K(-10)=%.6f\n",
                    K[0], K[1], K[2]);
    }

    std::printf("\n%d checks, %d failures\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
