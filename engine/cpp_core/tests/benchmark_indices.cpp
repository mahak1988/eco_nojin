// benchmark_indices.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/indices.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking indices functions...\n";

    const size_t N = 4000 * 4000; // Simulate a 4k x 4k image band
    std::vector<double> red(N, 0.1);
    std::vector<double> nir(N, 0.8);
    std::vector<double> blue(N, 0.05);
    std::vector<double> green(N, 0.2);
    std::vector<double> swir(N, 0.3);

    // Benchmark NDVI array
    auto start = std::chrono::high_resolution_clock::now();
    auto ndvi_result = ndvi_array(red, nir);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_ndvi = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "ndvi_array with " << N << " pixels took: " << duration_ndvi.count() << " ms\n";

    // Benchmark EVI array
    start = std::chrono::high_resolution_clock::now();
    auto evi_result = evi_array(red, nir, blue);
    end = std::chrono::high_resolution_clock::now();
    auto duration_evi = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "evi_array with " << N << " pixels took: " << duration_evi.count() << " ms\n";

    // Benchmark SAVI array
    start = std::chrono::high_resolution_clock::now();
    auto savi_result = savi_array(red, nir, 0.5);
    end = std::chrono::high_resolution_clock::now();
    auto duration_savi = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "savi_array with " << N << " pixels took: " << duration_savi.count() << " ms\n";

    if (ndvi_result.size() == N && duration_ndvi.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}