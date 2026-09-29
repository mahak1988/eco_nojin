// HyDroMa C++ core — Nojin suitability tests
//
// These replace the four "efficacy" checks that previously asserted 0.75, 0.50,
// 0.75 and 0.75. Investigation established those four numbers could not be
// produced by any consistent version of the removed formula:
//
//   * three "base" cases shared identical structural inputs yet expected one
//     value, while the implementation's three type branches returned three
//     different values (0.400, 0.375, 0.000);
//   * a multiplicative model needs f(7)/f(5) = 1.5 between the two
//     nitrogen_fixer cases, and none of six conventional pH responses gives it;
//   * 0.75 -> 0.50 is not a halving, so the two expectations were not even
//     mutually consistent.
//
// The closed-form efficacy model was removed because no standard defines one:
// ISO 17088, ISO 8268:1989, the FAO Guidelines (2016) and national fertilizer
// orders are product-quality standards, and efficacy is a measured quantity
// (15N methods reported as %Ndfa, or the yield/NUE/PUE response).
//
// What is tested now is a suitability screen against published pH ranges.

#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <vector>

#include "hydroma/nojin_calculator.hpp"

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
    std::printf("Nojin suitability tests\n");

    std::printf("[Published pH ranges]\n");
    {
        double lo = 0.0, hi = 0.0;
        check(published_ph_range("nitrogen_fixer", lo, hi) && lo == 6.8 && hi == 7.5,
              "nitrogen_fixer range is 6.8-7.5");
        check(published_ph_range("phosphate_solubilizer", lo, hi) && lo == 6.5 && hi == 7.5,
              "phosphate_solubilizer range is 6.5-7.5");
        check(published_ph_range("mycorrhiza", lo, hi) && lo == 6.0 && hi == 7.5,
              "mycorrhiza range is 6.0-7.5");
        check(!published_ph_range("potash_mobilizer", lo, hi),
              "potash_mobilizer has no published range");
        check(!published_ph_range("pgpr", lo, hi),
              "pgpr has no published range");
    }

    std::printf("[Suitability verdicts]\n");
    {
        // Azospirillum range 6.8-7.5, so pH 7.0 is inside it.
        auto in = assess_biofertilizer_suitability("nitrogen_fixer", 7.0, 5.0, 3.0);
        check(in.verdict == "optimal", "nitrogen_fixer at pH 7.0 is optimal");
        check(in.ph_min == 6.8 && in.ph_max == 7.5, "the reported band is the published one");
        check(!in.ph_reference.empty(), "the band cites its source");

        // pH 5.0 is outside 6.8-7.5. The removed formula returned exactly 0.0
        // here, which silently reported "no value" for a merely acidic soil.
        auto out = assess_biofertilizer_suitability("nitrogen_fixer", 5.0, 5.0, 3.0);
        check(out.verdict == "unsuitable", "nitrogen_fixer at pH 5.0 is unsuitable");

        auto psb = assess_biofertilizer_suitability("phosphate_solubilizer", 6.0, 5.0, 3.0);
        check(psb.verdict == "unsuitable", "phosphate_solubilizer at pH 6.0 is below 6.5");

        auto amf = assess_biofertilizer_suitability("mycorrhiza", 6.2, 5.0, 3.0);
        check(amf.verdict == "optimal", "mycorrhiza at pH 6.2 is inside 6.0-7.5");

        // Band edges are inclusive.
        check(assess_biofertilizer_suitability("nitrogen_fixer", 6.8, -1.0, -1.0).verdict == "optimal",
              "lower pH edge is inclusive");
        check(assess_biofertilizer_suitability("nitrogen_fixer", 7.5, -1.0, -1.0).verdict == "optimal",
              "upper pH edge is inclusive");
        check(assess_biofertilizer_suitability("nitrogen_fixer", 7.6, -1.0, -1.0).verdict == "unsuitable",
              "just above the upper pH edge is unsuitable");
    }

    std::printf("[No invented ranges]\n");
    {
        auto potash = assess_biofertilizer_suitability("potash_mobilizer", 7.0, 5.0, 3.0);
        check(potash.verdict == "unrated",
              "potash_mobilizer is unrated rather than given an invented pH response");
        check(potash.ph_min == 0.0 && potash.ph_max == 0.0,
              "an unrated type reports no pH band");
        check(!potash.rationale.empty(), "an unrated verdict still explains itself");

        auto pgpr = assess_biofertilizer_suitability("pgpr", 7.0, 5.0, 3.0);
        check(pgpr.verdict == "unrated", "pgpr is unrated");
    }

    std::printf("[Measured efficacy is passed through, not invented]\n");
    {
        check_close(report_measured_efficacy_percent_ndfa(48.5), 48.5, 1e-12,
                    "a measured %Ndfa is reported unchanged");
        check_close(report_measured_efficacy_percent_ndfa(0.0), 0.0, 1e-12,
                    "zero %Ndfa is a valid measurement");

        bool threw = false;
        try {
            report_measured_efficacy_percent_ndfa(-1.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "a negative %Ndfa is rejected");

        threw = false;
        try {
            report_measured_efficacy_percent_ndfa(140.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "a %Ndfa above 100 is rejected");
    }

    std::printf("[Contextual bands from Schuetz et al. 2018]\n");
    {
        auto low_p = assess_biofertilizer_suitability("mycorrhiza", 7.0, 4.0, 2.0);
        check(low_p.phosphorus_band == "low (< 10 mmHg/kg)", "low available P is banded");
        check(low_p.organic_matter_band == "low (< 5% OM)", "low organic matter is banded");
        check(low_p.rationale.find("Schuetz") != std::string::npos,
              "the rationale cites the meta-analysis");

        auto high_p = assess_biofertilizer_suitability("mycorrhiza", 7.0, 40.0, 8.0);
        check(high_p.phosphorus_band == "high (>= 25 mmHg/kg)", "high available P is banded");
        check(high_p.organic_matter_band == "high (>= 5% OM)", "high organic matter is banded");

        auto unmeasured = assess_biofertilizer_suitability("mycorrhiza", 7.0, -1.0, -1.0);
        check(unmeasured.phosphorus_band.empty(), "unmeasured P is not banded");
        check(unmeasured.organic_matter_band.empty(), "unmeasured OM is not banded");
        check(unmeasured.verdict == "optimal", "the pH verdict stands without the context bands");
    }

    std::printf("[Input validation]\n");
    {
        bool threw = false;
        try {
            assess_biofertilizer_suitability("unknown_type", 7.0, 5.0, 3.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "unknown biofert type throws");

        threw = false;
        try {
            assess_biofertilizer_suitability("", 7.0, 5.0, 3.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "empty biofert type throws");

        threw = false;
        try {
            assess_biofertilizer_suitability("mycorrhiza", 15.0, 5.0, 3.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "out-of-range pH throws");

        threw = false;
        try {
            assess_biofertilizer_suitability("mycorrhiza", 7.0, 5.0, 150.0);
        } catch (const std::invalid_argument&) {
            threw = true;
        }
        check(threw, "out-of-range organic matter throws");
    }

    std::printf("\n%d checks, %d failures\n", g_checks, g_failures);
    return g_failures == 0 ? 0 : 1;
}
