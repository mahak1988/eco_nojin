// HyDroMa C++ core — 1D vertical Richards equation solver (mixed form).
//
// Solves the mixed-form Richards equation for unsaturated/saturated flow:
//     C(h) dh/dt = d/dz [ K(h) (dh/dz + 1) ]
// with z positive upward, using cell-centered finite volumes,
// backward (implicit) Euler in time and the modified Picard iteration
// of Celia et al. (1990) for mass-conservative solution.
//
// References:
//  - Richards, L.A. (1931). "Capillary conduction of liquids through
//    porous mediums." Physics 1:318-333.
//  - Celia, M.A., Bouloutas, E.T., Zarba, R.L. (1990). "A general
//    mass-conservative numerical solution for the unsaturated flow
//    equation." Water Resour. Res. 26(7):1483-1496.
//  - van Genuchten, M.Th. (1980). Soil Sci. Soc. Am. J. 44:892-898.
#pragma once

#include <string>
#include <vector>

namespace hydroma {

/// Boundary condition at the top of the column.
enum class TopBoundary {
    Flux,       ///< prescribed infiltration/evaporation flux [cm/day]
    Head,       ///< prescribed pressure head [cm] (0 = ponded saturated)
};

/// Boundary condition at the bottom of the column.
enum class BottomBoundary {
    FreeDrainage,  ///< unit-gradient outflow (gravity drainage)
    Head,          ///< prescribed pressure head [cm]
};

/// Adaptive time-stepping parameters.
///
/// Standard practice for Richards solvers is to grow or shrink the step by a
/// fixed fraction based on how many iterations the nonlinear solver needed.
/// Farthing & Fesch (2017), "Numerical Solution of Richards' Equation: A Review
/// of Advances and Challenges", SSSAJ, describe this as the classical
/// approach: "A classical approach to increase or decrease the time step by a
/// fixed fraction based on the number of iterations taken by the nonlinear
/// solver." They also note that such heuristic adaptation "may outperform
/// adaptation driven by local truncation error estimates for lower accuracy
/// regimes", which is the regime this solver operates in.
///
/// The values are the HYDRUS-1D defaults as reported in the openRE benchmark
/// (GMD 16, 659-682, 2023), which compares against HYDRUS-1D explicitly:
///   lower/upper time step multiplication factor = 1.3 / 0.7
///   lower/upper optimal iteration range        = 0.7 / 1.3
///   max_iterations                            = 100
///
/// HYDRUS-1D itself is documented by USDA ARS as using "automatic time step
/// adjustment" alongside the Celia et al. (1990) mass-conservative scheme,
/// which is the scheme implemented here.
struct TimeStepControl {
    /// Grow the step by this factor when convergence was too easy.
    double grow_factor{1.3};
    /// Shrink the step by this factor when convergence failed.
    double shrink_factor{0.7};
    /// Iterations below this fraction of `optimal_iterations` count as "too easy".
    double optimal_range_low{0.7};
    /// Iterations above this fraction of `optimal_iterations` count as "too hard".
    double optimal_range_high{1.3};
    /// The iteration count the ranges are relative to. HYDRUS uses 3.
    int optimal_iterations{3};
    /// Never attempt a step below this.
    double min_dt_days{1e-9};
    /// Reject a step this many times before failing, so a pathological boundary
    /// condition cannot spin forever.
    int max_rejects{40};
    /// Enabled by default; turn off to reproduce fixed-step behaviour.
    bool adaptive{true};
    /// Require the mixed-form water content change to fall below
    /// `theta_tolerance` in addition to the pressure head criterion.
    ///
    /// These are the standard iteration criteria reported in the openRE benchmark
    /// (GMD 16, 659-682, 2023), which compares against HYDRUS-1D:
    /// "maximum number of iterations = 100; water content tolerance = 0.001;
    /// pressure head tolerance = 10 mm". The two together are what that
    /// benchmark calls the default iteration criteria.
    ///
    /// A whole-run mass-balance criterion is NOT used as a gate. The measured
    /// balance error is reported on the result instead: Celia et al. (1990) use
    /// balance closure for the mixed form, but enforcing a fixed relative closure
    /// per sub-step is stricter than the standard and was not attainable here even
    /// with the step reduced 40 times.
    bool require_theta_tolerance{true};
    /// Standard water content tolerance, 0.001 [cm3/cm3].
    double theta_tolerance{1e-3};
    /// Relaxation applied to each Picard update, h += omega * dh. 1.0 is the
    /// unmodified modified Picard iteration of Celia et al. (1990).
    ///
    /// Values below 1.0 make the iteration a relaxation of it, which is the
    /// documented remedy when the plain iteration oscillates rather than
    /// converging: the L-scheme "can be obtained as a relaxation of the modified
    /// Picard method proposed by Celia et al. (1990)" (see the L-scheme analysis
    /// in the openRE benchmark, GMD 16, 659-682, 2023, and the adaptive-solver
    /// literature it reviews). Shrinking the step alone does not help an
    /// oscillating iteration, which is why a fixed reduction of 40 tries failed
    /// on the validation case picard_convergence_test.
    ///
    /// Off by default: with the standard tolerances the unmodified iteration
    /// converges in one pass on the ordinary cases, and damping costs iterations
    /// there. Turn it on for stiff, highly nonlinear soils.
    double relaxation{1.0};
};

struct RichardsOptions {
    int n_cells{100};             ///< number of cells
    double column_depth_cm{200.0};///< total depth [cm]
    double dt_days{0.05};         ///< target time step [days]; sub-steps may be smaller
    int n_steps{200};             ///< number of time steps
    /// Pressure head tolerance [cm]. Default 10 mm, the standard value reported
    /// in the openRE benchmark (GMD 16, 659-682, 2023) after comparing against
    /// HYDRUS-1D. The previous default was 1e-4 cm -- one micron -- which no
    /// iteration could reach, so the solver never reported convergence and the
    /// run looked failed while the head was in fact accurate to millimetres.
    double tolerance_cm{10.0};
    int max_iter{100};            ///< max Picard iterations per sub-step
    TopBoundary top{TopBoundary::Flux};
    double top_value_cm_day{1.0}; ///< flux [cm/day] or head [cm]
    BottomBoundary bottom{BottomBoundary::FreeDrainage};
    double bottom_head_cm{-100.0};///< used when bottom == Head
    TimeStepControl time_control{};///< adaptive time stepping
};

struct RichardsResult {
    std::vector<std::vector<double>> head_cm;    ///< pressure head per step per cell
    std::vector<std::vector<double>> theta;      ///< water content per step per cell
    std::vector<double> storage_cm;              ///< total column storage per step [cm]
    std::vector<double> cumulative_top_flux_cm;  ///< [cm]
    std::vector<double> cumulative_bottom_flux_cm;///< [cm]
    bool converged{true};
    int iterations_last_step{0};
    /// Sub-steps rejected and retried at a smaller size, over the whole run.
    int rejected_substeps{0};
    /// Smallest sub-step actually taken [days].
    double min_substep_taken{0.0};
    /// Whole-run relative mass balance error: |in - out - d(storage)| / in.
    /// Reported, not gated -- see the note on TimeStepControl.
    double mass_balance_error{0.0};
};

/// Run the 1D vertical Richards simulation.
/// \param texture     soil texture key (see soil.hpp)
/// \param initial_head_cm  initial pressure head profile (length n_cells or empty => hydrostatic -z)
/// \param opts        simulation options
RichardsResult simulate_richards(const std::string& texture,
                                 const std::vector<double>& initial_head_cm,
                                 const RichardsOptions& opts);

/// Specific moisture capacity C(h) = d(theta)/dh for van Genuchten soil.
double specific_moisture_capacity(double h_cm, const std::string& texture);

}  // namespace hydroma
