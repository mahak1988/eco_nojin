// test_crop_water_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/crop_water.hpp"

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
    std::cout << "Running crop water unit tests...\n";

    // Test 1: Basic simulation run
    std::cout << "[Crop Water - Basic Simulation]\n";
    {
        std::vector<double> et0{3.0, 4.0, 2.5, 5.0, 3.5};
        std::vector<double> rain{5.0, 0.0, 10.0, 0.0, 0.0};
        CropWaterParams p{};
        p.kcb_ini = 0.15;
        p.kcb_mid = 1.10;
        p.root_depth_m = 0.5;
        p.theta_fc = 0.35;
        p.theta_wp = 0.15;
        p.p_fraction = 0.5; // RAW = 0.5 * TAW

        auto result = simulate_crop_water(et0, rain, false, p);

        check(result.etc_mm.size() == et0.size(), "Output size matches input");
        check(result.total_etc_mm > 0.0, "Total ETc is positive");
        check(result.total_rain_mm > 0.0, "Total rain is positive");
        // Check water balance error is small
        check(std::abs(result.water_balance_error_mm) < 1e-6, "Water balance error is near zero");
    }

    // Test 2: Auto-irrigation
    std::cout << "[Crop Water - Auto-Irrigation]\n";
    {
        std::vector<double> et0(365, 5.0); // High ET0 for many days
        std::vector<double> rain(365, 0.0); // No rain
        CropWaterParams p{};
        p.kcb_mid = 1.10;
        p.root_depth_m = 0.5;
        p.theta_fc = 0.35;
        p.theta_wp = 0.15;
        p.p_fraction = 0.5;

        auto result_auto = simulate_crop_water(et0, rain, true, p);
        auto result_manual = simulate_crop_water(et0, rain, false, p);

        // Auto-irrigated field should have much higher irrigation and lower stress
        check(result_auto.total_irrigation_mm > result_manual.total_irrigation_mm * 10,
              "Auto-irrigation applies significant water");
        check(result_auto.total_etc_mm > result_manual.total_etc_mm * 0.9, // Allow some difference due to stress
              "Auto-irrigation maintains ETc better");
    }

    // Test 3: Error handling
    std::cout << "[Crop Water - Error Handling]\n";
    {
        std::vector<double> et0{1.0};
        std::vector<double> rain{2.0, 3.0}; // Size mismatch
        CropWaterParams p{};

        bool threw = false;
        try { simulate_crop_water(et0, rain, false, p); } catch (...) { threw = true; }
        check(threw, "Throws on ET0/rain length mismatch");
    }

    std::cout << "Crop water unit tests completed.\n";
    return 0;
}