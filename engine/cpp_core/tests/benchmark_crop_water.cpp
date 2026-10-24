// benchmark_crop_water.cpp
#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include "hydroma/crop_water.hpp"

using namespace hydroma;

int main() {
    std::cout << "Benchmarking crop water functions...\n";

    const size_t N_DAYS = 365 * 10; // 10 years
    std::vector<double> et0(N_DAYS, 0.0);
    std::vector<double> rain(N_DAYS, 0.0);

    // Generate synthetic weather data
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis_rain_prob(0.0, 1.0);
    std::uniform_int_distribution<> dis_rain_amount(0, 20);

    for(size_t i = 0; i < N_DAYS; ++i) {
        et0[i] = 2.0 + 1.5 * std::sin(2 * M_PI * i / 365); // Seasonal sine wave
        if (dis_rain_prob(gen) < 0.2) { // ~20% chance of rain
            rain[i] = 5.0 + dis_rain_amount(gen); // Random rain amount
        }
    }

    CropWaterParams p{};
    p.kcb_ini = 0.15;
    p.kcb_mid = 1.10;
    p.kcb_end = 0.35;
    p.root_depth_m = 0.6;
    p.theta_fc = 0.32;
    p.theta_wp = 0.15;
    p.p_fraction = 0.55;

    auto start = std::chrono::high_resolution_clock::now();
    auto result = simulate_crop_water(et0, rain, false, p);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "simulate_crop_water for " << N_DAYS << " days (" << (N_DAYS/365) << " years) took: " << duration.count() << " ms\n";
    std::cout << "Total ETc: " << result.total_etc_mm << " mm, Total Irrigation: " << result.total_irrigation_mm << " mm\n";

    if (duration.count() > 0 && result.etc_mm.size() == N_DAYS) {
        std::cout << "Benchmark completed successfully.\n";
    } else {
        std::cerr << "Benchmark failed!\n";
        return 1;
    }
    return 0;
}