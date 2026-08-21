// benchmark_saint_venant.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/saint_venant.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking saint-venant functions...\n";

    SaintVenantOptions opts{};
    opts.n_cells = 500; // Larger mesh
    opts.length_m = 5000.0;
    opts.width_m = 20.0;
    opts.bed_slope = 0.0005;
    opts.manning_n = 0.035;
    opts.t_end_s = 3600.0; // 1 hour
    opts.output_every = 100;

    std::vector<double> initial_depth(opts.n_cells, 0.05); // Small initial depth
    double inflow = 50.0; // m3/s

    auto start = std::chrono::high_resolution_clock::now();
    auto result = simulate_saint_venant(initial_depth, inflow, opts);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "simulate_saint_venant with " << opts.n_cells << " cells and " << opts.t_end_s << " seconds runtime took: " << duration.count() << " ms\n";
    std::cout << "Final state stable: " << (result.stable ? "Yes" : "No") << ", Mass balance: " << result.mass_balance << "\n";

    if (result.stable && duration.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}