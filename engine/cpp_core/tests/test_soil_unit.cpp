// test_soil_unit.cpp
// HyDroMa C++ core - Unit tests for soil physics module.
#include <cmath>
#include <cstdio>
#include <iostream>
#include <vector>
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
        std::printf("  [ OK ] %s\n", name.c_str());
    }
}

void check_close(double a, double b, double tol, const std::string& name) {
    check(std::abs(a - b) <= tol, name);
}

} // namespace

int main() {
    std::printf("Running soil physics unit tests...\n");

    // Test 1: Valid texture and basic behavior
    std::printf("[Soil Physics - Basic]\n");
    {
        std::vector<double> h = {0.0, 10.0, 100.0, 1000.0}; // Matric potential (cm)
        std::string texture = "loam";

        auto theta = soil_water_content(h, texture);
        auto k = hydraulic_conductivity(h, texture);

        // Check sizes
        check(theta.size() == h.size(), "Theta vector size matches input");
        check(k.size() == h.size(), "K vector size matches input");

        // Check boundary conditions
        const auto& p = soil_params(texture);
        check_close(theta[0], p.theta_s, 1e-10, "theta(h=0) = theta_s");
        check_close(k[0], p.Ks, 1e-10, "K(h=0) = Ks");

        // Check monotonicity (water content decreases with increasing suction)
        check(theta[0] >= theta[1] && theta[1] >= theta[2] && theta[2] >= theta[3],
              "theta decreases monotonically with suction");
        // Check conductivity monotonicity
        check(k[0] >= k[1] && k[1] >= k[2] && k[2] >= k[3],
              "K decreases monotonically with suction");

        // Check bounds
        for (double t : theta) {
            check(t >= p.theta_r - 1e-10 && t <= p.theta_s + 1e-10, "theta within bounds [theta_r, theta_s]");
        }
        for (double cond : k) {
            check(cond >= 0.0 && cond <= p.Ks + 1e-10, "K within bounds [0, Ks]");
        }
    }

    // Test 2: Invalid texture handling
    std::printf("[Soil Physics - Error Handling]\n");
    {
        std::vector<double> h = {10.0};
        bool exception_thrown = false;
        try {
            auto invalid_theta = soil_water_content(h, "invalid_texture");
        } catch (const std::invalid_argument&) {
            exception_thrown = true;
        }
        check(exception_thrown, "Exception thrown for invalid texture in soil_water_content");

        exception_thrown = false;
        try {
            auto invalid_k = hydraulic_conductivity(h, "invalid_texture_2");
        } catch (const std::invalid_argument&) {
            exception_thrown = true;
        }
        check(exception_thrown, "Exception thrown for invalid texture in hydraulic_conductivity");
    }

    // Test 3: Edge case - very high suction -> theta -> theta_r, K -> 0
    std::printf("[Soil Physics - Asymptotic Behavior]\n");
    {
        std::vector<double> h = {1e10}; // Very high suction
        std::string texture = "clay";
        const auto& p = soil_params(texture);

        auto theta = soil_water_content(h, texture);
        auto k = hydraulic_conductivity(h, texture);

        check_close(theta[0], p.theta_r, 1e-6, "theta -> theta_r at very high suction");
        check_close(k[0], 0.0, 1e-12, "K -> 0 at very high suction");
    }

    // Test 4: Specific Moisture Capacity
    std::printf("[Soil Physics - Capacity]\n");
    {
        std::vector<double> h = {-10.0, -100.0}; // Negative matric potential (unsaturated)
        std::string texture = "loam";
        auto caps = specific_moisture_capacity_array(h, texture);

        check(caps.size() == h.size(), "Capacity array size matches input");
        for (double cap : caps) {
            check(cap > 0.0, "Capacity is positive for unsaturated head");
        }

        // Test scalar version consistency
        double cap_scalar = specific_moisture_capacity(h[0], texture);
        check_close(caps[0], cap_scalar, 1e-12, "Array version matches scalar version");
    }

    // Test 5: Capacity at saturation
    std::printf("[Soil Physics - Capacity at Saturation]\n");
    {
        std::vector<double> h_sat = {0.0, 1.0}; // At or above saturation
        std::string texture = "sand";
        auto caps_sat = specific_moisture_capacity_array(h_sat, texture);

        for (double cap : caps_sat) {
            check(std::abs(cap) < 1e-10, "Capacity is ~zero at saturation (h >= 0)");
        }
    }


    if (g_failures == 0) {
        std::printf("\nAll %d soil physics tests PASSED.\n", g_checks);
    } else {
        std::printf("\n%d out of %d soil physics tests FAILED.\n", g_failures, g_checks);
        return 1;
    }

    return 0;
}