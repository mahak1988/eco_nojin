// benchmark_richards.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/richards.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking Richards solver...\n";

    std::string texture = "clay_loam";
    RichardsOptions opts{};
    opts.n_cells = 200; // Larger mesh
    opts.column_depth_cm = 200.0;
    opts.dt_days = 0.05;
    opts.n_steps = 500; // More steps
    opts.top_value_cm_day = 0.5; // Infiltration

    auto start = std::chrono::high_resolution_clock::now();
    auto result = simulate_richards(texture, {}, opts);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "simulate_richards with " << opts.n_cells << " cells and " << opts.n_steps << " steps took: " << duration.count() << " ms\n";
    std::cout << "Converged: " << (result.converged ? "Yes" : "No") << ", Last step iterations: " << result.iterations_last_step << "\n";

    if (result.converged && duration.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}