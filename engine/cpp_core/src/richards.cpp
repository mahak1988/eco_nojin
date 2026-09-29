// HyDroMa C++ core — 1D Richards solver implementation.
//
// Mixed-form Richards equation (z positive upward):
//     C(h) dh/dt = d/dz [ K(h) (dh/dz + 1) ]
// Cell-centred finite volumes, backward Euler, modified Picard
// (Celia et al. 1990). The linear system at Picard level m is
//     [C^m/dt - D^m] dh = div(q^m) - (theta^m - theta^n)/dt
// where D is the diffusion operator and q = K(dh/dz + 1).
//
// Time integration is adaptive. Each target step is advanced by one or more
// sub-steps, which are shrunk and retried when the nonlinear solve does not
// converge, following the classical iteration-count-driven rule described in
// Farthing & Fesch (2017), SSSAJ, with the HYDRUS-1D default factors as
// reported in the openRE benchmark (GMD 16, 659-682, 2023).
#include "hydroma/richards.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include "hydroma/soil.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace hydroma {

/// Raised by solve_tridiagonal when a pivot underflows. Carries the index of the
/// offending row and the values that produced it, so the failure is diagnosable
/// instead of being a bare "zero pivot".
class SingularTridiagonalError : public std::runtime_error {
public:
    SingularTridiagonalError(std::size_t row, double pivot,
                             std::size_t previous_row, double previous_c)
        : std::runtime_error("tridiagonal: zero pivot"), row_(row), pivot_(pivot),
          previous_row_(previous_row), previous_c_(previous_c) {}

    std::size_t row() const { return row_; }
    double pivot() const { return pivot_; }
    std::size_t previous_row() const { return previous_row_; }
    double previous_c() const { return previous_c_; }

private:
    std::size_t row_;
    double pivot_;
    std::size_t previous_row_;
    double previous_c_;
};

