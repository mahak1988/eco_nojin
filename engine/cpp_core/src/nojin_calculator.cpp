#include "hydroma/nojin_calculator.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

namespace hydroma {

namespace {

// Published pH ranges for inoculant types.
// Sources: Fertilizer Control Order (India) as summarised in the FCO
// specification and quality control review of biofertilizers; FAO Guidelines
// (2016); ISO 17088. Potash and silicate solubilizers have no published pH
// range in those sources, so they are reported as unrated rather than given an
// invented one.
struct PhRange {
    const char* type;
    double lo;
    double hi;
};

const PhRange kPhRanges[] = {
    {"nitrogen_fixer", 6.8, 7.5},
    {"phosphate_solubilizer", 6.5, 7.5},
    {"mycorrhiza", 6.0, 7.5},
    // potash_mobilizer and pgpr: no published range, deliberately absent.
};

// Schuetz et al. 2018 (Front. Plant Sci. 9:2204) found response larger at low
// plant-available soil P, with the order AMF > P solubilizer > N fixer. The
// band edges below are that ordering expressed as thresholds; they are an
// ordering device, not a measured dose-response.
const double kLowP_mmHg = 10.0;
const double kHighP_mmHg = 25.0;

// Schuetz et al. 2018 found AMF response larger at LOW organic matter, and
// decreasing with increasing organic matter for AMF and P solubilizers.
const double kHighOrganicMatterPct = 5.0;

const char* kPhRefFco = "Fertilizer Control Order (India) / FAO Guidelines 2016";
const char* kSchuetz = "Schuetz et al. 2018, Front. Plant Sci. 9:2204";

std::string phosphorus_band_for(const std::string& type, double p) {
    if (p < 0.0) return "";  // not measured
    const char* band = nullptr;
    if (p < kLowP_mmHg) {
        band = "low (< 10 mmHg/kg)";
    } else if (p < kHighP_mmHg) {
        band = "moderate (10-25 mmHg/kg)";
    } else {
        band = "high (>= 25 mmHg/kg)";
    }
    (void)type;
    return band;
}

std::string organic_matter_band_for(double om_pct) {
    if (om_pct < 0.0) return "";  // not measured
    return om_pct < kHighOrganicMatterPct ? "low (< 5% OM)" : "high (>= 5% OM)";
}

}  // namespace

bool published_ph_range(const std::string& biofert_type, double& lo, double& hi) {
    for (const auto& r : kPhRanges) {
        if (biofert_type == r.type) {
            lo = r.lo;
            hi = r.hi;
            return true;
        }
    }
    return false;
}

SuitabilityResult assess_biofertilizer_suitability(
    const std::string& biofert_type,
    double ph,
    double soil_available_p_mmhg,
    double soil_organic_matter_pct) {
    if (biofert_type.empty()) {
        throw std::invalid_argument("biofert_type must not be empty");
    }
    if (ph < 0.0 || ph > 14.0) {
        throw std::invalid_argument("pH must be in [0, 14]");
    }
    if (soil_organic_matter_pct < -1.0 || soil_organic_matter_pct > 100.0) {
        throw std::invalid_argument("organic_matter_pct must be in [0, 100], or -1 if unmeasured");
    }

    // Reject an unknown type here rather than silently rating everything.
    static const char* kKnown[] = {"nitrogen_fixer", "phosphate_solubilizer",
                                    "potash_mobilizer", "mycorrhiza", "pgpr"};
    if (std::none_of(std::begin(kKnown), std::end(kKnown),
                     [&](const char* t) { return biofert_type == t; })) {
        throw std::invalid_argument("Unknown biofert_type: " + biofert_type);
    }

    SuitabilityResult r{};
    r.phosphorus_band = phosphorus_band_for(biofert_type, soil_available_p_mmhg);
    r.organic_matter_band = organic_matter_band_for(soil_organic_matter_pct);

    double lo = 0.0, hi = 0.0;
    if (!published_ph_range(biofert_type, lo, hi)) {
        // No published pH range for this type. Saying so is the honest answer;
        // the removed function invented a pH response for every type.
        r.verdict = "unrated";
        r.ph_min = 0.0;
        r.ph_max = 0.0;
        r.ph_reference = "";
        r.rationale =
            std::string("no published pH range for ") + biofert_type +
            "; pH cannot be assessed against a standard for this type";
        return r;
    }

    r.ph_min = lo;
    r.ph_max = hi;
    r.ph_reference = kPhRefFco;

    if (ph >= lo && ph <= hi) {
        r.verdict = "optimal";
        r.rationale = "pH " + std::to_string(ph) + " is within the published range " +
                      std::to_string(lo) + "-" + std::to_string(hi) + " for " +
                      biofert_type;
    } else {
        r.verdict = "unsuitable";
        r.rationale = "pH " + std::to_string(ph) + " is outside the published range " +
                      std::to_string(lo) + "-" + std::to_string(hi) + " for " +
                      biofert_type;
    }

    // Contextual factors from the meta-analysis, appended so the caller can see
    // whether the conditions match where response was measured to be larger.
    if (biofert_type == "mycorrhiza" && soil_organic_matter_pct >= 0.0) {
        r.rationale += std::string("; ") + kSchuetz + " found AMF response larger at low OM, and this soil is " +
                       (soil_organic_matter_pct < kHighOrganicMatterPct ? "low OM" : "high OM");
    }
    if (soil_available_p_mmhg >= 0.0) {
        r.rationale += std::string("; ") + kSchuetz + " found response larger at low available P, and this soil is " +
                       r.phosphorus_band;
    }
    return r;
}

double report_measured_efficacy_percent_ndfa(double percent_ndfa) {
    if (!std::isfinite(percent_ndfa)) {
        throw std::invalid_argument("percent_ndfa must be finite");
    }
    if (percent_ndfa < 0.0 || percent_ndfa > 100.0) {
        throw std::invalid_argument(
            "percent_ndfa must be in [0, 100]; it is a measured quantity from a 15N method");
    }
    return percent_ndfa;
}

}  // namespace hydroma
