// test_sediment_unit.cpp
#include <iostream>
#include <vector>
#include <cmath>
#include "hydroma/sediment.hpp"
#include "hydroma/erosion.hpp" // For ls_factor if needed

using namespace hydroma;

namespace {
    void check(bool ok, const std::string& msg) {
        if (ok) std::cout << "  [OK] " << msg << "\n";
        else std::cerr << "  [FAIL] " << msg << "\n";
    }

    void check_close(double a, double b, double tol, const std::string& msg) {
        check(std::abs(a - b) <= tol, msg);
    }
}

int main() {
    std::cout << "Running sediment unit tests...\n";

    // Test 1: Basic rusle_grid
    std::cout << "[Sediment - Basic RUSLE Grid]\n";
    {
        std::vector<RusleCell> cells(3);
        cells[0].k = 0.35; cells[0].c = 0.1; cells[0].p = 0.9; cells[0].slope_percent = 3.0; cells[0].slope_length_m = 50.0;
        cells[1].k = 0.25; cells[1].c = 0.8; cells[1].p = 1.0; cells[1].slope_percent = 10.0; cells[1].slope_length_m = 30.0;
        cells[2].k = 0.40; cells[2].c = 0.05; cells[2].p = 0.8; cells[2].slope_percent = 1.0; cells[2].slope_length_m = 100.0;

        double r = 250.0;
        auto losses = rusle_grid(cells, r);

        check(losses.size() == cells.size(), "Output size matches input");
        check(losses[0] > 0.0 && losses[1] > 0.0 && losses[2] > 0.0, "All losses are positive");
        // Check that high C (cover) leads to lower loss (comparing cell 0 vs 1, other things being less different)
        check(losses[1] >= losses[0], "Higher C factor (0.8 vs 0.1) leads to higher loss (when other factors compensate)");
    }

    // Test 2: rusle_grid_total
    std::cout << "[Sediment - RUSLE Grid Total]\n";
    {
        std::vector<RusleCell> cells(2);
        cells[0].k = 0.3; cells[0].c = 0.5; cells[0].p = 1.0; cells[0].slope_percent = 5.0; cells[0].slope_length_m = 50.0;
        cells[1] = cells[0]; // Same cell
        double r = 300.0;
        double area = 0.5; // ha per cell

        auto losses = rusle_grid(cells, r);
        double total_from_grid = 0.0;
        for (double l : losses) total_from_grid += l * area;

        double total_calc = rusle_grid_total(cells, r, area);

        check_close(total_from_grid, total_calc, 1e-10, "rusle_grid_total matches sum of grid * area");
    }

    // Test 3: Sediment Delivery Ratio
    std::cout << "[Sediment - Sediment Delivery Ratio]\n";
    {
        double sdr = sediment_delivery_ratio(10.0); // Default params
        check(sdr > 0.0 && sdr < 1.0, "SDR is between 0 and 1");
        double sdr_large = sediment_delivery_ratio(1000.0); // Larger area -> lower SDR
        check(sdr_large < sdr, "Larger watershed has lower SDR");
    }

    // Test 4: Trap Efficiency
    std::cout << "[Sediment - Trap Efficiency]\n";
    {
        double te = trap_efficiency_brune(1.0); // Default k=0.15
        check(te > 0.0 && te < 1.0, "Trap efficiency is between 0 and 1");
        double te_high = trap_efficiency_brune(10.0); // Higher C/I -> higher TE
        check(te_high > te, "Higher C/I ratio leads to higher trap efficiency");
    }

    // Test 5: Error handling
    std::cout << "[Sediment - Error Handling]\n";
    {
        bool threw = false;
        try { rusle_grid({}, -1.0); } catch (...) { threw = true; }
        check(threw, "rusle_grid throws on negative R factor");
    }

    std::cout << "Sediment unit tests completed.\n";
    return 0;
}