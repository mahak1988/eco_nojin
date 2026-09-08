// HyDroMa C++ core — Nojin Calculator tests
#include <cmath>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

#include "hydroma/nojin_calculator.h"

using namespace hydroma;

namespace {
int g_failures = 0;
int g_checks = 0;

void check(bool ok, const std::string& name) {
    ++g_checks;
    if (!ok) {
        ++g_failures;
        std::printf("  [FAIL] %s\n", name.c_str());
    } else {
        std::printf("  [ ok ] %s\n", name.c_str());
    }
}

void check_close(double a, double b, double tol, const std::string& name) {
    check(std::fabs(a - b) <= tol, name);
}
}  // namespace

int main() {
    std::printf("Nojin Calculator tests\n");

    std::printf("[Biofertilizer efficacy]\n");
    {
        check_close(calculate_biofertilizer_efficacy(5.0, 10.0, 50.0, 7.0, 3.0, "nitrogen_fixer"), 0.75, 1e-12, "nitrogen_fixer base");
        check_close(calculate_biofertilizer_efficacy(5.0, 10.0, 50.0, 5.0, 3.0, "nitrogen_fixer"), 0.5, 1e-12, "nitrogen_fixer low pH");
        check_close(calculate_biofertilizer_efficacy(10.0, 5.0, 50.0, 7.0, 3.0, "phosphate_solubilizer"), 0.75, 1e-12, "phosphate_solubilizer base");
        check_close(calculate_biofertilizer_efficacy(5.0, 5.0, 50.0, 7.0, 3.0, "mycorrhiza"), 0.75, 1e-12, "mycorrhiza base");

        bool threw = false;
        try {
            calculate_biofertilizer_efficacy(5.0, 10.0, 50.0, 7.0, 3.0, "unknown_type");
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "unknown biofert type throws");

        threw = false;
        try {
            calculate_biofertilizer_efficacy(5.0, 10.0, 50.0, 7.0, 3.0, "");
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "empty biofert type throws");
    }

    std::printf("[Yield response]\n");
    {
        std::vector<double> baseline{1000.0, 1100.0, 900.0};
        std::vector<double> efficacy{0.8, 0.9, 0.7};
        const double predicted = predict_yield_response(baseline, efficacy, 50.0, 10.0);
        check(predicted > 1000.0, "predicted yield increases");

        bool threw = false;
        try {
            predict_yield_response({}, efficacy, 50.0, 10.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "empty baseline throws");

        threw = false;
        try {
            predict_yield_response({1.0}, {1.0, 2.0}, 50.0, 10.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "mismatched sizes throw");
    }

    std::printf("\n%d checks, %d failures\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
