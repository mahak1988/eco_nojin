// test_erosion_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/erosion.hpp"

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
    std::cout << "Running erosion unit tests...\n";

    // Test 1: Scalar RUSLE
    std::cout << "[Erosion - Scalar RUSLE]\n";
    {
        double loss = rusle_annual_soil_loss(100.0, 0.3, 1.2, 0.1, 0.8);
        check_close(loss, 100.0 * 0.3 * 1.2 * 0.1 * 0.8, 1e-10, "RUSLE calculation");
    }

    // Test 2: LS Factor
    std::cout << "[Erosion - LS Factor]\n";
    {
        double ls = ls_factor(100.0, 5.0); // 5% slope
        check(ls > 0.0, "LS factor is positive");
        // Approximate check for a known case (requires manual calculation or literature)
        // Example: slope=5% (0.05 fraction), length=100m -> LS ~ 1.0
        check(ls < 10.0, "LS factor is reasonable (< 10) for moderate inputs");
    }

    // Test 3: R-Erosivity estimation
    std::cout << "[Erosion - R-Erosivity Estimation]\n";
    {
        double r_est = estimate_rainfall_erosivity(800.0); // Below threshold
        double expected_r_low = 0.04830 * std::pow(800.0, 1.61);
        check_close(r_est, expected_r_low, 1e-6, "R estimated below threshold");

        r_est = estimate_rainfall_erosivity(1000.0); // Above threshold
        double expected_r_high = 587.8 - 1.219 * 1000.0 + 0.004105 * 1000.0 * 1000.0;
        check_close(r_est, expected_r_high, 1e-6, "R estimated above threshold");
    }

    // Test 4: Soil K factor
    std::cout << "[Erosion - Soil K Factor]\n";
    {
        double k = soil_erodibility_k("clay");
        check_close(k, 0.25, 1e-10, "Clay K factor");
        bool threw = false;
        try { soil_erodibility_k("unknown_texture"); } catch (...) { threw = true; }
        check(threw, "K factor throws on unknown texture");
    }

    // Test 5: Error handling
    std::cout << "[Erosion - Error Handling]\n";
    {
        bool threw = false;
        try { rusle_annual_soil_loss(-1.0, 1.0, 1.0, 1.0, 1.0); } catch (...) { threw = true; }
        check(threw, "RUSLE throws on negative input");
    }

    // Test 6: Array RUSLE
    std::cout << "[Erosion - Array RUSLE]\n";
    {
        std::vector<double> R{100.0, 110.0};
        std::vector<double> K{0.3, 0.32};
        std::vector<double> LS{1.2, 1.25};
        std::vector<double> C{0.1, 0.11};
        std::vector<double> P{0.8, 0.78};

        auto losses = rusle_annual_soil_loss_array(R, K, LS, C, P);

        check(losses.size() == R.size(), "Output size matches input");
        check_close(losses[0], 100.0 * 0.3 * 1.2 * 0.1 * 0.8, 1e-10, "RUSLE[0]");
        check_close(losses[1], 110.0 * 0.32 * 1.25 * 0.11 * 0.78, 1e-10, "RUSLE[1]");
    }

    // Test 7: Array LS Factor
    std::cout << "[Erosion - Array LS Factor]\n";
    {
        std::vector<double> len{50.0, 75.0};
        std::vector<double> perc{3.0, 5.0};

        auto ls_vals = ls_factor_array(len, perc);

        check(ls_vals.size() == len.size(), "Output size matches input");
        // Can add more specific checks if needed
        check(ls_vals[0] > 0.0 && ls_vals[1] > 0.0, "Both LS values are positive");
    }

    std::cout << "Erosion unit tests completed.\n";
    return 0;
}