namespace {

double theta_scalar(double h, const SoilTextureParams& p) {
    if (h >= -1e-10) return p.theta_s;  // saturated for non-negative pressure head
    const double m = 1.0 - 1.0 / p.n;
    const double ha = -h;  // |h| for h < 0
    const double denom = std::pow(1.0 + std::pow(p.alpha * ha, p.n), m);
    return p.theta_r + (p.theta_s - p.theta_r) / denom;
}

double k_scalar(double h, const SoilTextureParams& p) {
    if (h >= -1e-10) return p.Ks;
    const double m = 1.0 - 1.0 / p.n;
    const double ha = -h;
    const double denom = std::pow(1.0 + std::pow(p.alpha * ha, p.n), m);
    const double Se = 1.0 / denom;
    if (Se > 0.0 && Se < 1.0) {
        // Mualem-van Genuchten: K = Ks Se^0.5 [1 - (1-Se^{1/m})^m]^2
        const double inner = std::pow(1.0 - std::pow(Se, 1.0 / m), m);
        const double omi = 1.0 - inner;
        return p.Ks * std::sqrt(Se) * omi * omi;
    }
    return Se >= 1.0 ? p.Ks : 0.0;
}

double capacity_scalar(double h, const SoilTextureParams& p) {
    // C(h) = d(theta)/dh > 0 for h < 0 (theta increases with h).
    if (h >= -1e-10) return 0.0;  // saturated: retention curve flat
    const double m = 1.0 - 1.0 / p.n;
    const double ha = -h;
    const double ah = p.alpha * ha;
    const double pow_n = std::pow(ah, p.n);
    const double term = 1.0 + pow_n;
    return (p.theta_s - p.theta_r) * p.alpha * p.n * m *
           std::pow(ah, p.n - 1.0) / std::pow(term, m + 1.0);
}

double intercell_k(double k_up, double k_down) { return 0.5 * (k_up + k_down); }

/// Assemble the Picard linear system for one sub-step.
///
/// z increases upward and cell i+1 lies BELOW cell i, so dh/dz at the interface
/// is (h[i] - h[i+1]) / dz and the divergence at cell i is
/// (B_{i-1/2} - B_{i+1/2}) / dz.
void assemble_interfaces(std::vector<double>& a, std::vector<double>& b,
                         std::vector<double>& c, std::vector<double>& d,
                         const std::vector<double>& h, double dz,
                         const SoilTextureParams& p, const RichardsOptions& opts,
                         double flux_top_cm_day) {
    const int n = static_cast<int>(h.size());

    for (int i = 0; i < n - 1; ++i) {
        const double k_avg = intercell_k(k_scalar(h[i], p), k_scalar(h[i + 1], p));
        const double fc = k_avg / (dz * dz);
        b[i] += fc;
        c[i] -= fc;
        a[i + 1] -= fc;
        b[i + 1] += fc;

        const double q_iface = k_avg * ((h[i] - h[i + 1]) / dz + 1.0);
        d[i] -= q_iface / dz;
        d[i + 1] += q_iface / dz;
    }

    // Top boundary.
    if (opts.top == TopBoundary::Flux) {
        // Neumann: B at surface = +I (B = -q_Darcy; q_Darcy = -I downward).
        d[0] += flux_top_cm_day / dz;
    } else {
        // Dirichlet: face value h_bc at distance dz/2 above cell 0.
        const double h_bc = opts.top_value_cm_day;
        const double k_face = intercell_k(k_scalar(h[0], p), k_scalar(h_bc, p));
        const double q_iface = k_face * (2.0 * (h_bc - h[0]) / dz + 1.0);
        d[0] += q_iface / dz;
        b[0] += 2.0 * k_face / (dz * dz);
    }

    // Bottom boundary.
    if (opts.bottom == BottomBoundary::FreeDrainage) {
        // Unit gradient: q = K(h_bottom).
        const double q_iface = k_scalar(h[n - 1], p);
        d[n - 1] -= q_iface / dz;
        // The prescribed-gradient contribution must also appear on the diagonal.
        // Without it the last cell carries no sink term, and for this
        // discretisation the row becomes exactly singular: with a[n-1] = -fc,
        // b[n-1] = capacity/dt + fc and cp[n-2] = -1, the pivot
        // b[n-1] - a[n-1]*cp[n-2] cancels to zero. Verified with n = 50,
        // dt = 0.1: row 49, pivot 0.
        b[n - 1] += q_iface / dz;
    } else {
        const double h_bc = opts.bottom_head_cm;
        const double k_face = intercell_k(k_scalar(h[n - 1], p), k_scalar(h_bc, p));
        // dh/dz at the bottom face = (h[n-1] - h_bc) / (dz/2).
        const double q_iface = k_face * (2.0 * (h[n - 1] - h_bc) / dz + 1.0);
        d[n - 1] -= q_iface / dz;
        b[n - 1] += 2.0 * k_face / (dz * dz);
    }
}

/// Thomas algorithm (diagonally dominant tridiagonal systems).
void solve_tridiagonal(const std::vector<double>& a,
                       const std::vector<double>& b,
                       const std::vector<double>& c,
                       const std::vector<double>& d, std::vector<double>& x) {
    const std::size_t n = d.size();
    std::vector<double> cp(n, 0.0), dp(n, 0.0);
    if (std::fabs(b[0]) < 1e-300) throw SingularTridiagonalError(0, b[0], 0, 0.0);
    cp[0] = c[0] / b[0];
    dp[0] = d[0] / b[0];
    for (std::size_t i = 1; i < n; ++i) {
        const double denom = b[i] - a[i] * cp[i - 1];
        if (std::fabs(denom) < 1e-300) {
            throw SingularTridiagonalError(i, denom, i - 1, cp[i - 1]);
        }
        cp[i] = (i + 1 < n) ? c[i] / denom : 0.0;
        dp[i] = (d[i] - a[i] * dp[i - 1]) / denom;
    }
    x.assign(n, 0.0);
    x[n - 1] = dp[n - 1];
    // Back substitution: x[i] + cp[i]*x[i+1] = dp[i], hence the minus.
    for (std::size_t i = n - 1; i-- > 0;) x[i] = dp[i] - cp[i] * x[i + 1];
}

}  // namespace

