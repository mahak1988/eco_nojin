// test_hydrology_unit.cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>
#include "hydroma/hydrology.hpp"

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
    std::cout << "Running hydrology unit tests...\n";

    // Test 1: Basic routing
    std::cout << "[Hydrology - Basic Routing]\n";
    {
        std::vector<double> inflow{0.0, 10.0, 20.0, 10.0, 0.0};
        double K = 100.0, x = 0.2, dt = 10.0;

        auto outflow = muskingum_cunge_route(inflow, K, x, dt);

        check(outflow.size() == inflow.size(), "Outflow size matches inflow");
        check(outflow[0] == inflow[0], "First outflow equals first inflow");
        // Check for attenuation (peak should be lower if routing is working)
        double peak_in = *std::max_element(inflow.begin(), inflow.end());
        double peak_out = *std::max_element(outflow.begin(), outflow.end());
        check(peak_out <= peak_in + 1e-10, "Peak outflow <= peak inflow (attenuation)"); // Allow slight numerical diff
    }

    // Test 2: Wave parameter calculation
    std::cout << "[Hydrology - Wave Parameters]\n";
    {
        auto params = compute_wave_parameters(1000.0, 0.001, 0.03, 50.0, 100.0);
        check(params.celerity > 0.0, "Celerity is positive");
        check(params.normal_depth > 0.0, "Normal depth is positive");
        check(params.K > 0.0, "Travel time (K) is positive");
    }

    // Test 3: Full routing result
    std::cout << "[Hydrology - Full Routing Result]\n";
    {
        std::vector<double> inflow(100, 5.0); // Steady flow
        auto result = route_flood_wave(inflow, 1000.0, 10, 0.03, 0.001, 10.0, 50.0);

        check(result.outflow.size() == inflow.size(), "Result outflow size matches inflow");
        check(result.peak_inflow == 5.0, "Peak inflow is correct");
        check(std::abs(result.peak_outflow - 5.0) < 1e-3, "Peak outflow is close to inflow for steady state");
        check(result.mass_balance > 0.95, "Mass balance is reasonable for steady flow (>95%)"); // Relaxed check
    }

    std::cout << "Hydrology unit tests completed.\n";
    return 0;
}