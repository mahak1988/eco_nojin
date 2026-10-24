// benchmark_hydrology.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/hydrology.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking hydrology functions...\n";

    const int N = 50000; // Large hydrograph
    std::vector<double> inflow(N, 0.0);
    // Create a simple triangular hydrograph
    for (int i = 0; i < N / 2; ++i) {
        inflow[i] = static_cast<double>(i) * 100.0 / (N / 2);
    }
    for (int i = N / 2; i < N; ++i) {
        inflow[i] = inflow[N - 1 - i];
    }

    // Benchmark Muskingum-Cunge routing
    auto start = std::chrono::high_resolution_clock::now();
    auto outflow = muskingum_cunge_route(inflow, 1000.0, 0.2, 30.0);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_mc = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "muskingum_cunge_route with " << N << " steps took: " << duration_mc.count() << " ms\n";

    // Benchmark full routing
    start = std::chrono::high_resolution_clock::now();
    auto result = route_flood_wave(inflow, 5000.0, 50, 0.04, 0.0005, 30.0, 100.0);
    end = std::chrono::high_resolution_clock::now();
    auto duration_full = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "route_flood_wave with " << N << " steps took: " << duration_full.count() << " ms\n";

    if (result.outflow.size() == N && duration_mc.count() > 0 && duration_full.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}