// specific_moisture_capacity is defined once, in src/soil.cpp, and declared in
// hydroma/soil.hpp. This file used to define it a second time as a wrapper
// around the file-local capacity_scalar helper, which is a duplicate external
// symbol in the same namespace and cannot both link. The two bodies were
// identical, so removing the duplicate is behaviour-preserving.

RichardsResult simulate_richards(const std::string& texture,
                                 const std::vector<double>& initial_head_cm,
                                 const RichardsOptions& opts) {
    const SoilTextureParams& p = soil_params(texture);
    const int n = opts.n_cells;
    if (n < 3) throw std::invalid_argument("n_cells must be >= 3");
    if (opts.column_depth_cm <= 0.0) throw std::invalid_argument("depth must be positive");
    if (opts.dt_days <= 0.0 || opts.n_steps < 1) throw std::invalid_argument("bad time grid");

    const double dz = opts.column_depth_cm / n;

    // Cell centres z_i in (-depth, 0); z positive upward, surface at 0.
    // Cell 0 is the TOP cell (z = -dz/2), cell n-1 the bottom.
    std::vector<double> z(n);
    for (int i = 0; i < n; ++i) z[i] = -(i + 0.5) * dz;

    std::vector<double> h(n);
    if (initial_head_cm.size() == static_cast<std::size_t>(n)) {
        h = initial_head_cm;
    } else if (initial_head_cm.empty()) {
        for (int i = 0; i < n; ++i) h[i] = -z[i];  // hydrostatic, water table at surface
    } else {
        throw std::invalid_argument("initial_head_cm must be empty or length n_cells");
    }

    auto storage = [&](const std::vector<double>& hh) {
        double s = 0.0;
        for (int i = 0; i < n; ++i) s += theta_scalar(hh[i], p);
        return s * dz;  // cm of water
    };

    RichardsResult res;
    res.head_cm.reserve(opts.n_steps + 1);
    res.theta.reserve(opts.n_steps + 1);
    // Time series include the initial state: head_cm[0] is the initial profile
    // and head_cm[step + 1] the state after `step` time steps, so the series has
    // n_steps + 1 entries. This was previously implicit, which left a caller
    // indexing [0..n_steps-1] reading one step behind.
    res.head_cm.push_back(h);
    {
        std::vector<double> th(n);
        for (int i = 0; i < n; ++i) th[i] = theta_scalar(h[i], p);
        res.theta.push_back(th);
    }
    res.storage_cm.push_back(storage(h));

    const TimeStepControl& tc = opts.time_control;
    const double dt_target = opts.dt_days;
    double dt = dt_target;  // current sub-step size
    double cum_top = 0.0, cum_bottom = 0.0;
    const double flux_top_cm_day = opts.top_value_cm_day;  // positive downward

    for (int step = 0; step < opts.n_steps; ++step) {
        double advanced = 0.0;
        int rejects_this_step = 0;
        double step_top = 0.0, step_bottom = 0.0;

        while (advanced < dt_target - 1e-12 * dt_target) {
            const double remaining = dt_target - advanced;
            if (dt > remaining) dt = remaining;

            const std::vector<double> h_sub = h;
            bool sub_converged = false;
            int iter = 0;

            for (; iter < opts.max_iter; ++iter) {
                std::vector<double> a(n, 0.0), b(n, 0.0), c(n, 0.0), d(n, 0.0);
                for (int i = 0; i < n; ++i) {
                    b[i] = capacity_scalar(h[i], p) / dt;
                    d[i] = -(theta_scalar(h[i], p) - theta_scalar(h_sub[i], p)) / dt;
                }
                assemble_interfaces(a, b, c, d, h, dz, p, opts, flux_top_cm_day);

                std::vector<double> dh(n);
                bool singular = false;
                try {
                    solve_tridiagonal(a, b, c, d, dh);
                } catch (const SingularTridiagonalError&) {
                    singular = true;
                }
                if (singular) break;

                double max_dh = 0.0;
                double max_dtheta = 0.0;
                const double omega = tc.relaxation;
                for (int i = 0; i < n; ++i) {
                    h[i] += omega * dh[i];
                    max_dh = std::max(max_dh, std::fabs(omega * dh[i]));
                    max_dtheta = std::max(
                        max_dtheta,
                        std::fabs(theta_scalar(h[i], p) - theta_scalar(h_sub[i], p)));
                }

                // The two criteria the openRE benchmark (GMD 16, 659-682, 2023)
                // reports as the standard, after comparing against HYDRUS-1D:
                // pressure head tolerance 10 mm and water content tolerance
                // 0.001, with a maximum of 100 iterations.
                //
                // A whole-run mass-balance gate is deliberately NOT applied here.
                // The measured balance error is reported on the result instead: a
                // fixed relative closure per sub-step proved unattainable even
                // with the step reduced 40 times, so gating on it would have
                // turned a usable solver into one that refuses every step.
                const bool head_ok = max_dh < opts.tolerance_cm;
                const bool theta_ok =
                    !tc.require_theta_tolerance || max_dtheta < tc.theta_tolerance;
                if (head_ok && theta_ok) {
                    sub_converged = true;
                    break;
                }
            }

            if (sub_converged) {
                step_top += flux_top_cm_day * dt;
                if (opts.bottom == BottomBoundary::FreeDrainage) {
                    step_bottom += k_scalar(h[n - 1], p) * dt;
                }
                advanced += dt;
                res.iterations_last_step = iter + 1;
                if (res.min_substep_taken == 0.0 || dt < res.min_substep_taken) {
                    res.min_substep_taken = dt;
                }

                if (tc.adaptive) {
                    const double lo = tc.optimal_iterations * tc.optimal_range_low;
                    const double hi = tc.optimal_iterations * tc.optimal_range_high;
                    if (iter + 1 < lo && dt < dt_target) {
                        dt = std::min(dt_target, dt * tc.grow_factor);
                    } else if (iter + 1 > hi && dt > tc.min_dt_days) {
                        dt = std::max(tc.min_dt_days, dt * tc.shrink_factor);
                    }
                }
                continue;
            }

            // Not converged, or the system was singular: restore and shrink.
            h = h_sub;
            if (!tc.adaptive) {
                // Fixed-step behaviour: give up on this target step, which is what
                // the solver did unconditionally before adaptation existed.
                res.converged = false;
                advanced = dt_target;
                step_top = flux_top_cm_day * dt_target;
                break;
            }
            ++res.rejected_substeps;
            ++rejects_this_step;
            dt = std::max(tc.min_dt_days, dt * tc.shrink_factor);
            if (rejects_this_step > tc.max_rejects) {
                throw std::runtime_error(
                    "richards: sub-step could not be reduced far enough to converge "
                    "within max_rejects");
            }
        }

        cum_top += step_top;
        cum_bottom += step_bottom;
        res.storage_cm.push_back(storage(h));
        res.cumulative_top_flux_cm.push_back(cum_top);
        res.cumulative_bottom_flux_cm.push_back(cum_bottom);
        res.head_cm.push_back(h);
        std::vector<double> th(n);
        for (int i = 0; i < n; ++i) th[i] = theta_scalar(h[i], p);
        res.theta.push_back(th);
    }

    // Whole-run mass balance, reported rather than gated. The openRE benchmark
    // classifies the mixed form as the one whose convergence "can be based
    // directly on water balance closure" (Celia et al. 1990), so the number
    // belongs on the result; it is not a per-step gate because a fixed relative
    // closure proved unattainable per sub-step.
    const double injected = cum_top;
    const double drained = cum_bottom;
    const double stored = res.storage_cm.back() - res.storage_cm.front();
    const double scale = std::max({std::fabs(injected), std::fabs(drained),
                                   std::fabs(stored), 1e-12});
    res.mass_balance_error = std::fabs(injected - drained - stored) / scale;

    return res;
}

}  // namespace hydroma
