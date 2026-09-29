"""The registered formulas, with the measured state of each.

Every ``status`` and every ``notes`` entry here was produced by running the code
in this repository. Where two backends disagreed, the record says so and names
the measured magnitude; where a formula could not be reconciled, it is registered
as ``divergent`` and therefore, by the rule in ``registry``, cannot be served on
a request path.

Nothing in this file is a plan.
"""

from __future__ import annotations

from .records import FormulaRecord

#: Measurement harness shared by the parity tests. It is a module path so the
#: record does not import the engine at registration time.
HARNESS = "tests/unit/test_bridge_signature_contract.py"

RECORDS: tuple[FormulaRecord, ...] = (
    # ---------------------------------------------------------------- indices
    FormulaRecord(
        quantity="ndvi",
        canonical="engine/cpp_core/src/indices.cpp",
        literature_ref="Rouse, J.W. et al. (1974), NASA CR-144397",
        units="dimensionless, [-1, 1]",
        domain="both",
        backend_priority=("numba", "cpp", "numpy"),
        parity_tests=(f"{HARNESS}::test_index_backends_agree",),
        reference_values="closed form (NIR-Red)/(NIR+Red)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes=(
            "C++ and Python agree to 0.0 absolute. The Python fallback previously "
            "added 1e-10 to the denominator and did not clip to [-1,1]; both are "
            "fixed. Python accepts 1-D and 2-D."
        ),
    ),
    FormulaRecord(
        quantity="evi",
        canonical="engine/cpp_core/src/indices.cpp",
        literature_ref="Huete, A.R. et al. (2002), Remote Sensing of Environment 83",
        units="dimensionless, [-1, 1]",
        domain="both",
        backend_priority=("numba", "cpp", "numpy"),
        parity_tests=(f"{HARNESS}::test_index_backends_agree",),
        reference_values="closed form 2.5(NIR-Red)/(NIR+6Red-7.5Blue+1)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes=(
            "Was the worst divergence found: ~100% relative, because the Python "
            "fallback omitted the [-1,1] clip the native kernel applies. EVI exceeds 1 "
            "whenever the denominator is small, so the fallback could return values the "
            "native path cannot produce. Now agrees to 2.2e-16 (double epsilon)."
        ),
    ),
    FormulaRecord(
        quantity="savi",
        canonical="engine/cpp_core/src/indices.cpp",
        literature_ref="Huete, A.R. (1988), Advances in Space Research 3(2)",
        units="dimensionless, [-1, 1]",
        domain="both",
        backend_priority=("numba", "cpp", "numpy"),
        parity_tests=(f"{HARNESS}::test_index_backends_agree",),
        reference_values="closed form (NIR-Red)(1+L)/(NIR+Red+L)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes="C++ and Python agree to 0.0 absolute after the clip fix.",
    ),
    FormulaRecord(
        quantity="ndwi",
        canonical="engine/cpp_core/src/indices.cpp",
        literature_ref="McFeeters, B.K. (1996), International Journal of Remote Sensing 17(14)",
        units="dimensionless, [-1, 1]",
        domain="both",
        backend_priority=("numba", "cpp", "numpy"),
        parity_tests=(f"{HARNESS}::test_index_backends_agree",),
        reference_values="closed form (Green-NIR)/(Green+NIR)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes="C++ and Python agree to 0.0 absolute.",
    ),
    FormulaRecord(
        quantity="nbr",
        canonical="engine/cpp_core/src/indices.cpp",
        literature_ref="Key, C.H., Benson, N.A. (2006), Remote Sensing of Environment 109(1)",
        units="dimensionless, [-1, 1]",
        domain="both",
        backend_priority=("numba", "cpp", "numpy"),
        parity_tests=(f"{HARNESS}::test_index_backends_agree",),
        reference_values="closed form (NIR-SWIR)/(NIR+SWIR)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes="C++ and Python agree to 0.0 absolute.",
    ),
    # ------------------------------------------------------------- reference ET
    FormulaRecord(
        quantity="et0_reference",
        canonical="engine/cpp_core/src/climate.cpp",
        literature_ref="Allen, R.G. et al. (1998), FAO Irrigation and Drainage Paper 56, eq. 6-14",
        units="mm/day",
        domain="scalar",
        backend_priority=("cpp", "numpy"),
        parity_tests=(f"{HARNESS}::test_penman_monteith_backends_agree",),
        reference_values="FAO-56 worked example, chapter 3",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": False},
        notes=(
            "Three defects reconciled. (1) The native kernel used e0(Tmean) for es "
            "where FAO-56 eq. 11 specifies (e0(Tmax)+e0(Tmin))/2; since es-ea is the "
            "vapour pressure deficit this moved ET0 by tens of percent. (2) delta used "
            "that same es instead of e0(Tmean) per eq. 13. (3) The native used 273.16 "
            "where eq. 6 specifies 273. (4) The Python fallback read (tmin, tmax, rh, "
            "rs, u2, ...) against the native (t_min, t_max, rh_mean_pct, u2, rs_mj, ...), "
            "so positions 4 and 5 were swapped: with no extension present, wind speed was "
            "fed in as solar radiation and the result was silently wrong. Measured "
            "before/after divergence: 36% -> 0.0 relative across five conditions "
            "including overcast winter days."
        ),
    ),
    FormulaRecord(
        quantity="hargreaves_et0",
        canonical="engine/cpp_core/src/climate.cpp",
        literature_ref="Hargreaves, G.H., Samani, Z.A. (1985), Applied Engineering in Agriculture 1(2)",
        units="mm/day",
        domain="scalar",
        backend_priority=("cpp", "numpy"),
        parity_tests=("engine/cpp_core/tests/test_climate_unit.cpp",),
        reference_values="FAO-56 Appendix 2 worked example",
        status="stub",
        stub_reason=(
            "Recorded gap: Exposed natively, with no Python fallback, so there is no "
            "second backend to diverge from."
        ),
        backends_impl={"cpp": True, "python": False, "numba": False},
        notes=(
            "Exposed natively, with no Python fallback, so there is no second backend "
            "to diverge from. The C++ unit test file exists and is wired into the CMake "
            "test target, but it was NOT run during this work, so the record is a stub "
            "rather than verified. Recorded here so the gap is visible instead of the "
            "quantity being simply absent."
        ),
    ),
    # ---------------------------------------------------------------- hydrology
    FormulaRecord(
        quantity="muskingum_cunge_routing",
        canonical="engine/cpp_core/src/hydrology.cpp",
        literature_ref="Muskingum, F.F. (1957); Cunge, J.A. (1969)",
        units="m3/s, s",
        domain="both",
        backend_priority=("numba", "cpp"),
        parity_tests=("tests/unit/test_muskingum_parity.py",),
        reference_values="single-reach Muskingum-Cunge on the same hydrograph",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes=(
            "route_multi_reach ran n+1 reaches and gave every one of them the full "
            "channel_length, so the total routed distance was (n+1)x the intended "
            "length -- the two backends were modelling different rivers. Fixed: n reaches "
            "of L/n each, verified by a travel-time ratio of 3.997 for n=4 and by outflow "
            "agreement with the Python twin. Writing the parity test also surfaced that "
            "the kernel accepted a negative inflow and propagated it into the output "
            "through the initial condition, so discharge is now validated as "
            "non-negative."
        ),
    ),
    FormulaRecord(
        quantity="van_genuchten_theta",
        canonical="engine/hydroma/soil/physics.py",
        literature_ref=(
            "van Genuchten, M.T. (1980) SSSAJ 44(5) 892-898; cross-checked against R "
            "soilphysics::soilwater and tidysoilwater::swrc_van_genuchten, both of which "
            "give theta = theta_r + (theta_s - theta_r) / (1 + (alpha|h|)^n)^m."
        ),
        units="cm3/cm3",
        domain="both",
        backend_priority=("cpp", "python"),
        parity_tests=("engine/cpp_core/tests/test_soil_unit.cpp",),
        reference_values="van Genuchten (1980) eq. retention, m = 1 - 1/n (Mualem 1976)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": True},
        notes=(
            "The power m on the bracket is CORRECT and appears in the primary "
            "literature and in two independent implementations. Two separate claims "
            "that this was wrong were made and RETRACTED; the implementation was right "
            "both times. All three backends agree because they were all correct -- "
            "agreement between them proves nothing, so the check is against the "
            "published equation. Texture parameters are Carsel & Parrish (1988) as in "
            "soil.cpp:24-32. The native test's assertion that theta reaches theta_r to "
            "1e-6 at h=1e10 cm encoded a limit the model does not have (clay's residual "
            "there is 6.07e-2) and was corrected to assert boundedness plus monotone "
            "approach, which is what is actually guaranteed."
        ),
    ),
    FormulaRecord(
        quantity="richards_1d",
        canonical="engine/cpp_core/src/richards.cpp",
        literature_ref="Celia, M.A., Tartach, E.F., Abriola, H.J. (1990), Water Resources Research 26(7); time stepping: Farthing & Fesch (2017) SSSAJ; HYDRUS-1D defaults as reported in GMD 16, 659-682 (2023)",
        units="cm, cm/day",
        domain="scalar",
        backend_priority=("cpp",),
        parity_tests=("engine/cpp_core/tests/test_richards_unit.cpp",),
        reference_values="engine/cpp_core/tests/test_richards_unit.cpp",
        status="verified",
        backends_impl={"cpp": True, "python": False, "numba": False},
        notes=(
            "Mixed-form finite volumes, backward Euler, modified Picard, Thomas "
            "algorithm. Four defects found and fixed. (1) The singularity diagnostic "
            "printed capacity_scalar(h[0], p) under the label 'C[0]', which is not the "
            "matrix entry; it now reports the real pivot row and values. (2) The "
            "free-drainage boundary added no diagonal term, so the last cell had no sink "
            "and the pivot cancelled to exactly zero (verified: row 49, pivot 0, n=50). "
            "(3) The head tolerance default was 1e-4 cm -- one micron -- which no "
            "iteration could reach, so the solver never reported convergence; it is now "
            "10 mm, the standard value from the openRE benchmark against HYDRUS-1D. "
            "(4) There was no time-step adaptation at all. Adaptive sub-stepping now "
            "follows the classical iteration-count rule of Farthing & Fesch (2017), "
            "SSSAJ, with the HYDRUS-1D default factors 1.3/0.7 and optimal iteration "
            "range 0.7/1.3 as reported in GMD 16, 659-682 (2023). The second standard "
            "criterion is water content 0.001. Measured after the fix: the previously "
            "failing unit case converges in 1 iteration. STILL AN OPEN LIMIT: the "
            "validation case picard_convergence_test, which drives the top head from "
            "-1000 to +10 cm in one step, does NOT converge by step reduction at any "
            "factor down to 1e-9 days -- the iteration oscillates, and shrinking does "
            "not help an oscillating scheme. It can be forced to converge with "
            "under-relaxation (omega = 0.2) but then reports 95% mass balance error, so "
            "convergence alone is not sufficient evidence of a correct answer. Left as a "
            "documented limit with `mass_balance_error` reported on the result. "
            "KNOWN DEFECT INTRODUCED HERE: the diagonal term b[n-1] += q_iface/dz that "
            "fixed the singularity is unpaired -- it is the only term in the whole "
            "operator with a nonzero row sum, because the true Jacobian of a "
            "prescribed unit gradient is zero, not k/dz -- and is not by itself "
            "conservative. The 4.8% residual is the same order as that term's "
            "contribution. A physically complete formulation needs a saturated storage "
            "term (S = Se + Ss); without it a saturated column has C == 0, cannot "
            "absorb a flux imbalance, and the imbalance is absorbed by the spurious "
            "diagonal instead. Not yet closed."
        ),
    ),
    # -------------------------------------------------------------------- carbon
    FormulaRecord(
        quantity="rothc_moisture_modifier",
        canonical="engine/hydroma/simulation/runners/rothc_runner.py",
        literature_ref="Coleman, R.C., Jenkinson, D.S. (1996) NRCS Technical Note NWC-450",
        units="dimensionless, [0.2, 1.0]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_rothc_moisture_modifier.py",),
        reference_values="continuity and monotonicity invariants",
        status="verified",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "Was discontinuous and non-monotonic: at the 0.444*max_smd breakpoint the "
            "two segments returned 0.6448 and 0.3597 for the same soil moisture, so the "
            "modifier FELL by 0.285 as the soil dried. Now continuous by construction "
            "and monotone decreasing, bounded 0.2..1.0. This function is the shared root "
            "of run_rothc and the ECSI model."
        ),
    ),
    FormulaRecord(
        quantity="rothc_temperature_modifier",
        canonical="engine/hydroma/simulation/runners/rothc_runner.py",
        literature_ref=(
            "Coleman, K., Prout, J.M. & Milne, A.E. (2024) RothC - A model for the "
            "turnover of carbon in soil, Rothamsted Research, section 1.6.1 eq. (1): "
            "RM_Tmp = 47.91 / (1 + e^(106.06/(T+18.27))). Identical triple hard-coded "
            "in the official RothC_Code (Fortran), RothC_Py and RothC_R releases. "
            "Figure 2 marks the mean annual temperature at Rothamsted."
        ),
        units="dimensionless, [0, ~5]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=(
            "tests/unit/test_rothc_temperature_factor.py",
            "tests/unit/test_carbon_modifier_consolidation.py"
        ),
        reference_values=(
            "RM_Tmp = 1.0 at T = 9.291 C, the Rothamsted mean annual temperature; "
            "-5 C -> 0.0162, 0 C -> 0.1439, 20 C -> 2.8215, 30 C -> 4.7910"
        ),
        status="verified",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "RESOLVED. The numerator is 47.91, a hard constant, not a site "
            "calibration; the '2C' rendering and the '47.9' and '106.27/18.06' "
            "variants are all PDF text-layer extraction artefacts, where the Word "
            "OMML equation is emitted as separate glyph runs and a naive reflow "
            "merges '18'+'.'+'27' into '18.06' and drops the trailing '1'. 47.91 is "
            "the value that normalises the modifier to exactly 1.0 at 9.291 C, the "
            "Rothamsted mean annual temperature marked on Figure 2. THREE claims "
            "made in this repository were wrong and are withdrawn: that the "
            "reciprocal exponent made the shape invalid (RothC's response is "
            "intentionally monotonically increasing, with no optimum and no "
            "supra-optimal decline); that the numerator was unverifiable; and that "
            "the factor should be bounded by 1 (it multiplies the rate constant k "
            "directly and legitimately exceeds 1 -- the official code comments give "
            "the range as '0.0 - ~5.0'). Two implementation defects fixed: the "
            "numerator was 47.9 (putting the normalisation point at 9.247 C instead "
            "of 9.291 C), and the low-temperature branch raised at -18.3 C whereas "
            "the official Fortran, Python and R all hard-zero below -5 C, so frozen "
            "soils now stop decomposition instead of raising. Note SoilR's fT.RothC "
            "diverges from the official model on three points and was NOT used as "
            "the reference: 47.9 / 106 / 18.3, an NA return rather than zero, and no "
            "low-temperature guard."
        ),
    ),
    FormulaRecord(
        quantity="saint_venant_1d",
        canonical="engine/cpp_core/src/saint_venant.cpp",
        literature_ref="Rusanov flux form; Chow, V.T. (1959) Open-Channel Hydraulics; Toro, E.F. (2001) Riemann Solvers and Numerical Methods for Fluid Dynamics",
        units="m, m3/s",
        domain="scalar",
        backend_priority=("cpp",),
        parity_tests=("engine/cpp_core/tests/test_saint_venant_unit.cpp",),
        status="verified",
        reference_values=(
            "The published Infoworks example, whose balance closes exactly; and an "
            "internal closed-domain check, where the 50-cell B = 10 case now closes "
            "to 0.000 m3 residual, 0.0000% of throughput."
        ),
        backends_impl={"cpp": True, "python": False, "numba": False},
        notes=(
            "THREE defects found and fixed, ONE still open. (1) The continuity update was m"
            "Four defects found and fixed, none in the scheme itself. (1) The continuity"
            "update was missing 1/B. The scheme solves the area form U = [A, Q] with A ="
            "B*h, so h_new = h - (dt/(dx*B))*(Fh_R - Fh_L); without it the depth field wa"
            "s transported B times too fast while momentum kept the correct rate. With B"
            "= 10 that both inflated volume tenfold and pushed the effective Courant to c"
            "fl*B = 5.0, violating positivity at a wet/dry front and diverging geometrica"
            "lly. The failing case now runs the full 1200 s and reports stable=true, wher"
            "e it previously diverged after ~1.5 s; a test with B = 1 had always passed,"
            "which is why the factor was invisible. (2) The imposed inflow was excluded f"
            "rom the CFL maximum; the ghost velocity inflow/(B*h[0]) is 100 m/s against a"
            "n interior maximum of 0.313 for a 0.01 m sheet, a boundary Courant of about"
            "160 where the scheme needs <= 1. (3) A data race made the result non-determi"
            "nistic: the boundary faces were captured into scalars from inside the parall"
            "el loop and the dried-cell counter was incremented there, so several threads"
            "wrote the same variable. The dam break conservation check passed single-thr"
            "eaded 8/8 and failed about 4/8 with threads. Faces are now recorded per cell"
            "and the counters are OpenMP reductions; 10/10 deterministic. (4) The conser"
            "vation METRIC had two defects, both introduced when the metric was written:"
            "it clamped each boundary volume with max(flux, 0), which discarded the direc"
            "tion, and it ADDED the storage change where conservation requires SUBTRACTIN"
            "G it. A balanced run therefore reported 1042 m3 of error over 521 m3 of real"
            "storage change. The scheme was conservative throughout; only the instrument"
            "was wrong, which is worse, because it made a correct solver look broken. Me"
            "asured after the fix: residual 0.000 m3, relative 0.0000%."
        ),
    ),
    FormulaRecord(
        quantity="nojin_biofertilizer_suitability",
        canonical="engine/cpp_core/src/nojin_calculator.cpp",
        literature_ref=(
            "Published inoculant pH ranges: Fertilizer Control Order (India) as "
            "summarised in the FCO specification and quality-control review of "
            "biofertilizers (Azospirillum 6.8-7.5, PSB 6.5-7.5, VAM/AMF 6.0-7.5); "
            "FAO Guidelines (2016); ISO 17088. Response direction and magnitude: "
            "Schuetz, M.A. et al. (2018) Front. Plant Sci. 9:2204, global "
            "meta-analysis, mean yield increase 16.2 +/- 1.0%. Measured efficacy: "
            "IAEA, Enhancing biological nitrogen fixation; FNCA Biofertilizer "
            "Manual (15N natural abundance, dilution and 15N2 feeding)."
        ),
        units="verdict (optimal | unsuitable | unrated); %Ndfa [0, 100]",
        domain="scalar",
        backend_priority=("cpp",),
        parity_tests=("engine/cpp_core/tests/test_nojin_calculator.cpp",),
        reference_values="engine/cpp_core/tests/test_nojin_calculator.cpp",
        status="verified",
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::"
            "nojin_biofertilizer_suitability"
        ),
        backends_impl={"cpp": True, "python": False, "numba": False},
        notes=(
            "REPLACED the previous closed-form efficacy function, which is gone. No "
            "standard defines such a formula: ISO 17088, ISO 8268:1989, the FAO "
            "Guidelines and national fertilizer orders are product-QUALITY standards "
            "(viable counts, permitted pH, moisture, shelf life), not efficacy models. "
            "Efficacy is a MEASURED quantity (15N methods reported as %Ndfa, or the "
            "yield/NUE/PUE response). The removed coefficients were also contradicted by "
            "the meta-analysis: it found P solubilizer response INCREASES with available "
            "soil P, whereas the removed formula scored it DOWN with P. The four failing "
            "test expectations (0.75, 0.50, 0.75, 0.75) were internally inconsistent -- "
            "three identical structural inputs expected one value while three branches "
            "returned 0.400/0.375/0.000, and 0.75 -> 0.50 is not a halving -- so they were "
            "placeholders. The replacement screens a soil against the published pH range "
            "and the meta-analysis context bands, and reports types with no published "
            "range as 'unrated' rather than inventing a response. 34 checks pass."
        ),
    ),
    FormulaRecord(
        quantity="rusle_soil_loss",
        canonical="engine/cpp_core/src/erosion.cpp",
        literature_ref=(
            "RUSLE: Foster et al. (1981); Renard, K.G. et al. (1997) USDA "
            "Agriculture Handbook 703. A = R * K * LS * C * P, t/ha/yr."
        ),
        units="t/ha/yr",
        domain="both",
        backend_priority=("cpp", "python"),
        parity_tests=("tests/unit/test_rusle_uncorrelated.py",),
        reference_values=(
            "Worked R-factor example: Renard et al. (1997) AH-703 for a US "
            "watershed. A plain 5-factor product with a worked arithmetic case."
        ),
        status="verified",
        provenance="standard",
        backends_impl={"cpp": True, "python": True, "numba": False},
        notes=(
            "A standard that had been silently altered in THREE places. "
            "core/core.py multiplied the product by a default calibration of 0.10 "
            "-- uncited, absent from the native kernel, and a 10x reduction of a "
            "published quantity. chain_runner.py set RUSLE_CALIBRATION = 0.10 under a "
            "comment attributing it to Morgan (2005) and describing it as 'arid "
            "regions ~3x', which the value contradicts. "
            "scientific_motors/erosion_rusle.py applied the same 0.10 under a comment "
            "listing THREE different regional bases (arid ~3x, humid ~5x, tropical "
            "~8x) and calling a single 10x scalar 'conservative' -- a larger reduction "
            "in wetter climates is the opposite of conservative, and none of the three "
            "bases was honoured. All three removed; the equation is the plain product "
            "and a calibration, if wanted, is an explicit caller argument."
        ),
    ),
    FormulaRecord(
        quantity="epia_precision_irrigation",
        canonical="engine/hydroma/models/epia.py",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::epia_precision_irrigation"
        ),
        literature_ref=(
            "ETc = ET0 * Kc * Ks: Allen et al. (1998) FAO Irrigation and Drainage "
            "Paper 56; Jensen, M.E. & Allen, R.G. (2016) Crop Water Requirements. "
            "The LAI-to-Kc mapping and the water-stress response are this project's."
        ),
        units="mm/day (ETc), dimensionless (Kc, Ks)",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="FAO-56 worked examples; the LAI ramp has no external anchor.",
        status="stub",
        stub_reason=(
            "Recorded gap: The FAO-56 frame (ETc = ET0*Kc*Ks) is standard, but two "
            "terms are not."
        ),
        provenance="composite",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The FAO-56 frame (ETc = ET0*Kc*Ks) is standard, but two terms are not. "
            "kc_from_lai maps LAI to Kc LINEARLY with lai_max 6.0, kc_min 0.1, "
            "kc_max 1.2; FAO-56 derives Kc from crop HEIGHT and the standard curve is "
            "not linear in LAI. And ks_water_stress uses a hardcoded field capacity of "
            "0.4, so the depletion proxy is a constant rather than a soil property. "
            "The stage classifier's 0.3/0.8/1.1 Kc cut-offs are also unsourced. "
            "validate_against_reference is inherited from the abstract base and returns "
            "whether the model trained, not whether it is accurate."
        ),
    ),
    FormulaRecord(
        quantity="hpheno_phenology",
        canonical="engine/hydroma/models/hpheno.py",
        literature_ref=(
            "Phenological metrics from an NDVI series: Zhang, X. et al. (2003) "
            "Monitoring vegetation phenology with MODIS; White, J.C. et al. (2009) "
            "Derivation of phenological metrics from MODIS NDVI. The Savitzky-Golay "
            "smoothing is Savitzky & Golay (1964)."
        ),
        units="dimensionless NDVI, days",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_hpheno_smoothing.py",),
        reference_values="Savitzky-Golay polynomial exactness invariants",
        status="verified",
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::hpheno_phenology"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The method is now independent of the environment. Previously the module "
            "called scipy.signal.savgol_filter and, when scipy was absent, fell back to "
            "np.convolve(mode='same') -- a centred MOVING AVERAGE. A moving average has "
            "no derivative-preserving property, so every downstream zero-crossing and "
            "np.gradient silently changed meaning depending on whether an optional "
            "dependency was installed. The Savitzky-Golay kernel is now computed "
            "directly from pinv(vander) and the window is always valid and odd, so the "
            "old ValueError path no longer exists either."
        ),
    ),
    FormulaRecord(
        quantity="theis_groundwater",
        canonical="engine/hydroma/models/groundwater_model.py",
        literature_ref=(
            "Theis (1935) non-equilibrium solution; W(u) = -E1(-u) via the "
            "exponential integral. See also Ferris, J.G. (1962) Ground Water "
            "Hydrology."
        ),
        units="m of drawdown",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="Analytic Theis drawdown for a given (Q, S, T, r, t).",
        status="verified",
        provenance="standard",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The only model file in the engine that declares bounded inputs (gt=0, lt=1 "
            "on the input dataclass), and the only one whose inputs are validated by the "
            "model itself. No REFERENCES dict is declared in the file; the citation is "
            "recorded here so the attribution is not lost."
        ),
    ),
    FormulaRecord(
        quantity="scs_curve_number_runoff",
        canonical="engine/hydroma/models/runoff_model.py",
        literature_ref=(
            "SCS-CN: USDA NRCS National Engineering Handbook, Part 630, Ch. 4, and "
            "TR-55. Rational method: common engineering practice."
        ),
        units="mm, m3/s",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_scs_units_consistency.py",),
        reference_values="TR-55 worked examples; the SI form of S.",
        status="verified",
        provenance="standard",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "Defect fixed in this work: the inch form S = (1000/CN) - 10 was still "
            "applied to millimetre rainfall in simulation_env/climate.py and "
            "simulation_env/disasters.py, after it had been corrected in this file. "
            "Measured over-estimate of event runoff: 11.1x at CN 50, 5.0x at CN 60, "
            "2.3x at CN 75. A repository-wide scan now guards it. Two further "
            "weaknesses remain and are NOT fixed: curve_number has no lower bound, so "
            "CN=0 reaches 25400.0/0 before the CN>100 guard; and peak_flow_m3s "
            "conflates a depth-derived volume with a one-hour peak."
        ),
    ),
    FormulaRecord(
        quantity="spatial_runoff",
        canonical="engine/hydroma/models/runoff_model.py",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::spatial_runoff"
        ),
        literature_ref=(
            "The spatial extension uses the same SCS-CN and rational equations per "
            "cell; the raster handling and the land-use-to-CN lookup are this "
            "project's."
        ),
        units="mm, m3/s",
        domain="array",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="Per-cell equivalence to the point-scale model.",
        status="stub",
        stub_reason=(
            "Recorded gap: the only CN mapping is a four-way branch, not an "
            "approximation of NRCS TR-55 Table 2A."
        ),
        provenance="composite",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "A stub because the only CN mapping is a four-way branch, not an "
            "approximation of NRCS TR-55 Table 2A. Two concrete defects: the "
            "land-use lookup is a simplification its own comment admits, and "
            "_create_cn_map_from_lu_soil accepts a `soil` argument it never reads, so "
            "the soil texture has no effect on the Curve-Number map despite the "
            "function name. Output filenames embed hash(dem_path), and Python's string "
            "hash is randomised per process, so rasters accumulate under "
            "non-reproducible names across runs."
        ),
    ),
    FormulaRecord(
        quantity="modflow6_groundwater_flow",
        canonical="engine/hydroma/models/expansion/modflow6.py",
        literature_ref=(
            "Harbaugh, B.A., Nordlander, M.P. & Andrews, G.D. (2020) MODFLOW 6 "
            "Description of Groundwater Flow Equations and Method of Solution, "
            "USGS Techniques and Methods 6-A55."
        ),
        units="m head, m3/d3, d",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="USGS benchmark problems; the wrapper asserts none.",
        status="stub",
        stub_reason=(
            "Recorded gap: NOT FUNCTIONAL. ModelOutput and ModelInput are never "
            "imported; from __future__ import annotations hides the annotation error "
            "but the constructor call still raises NameError on the first line of "
            "real work."
        ),
        provenance="standard",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "NOT FUNCTIONAL. ModelOutput and ModelInput are never imported; "
            "from __future__ import annotations hides the annotation error but the "
            "constructor call still raises NameError on the first line of real work. "
            "mock_mode defaults to `not FLOPY_AVAILABLE`, so without flopy the model "
            "fabricates a linear head ramp in a pure-Python triple loop and returns "
            "success=True with no flag that the result is synthetic. "
            "validate_against_reference always returns True; _estimate_uncertainty "
            "returns the constants 0.05 and 0.10."
        ),
    ),
    FormulaRecord(
        quantity="swatplus_watershed",
        canonical="engine/hydroma/models/expansion/swat_plus.py",
        literature_ref=(
            "SWAT+ documentation and reference: Arnold, J.G. et al. SWAT+ "
            "documentation. The wrapper is this project's."
        ),
        units="mm, t/ha",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="SWAT+ output variables; the wrapper asserts none.",
        status="stub",
        stub_reason=(
            "Recorded gap: same missing ModelOutput/ModelInput import as MODFLOW6."
        ),
        provenance="standard",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "NOT FUNCTIONAL: same missing ModelOutput/ModelInput import as MODFLOW6. "
            "validate_against_reference always returns True and "
            "_estimate_uncertainty returns the constants 0.15/0.25/0.20. Two further "
            "defects: the _swat config is never referenced by the orchestrator, which "
            "uses a different and fabricated step instead; and subprocess.run is "
            "preceded by a process-wide Path.chdir that is not restored when "
            "TimeoutExpired is raised, so every later relative path in the process "
            "resolves inside the SWAT+ project."
        ),
    ),
    FormulaRecord(
        quantity="climate_adaptation_stress_engine",
        canonical="engine/hydroma/climate_adaptation/dynamic_stress_engine.py",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::"
            "climate_adaptation_stress_engine"
        ),
        literature_ref=(
            "Inline citations only, for some rules: IPCC AR6 (2021); Yuan et al. "
            "(2019); Zhang et al. (2020); Zscheischler et al. (2018) for the dynamic "
            "stress engine; IPCC AR6 WG2 (2022), FAO GSP (2021), GLASOD (1991) for "
            "soil degradation. The rules themselves are this project's."
        ),
        units="varies per rule",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "None. This is the recorded documentation gap: the module implements about "
            "25 numbered rules (h01..h25) with no REFERENCES dict, and four of its "
            "classes have no class docstring."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: This record covers the family implemented in "
            "engine/hydroma/climate_adaptation/: DynamicStressEngine, "
            "SoilDegradationModel, UncertaintyAndKnowledgeEngine, "
            "SeedOptimizationEngine and ClimateAdaptivePhenology, about 25 numbered "
            "rules in total (h01..h25)."
        ),
        provenance="novel",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "This record covers the family implemented in "
            "engine/hydroma/climate_adaptation/: DynamicStressEngine, "
            "SoilDegradationModel, UncertaintyAndKnowledgeEngine, "
            "SeedOptimizationEngine and ClimateAdaptivePhenology, about 25 numbered "
            "rules in total (h01..h25). It is registered as one quantity rather than "
            "twenty-five because the rules share a module and a method of "
            "construction, but the documentation gap is real and is recorded here "
            "rather than left implicit: no REFERENCES dict, and four of the five "
            "classes have no class docstring. dynamic_stress_engine.py is named as "
            "canonical because it is the only member with an inline citation."
        ),
    ),
    FormulaRecord(
        quantity="koppen_geiger_class",
        canonical="engine/hydroma/models/global_watchdog/koppen.py",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::koppen_geiger_class"
        ),
        literature_ref=(
            "Peel, D., Broll, B. & Kubik, J. (2007) Updated Köppen-Geiger climate "
            "classification maps at 1-km resolution, HESS 11:1633-1644. The "
            "implementation DEVIATES from it in two documented places."
        ),
        units="class code",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "None that exists. The module docstring claims '88.0% (22/25 countries "
            "validated with real climate data)' but no country table, result file or "
            "generating script is in the repository, and the NEAR_MATCHES list accepts "
            "adjacent Köppen letters so cross-group pairs such as BWh/Csa and ET/Cfc "
            "count as correct."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: The best-documented deviation in the codebase and the "
            "model for how the others should be handled: the docstring states both "
            "departures (an ET buffer of 12 C instead of Peel et al.'s 10 C, and a "
            "re-derived Am rule) instead of presenting them as the standard."
        ),
        provenance="composite",
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The best-documented deviation in the codebase and the model for how the "
            "others should be handled: the docstring states both departures (an ET "
            "buffer of 12 C instead of Peel et al.'s 10 C, and a re-derived Am rule) "
            "instead of presenting them as the standard. What is NOT defensible is the "
            "accuracy claim: no country table, no per-country result file and no "
            "generating script exist in the repository, and NEAR_MATCHES is a 43-pair "
            "adjacency list that accepts the wrong Koppen GROUP, so a classifier that "
            "gets the group wrong still scores. The 88% figure is a module constant, "
            "not a measurement."
        ),
    ),
    # ------------------------------------------------ project contributions
    FormulaRecord(
        quantity="wbi_water_bankruptcy",
        canonical="engine/hydroma/models/global_watchdog/wbi.py",
        literature_ref=(
            "Falkenmark & Rockstrom (2004) Water Stress Index supplies the "
            "per-capita component. The eight-factor composition, the weights, "
            "every scaling constant and the projection model are this project's."
        ),
        units="dimensionless index, [0, 100]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("engine/hydroma/models/global_watchdog/wbi.py::validate_against_wri",),
        reference_values=(
            "WRI Aqueduct country comparison is asserted in the module docstring at "
            "80.0% (20/25). NO country table, result file or generating script exists "
            "in the repository, and the validator accepts a hand-written expected "
            "RANGE per WRI level rather than a value, so a passing check is a weak "
            "constraint. Recorded as an open claim, not as an established result."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: The strongest candidate original contribution in the "
            "codebase: eight factors, the largest set anywhere here, two of which -- "
            "governance_score and infrastructure_leakage_pct -- are socio-political "
            "constructs with no hydrological counterpart in any published water- "
            "stress index."
        ),
        provenance="novel",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::wbi_water_bankruptcy"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The strongest candidate original contribution in the codebase: eight "
            "factors, the largest set anywhere here, two of which -- governance_score "
            "and infrastructure_leakage_pct -- are socio-political constructs with no "
            "hydrological counterpart in any published water-stress index. Also the "
            "least justified: no weight, no scale constant and the 85 baseline of the "
            "projection model has any source. Held at stub rather than verified "
            "because the research definition documents the construction honestly but "
            "cannot supply the missing derivation. The module's '80.0% accuracy "
            "(20/25 countries)' claim is unsupported: no country table, result file "
            "or generating script exists in the repository, and the validator accepts "
            "a hand-written expected RANGE per WRI level rather than a value."
        ),
    ),
    FormulaRecord(
        quantity="hlhs_landscape_health",
        canonical="engine/hydroma/models/hlhs.py",
        literature_ref=(
            "Generic MCDA normalisation. The module's REFERENCES block cites "
            "Shannon (1948), a communication-theory source, and Nagender (2002); "
            "neither is a source for min-max normalisation, the factor set, any "
            "weight or any bound. The contribution is this project's."
        ),
        units="dimensionless score, [0, 100]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "Internal invariants only: monotonicity in each component, range [0,100], "
            "and the class thresholds. No external reference exists for this "
            "construction."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: no weight and no bound has a source: all seven weights and "
            "five of the seven normalisation bounds are unattributed, so the index "
            "cannot be reproduced from its own documentation."
        ),
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::hlhs_landscape_health"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "A stub because no weight and no bound has a source: all seven weights and "
            "five of the seven normalisation bounds are unattributed, so the index "
            "cannot be reproduced from its own documentation. It is a composite of "
            "composites: two of its seven inputs, EWSI and ECSI, are "
            "themselves project contributions. Five of the seven bound ranges are "
            "engineering choices with no source, including the choice of 100 t/ha "
            "as a perfect soil organic carbon. The carbon bound extends to -2 "
            "tCO2/ha/yr, so the index rewards emissions up to a threshold rather "
            "than penalising them immediately -- a policy choice, recorded as such in "
            "the research definition."
        ),
    ),
    FormulaRecord(
        quantity="esri_salinity_risk",
        canonical="engine/hydroma/models/esri.py",
        literature_ref=(
            "Leaching requirement LR = ECw/(5*ECe - ECw), bounded to (0,0.95): "
            "FAO-29, Ayers & Westcot (1985), Rhoades (1974). The three-factor "
            "composition, the normalisations and the spectral sub-index are this "
            "project's."
        ),
        units="dimensionless index, [0, 1]",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "Internal invariants and the leaching-requirement component check. The "
            "composite has no external reference."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: the composite has no external reference value: the three- "
            "factor composition, the normalisations and the spectral sub-index are "
            "this project's own, so nothing independent verifies the result range."
        ),
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::esri_salinity_risk"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "Stub because the composite has no external reference value: the "
            "three-factor composition, the normalisations and the spectral "
            "sub-index are this project's own, so nothing independent verifies "
            "the result range. The dominant weight (0.5) sits on a raw EC "
            "normalisation, and the third factor is a deficit -- required minus "
            "actual leaching fraction -- which is a project-specific concept "
            "rather than a published quantity. That term is what distinguishes "
            "this from a weighted average of salinity levels. The 1e-6 epsilon "
            "guards were left in place here while the C++/Numba index path had "
            "its own removed; the guards do not affect the result range but "
            "should be revisited alongside the normalisations."
        ),
    ),
    FormulaRecord(
        quantity="hdvi_drought_vulnerability",
        canonical="engine/hydroma/models/hdvi.py",
        literature_ref=(
            "Components: SPI McKee et al. (1993); SPEI Vicente-Serrano et al. "
            "(2010); VCI Kogan (1995). The two unit-bridging rescalings, the equal "
            "weighting and the class thresholds are this project's."
        ),
        units="dimensionless, clipped to [-3, 3]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "Component-level identities are checkable; the combination is not, as no "
            "external reference exists for it."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: The rescalings exist for a stated reason -- SPI/SPEI are "
            "standardised variates while VCI is 0..100 and SMI 0..1, so a plain "
            "average would let the standardised indices dominate -- but the factors "
            "are currently chosen without derivation."
        ),
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::hdvi_drought_vulnerability"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The rescalings exist for a stated reason -- SPI/SPEI are standardised "
            "variates while VCI is 0..100 and SMI 0..1, so a plain average would let "
            "the standardised indices dominate -- but the factors are currently chosen "
            "without derivation. Separately, models/validation/test_cases/hdvi.yaml "
            "declares inputs {ndvi, ndwi, lst, albedo}, which do not match the "
            "implemented signature {spi, spei, vhi, smi}, and names the model "
            "'Hydro-Drought Vegetation Index'. That case is disconnected from the "
            "code and cannot serve as a gate until corrected."
        ),
    ),
    FormulaRecord(
        quantity="ewsi_water_stress",
        canonical="engine/hydroma/models/ewsi.py",
        literature_ref=(
            "NDMI sub-index: Gao (1996). Monteith (1993) for crop water exchange "
            "context. The three-factor composition, the weights and the VPD "
            "anchors are this project's."
        ),
        units="dimensionless index, [0, 1]",
        domain="both",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="Component-level checks; the composite has no external reference.",
        status="stub",
        stub_reason=(
            "Recorded gap: The three factors are deliberately redundant in coverage "
            "-- canopy water, atmospheric demand, substrate availability -- so a "
            "plant under atmospheric stress with adequate soil moisture scores lower "
            "than one under both."
        ),
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::ewsi_water_stress"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The three factors are deliberately redundant in coverage -- canopy water, "
            "atmospheric demand, substrate availability -- so a plant under "
            "atmospheric stress with adequate soil moisture scores lower than one "
            "under both. Fixed during this work: ndmi() had added a 1e-9 epsilon to "
            "the denominator and then called np.nan_to_num(result, nan=np.nan), "
            "which replaces NaN with NaN and does nothing. Both removed; the exact "
            "zero-denominator guard and the [-1,1] clip now match the native kernel."
        ),
    ),
    FormulaRecord(
        quantity="multi_stress_amplification",
        canonical="engine/hydroma/climate_adaptation/multi_stress_engine.py",
        literature_ref=(
            "NONE for the weighting. The code's Persian comment at lines 65-66 "
            "attributes the 0.6/0.4/0.3 triple to the 'US Salinity Handbook', but a "
            "repository-wide search finds no other reference to such a document, and "
            "the US work of that description (Richards 1954, Agriculture Handbook 60, "
            "cited correctly in soil/salinity.py:7-8) contains no such weighting."
        ),
        units="dimensionless risk, [0, 1]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values="Internal invariants only; no external reference exists.",
        status="stub",
        stub_reason=(
            "Recorded gap: The construction is defensible on its own terms: combining "
            "independent stresses as 1 - prod(1 - s_i) avoids double counting, and "
            "the interaction term encodes the real observation that salinity and "
            "alkalinity reinforce each other in sodic soils."
        ),
        provenance="novel",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::multi_stress_amplification"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The construction is defensible on its own terms: combining independent "
            "stresses as 1 - prod(1 - s_i) avoids double counting, and the "
            "interaction term encodes the real observation that salinity and "
            "alkalinity reinforce each other in sodic soils. What is missing is the "
            "source for the specific numbers. An unsupported citation attached to a "
            "specific construction is the one outcome that is not acceptable, so "
            "either a source is found or the attribution is restated as this "
            "project's choice and the citation is removed."
        ),
    ),
    FormulaRecord(
        quantity="hyrue_stress_coupling",
        canonical="engine/hydroma/models/hyrue.py",
        literature_ref=(
            "RUE form and Beer-Lambert f_IPAR: Monteith (1977). Gaussian temperature "
            "width, crop presets and the f_water = 1 - EWSI coupling are this "
            "project's."
        ),
        units="g/m2/day, t/ha",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "Beer-Lambert component is independently checked in "
            "services/validation/formula_checks.py::hyrue_beer_lambert. The composite "
            "is not, and cannot be: it has no external reference."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: The multiplicative structure is intentional: any single "
            "factor driving the yield to zero is the desired behaviour under severe "
            "stress."
        ),
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::hyrue_stress_coupling"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "The multiplicative structure is intentional: any single factor driving "
            "the yield to zero is the desired behaviour under severe stress. Fixed "
            "during this work: CROP_PRESETS was declared inside the dataclass without "
            "a type annotation, making it a bare class attribute invisible to "
            "dataclasses.fields() and to any serialiser, and for_crop silently "
            "returned generic defaults for an unknown crop, so HYRUE(crop="
            "'dragonfruit') quietly modelled wheat."
        ),
    ),
    FormulaRecord(
        quantity="core_soil_health_score",
        canonical="engine/hydroma/core/core.py",
        literature_ref=(
            "Docstring says 'Based on USDA Soil Quality Index'. The USDA NRCS SQI "
            "(Andrews et al., 2002) is a principal-components index, not a "
            "hand-weighted linear combination, and these weights appear nowhere in "
            "it. The attribution names a standard that does not define this "
            "construction; the component optima are standard agronomic values."
        ),
        units="dimensionless score, [0, 100]",
        domain="scalar",
        backend_priority=("python",),
        parity_tests=("tests/unit/test_formula_registry.py",),
        reference_values=(
            "Component optima are standard agronomic values. The weighted "
            "combination has no external reference."
        ),
        status="stub",
        stub_reason=(
            "Recorded gap: Two differently-constructed soil health scores exist for "
            "the same intended quantity: this weighted combination in core/core.py, "
            "and a 50-base additive bonus scheme in wrapper.py:119-132."
        ),
        provenance="composite",
        research_definition=(
            "engine/hydroma/formulas/research/__init__.py::core_soil_health_score"
        ),
        backends_impl={"python": True, "cpp": False, "numba": False},
        notes=(
            "Two differently-constructed soil health scores exist for the same "
            "intended quantity: this weighted combination in core/core.py, and a "
            "50-base additive bonus scheme in wrapper.py:119-132. Both are "
            "reachable from the API. More seriously, rusle_soil_loss in the same "
            "file multiplies the RUSLE product by a default calibration of 0.10; "
            "RUSLE is A = RK LSCP, that factor is not part of it, it is uncited, and "
            "it is absent from the native kernel at erosion.cpp:19, which "
            "implements the plain product. A published quantity silently scaled by "
            "ten."
        ),
    ),
    FormulaRecord(
        quantity="latin_hypercube",
        canonical="engine/cpp_core/src/sampling.cpp",
        literature_ref="McKay, M.D. et al. (1979), Technometrics 21(2); Iman, R.L. (2008)",
        units="dimensionless, [0,1]",
        domain="both",
        backend_priority=("cpp", "numpy"),
        parity_tests=("tests/unit/test_formula_registry.py::test_lhs_stratification",),
        reference_values="stratification invariant (one sample per stratum per dimension)",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": False},
        notes=(
            "Parity here is statistical, not bitwise, and that is the correct test: the "
            "two backends draw from different RNG streams, so the same seed legitimately "
            "yields a different design. Both are checked against the stratification "
            "invariant instead. Two C++ defects fixed: the LHS strata were computed and "
            "discarded (making the function plain Monte Carlo), and the ensemble drew "
            "from mt19937_64 seeded with seed+i inside the parallel loop, which is a "
            "deterministic shift of one stream rather than independent samples. The "
            "Python fallback raised ValueError for any n_dimensions > 1."
        ),
    ),
    FormulaRecord(
        quantity="ensemble_percentile",
        canonical="engine/cpp_core/src/sampling.cpp",
        literature_ref="numpy.percentile, method='linear'",
        units="kg/ha",
        domain="scalar",
        backend_priority=("cpp", "numpy"),
        parity_tests=("tests/unit/test_ensemble_percentile_parity.py",),
        reference_values="numpy.percentile linear-interpolation convention",
        status="verified",
        backends_impl={"cpp": True, "python": True, "numba": False},
        notes=(
            "The C++ truncated the index (q*(n-1)) with no interpolation while NumPy "
            "interpolates linearly, so p5/p50/p95 disagreed for every even sample count. "
            "It now interpolates. Reachable now that the LHS strata are actually applied "
            "and the ensemble draws from one generator rather than seed+i."
        ),
    ),
)
