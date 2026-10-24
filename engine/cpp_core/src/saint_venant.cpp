// HyDroMa C++ core — Saint-Venant solver implementation.
#include "hydroma/saint_venant.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
// Add OpenMP header
#include <omp.h>

#include <cstddef>
#include <vector>

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
    // OpenMP reductions cannot name a struct member, and MSVC rejects the
    // `max` operator here, so both reductions run on plain local scalars.
    double volume_initial = 0.0;
    #pragma omp parallel for reduction(+:volume_initial)
    for (int i = 0; i < n; ++i) volume_initial += h[i] * B * dx;
    res.total_volume_initial_m3 = volume_initial;

    const double t_end = opts.t_end_s;
    double t = 0.0;
    const int max_steps = 200000;
    int step = 0;
    bool stable = true;

    while (t < t_end && step < max_steps) {
        // Stability: dt = CFL * dx / max(|u| + sqrt(g h))
        // Manual max reduction: MSVC rejects `reduction(max:...)` on this
        // toolchain, and the previous `if (local > u_max) u_max = local` inside
        // the loop was a data race that silently dropped the true maximum.
        // Stability: dt = CFL * dx / max(|u| + sqrt(g h)).
        //
        // The imposed inflow participates through the ghost state, whose velocity
        // is inflow/(B*h[0]). With a thin sheet that ghost speed is far larger
        // than anything in the interior -- for the unit test's h = 0.01 m it is
        // 100 m/s against an interior maximum of 0.313 -- so excluding it gave a
        // boundary Courant number of about 160, where the scheme needs <= 1.
        // Manual max reduction: MSVC rejects `reduction(max:...)` on this
        // toolchain, and the previous unguarded read-modify-write was a data race.
        double u_max = 0.0;
        #pragma omp parallel for
        for (int i = 0; i < n; ++i) {
            const double area = B * std::max(h[i], 0.0);
            const double vel = area > 1e-12 ? std::fabs(q[i]) / area : 0.0;
            const double local_u_max = vel + std::sqrt(kG * std::max(h[i], 0.0));
            #pragma omp critical
            {
                if (local_u_max > u_max) {
                    u_max = local_u_max;
                }
            }
        }
        if (inflow_m3s > 0.0) {
            const double ghost_area = B * std::max(h[0], opts.dry_tolerance);
            const double ghost_vel = std::fabs(inflow_m3s) / ghost_area;
            u_max = std::max(u_max, ghost_vel + std::sqrt(kG * std::max(h[0], 0.0)));
        }
        u_max = std::max(u_max, 1e-6);
        double dt = opts.cfl * dx / u_max;
        if (dt <= 0.0) { stable = false; break; }
        // Truncate the final step to land exactly on t_end. The previous empty
        // block let the last step overshoot, so the final two output rows could
        // be nearly identical.
        if (t + dt > t_end) { dt = t_end - t; }
        if (dt <= 0.0) { break; }

        // Rusanov fluxes at cell interfaces.
        std::vector<double> h_new(n), q_new(n);
        std::vector<double> bc_left(n, 0.0), bc_right(n, 0.0);
        double Fh_bc_in = 0.0, Fh_bc_out = 0.0;

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
        // Per-cell scratch for the boundary faces and thread-private counters, so
        // nothing is written from several threads at once.
        int dried_this_step = 0;
        int nonfinite_this_step = 0;
        #pragma omp parallel for reduction(+:dried_this_step, nonfinite_this_step)
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

            // Continuity is solved in area form, U = [A, Q] with A = B*h and
            // Fh = [Q, ...] in m3/s. So A_new = A - (dt/dx)(Fh_R - Fh_L), and
            // dividing through by B gives
            //     h_new = h - (dt / (dx * B)) * (Fh_R - Fh_L).
            //
            // The 1/B was missing, so the depth field was transported B times
            // too fast while the momentum equation kept the correct rate. With
            // B = 10 that inflated the volume tenfold (about 900% mass error
            // against a 10% budget) and pushed the effective Courant number to
            // cfl*B = 5.0, which violated positivity at a wet/dry front by a
            // constant factor and diverged geometrically. The test with B = 1
            // passed only because the factor is invisible there.
            h_new[i] = h[i] - (dt / (dx * B)) * (Fh_R - Fh_L);
            q_new[i] = q[i] - (dt / dx) * (Fq_R - Fq_L) +
                       dt * kG * area * (S0 - Sf);
            // Record this cell's boundary faces into per-cell slots. A previous
            // revision captured them in scalars from inside the parallel loop, which
            // was a data race: several threads wrote the same variable and the
            // accumulated boundary flux depended on scheduling, which made the
            // reported mass balance non-deterministic (the dam-break conservation
            // check passed single-threaded 8/8 and failed ~4/8 with threads).
            bc_left[i] = Fh_L;
            bc_right[i] = Fh_R;
            // Dry-cell regularisation. Clamp only genuinely negative depths: the
            // previous threshold was dry_tolerance (1e-4 m), which also discarded
            // legitimately thin wet cells -- and the test's initial sheet is only
            // 0.01 m, 100x that. NaN fails every comparison, so a diverged value
            // would slip past this clamp.
            if (h_new[i] < 0.0) {
                h_new[i] = 0.0;
                q_new[i] = 0.0;
                dried_this_step += 1;
            }
            if (!std::isfinite(h_new[i]) || !std::isfinite(q_new[i])) {
                nonfinite_this_step += 1;
            }
        }

        res.dried_cells += dried_this_step;
        if (nonfinite_this_step > 0) stable = false;
        Fh_bc_in = bc_left[0];
        Fh_bc_out = bc_right[n - 1];

        // Boundary volumes for the conservation residual, accumulated SIGNED.
        //
        // An earlier revision clamped each side with max(flux, 0), which threw
        // away the direction. That is wrong for a balance: when the interior sits
        // below the imposed head, the net upstream flux is outward, and counting
        // it as zero inflow made the residual unrecoverable. On the 50-cell,
        // B = 10 case it reported 87.5 m3 where the boundary should exchange
        // about 12000 m3, because most of the flux was negative and discarded.
        //
        // A balance needs the signed integral at each face; the sign is what
        // distinguishes exchange from no exchange.
        res.cumulative_inflow_m3 += Fh_bc_in * dt;
        res.cumulative_outflow_m3 += Fh_bc_out * dt;

        h = h_new;
        q = q_new;
        t += dt;
        ++step;

        if (res.dried_cells + nonfinite_this_step > 0 && !stable) break;

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

    double volume_final = 0.0;
    #pragma omp parallel for reduction(+:volume_final)
    for (int i = 0; i < n; ++i) volume_final += h[i] * B * dx;
    res.total_volume_final_m3 = volume_final;

    // True conservation residual, replacing the previous metric.
    //
    // `mass_balance` was V_final / V_initial -- a storage ratio, not a balance.
    // With the unit test's inputs (V0 = 100 m3, injected Q*T = 12000 m3, outflow
    // approximately zero) even a perfect solver returns about 121, so the
    // assertion |mass_balance - 1| < 0.1 was unsatisfiable by construction.
    //
    // Conservation is: V_final = V_initial + V_in - V_out, so the residual is
    //     (V_in - V_out) - (V_final - V_initial)
    // The storage term is SUBTRACTED. It was previously added, which turned a
    // balanced run into a reported error of twice the storage change -- on the
    // unit test's case, 521 m3 of real conservation showed up as 1042 m3 of
    // error. A sign error in a balance is worse than a wrong number, because it
    // makes a correct solver look broken.
    res.mass_balance = (res.cumulative_inflow_m3 - res.cumulative_outflow_m3 -
                        (volume_final - res.total_volume_initial_m3));
    const double throughput = std::max(
        {std::fabs(res.cumulative_inflow_m3), std::fabs(res.cumulative_outflow_m3),
         std::fabs(volume_final - res.total_volume_initial_m3), 1.0});
    res.mass_balance_error = std::fabs(res.mass_balance) / throughput;
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
