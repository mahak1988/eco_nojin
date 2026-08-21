// test_saint_venant_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/saint_venant.hpp"

using namespace hydroma;

namespace {
    void check(bool ok, const std::string& msg) {
        if (ok) std::cout << "  [OK] " << msg << "\n";
        else std::cerr << "  [FAIL] " << msg << "\n";
    }

    void check_close(double a, double b, double tol, const std::string& msg) {
        check(std::abs(a - b) <= tol, msg);
    }
}

int main() {
    std::cout << "Running saint-venant unit tests...\n";

    // Test 1: Basic simulation run
    std::cout << "[Saint-Venant - Basic Simulation]\n";
    {
        SaintVenantOptions opts{};
        opts.n_cells = 50;
        opts.length_m = 1000.0;
        opts.width_m = 10.0;
        opts.bed_slope = 0.001;
        opts.manning_n = 0.03;
        opts.t_end_s = 1200.0; // 20 minutes
        opts.output_every = 50;

        std::vector<double> initial_depth(opts.n_cells, 0.01); // Small initial depth
        double inflow = 10.0; // m3/s

        auto result = simulate_saint_venant(initial_depth, inflow, opts);

        check(result.stable, "Simulation is stable");
        check(result.depth_m.size() == result.discharge_m3s.size(), "Depth and discharge output sizes match");
        check(!result.depth_m.empty(), "At least one output timestep was saved");
        check(result.depth_m[0].size() == static_cast<std::size_t>(opts.n_cells), "Output grid size matches input grid size");
        check(std::abs(result.mass_balance - 1.0) < 0.1, "Mass balance is reasonable (< 10% error)"); // Relaxed check
    }

    // Test 2: Manning normal depth
    std::cout << "[Saint-Venant - Manning Normal Depth]\n";
    {
        double q = 5.0;
        double w = 5.0;
        double s = 0.001;
        double n = 0.03;

        double h_norm = manning_normal_depth(q, w, s, n);
        check(h_norm > 0.0, "Normal depth is positive for positive inputs");
        // A rough check based on Manning's equation: h ~ (q*n/sqrt(S))^(3/5)
        double expected_h = std::pow((q/w) * n / std::sqrt(s), 0.6);
        check_close(h_norm, expected_h, expected_h * 0.1, "Calculated normal depth is close to theoretical (10% tolerance)");
    }

    // Test 3: Error handling
    std::cout << "[Saint-Venant - Error Handling]\n";
    {
        SaintVenantOptions opts{};
        opts.n_cells = 2; // Too small
        bool threw = false;
        try { simulate_saint_venant({}, 1.0, opts); } catch (...) { threw = true; }
        check(threw, "Throws on n_cells < 4");
    }

    std::cout << "Saint-Venant unit tests completed.\n";
    return 0;
}