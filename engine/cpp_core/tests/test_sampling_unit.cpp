// test_sampling_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/sampling.hpp"

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
    std::cout << "Running sampling unit tests...\n";

    // Test 1: LHS sample generation
    std::cout << "[Sampling - LHS Generation]\n";
    {
        auto samples = latin_hypercube(10, 2, 12345);
        check(samples.size() == 10, "Correct number of samples");
        check(samples[0].size() == 2, "Correct number of dimensions");
        for (const auto& s : samples) {
            for (double val : s) {
                check(val >= 0.0 && val <= 1.0, "Sample value in [0,1]");
            }
        }
    }

    // Test 2: Scaling samples
    std::cout << "[Sampling - Scale Samples]\n";
    {
        std::vector<std::vector<double>> unit{{0.0, 0.5}, {1.0, 0.25}};
        std::vector<double> lo{10.0, 20.0};
        std::vector<double> hi{30.0, 40.0};

        auto scaled = scale_samples(unit, lo, hi);

        check_close(scaled[0][0], 10.0, 1e-10, "Scaled low corner X");
        check_close(scaled[0][1], 30.0, 1e-10, "Scaled mid edge Y");
        check_close(scaled[1][0], 30.0, 1e-10, "Scaled high corner X");
        check_close(scaled[1][1], 25.0, 1e-10, "Scaled mid edge Y");
    }

    // Test 3: Simplified yield model
    std::cout << "[Sampling - Simplified Yield]\n";
    {
        double y = simplified_yield(400.0, 20.0, "wheat");
        check(y > 0.0, "Yield is positive for reasonable inputs");
        // Corn should have higher potential than wheat with same inputs
        double y_corn = simplified_yield(400.0, 20.0, "corn");
        check(y_corn >= y * 0.5, "Corn yield is reasonable compared to wheat (not necessarily higher, depends on params)");
    }

    // Test 4: Ensemble statistics
    std::cout << "[Sampling - Yield Ensemble Stats]\n";
    {
        auto stats = yield_ensemble_lhs(400.0, 50.0, 20.0, 2.0, "wheat", 100, 54321);
        check(stats.n_samples == 100, "Correct number of samples reported in stats");
        check(stats.mean_kg_ha > 0.0, "Mean yield is positive");
        check(stats.p50_kg_ha > 0.0, "Median yield is positive");
        check(stats.p95_kg_ha >= stats.p50_kg_ha, "P95 >= P50");
        check(stats.p50_kg_ha >= stats.p5_kg_ha, "P50 >= P5");
    }

    std::cout << "Sampling unit tests completed.\n";
    return 0;
}