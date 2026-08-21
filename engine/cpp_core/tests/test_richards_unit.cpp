// test_richards_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/richards.hpp"
#include "hydroma/soil.hpp"

using namespace hydroma;

namespace {
    void check(bool ok, const std::string& msg) {
        if (ok) std::cout << "  [OK] " << msg << "\n";
        else std::cerr << "  [FAIL] " << msg << "\n";
    }
}

int main() {
    std::cout << "Running Richards unit tests...\n";

    std::string texture = "loam";
    RichardsOptions opts{};
    opts.n_cells = 50;
    opts.column_depth_cm = 100.0;
    opts.dt_days = 0.1;
    opts.n_steps = 10;

    // Test 1: Basic simulation run
    std::cout << "[Richards - Basic Run]\n";
    {
        auto result = simulate_richards(texture, {}, opts);
        check(result.converged, "Simulation converged");
        check(result.head_cm.size() == static_cast<size_t>(opts.n_steps), "Correct number of time steps for head");
        check(result.theta.size() == static_cast<size_t>(opts.n_steps), "Correct number of time steps for theta");
        check(!result.head_cm.empty() && !result.head_cm[0].empty(), "Head matrix is populated");
        check(!result.theta.empty() && !result.theta[0].empty(), "Theta matrix is populated");
    }

    // Test 2: Error handling
    std::cout << "[Richards - Error Handling]\n";
    {
        opts.n_cells = 1; // Too small
        bool threw = false;
        try { simulate_richards(texture, {}, opts); } catch (...) { threw = true; }
        check(threw, "Threw exception for n_cells < 3");
    }

    // Test 3: Capacity function
    std::cout << "[Richards - Capacity]\n";
    {
        double cap = specific_moisture_capacity(-50.0, texture);
        check(cap > 0.0, "Capacity is positive for negative head");
        cap = specific_moisture_capacity(0.0, texture);
        check(std::abs(cap) < 1e-10, "Capacity is ~zero for head >= 0");
    }

    std::cout << "Richards unit tests completed.\n";
    return 0;
}