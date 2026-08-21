// HyDroMa C++ core — 1D Richards solver implementation.
//
// Mixed-form Richards equation (z positive upward):
//     C(h) dh/dt = d/dz [ K(h) (dh/dz + 1) ]
// Cell-centered finite volumes, backward Euler, modified Picard
// (Celia et al. 1990). The linear system at Picard level m is
//     [C^m/dt - D^m] dh = div(q^m) - (theta^m - theta^n)/dt
// where D is the diffusion operator and q = K(dh/dz + 1).
#include "hydroma/richards.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include "hydroma/soil.hpp"

namespace hydroma {

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

// Thomas algorithm (diagonally dominant tridiagonal systems).
void solve_tridiagonal(const std::vector<double>& a,
                       const std::vector<double>& b,
                       const std::vector<double>& c,
                       const std::vector<double>& d, std::vector<double>& x) {
    const std::size_t n = d.size();
    std::vector<double> cp(n, 0.0), dp(n, 0.0);
    if (std::fabs(b[0]) < 1e-300) throw std::runtime_error("tridiagonal: zero pivot");
    cp[0] = c[0] / b[0];
    dp[0] = d[0] / b[0];
    for (std::size_t i = 1; i < n; ++i) {
        const double denom = b[i] - a[i] * cp[i - 1];
        if (std::fabs(denom) < 1e-300) throw std::runtime_error("tridiagonal: zero pivot");
        cp[i] = (i + 1 < n) ? c[i] / denom : 0.0;
        dp[i] = (d[i] - a[i] * dp[i - 1]) / denom;
    }
    x.assign(n, 0.0);
    x[n - 1] = dp[n - 1];
    for (std::size_t i = n - 1; i-- > 0;) x[i] = dp[i] - cp[i] * x[i + 1];
}

}  // namespace

double specific_moisture_capacity(double h_cm, const std::string& texture) {
    return capacity_scalar(h_cm, soil_params(texture));
}

RichardsResult simulate_richards(const std::string& texture,
                                 const std::vector<double>& initial_head_cm,
                                 const RichardsOptions& opts) {
    const SoilTextureParams& p = soil_params(texture);
    const int n = opts.n_cells;
    if (n < 3) throw std::invalid_argument("n_cells must be >= 3");
    if (opts.column_depth_cm <= 0.0) throw std::invalid_argument("depth must be positive");
    if (opts.dt_days <= 0.0 || opts.n_steps < 1) throw std::invalid_argument("bad time grid");

    const double dz = opts.column_depth_cm / n;
    const double dt = opts.dt_days;  // [days]; K is in cm/day, theta dimensionless

    // Cell centers z_i in (-depth, 0); z positive upward, surface at 0.
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

    RichardsResult res;
    res.head_cm.reserve(opts.n_steps + 1);
    res.theta.reserve(opts.n_steps + 1);
    res.head_cm.push_back(h);
    {
        std::vector<double> th(n);
        for (int i = 0; i < n; ++i) th[i] = theta_scalar(h[i], p);
        res.theta.push_back(th);
    }

    auto storage = [&](const std::vector<double>& hh) {
        double s = 0.0;
        for (int i = 0; i < n; ++i) s += theta_scalar(hh[i], p);
        return s * dz;  // cm of water
    };
    res.storage_cm.push_back(storage(h));

    double cum_top = 0.0, cum_bottom = 0.0;
    const double flux_top_cm_day = opts.top_value_cm_day;  // positive downward

    for (int step = 0; step < opts.n_steps; ++step) {
        const std::vector<double> h_old = h;
        bool step_converged = false;
        int iter = 0;

        for (; iter < opts.max_iter; ++iter) {
            std::vector<double> a(n, 0.0), b(n, 0.0), c(n, 0.0), d(n, 0.0);

            for (int i = 0; i < n; ++i) {
                b[i] = capacity_scalar(h[i], p) / dt;
                d[i] = -(theta_scalar(h[i], p) - theta_scalar(h_old[i], p)) / dt;
            }

            // Interior interfaces: matrix coupling + RHS flux divergence.
            // z increases upward and cell i+1 lies BELOW cell i, so
            // dh/dz at the interface = (h[i] - h[i+1]) / dz, and the
            // divergence at cell i is (B_{i-1/2} - B_{i+1/2}) / dz.
            for (int i = 0; i < n - 1; ++i) {
                const double k_avg = intercell_k(k_scalar(h[i], p), k_scalar(h[i + 1], p));
                const double fc = k_avg / (dz * dz);
                b[i] += fc;
                c[i] -= fc;
                a[i + 1] -= fc;
                b[i + 1] += fc;

                const double q_iface = k_avg * ((h[i] - h[i + 1]) / dz + 1.0);
                d[i] -= q_iface / dz;    // lower interface of cell i
                d[i + 1] += q_iface / dz;  // upper interface of cell i+1
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
                // Unit gradient: B = K(h_bottom) (explicit in K; Picard handles it).
                const double q_iface = k_scalar(h[n - 1], p);
                d[n - 1] -= q_iface / dz;
            } else {
                const double h_bc = opts.bottom_head_cm;
                const double k_face = intercell_k(k_scalar(h[n - 1], p), k_scalar(h_bc, p));
                // dh/dz at the bottom face = (h[n-1] - h_bc) / (dz/2).
                const double q_iface = k_face * (2.0 * (h[n - 1] - h_bc) / dz + 1.0);
                d[n - 1] -= q_iface / dz;
                b[n - 1] += 2.0 * k_face / (dz * dz);
            }

            std::vector<double> dh(n);
            try {
                solve_tridiagonal(a, b, c, d, dh);
            } catch (const std::runtime_error&) {
                // Singular system: abort this step (reported as not converged).
                // Diagnostics for the first failing step only.
                if (step == 0) {
                    std::fprintf(stderr,
                                 "[richards] step %d iter %d: singular system; "
                                 "b[0]=%.6g b[n-1]=%.6g C[0]=%.6g\n",
                                 step, iter, b[0], b[n - 1],
                                 capacity_scalar(h[0], p));
                }
                break;
            }

            double max_dh = 0.0;
            for (int i = 0; i < n; ++i) {
                h[i] += dh[i];
                max_dh = std::max(max_dh, std::fabs(dh[i]));
            }
            if (max_dh < opts.tolerance_cm) {
                step_converged = true;
                break;
            }
        }

        res.converged = res.converged && step_converged;
        res.iterations_last_step = iter;

        // Cumulative boundary fluxes [cm of water].
        double q_top = 0.0, q_bottom = 0.0;
        if (opts.top == TopBoundary::Flux) q_top = flux_top_cm_day;
        if (opts.bottom == BottomBoundary::FreeDrainage) {
            q_bottom = k_scalar(h[n - 1], p);  // [cm/day]
        }
        cum_top += q_top * dt;
        cum_bottom += q_bottom * dt;

        res.storage_cm.push_back(storage(h));
        res.cumulative_top_flux_cm.push_back(cum_top);
        res.cumulative_bottom_flux_cm.push_back(cum_bottom);
        res.head_cm.push_back(h);
        std::vector<double> th(n);
        for (int i = 0; i < n; ++i) th[i] = theta_scalar(h[i], p);
        res.theta.push_back(th);
    }

    return res;
}

}  // namespace hydroma
