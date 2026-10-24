// benchmark_sampling.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/sampling.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking sampling functions...\n";

    // Benchmark LHS sample generation
    const size_t N_SAMPLES = 10000;
    const size_t N_DIMS = 5;
    unsigned long long seed = 12345;

    auto start = std::chrono::high_resolution_clock::now();
    auto samples_lhs = latin_hypercube(N_SAMPLES, N_DIMS, seed);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_lhs_gen = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "latin_hypercube generation with " << N_SAMPLES << " samples and " << N_DIMS << " dims took: " << duration_lhs_gen.count() << " ms\n";

    // Benchmark yield ensemble (this calls the loop we want to optimize)
    start = std::chrono::high_resolution_clock::now();
    auto stats = yield_ensemble_lhs(400.0, 50.0, 20.0, 2.0, "wheat", N_SAMPLES, seed);
    end = std::chrono::high_resolution_clock::now();
    auto duration_ensemble = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "yield_ensemble_lhs with " << N_SAMPLES << " samples took: " << duration_ensemble.count() << " ms\n";
    std::cout << "  Mean Yield: " << stats.mean_kg_ha << " kg/ha\n";

    if (samples_lhs.size() == N_SAMPLES && duration_ensemble.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}