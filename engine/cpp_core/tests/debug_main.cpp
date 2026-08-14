// Quick debug harness for Richards + crop water balance.
#include <cmath>
#include <cstdio>
#include <vector>

#include "hydroma/crop_water.hpp"
#include "hydroma/richards.hpp"

using namespace hydroma;

int main() {
    // --- Richards infiltration debug ---
    {
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
        const RichardsResult r = simulate_richards("sandy_loam", h_dry, inf);
        std::printf("RICHARDS: converged=%d iters_last=%d\n", r.converged ? 1 : 0,
                    r.iterations_last_step);
        std::printf("  storage: %.4f -> %.4f (ds=%.4f)\n", r.storage_cm.front(),
                    r.storage_cm.back(), r.storage_cm.back() - r.storage_cm.front());
        std::printf("  cum top=%.4f bottom=%.4f net=%.4f\n",
                    r.cumulative_top_flux_cm.back(),
                    r.cumulative_bottom_flux_cm.back(),
                    r.cumulative_top_flux_cm.back() -
                        r.cumulative_bottom_flux_cm.back());
        std::printf("  theta top: %.4f -> %.4f ; head top: %.3f -> %.3f\n",
                    r.theta.front()[0], r.theta.back()[0], r.head_cm.front()[0],
                    r.head_cm.back()[0]);
        std::printf("  head bottom: %.3f -> %.3f\n", r.head_cm.front()[59],
                    r.head_cm.back()[59]);
        std::printf("  profile (depth cm | theta):\n");
        for (int i = 0; i < 60; i += 6) {
            std::printf("    z=%.1f theta %.3f -> %.3f (head %.1f -> %.1f)\n",
                        -(i + 0.5) * 2.5, r.theta.front()[i], r.theta.back()[i],
                        r.head_cm.front()[i], r.head_cm.back()[i]);
        }
        // water content change per layer
        double wet_total = 0.0, dry_total = 0.0;
        for (int i = 0; i < 60; ++i) {
            const double dth = r.theta.back()[i] - r.theta.front()[i];
            if (dth > 0) wet_total += dth * 2.5;
            else dry_total += dth * 2.5;
        }
        std::printf("  wet gain=%.3f cm, dry loss=%.3f cm\n", wet_total,
                    dry_total);
        std::printf("  per-step top cell (theta | head | B_iface):\n");
        for (int s = 0; s <= 120; s += 10) {
            // Recompute interface flux B = K_avg*((h0-h1)/dz + 1) in cm/day.
            double k0 = 0.0, k1 = 0.0;
            // (mirror of soil van Genuchten K; approximate via helper below)
            const double dz = 2.5;
            double ha0 = -r.head_cm[s][0];
            if (r.head_cm[s][0] >= -1e-10) { k0 = 4.42; } else {
                const double ah = 0.075 * ha0;
                const double Se = 1.0 / std::pow(1.0 + std::pow(ah, 1.89), 1.0 - 1.0 / 1.89);
                const double m = 1.0 - 1.0 / 1.89;
                k0 = 4.42 * std::sqrt(Se) *
                     std::pow(1.0 - std::pow(1.0 - std::pow(Se, 1.0 / m), m), 2.0);
            }
            double ha1 = -r.head_cm[s][1];
            if (r.head_cm[s][1] >= -1e-10) { k1 = 4.42; } else {
                const double ah = 0.075 * ha1;
                const double Se = 1.0 / std::pow(1.0 + std::pow(ah, 1.89), 1.0 - 1.0 / 1.89);
                const double m = 1.0 - 1.0 / 1.89;
                k1 = 4.42 * std::sqrt(Se) *
                     std::pow(1.0 - std::pow(1.0 - std::pow(Se, 1.0 / m), m), 2.0);
            }
            const double kavg = 0.5 * (k0 + k1);
            const double b_iface = kavg * ((r.head_cm[s][0] - r.head_cm[s][1]) / dz + 1.0);
            std::printf("    step %3d: theta %.4f head %.2f B_iface %.6g\n", s,
                        r.theta[s][0], r.head_cm[s][0], b_iface);
        }
    }

    // --- Crop water debug ---
    {
        const int nd = 120;
        std::vector<double> et0(nd, 5.0), rain(nd, 0.0);
        for (int i = 20; i < 25; ++i) rain[i] = 15.0;
        CropWaterParams p;
        const CropWaterResult r = simulate_crop_water(et0, rain, false, p);
        std::printf("CROP: P=%.2f I=%.2f ETc=%.2f DP=%.2f dr_final=%.2f "
                    "wb_err=%.4f\n",
                    r.total_rain_mm, r.total_irrigation_mm, r.total_etc_mm,
                    r.total_dp_mm, r.depletion_mm.back(),
                    r.water_balance_error_mm);
        std::printf("  day10: dep=%.2f stress=%.3f kc=%.3f | day119: dep=%.2f "
                    "stress=%.3f kc=%.3f\n",
                    r.depletion_mm[10], r.stress_factor[10], r.kc_effective[10],
                    r.depletion_mm[119], r.stress_factor[119],
                    r.kc_effective[119]);
        // manual closure recompute
        double etc_sum = 0, ke_sum = 0, kcbks_sum = 0;
        for (int d = 0; d < nd; ++d) {
            etc_sum += r.etc_mm[d];
        }
        std::printf("  expected imbalance (2*dp): %.4f\n", 2.0 * r.total_dp_mm);
    }
    return 0;
}
