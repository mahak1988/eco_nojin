// HyDroMa C++ core — Saint-Venant solver implementation.
#include "hydroma/saint_venant.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

namespace hydroma {

namespace {
constexpr double kG = 9.81;
}

double manning_normal_depth(double discharge_m3s, double width_m,
                            double bed_slope, double manning_n) {
    if (discharge_m3s <= 0.0 || width_m <= 0.0 || bed_slope <= 0.0) return 0.0;
    // q = Q/B ; h = (q n / sqrt(S))^(3/5)
    const double q = discharge_m3s / width_m;
    return std::pow(q * manning_n / std::sqrt(bed_slope), 0.6);
}

SaintVenantResult simulate_saint_venant(const std::vector<double>& initial_depth_m,
                                        double inflow_m3s,
                                        const SaintVenantOptions& opts) {
    if (opts.n_cells < 4) throw std::invalid_argument("n_cells must be >= 4");
    const int n = opts.n_cells;
    const double dx = opts.length_m / n;
    const double B = opts.width_m;
    const double S0 = opts.bed_slope;
    const double nn = opts.manning_n;

    std::vector<double> h(initial_depth_m.size() == static_cast<std::size_t>(n)
                              ? initial_depth_m
                              : std::vector<double>(n, 0.0));
    std::vector<double> q(n, 0.0);

    SaintVenantResult res;
    res.total_volume_initial_m3 = 0.0;
    #pragma omp parallel for reduction(+:res.total_volume_initial_m3)
    for (int i = 0; i < n; ++i) res.total_volume_initial_m3 += h[i] * B * dx;

    const double t_end = opts.t_end_s;
    double t = 0.0;
    const int max_steps = 200000;
    int step = 0;
    bool stable = true;

    while (t < t_end && step < max_steps) {
        // Stability: dt = CFL * dx / max(|u| + sqrt(g h))
        double u_max = 0.0;
        // Parallel reduction to find the maximum value
        #pragma omp parallel for reduction(max:u_max)
        for (int i = 0; i < n; ++i) {
            const double area = B * h[i];
            const double vel = area > 1e-12 ? std::fabs(q[i]) / area : 0.0;
            double local_u_max = vel + std::sqrt(kG * std::max(h[i], 0.0));
            if (local_u_max > u_max) {
                u_max = local_u_max;
            }
        }
        u_max = std::max(u_max, 1e-6);
        const double dt = opts.cfl * dx / u_max;
        if (dt <= 0.0) { stable = false; break; }
        if (t + dt > t_end) { /* allow final partial step */ }

        // Rusanov fluxes at cell interfaces.
        std::vector<double> h_new(n), q_new(n);

        auto flux = [&](int iL, int iR, double& Fh, double& Fq, double& smax) {
            const double hL = std::max(h[iL], 0.0), hR = std::max(h[iR], 0.0);
            const double AL = B * hL, AR = B * hR;
            const double uL = AL > 1e-12 ? q[iL] / AL : 0.0;
            const double uR = AR > 1e-12 ? q[iR] / AR : 0.0;
            const double cL = std::sqrt(kG * hL), cR = std::sqrt(kG * hR);
            const double smax_local = std::max(std::fabs(uL) + cL, std::fabs(uR) + cR) + 1e-9;
            smax = smax_local;

            // Physical fluxes.
            const double FhL = q[iL];
            const double FqL = q[iL] * uL + 0.5 * kG * B * hL * hL;
            const double FhR = q[iR];
            const double FqR = q[iR] * uR + 0.5 * kG * B * hR * hR;

            Fh = 0.5 * (FhL + FhR) - 0.5 * smax * (AR - AL);
            Fq = 0.5 * (FqL + FqR) - 0.5 * smax * (q[iR] - q[iL]);
        };

        // Interior updates (cell i receives fluxes at i-1/2 and i+1/2).
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            double Fh_L, Fq_L, sm_L, Fh_R, Fq_R, sm_R;
            if (i == 0) {
                // Upstream boundary: imposed inflow. Construct ghost state.
                const double hL = std::max(h[0], 0.0);
                const double AL = B * hL;
                const double uL = AL > 1e-12 ? q[0] / AL : 0.0;
                const double cL = std::sqrt(kG * hL);
                double Fh_ghost, Fq_ghost, smax_ghost;
                // Ghost cell: depth h[0], discharge = inflow.
                const double hG = hL, qG = inflow_m3s;
                const double AG = B * hG;
                const double uG = AG > 1e-12 ? qG / AG : 0.0;
                const double cG = std::sqrt(kG * hG);
                smax_ghost = std::max(std::fabs(uL) + cL, std::fabs(uG) + cG) + 1e-9;
                Fh_ghost = 0.5 * (q[0] + qG) - 0.5 * smax_ghost * (AG - AL);
                Fq_ghost = 0.5 * (q[0] * uL + 0.5 * kG * B * hL * hL +
                                  qG * uG + 0.5 * kG * B * hG * hG) -
                           0.5 * smax_ghost * (qG - q[0]);
                Fh_L = Fh_ghost; Fq_L = Fq_ghost; sm_L = smax_ghost;
            } else {
                flux(i - 1, i, Fh_L, Fq_L, sm_L);
            }
            if (i == n - 1) {
                // Downstream: transmissive (zero-gradient) outflow.
                Fh_R = q[n - 1];
                const double hR = std::max(h[n - 1], 0.0);
                const double AR = B * hR;
                const double uR = AR > 1e-12 ? q[n - 1] / AR : 0.0;
                Fq_R = q[n - 1] * uR + 0.5 * kG * B * hR * hR;
                sm_R = 0.0;
            } else {
                flux(i, i + 1, Fh_R, Fq_R, sm_R);
            }

            const double area = B * std::max(h[i], 0.0);
            const double vel = area > 1e-12 ? q[i] / area : 0.0;
            const double Sf = area > 1e-12 && nn > 0.0
                                  ? (nn * nn * vel * std::fabs(vel) /
                                     std::pow(area / B, 4.0 / 3.0))
                                  : 0.0;

            h_new[i] = h[i] - (dt / dx) * (Fh_R - Fh_L);
            q_new[i] = q[i] - (dt / dx) * (Fq_R - Fq_L) +
                       dt * kG * area * (S0 - Sf);
            // Dry-cell regularization: h < 0 => dry; q zeroed.
            if (h_new[i] < opts.dry_tolerance) {
                h_new[i] = 0.0;
                q_new[i] = 0.0;
            }
            if (!std::isfinite(h_new[i]) || !std::isfinite(q_new[i])) {
                // Note: Writing to shared 'stable' flag inside a parallel region is complex.
                // A more robust way would be to use a thread-local flag and reduce it afterwards.
                // For simplicity here, we assume the condition is rare and performance is priority.
                // A critical section could be used: #pragma omp critical
                // But it defeats the purpose of parallelism for this check.
                // Let's assume instability is caught in the next sequential check.
            }
        }

        h = h_new;
        q = q_new;
        t += dt;
        ++step;

        // Check stability after parallel region
        bool local_stable = stable;
        #pragma omp parallel for shared(local_stable)
        for (int i = 0; i < n; ++i) {
            if (!std::isfinite(h[i]) || !std::isfinite(q[i])) {
                local_stable = false;
            }
        }
        stable = local_stable;

        if (!stable) break;
        if (step % opts.output_every == 0) {
            res.time_s.push_back(t);
            res.depth_m.push_back(h);
            res.discharge_m3s.push_back(q);
        }
    }

    res.total_volume_final_m3 = 0.0;
    #pragma omp parallel for reduction(+:res.total_volume_final_m3)
    for (int i = 0; i < n; ++i) res.total_volume_final_m3 += h[i] * B * dx;
    res.mass_balance = res.total_volume_initial_m3 > 0.0
                           ? res.total_volume_final_m3 / res.total_volume_initial_m3
                           : 1.0;
    res.stable = stable;
    // Always expose at least the final state.
    if (res.time_s.empty() || res.time_s.back() < t) {
        res.time_s.push_back(t);
        res.depth_m.push_back(h);
        res.discharge_m3s.push_back(q);
    }
    return res;
}

}  // namespace hydroma
