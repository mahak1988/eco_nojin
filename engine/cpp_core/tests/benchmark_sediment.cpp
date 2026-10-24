// benchmark_sediment.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/sediment.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking sediment functions...\n";

    const size_t N_CELLS = 1000 * 1000; // 1 million grid cells
    std::vector<RusleCell> cells(N_CELLS);
    double r_factor = 350.0;
    double cell_area = 1.0; // ha
    double watershed_area = 50.0; // km2

    // Initialize cells with random-ish values
    for(size_t i = 0; i < N_CELLS; ++i) {
        cells[i].k = 0.2 + (i % 100) * 0.001; // Vary K slightly
        cells[i].c = 0.1 + (i % 50) * 0.01;   // Vary C
        cells[i].p = 0.8 + (i % 20) * 0.005;  // Vary P
        cells[i].slope_percent = 2.0 + (i % 200) * 0.01; // Vary slope
        cells[i].slope_length_m = 30.0 + (i % 1000) * 0.1; // Vary length
    }

    // Benchmark rusle_grid (baseline - scalar loop inside)
    std::cout << "Baseline (Parallel rusle_grid inside):\n";
    auto start = std::chrono::high_resolution_clock::now();
    auto losses_scalar = rusle_grid(cells, r_factor);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_scalar = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  rusle_grid (with internal parallel loop) with " << N_CELLS << " cells took: " << duration_scalar.count() << " ms\n";

    // Benchmark rusle_grid_total (includes grid calculation)
    start = std::chrono::high_resolution_clock::now();
    double total_scalar = rusle_grid_total(cells, r_factor, cell_area);
    end = std::chrono::high_resolution_clock::now();
    auto duration_total = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  rusle_grid_total (includes grid calc) with " << N_CELLS << " cells took: " << duration_total.count() << " ms\n";

    if (losses_scalar.size() == N_CELLS && duration_scalar.count() > 0) {
        std::cout << "Benchmark completed successfully. Total erosion approx: " << total_scalar << " t/yr\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}