// test_climate_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/climate.hpp"

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
    std::cout << "Running climate unit tests...\n";

    // Test 1: Hargreaves ET0
    std::cout << "[Climate - Hargreaves ET0]\n";
    {
        double et0 = hargreaves_et0(10.0, 30.0, 20.0, 25.0);
        check(et0 > 0.0, "ET0 is positive");
        // Approximate check (literature values vary)
        check(et0 < 10.0, "ET0 is reasonable (< 10 mm/day)");
    }

    // Test 2: Extraterrestrial Radiation
    std::cout << "[Climate - Extraterrestrial Radiation]\n";
    {
        double ra = extraterrestrial_radiation(35.0, 172); // Summer solstice, mid-lat
        check(ra > 0.0, "Ra is positive");
        check(ra > 30.0, "Ra is high in summer (~35 MJ/m2/day)");
    }

    // Test 3: Penman-Monteith ET0 (simple case)
    std::cout << "[Climate - Penman-Monteith ET0]\n";
    {
        double et0_pm = penman_monteith_et0(15.0, 35.0, 45.0, 2.0, 20.0, 100.0, 35.0, 172);
        check(et0_pm > 0.0, "PM ET0 is positive");
        // PM is usually higher than Hargreaves
        double et0_hg = hargreaves_et0(15.0, 35.0, 25.0, 20.0);
        check(et0_pm >= et0_hg * 0.8, "PM ET0 is typically higher than Hargreaves (allowing for variation)");
    }

    // Test 4: Error handling
    std::cout << "[Climate - Error Handling]\n";
    {
        bool threw = false;
        try { hargreaves_et0(30.0, 10.0, 20.0, 25.0); } catch (...) { threw = true; }
        check(threw, "Hargreaves throws on t_max < t_min");
    }

    // Test 5: Array Hargreaves ET0
    std::cout << "[Climate - Array Hargreaves ET0]\n";
    {
        std::vector<double> t_min{10.0, 12.0};
        std::vector<double> t_max{30.0, 32.0};
        std::vector<double> t_mean{20.0, 22.0};
        std::vector<double> ra{25.0, 26.0};

        auto et0_arr = hargreaves_et0_array(t_min, t_max, t_mean, ra);

        check(et0_arr.size() == t_min.size(), "Output size matches input");
        check(et0_arr[0] > 0.0 && et0_arr[1] > 0.0, "Both ET0 values are positive");
        // Compare with scalar calculation
        check_close(et0_arr[0], hargreaves_et0(t_min[0], t_max[0], t_mean[0], ra[0]), 1e-10, "Array[0] matches scalar");
        check_close(et0_arr[1], hargreaves_et0(t_min[1], t_max[1], t_mean[1], ra[1]), 1e-10, "Array[1] matches scalar");
    }

    std::cout << "Climate unit tests completed.\n";
    return 0;
}