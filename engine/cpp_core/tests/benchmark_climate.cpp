// benchmark_climate.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include "hydroma/climate.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking climate functions...\n";

    const size_t N = 1000000; // 1 million daily calculations
    std::vector<double> t_min(N, 10.0);
    std::vector<double> t_max(N, 30.0);
    std::vector<double> t_mean(N, 20.0);
    std::vector<double> ra(N, 25.0);
    std::vector<double> rh(N, 45.0);
    std::vector<double> u2(N, 2.0);
    std::vector<double> rs(N, 20.0);
    std::vector<double> elev(N, 100.0);
    std::vector<double> lat(N, 35.0);
    std::vector<int> doy(N, 172);

    // Benchmark Hargreaves (scalar loop - baseline)
    std::cout << "Baseline (Scalar Loops):\n";
    auto start = std::chrono::high_resolution_clock::now();
    double total_et0_hg = 0.0;
    for(size_t i = 0; i < N; ++i) {
        total_et0_hg += hargreaves_et0(t_min[i], t_max[i], t_mean[i], ra[i]);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_hg_scalar = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  hargreaves_et0 (scalar loop) with " << N << " days took: " << duration_hg_scalar.count() << " ms\n";

    // Benchmark Penman-Monteith (scalar loop - baseline)
    start = std::chrono::high_resolution_clock::now();
    double total_et0_pm = 0.0;
    for(size_t i = 0; i < N; ++i) {
        total_et0_pm += penman_monteith_et0(t_min[i], t_max[i], rh[i], u2[i], rs[i], elev[i], lat[i], doy[i]);
    }
    end = std::chrono::high_resolution_clock::now();
    auto duration_pm_scalar = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  penman_monteith_et0 (scalar loop) with " << N << " days took: " << duration_pm_scalar.count() << " ms\n";

    // Benchmark NEW parallel functions
    std::cout << "Optimized (Parallel Functions):\n";
    start = std::chrono::high_resolution_clock::now();
    auto et0_hg_parallel = hargreaves_et0_array(t_min, t_max, t_mean, ra);
    end = std::chrono::high_resolution_clock::now();
    auto duration_hg_parallel = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  hargreaves_et0_array (parallel) with " << N << " days took: " << duration_hg_parallel.count() << " ms\n";

    start = std::chrono::high_resolution_clock::now();
    auto et0_pm_parallel = penman_monteith_et0_array(t_min, t_max, rh, u2, rs, elev, lat, doy);
    end = std::chrono::high_resolution_clock::now();
    auto duration_pm_parallel = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "  penman_monteith_et0_array (parallel) with " << N << " days took: " << duration_pm_parallel.count() << " ms\n";

    if (duration_hg_scalar.count() > 0 && duration_pm_scalar.count() > 0 &&
        duration_hg_parallel.count() > 0 && duration_pm_parallel.count() > 0) {
        std::cout << "Benchmark completed successfully.\n";
        std::cout << "Speedup for Hargreaves: ~" << (double)duration_hg_scalar.count() / duration_hg_parallel.count() << "x\n";
        std::cout << "Speedup for Penman-Monteith: ~" << (double)duration_pm_scalar.count() / duration_pm_parallel.count() << "x\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}