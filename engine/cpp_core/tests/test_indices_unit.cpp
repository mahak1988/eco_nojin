// test_indices_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/indices.hpp"

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
    std::cout << "Running indices unit tests...\n";

    // Test 1: Scalar NDVI
    std::cout << "[Indices - Scalar NDVI]\n";
    {
        double ndvi_val = ndvi(0.1, 0.8);
        check_close(ndvi_val, (0.8 - 0.1) / (0.8 + 0.1), 1e-10, "NDVI calculation");
        check(ndvi_val >= -1.0 && ndvi_val <= 1.0, "NDVI within range");
        ndvi_val = ndvi(0.5, 0.5); // Zero denominator
        check(ndvi_val == 0.0, "NDVI with zero denominator is 0.0");
    }

    // Test 2: Array NDVI
    std::cout << "[Indices - Array NDVI]\n";
    {
        std::vector<double> red{0.1, 0.2, 0.3};
        std::vector<double> nir{0.8, 0.7, 0.6};
        auto ndvi_arr = ndvi_array(red, nir);

        check(ndvi_arr.size() == red.size(), "Output size matches input");
        check_close(ndvi_arr[0], (0.8 - 0.1) / (0.8 + 0.1), 1e-10, "NDVI[0]");
        check_close(ndvi_arr[1], (0.7 - 0.2) / (0.7 + 0.2), 1e-10, "NDVI[1]");
        check_close(ndvi_arr[2], (0.6 - 0.3) / (0.6 + 0.3), 1e-10, "NDVI[2]");
    }

    // Test 3: Array EVI
    std::cout << "[Indices - Array EVI]\n";
    {
        std::vector<double> red{0.1, 0.15};
        std::vector<double> nir{0.8, 0.75};
        std::vector<double> blue{0.05, 0.06};
        auto evi_arr = evi_array(red, nir, blue);

        double expected_evi0 = 2.5 * (0.8 - 0.1) / (0.8 + 6.0 * 0.1 - 7.5 * 0.05 + 1.0);
        check_close(evi_arr[0], expected_evi0, 1e-10, "EVI[0] calculation");
        check(evi_arr[0] >= -1.0 && evi_arr[0] <= 1.0, "EVI[0] within range");
    }

    // Test 4: Error handling
    std::cout << "[Indices - Error Handling]\n";
    {
        std::vector<double> red{0.1, 0.2};
        std::vector<double> nir{0.8}; // Different size
        bool threw = false;
        try { ndvi_array(red, nir); } catch (...) { threw = true; }
        check(threw, "ndvi_array throws on size mismatch");
    }

    std::cout << "Indices unit tests completed.\n";
    return 0;
}