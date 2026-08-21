// benchmark_soil_extended.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/soil.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking extended soil physics functions...\n";

    const size_t N = 10000000; // 10 million elements
    std::vector<double> h_matric(N, -50.0); // Unsaturated, negative head
    std::string texture = "loam";

    // Benchmark new capacity function
    auto start = std::chrono::high_resolution_clock::now();
    auto capacity_result = specific_moisture_capacity_array(h_matric, texture);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_capacity = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "specific_moisture_capacity_array with " << N << " elements took: " << duration_capacity.count() << " ms\n";

    // Compare with old functions
    start = std::chrono::high_resolution_clock::now();
    auto theta_result = soil_water_content(h_matric, texture);
    end = std::chrono::high_resolution_clock::now();
    auto duration_theta = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "soil_water_content (parallel) with " << N << " elements took: " << duration_theta.count() << " ms\n";

    start = std::chrono::high_resolution_clock::now();
    auto k_result = hydraulic_conductivity(h_matric, texture);
    end = std::chrono::high_resolution_clock::now();
    auto duration_k = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "hydraulic_conductivity (parallel) with " << N << " elements took: " << duration_k.count() << " ms\n";

    std::cout << "Total time for all three parallel functions: " << (duration_capacity.count() + duration_theta.count() + duration_k.count()) << " ms\n";

    if (capacity_result.size() == N && duration_capacity.count() > 0) {
        std::cout << "Extended benchmark completed successfully.\n";
    } else {
        std::cerr << "Extended benchmark failed!\n";
        return 1;
    }
    return 0;
}