// benchmark_erosion.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/erosion.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking erosion functions...\n";

    const size_t N = 2000 * 2000; // Simulate a 2k x 2k grid cell
    std::vector<double> R(N, 120.0);
    std::vector<double> K(N, 0.35);
    std::vector<double> LS(N, 1.1);
    std::vector<double> C(N, 0.15);
    std::vector<double> P(N, 0.9);
    std::vector<double> slope_len(N, 50.0);
    std::vector<double> slope_perc(N, 3.0);
    std::vector<double> rain(N, 900.0);
    std::vector<std::string> textures(N, "loam");

    // Benchmark RUSLE calculation (scalar loop - baseline)
    std::cout << "Baseline (Scalar Loops):\n";
    auto start = std::chrono::high_resolution_clock::now();
    double total_loss = 0.0;
    for(size_t i = 0; i < N; ++i) {
        total_loss += rusle_annual_soil_loss(R[i], K[i], LS[i], C[i], P[i]);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_rusle_scalar = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  rusle_annual_soil_loss (scalar loop) with " << N << " cells took: " << duration_rusle_scalar.count() << " ms\n";

    // Benchmark LS factor (scalar loop - baseline)
    start = std::chrono::high_resolution_clock::now();
    double total_ls = 0.0;
    for(size_t i = 0; i < N; ++i) {
        total_ls += ls_factor(slope_len[i], slope_perc[i]);
    }
    end = std::chrono::high_resolution_clock::now();
    auto duration_ls_scalar = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  ls_factor (scalar loop) with " << N << " cells took: " << duration_ls_scalar.count() << " ms\n";

    // Benchmark NEW parallel functions
    std::cout << "Optimized (Parallel Functions):\n";
    start = std::chrono::high_resolution_clock::now();
    auto losses_parallel = rusle_annual_soil_loss_array(R, K, LS, C, P);
    end = std::chrono::high_resolution_clock::now();
    auto duration_rusle_parallel = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  rusle_annual_soil_loss_array (parallel) with " << N << " cells took: " << duration_rusle_parallel.count() << " ms\n";

    start = std::chrono::high_resolution_clock::now();
    auto ls_parallel = ls_factor_array(slope_len, slope_perc);
    end = std::chrono::high_resolution_clock::now();
    auto duration_ls_parallel = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  ls_factor_array (parallel) with " << N << " cells took: " << duration_ls_parallel.count() << " ms\n";

    start = std::chrono::high_resolution_clock::now();
    auto rain_parallel = estimate_rainfall_erosivity_array(rain);
    end = std::chrono::high_resolution_clock::now();
    auto duration_rain_parallel = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  estimate_rainfall_erosivity_array (parallel) with " << N << " cells took: " << duration_rain_parallel.count() << " ms\n";

    if (duration_rusle_scalar.count() > 0 && duration_ls_scalar.count() > 0 &&
        duration_rusle_parallel.count() > 0 && duration_ls_parallel.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
        std::cout << "Speedup for RUSLE: ~" << (double)duration_rusle_scalar.count() / duration_rusle_parallel.count() << "x\n";
        std::cout << "Speedup for LS Factor: ~" << (double)duration_ls_scalar.count() / duration_ls_parallel.count() << "x\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}