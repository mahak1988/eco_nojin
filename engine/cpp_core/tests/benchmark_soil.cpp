// benchmark_soil.cpp
// Simple benchmark for soil physics functions.
#include <chrono>
#include <iostream>
#include <vector>
#include "hydroma/soil.hpp"

using namespace hydroma;

int main() {
    const size_t N = 1000000; // 1 million elements
    std::vector<double> h_matric(N, 50.0); // Simulate a large array of potentials
    std::string texture = "loam";

    std::cout << "Benchmarking soil physics functions with " << N << " elements...\n";

    // Benchmark soil_water_content
    auto start = std::chrono::high_resolution_clock::now();
    auto theta = soil_water_content(h_matric, texture);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_theta = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "soil_water_content took: " << duration_theta.count() << " ms\n";

    // Benchmark hydraulic_conductivity
    start = std::chrono::high_resolution_clock::now();
    auto k = hydraulic_conductivity(h_matric, texture);
    end = std::chrono::high_resolution_clock::now();
    auto duration_k = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "hydraulic_conductivity took: " << duration_k.count() << " ms\n";

    std::cout << "Total time: " << (duration_theta.count() + duration_k.count()) << " ms\n";

    // Optional: Verify results are non-zero
    if (!theta.empty() && !k.empty() && theta[0] > 0.0 && k[0] > 0.0) {
        std::cout << "Benchmark completed successfully. Results seem valid.\n";
    } else {
        std::cerr << "Error: Unexpected zero or empty results!\n";
        return 1;
    }
    return 0;
}