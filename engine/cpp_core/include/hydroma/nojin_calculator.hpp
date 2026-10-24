#ifndef HYDROMA_NOJIN_CALCULATOR_HPP
#define HYDROMA_NOJIN_CALCULATOR_HPP

// Nojin biofertilizer suitability assessment.
//
// REPLACES the previous closed-form "efficacy" function.
//
// Why it was replaced
// -------------------
// The removed function returned a continuous 0..1 score from hard-coded
// coefficients (10, 20, 100, 0.5, 7, 6, 2) that were cited nowhere in the
// repository. Investigation established that:
//
//   * no closed-form biofertilizer efficacy standard exists. ISO 17088,
//     ISO 8268:1989, the FAO Guidelines (2016) and national orders such as
//     India's Fertilizer Control Order are PRODUCT QUALITY standards -- viable
//     cell counts, permitted pH range, moisture, shelf life, contamination --
//     not efficacy models.
//   * efficacy is a MEASURED quantity, not a computed one. The standard
//     practice is the 15N methods (natural abundance, dilution, or 15N2 gas
//     feeding) reported as %Ndfa, or the yield / nitrogen-use-efficiency /
//     phosphorus-use-efficiency response (Schuetz et al. 2018, Front. Plant Sci.
//     9:2204, a global meta-analysis reporting an average yield increase of
//     16.2 +/- 1.0%).
//   * the coefficients were partly contradicted by that meta-analysis: P
//     solubilizer response INCREASES with available soil P, whereas the removed
//     formula scored it DOWN with P.
//
// What this replaces it with
// --------------------------
// A suitability assessment against PUBLISHED ranges, returning the band
// comparison rather than a fabricated score. Every range below is citable, so
// every output is traceable.
//
//   pH ranges, per inoculant type:
//     Azospirillum (N fixer)   6.8 - 7.5   (Fertilizer Control Order, India;
//                                             FAO Guidelines 2016)
//     Phosphate solubilizer    6.5 - 7.5   (Fertilizer Control Order, India)
//     VAM / AMF (mycorrhiza)  6.0 - 7.5   (Fertilizer Control Order, India)
//     Potash / silicate       no published range -> always "unrated"
//
//   Available phosphorus: Schuetz et al. (2018) found P solubilizer, AMF and N
//   fixer response all larger at low plant-available P, with the order
//   AMF > P solubilizer > N fixer. The banding used here follows that finding.
//
//   Organic matter: Schuetz et al. (2018) found AMF response larger at LOW
//   organic matter, and decreasing with increasing organic matter for both AMF
//   and P solubilizers.
//
// This is a suitability screen, not a prediction. A crop trial is still required
// before any efficacy claim.

#include <string>

namespace hydroma {

/// Suitability of a soil for a given biofertilizer type, against published ranges.
struct SuitabilityResult {
    /// "optimal" | "suboptimal" | "unsuitable" | "unrated"
    std::string verdict;
    /// pH band required by the relevant standard, empty when none is published.
    double ph_min;
    double ph_max;
    /// The pH band, empty when none is published.
    std::string ph_reference;
    /// Available-phosphorus band name, empty when not assessed.
    std::string phosphorus_band;
    /// Organic-matter band name, empty when not assessed.
    std::string organic_matter_band;
    /// Human-readable justification for the verdict.
    std::string rationale;
};

/// Published pH range for an inoculant type.
/// Returns false and leaves the outputs untouched when no standard range exists.
bool published_ph_range(const std::string& biofert_type, double& lo, double& hi);

/// Assess whether a soil suits a biofertilizer type.
/// `soil_available_p_mmhg` and `soil_organic_matter_pct` may be negative to
/// signal "not measured", in which case that factor is reported as unassessed.
SuitabilityResult assess_biofertilizer_suitability(
    const std::string& biofert_type,
    double ph,
    double soil_available_p_mmhg,
    double soil_organic_matter_pct);

/// Standard measured efficacy reporting, retained from the previous interface.
///
/// `percent_ndfa` is the percentage of plant nitrogen derived from the
/// atmosphere, as measured by a 15N method (IAEA, "Enhancing biological
/// nitrogen fixation"; FNCA Biofertilizer Manual). It is a MEASUREMENT, so this
/// function does not invent one: it validates and reports the supplied value.
double report_measured_efficacy_percent_ndfa(double percent_ndfa);

}  // namespace hydroma

#endif  // HYDROMA_NOJIN_CALCULATOR_HPP
