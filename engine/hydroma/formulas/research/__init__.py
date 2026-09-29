"""Written definitions of this project's original formula contributions.

A formula that follows a published standard needs a citation. A formula that
does not needs something else, and the something is not a weaker requirement: it
is a different one.

This directory holds a research definition for every ``provenance="novel"`` or
``provenance="composite"`` formula registered in
:mod:`engine.hydroma.formulas`. Each definition states the expression in closed
form, the rationale for each factor, the domain of validity, and -- honestly --
which coefficients have a source and which do not.

Why this is not a documentation chore
-------------------------------------
A published equation carries its own authority: a reader can look it up. An
original one does not. Without a written definition the only thing that
distinguishes a considered contribution from a number someone typed is the
commit that introduced it, and nobody can review, reproduce, improve, or safely
depend on that.

So the bar for a novel formula is the same bar a standard formula must clear --
one canonical implementation, a stated expression, a bounded output, tests --
with the published source replaced by this definition. What a novel formula does
*not* need is to have been published first. Requiring that would keep the
contributions most worth recording out of the registry.

A note on honesty in these definitions
--------------------------------------
Several of these composites carry coefficients that no source in the repository
explains. That is recorded as ``UNSOURCED`` rather than smoothed over. A
contribution whose weights are not yet justified is still a contribution; it is
simply not finished, and the record should say so.
"""

from __future__ import annotations

DEFINITIONS: dict[str, str] = {
    "nojin_biofertilizer_suitability": """
# Biofertilizer soil-suitability screen

Provenance: composite. The factors are published; the composition is this
project's.

## What it computes

A three-valued verdict for a soil and inoculant type -- `optimal`, `unsuitable` or
`unrated` -- plus the context bands the verdict was read against.

## Why this exists and why it is not a standard

No standard defines biofertilizer efficacy as a computable quantity. What exists
is product *quality*: ISO 17088, ISO 8268:1989, the FAO Guidelines (2016) and
national orders such as India's Fertilizer Control Order all specify viable cell
counts, a permitted pH range, carrier moisture, shelf life and contamination
limits. Efficacy is *measured*, not computed: the 15N methods (natural abundance,
dilution, 15N2 gas feeding) reported as %Ndfa, or the yield / NUE / PUE response
(Schuetz et al. 2018, Front. Plant Sci. 9:2204, mean yield increase
16.2 +/- 1.0%).

So a computable suitability screen is a contribution, not a restatement. It is
useful precisely because it is cheap enough to run on every sample the ingest
pipeline already handles, where a 15N assay is not.

## Definition

    (lo, hi) = band_lookup(T)

    band_lookup("nitrogen_fixer")        = (6.8, 7.5)   # Azospirillum, FCO/FAO
    band_lookup("phosphate_solubilizer") = (6.5, 7.5)   # PSB, FCO
    band_lookup("mycorrhiza")            = (6.0, 7.5)   # VAM/AMF, FCO
    band_lookup(T), any other T          = None          # no published range

    verdict = "unrated"     if (lo, hi) is None
            = "optimal"     if lo <= pH <= hi
            = "unsuitable"  otherwise

Context bands, reported but never used to form the verdict:

    phosphorus_band = "low"       if 0 <= P < 10   mmHg/kg
                    = "moderate"  if 10 <= P < 25  mmHg/kg
                    = "high"      if P >= 25         mmHg/kg
                    = unmeasured  if P < 0

    organic_matter_band = "low"     if 0 <= OM < 5   %
                        = "high"    if OM >= 5        %
                        = unmeasured if OM < 0

Band edges follow Schuetz et al. (2018), who found P solubilizer, AMF and N fixer
response all larger at low plant-available P, ordered AMF > P solubilizer > N
fixer, and AMF response larger at low organic matter. The edges are an ordering
device, not a measured dose-response.

## Domain of validity

* pH in [0, 14]; available P in mmHg/kg; organic matter in percent.
* Negative P or OM mean "not measured" and produce an empty band, never a band.
* The verdict is about **suitability**, not efficacy. A soil can be `optimal` and
  the inoculation still fail.

## Coefficient status

SOURCED: the three pH bands (Fertilizer Control Order, FAO Guidelines 2016,
ISO 17088) and the direction of the context bands (Schuetz et al. 2018). The band
*edges* -- 10 and 25 mmHg/kg, 5% organic matter -- are this project's ordering
device, not measured dose-response values.

## Deliberate non-behaviour

A type with no published pH range is reported `unrated`. It is not assigned an
invented response. The formula this replaced gave every type a pH response,
including `potash_mobilizer` and `pgpr`, for which none is published.

## Anchor cases

| type | pH | verdict |
|---|---|---|
| nitrogen_fixer | 6.8, 7.0, 7.5 | optimal (band edges inclusive) |
| nitrogen_fixer | 7.6 | unsuitable |
| phosphate_solubilizer | 6.0 | unsuitable |
| mycorrhiza | 6.2 | optimal |
| potash_mobilizer, pgpr | any | unrated |
| any | 15.0 | raises (out of range) |
| unknown / empty type | any | raises |
""",
    "wbi_water_bankruptcy": """
# Water Bankruptcy Index (WBI v3)

Provenance: novel. The Falkenmark component is published; the eight-factor
composition, the weights, the scaling constants and the projection model are this
project's.

## What it computes

    WBI = clip(sum_k(WEIGHTS[k] * score_k), 0, 100)                      [wbi.py:173]

    WEIGHTS = {falkenmark 0.15, withdrawal 0.25, groundwater 0.20, quality 0.08,
               drought 0.12, demand 0.10, infrastructure 0.05, governance 0.05}

Sub-scores, with the scaling constants as implemented:

    falkenmark(per_capita)  Falkenmark & Rockstrom (2004) water stress index;
                            the 1700 / 500 m3 per capita edges are published
    withdrawal(r)           100*((r-0.2)/0.8)^0.8   for r > 0.6, else 100*(r-0.2)/0.8
    groundwater(dep)        min(100, dep*12)
    quality(idx)            linear
    drought(events)         min(100, events*40)
    demand(growth)          min(100, growth*28)
    infrastructure(leak)    min(100, leak*2)
    governance(score)       linear

Projection:

    remaining  = 85 - WBI
    adaptation = 0.5 + governance_score * 1.5
    years      = max(3, remaining / (demand_growth_pct * 1.5) * adaptation)
    ytb        = (int(years*0.6), int(years*1.6))

## Domain of validity

Per-capita renewable water in m3/yr, withdrawal ratio 0..1, groundwater
depletion in mm/yr, quality index 0..1, drought events per year, demand growth in
percent, infrastructure leakage in percent, governance score 0..1.

## Coefficient status

SOURCED:
* the Falkenmark per-capita thresholds.

UNSOURCED -- no source in the repository:
* the seven weights;
* the exponent 0.8 in the withdrawal curve, and the deliberate sharpening above
  r = 0.6;
* every scale constant: 12, 40, 28, 2;
* the +/-15% band on the validation ranges;
* the 85 baseline, the 1.5 adaptation coefficient and the 1.5 demand scaling in
  the projection.

## Open validation claim

The module docstring asserts "80.0% accuracy (20/25 countries vs WRI Aqueduct
4.0)". **No country table, per-country result file, or script producing that
figure exists in the repository.** `validate_against_wri()` accepts a hand-written
expected *range* per WRI level rather than a value, so a passing check is a weak
constraint. The claim is recorded here and is not treated as established.

## Design note

`governance_score` and `infrastructure_leakage_pct` have no hydrological
counterpart in any published water-stress index; they are the parts of this
contribution that are least anchored to published work, and the ones a reviewer
should press on first.
""",
    "hlhs_landscape_health": """
# HyDroMa Landscape Health Score (HLHS)

Provenance: composite. Several components are themselves project contributions,
so this is a composite of composites.

## What it computes

    HLHS = 100 * sum_k(WEIGHTS[k] * (X_k - Xmin_k) / (Xmax_k - Xmin_k))  [hlhs.py:114]

    WEIGHTS = {vegetation 0.20, water 0.20, soil 0.15, biodiversity 0.15,
               carbon 0.15, topography 0.10, connectivity 0.05}

    BOUNDS = {vegetation (0, 0.8), water (0, 1.0), soil (0, 100),
              biodiversity (0, 3.0), carbon (-2, 5), topography (0, 1),
              connectivity (0, 1)}

Bands: 5 classes at 80 / 60 / 40 / 20.

## Inputs

`ndvi_mean`, `ewsi_mean` (a project contribution), `soc_t_ha`, `shdi`,
`ecsi_t_co2_ha_yr` (a project contribution), `slope_stability`,
`connectivity`.

## Domain of validity

Each component is first min-max normalised against its own bound, so the score is
insensitive to the input range only within those bounds. A component outside its
bound saturates. The bounds are engineering choices, not agronomic limits, so
HLHS is comparable across sites only while the same bounds are in use.

## Coefficient status

SOURCED: nothing in the construction.

UNSOURCED -- no source in the repository:
* all seven weights;
* five of the seven bound ranges, including the choice of 100 t/ha as a
  "perfect" soil organic carbon;
* the class thresholds 80/60/40/20.

The module's `REFERENCES` block cites Shannon (1948), a communication-theory
source, and Nagendra (2002). Neither is a source for min-max normalisation, for
the factor set, for any weight, or for any bound.

## Deliberate design choice worth recording

The carbon bound extends to **-2 tCO2/ha/yr**, so the index rewards emissions up
to a threshold rather than penalising them immediately. That is a policy choice,
not a scientific one, and it should be revisited when the weights are justified.

## Structure

The formula in the docstring, `HLHS = sum(w_i * (X_i - X_min)/(X_max - X_min))`,
is generic MCDA. The contribution is the specific factor set, the bounds and the
weights, not the normalisation.
""",
    "esri_salinity_risk": """
# EcoNojin Salinity Risk Index (ESRI)

Provenance: composite. The leaching-requirement component is published; the
factor set, the weights, the normalisations and the spectral index are this
project's.

## What it computes

    si_norm  = clip(si / 10, 0, 1)                                    [esri.py:92]
    ec_norm  = clip(ec_soil_dsm / 16, 0, 1)                           [esri.py:94]
    lr_gap   = clip(lr_required - actual_leaching_fraction, 0, 1)     [esri.py:97]
    ESRI     = 0.3*si_norm + 0.5*ec_norm + 0.2*lr_gap                [esri.py:99]

Spectral sub-index:

    si = sqrt(blue*red) / ((nir/(swir+1e-6)) * (blue/(red+1e-6)) + 1e-6)

Bands: 4 classes at 0.3 / 0.6 / 0.8.

## Inputs

Four reflectances, soil and irrigation water EC in dS/m, and the actual leaching
fraction applied.

## Domain of validity

Reflectance in the sensor's native units; soil and irrigation EC in dS/m; the
actual leaching fraction as a fraction in [0, 1]. Designed for the 0-16 dS/m range
the EC normaliser spans, so an EC above 16 saturates that factor by design rather
than by a clipping artefact.

## Coefficient status

SOURCED:
* `leaching_requirement = ECw / (5*ECe - ECw)`, bounded to (0, 0.95) -- FAO-29,
  Ayers & Westcot (1985), Rhoades (1974).

UNSOURCED -- no source in the repository:
* the 10 divisor in `si_norm` and the 16 divisor in `ec_norm`;
* the weights 0.3 / 0.5 / 0.2;
* the form of the four-band spectral sub-index, which appears in no cited work;
* the three `1e-6` epsilon guards;
* the class thresholds.

The `REFERENCES` block cites Ayers & Westcot and Richards (1954), which justify
the leaching requirement and nothing else.

## Design note

The dominant weight (0.5) sits on a raw EC normalisation, and the third factor is
a *deficit* -- required minus actual leaching fraction -- which is a
project-specific concept rather than a published quantity. That term is what
distinguishes this from a weighted average of salinity levels.
""",
    "hdvi_drought_vulnerability": """
# HyDroMa Drought Vulnerability Index (HDVI)

Provenance: composite. The three inputs are published indices; the combination
is this project's.

## What it computes

    vhi_norm = (vhi_value - 50) / 50 * 3                             [hdvi.py:101]
    smi_norm = (smi_value - 0.5) * 6                                [hdvi.py:102]
    HDVI     = 0.25*spi + 0.25*spei + 0.25*vhi_norm + 0.25*smi_norm [hdvi.py:104]
    HDVI     = clip(HDVI, -3, 3)

Bands: 4 classes at 0 / -1 / -2.

## Inputs and their sources

| input | source |
|---|---|
| `spi_value` | SPI, McKee et al. (1993) |
| `spei_value` | SPEI, Vicente-Serrano et al. (2010) |
| `vhi_value` | VCI, Kogan (1995) |
| `smi_value` | soil moisture index, rescaled here |

## Domain of validity

SPI and SPEI are standardised variates, in practice about [-4, 4]; VCI is 0-100;
SMI is 0-1. The rescalings assume those conventional ranges. Outside them the
equal weighting stops being meaningful, and the +/-3 clip conceals rather than
reports that.

## Coefficient status

SOURCED: the four component indices.

UNSOURCED -- no source in the repository:
* the two unit-bridging rescalings `(vhi-50)/50*3` and `(smi-0.5)*6`;
* the equal 0.25 weights;
* the +/-3 clip;
* the class thresholds.

## Purpose of the rescalings, and why it is a contribution

SPI and SPEI are standardised variates, roughly [-4, 4]. VCI is 0..100. The soil
moisture index is 0..1. Averaging them directly would let the standardised
indices dominate entirely. The two linear rescalings put VCI and SMI onto
approximately the same range as SPI/SPEI, so the equal weighting is meaningful.
That is a defensible construction, but the rescaling factors are currently
chosen without derivation.

## Known disconnect

`models/validation/test_cases/hdvi.yaml` names the model "Hydro-Drought
Vegetation Index" while the class is "Hydroma Drought Vulnerability Index", and
its declared inputs are `{ndvi, ndwi, lst, albedo}`, which do not match the
implemented `compute()` signature `{spi, spei, vhi, smi}`. The validation case is
disconnected from the code and must be corrected before it can serve as a gate.
""",
    "ewsi_water_stress": """
# EcoNojin Water Stress Index (EWSI)

Provenance: composite. The NDMI component is published; the factor set, the
weights and the VPD anchors are this project's.

## What it computes

    ndmi_stress = clip(1 - ndmi(nir, swir), 0, 1)                      [ewsi.py:117]
    vpd_stress  = clip((vpd_kpa - 0.5) / 3.5, 0, 1)                  [ewsi.py:120]
    soil_stress = clip(1 - (soil_moisture / soil_field_capacity), 0, 1) [ewsi.py:123]
    EWSI = 0.4*ndmi_stress + 0.3*vpd_stress + 0.3*soil_stress        [ewsi.py:126]

Weights default to 0.4 / 0.3 / 0.3 and are renormalised to sum to 1.

Bands: 4 classes at 0.3 / 0.6 / 0.8.

## Inputs

`nir`, `swir` reflectance, `vpd` in kPa, `soil_moisture` and
`soil_field_capacity` in the same volumetric units.

## Domain of validity

VPD in kPa, with the normalisation anchored over roughly 0.5-4 kPa; soil
moisture and field capacity as volumetric fractions, so the ratio is
dimensionless and unit-safe; NDMI in [-1, 1]. Not intended for a greenhouse or a
fully irrigated setting, where soil moisture is pinned near field capacity and
the third factor contributes nothing.

## Coefficient status

SOURCED: the NDMI sub-index, via Gao (1996).

UNSOURCED -- no source in the repository:
* the weights 0.4 / 0.3 / 0.3;
* the 0.5 and 3.5 kPa anchors in the VPD normalisation;
* the 1.1x field-capacity validation tolerance;
* the class thresholds.

Monteith (1993) is also cited and justifies the crop water exchange context, not
any term in the formula.

## Design note

The three factors are deliberately redundant in coverage: NDMI captures canopy
water content, VPD captures atmospheric demand, and the soil term captures
substrate availability. A plant under atmospheric stress but with adequate soil
moisture should score lower than one under both. That intent is stated; the
anchors that operationalise it are not sourced.

## Fixed during the formula work

`ndmi()` previously added a 1e-9 epsilon to the denominator and then called
`np.nan_to_num(result, nan=np.nan)`, which replaces NaN with NaN and does nothing.
Both are gone: the exact zero-denominator guard from the native kernels is used,
and the result is clipped to [-1, 1] as the native kernel does.
""",
    "multi_stress_amplification": """
# Combined-stress amplification and sodification risk

Provenance: novel.

## What it computes

Blanket amplification of independent stress factors [multi_stress_engine.py:14-15]:

    combined  = 1 - (1-heat)*(1-drought)*(1-salinity)
    amplified = min(1.0, combined * 1.5)

Sodification risk [multi_stress_engine.py:67-72]:

    salinity_stress  = clip((ec - 4) / 16, 0, 1)
    alkalinity_stress = clip((pH - 8.5) / 5.5, 0, 1)
    sodification_risk = min(1.0, 0.6*salinity_stress + 0.4*alkalinity_stress
                                   + 0.3*salinity_stress*alkalinity_stress)

## Domain of validity

`ec` in dS/m, pH in standard units, and the three stress factors each in [0, 1].

## Coefficient status

UNSOURCED -- and this is the important part.

The code carries a Persian comment at `multi_stress_engine.py:65-66` attributing
the 0.6 / 0.4 / 0.3 weighting to "the US Salinity Handbook", with salinity as the
primary factor at 60%, alkalinity as the amplifier at 40%, and a 30% interaction
term. **A repository-wide search finds no other reference to a "US Salinity
Handbook" anywhere.** The US document of that description is Richards (1954)
Agriculture Handbook 60, which is cited correctly in `soil/salinity.py:7-8` and
which contains no such weighting.

The 1.5 blanket amplification factor has no citation and no note beyond the
inline comment.

## Why this is still recorded as a contribution rather than deleted

The construction is defensible in its own terms: treating stresses as
independent failure modes and combining them as `1 - prod(1 - s_i)` is the
standard way to avoid double-counting, and the interaction term encodes the
real observation that salinity and alkalinity reinforce each other in sodic
soils. What is missing is the source for the specific numbers and the removal of
a citation that does not support them.

## Required before this is `verified`

Either cite a source for 0.6 / 0.4 / 0.3 and for the 1.5 amplification, or
restate the provenance as "chosen by this project" and remove the attribution.
Leaving an unsupported citation attached to a specific construction is the one
outcome that is not acceptable.
""",
    "hyrue_stress_coupling": """
# HY-RUE water-stress coupling

Provenance: composite. The RUE skeleton and the Beer-Lambert light interception
are published; the stress coupling is this project's.

## What it computes

    f_IPAR = 1 - exp(-k * LAI)                       Monteith (1977)      [hyrue.py:83]
    f_temp = exp(-((T - 25)/8)^2)  for 5 <= T <= 35, else 0            [hyrue.py:86-92]
    f_water = 1 - EWSI                                                 [hyrue.py:103]
    B = APAR * epsilon * f_IPAR * f_water * f_temp                    [hyrue.py:109]
    Y = B * days * harvest_index                                      [hyrue.py:124-125]

## Domain of validity

LAI up to the crop's saturating point, mean temperature 5-35 C (outside which
f_temp is 0), EWSI in [0, 1], and any number of days. The 5-35 C window is
deliberate: a crop outside it should be predicted at zero yield rather than at a
reduced rate.

## Coefficient status

SOURCED:
* the RUE form and Beer-Lambert f_IPAR, Monteith (1977);
* the g/m2 to t/ha conversion, 1 g/m2 = 0.1 t/ha.

UNSOURCED -- no source in the repository:
* the Gaussian width sigma = 8 C;
* the crop presets for epsilon, k and harvest index (hyrue.py:25-39);
* the coupling `f_water = 1 - EWSI`, which imports another project contribution;
* the photosynthetic active radiation fraction inside APAR.

## Design note

The multiplicative structure means any single factor can drive the yield to zero,
which is intended: a crop under severe water stress should not be predicted to
yield at a reduced rate. The 35 C ceiling on f_temp reflects that.

## Known defect fixed during the formula work

`CROP_PRESETS` was declared inside the dataclass without a type annotation, so it
was a bare class attribute rather than a field: invisible to `dataclasses.fields()`
and to any serialiser. `for_crop` also silently returned generic defaults for an
unknown crop name, so `HYRUE(crop="dragonfruit")` quietly modelled wheat.
""",
    "epia_precision_irrigation": """
# Precision irrigation advisor (EPIA)

Provenance: composite. The FAO-56 evapotranspiration frame is published; the
LAI-to-Kc mapping and the water-stress response are this project's.

## What it computes

    ETc = ET0 * Kc * Ks                                    FAO-56

    Kc = clip(kc_min + (kc_max - kc_min) * LAI/lai_max,
              kc_min, kc_max)            kc_min 0.1, kc_max 1.2, lai_max 6.0

    Ks = clip((TAW - Dr) / (TAW * (1 - p)), 0, 1)         FAO-56 eq. 84

## Why part of it is not a standard

FAO-56 derives Kc from crop HEIGHT through a curve over growth stages, not from
LAI, and that curve is not linear in LAI. The mapping used here is a linear ramp
with three free constants. The crop coefficient values themselves are therefore
this project's, and the resulting ETc carries an error that grows wherever the
real FAO-56 curve departs from a straight line -- that is, across most of the
season.

Separately, the water-stress term uses a hardcoded field capacity of 0.4 in the
depletion proxy, so it does not respond to soil type at all.

## Coefficient status

SOURCED:
* ETc = ET0 * Kc * Ks and the Ks shape: Allen et al. (1998) FAO-56; Jensen & Allen
  (2016). The module declares these in its REFERENCES dict.

UNSOURCED -- no source in the repository:
* the linear LAI-to-Kc ramp and its three constants (0.1, 1.2, 6.0);
* the field capacity 0.4 in the depletion proxy;
* the 0.3 / 0.8 / 1.1 Kc cut-offs in the growth-stage classifier.

## Known weakness in its validation

`validate_against_reference` is inherited from the abstract `ScientificModel`
base and returns whether the model ran, not whether it is accurate. Nothing
anchors the LAI ramp to a measured ETc.

## Domain of validity

Rainfall in mm, crop coefficient and soil moisture fraction both in [0, 1], LAI
from 0 up to the crop's saturating value. The linear Kc ramp is only meaningful
while LAI is below the point where the real FAO-56 curve bends, which is most of
the season -- outside that range the mapping is a guess, and nothing in the code
marks the difference. The depletion proxy assumes a field capacity of 0.4, so the
Ks term is not transferable to a soil with different texture without changing the
constant.

## Anchor cases

None exist yet. Adding a worked example -- LAI series plus the ETc it should
produce under a known FAO-56 crop coefficient curve -- is the first thing needed to
move this off stub.
""",
    "spatial_runoff": """
# Spatially distributed surface runoff

Provenance: composite. The per-cell equations are published; the spatial extension
is this project's.

## What it computes

Per cell, the same two published equations the point-scale model uses:

    SCS-CN:  S = (25400/CN) - 254  [mm];  Ia = 0.2 S;  Q = (P - Ia)^2 / (P + 0.8 S)
    Rational: Q = C * i * A / 360

mapped over a raster, with a land-use to Curve-Number lookup.

## Why part of it is not a standard

The land-use to Curve-Number mapping is a four-way branch:

    lu == 1 -> 60      lu == 2 -> 70
    lu == 3 -> 85      otherwise  -> 75

The function's own comment calls this "a simplified mapping" and says a real
implementation would use a lookup table. NRCS TR-55 Table 2A, which is the
published source, has ~50 land-use/condition/HSG rows; four branches is not an
approximation of it, it is a different thing.

The helper `_create_cn_map_from_lu_soil` accepts a `soil` argument and never
reads it, so **the soil texture has no effect on the Curve-Number map at all**,
despite the function name promising otherwise.

## Coefficient status

SOURCED: the SCS-CN and rational equations themselves.

UNSOURCED: the four CN branches; the spatial rasterisation itself.

## Known defect

Output filenames embed `hash(dem_path)`. Python's string hash is randomised per
process by PYTHONHASHSEED, so two runs over the same DEM write to different names
and the output directory accumulates non-reproducible rasters.

## Domain of validity

Rainfall in mm, Curve Number in 1..100, runoff coefficient in [0, 1], area in any
consistent unit, over a raster whose cells share one CRS. The four-branch
land-use mapping holds only for whatever discrete land-use classes the caller
happens to encode, and since the soil argument is ignored the map is a function
of land use alone.

## Anchor cases

Per-cell equivalence to the point-scale model on a constant-CN grid; and
sensitivity of the CN map to the soil argument, which currently is none and
should be asserted as such until it is implemented.
""",
    "koppen_geiger_class": """
# Koppen-Geiger climate classification (v5)

Provenance: composite. Peel et al. (2007) is the base, and the implementation
departs from it in two places it documents.

## What it computes

Standard Koppen-Geiger threshold classification, with two project modifications:

1. the ET (polar) buffer is 12 C where Peel et al. use 10 C;
2. the Am (monsoon) rule is replaced with two independent thresholds,
   `P_ann > 1500 and P_dry < 60`, where the published rule is
   `P_ann >= 100 * P_dry`.

## Why this is well documented and still not defensible as written

The two deviations are stated in the module docstring rather than presented as
the standard. That is the right habit and is the model the other composites
should follow.

What is not defensible is the accuracy claim. The module docstring asserts
"88.0% (22/25 countries validated with real climate data)", and:

* no country table, per-country result file, or script producing that figure
  exists anywhere in the repository;
* the figure is a module constant, not a measurement;
* `NEAR_MATCHES` is a 43-pair adjacency list that accepts adjacent Koppen
  LETTERS as valid. It includes cross-GROUP pairs such as BWh/Csa (hot desert vs
  hot-summer Mediterranean) and ET/Cfc (polar vs subpolar oceanic). A classifier
  that gets the Koppen group wrong still scores as correct, so the reported figure
  measures much less than it appears to.

There is also a hardcoded Berlin override in the validator.

## Coefficient status

SOURCED: the thresholds follow Peel et al. (2007), with the two departures
stated above.

UNSOURCED: the accuracy claim, and the "validated with real climate data"
assertion -- see the next section. The thresholds themselves trace to the
published classification; it is the measurement of the implementation against it
that has no artefact.

## Domain of validity

Monthly mean temperature and precipitation in degrees Celsius and mm, plus any
seasonal shift the caller supplies. The classification is defined for the
standard Koppen thresholds; the two deviations move the ET and Am boundaries, so
results in the polar and monsoon classes are this project's rather than Peel
et al.'s, and the docstring says so.

## What would make this verifiable

A country table with expected class per country, a script that runs the classifier
over it, and a metric that does not accept the wrong group. Until then the claim
is recorded, not counted.
""",
    "climate_adaptation_stress_engine": """
# Climate-adaptation stress engines

Provenance: novel. This is the project's own construction throughout, and it is
also the largest documentation gap in the engine.

## What it computes

About 25 numbered rules (h01..h25) across five classes in
`engine/hydroma/climate_adaptation/`:

    ClimateAdaptivePhenology      phenology shift under climate change
    DynamicStressEngine           VPD, night-temperature, ET and stress response
    SoilDegradationModel          AWC, root depth, salinity, compaction, fertility
    UncertaintyAndKnowledgeEngine Monte Carlo uncertainty, multi-scale fusion
    SeedOptimizationEngine        seed selection under scenario

The two rules that were reviewed in this work are the sodification risk and the
blanket stress amplification; they are documented in
`multi_stress_amplification` above.

## Coefficient status

SOURCED, and only as inline comments in two files:
* dynamic_stress_engine.py cites IPCC AR6 (2021), Yuan et al. (2019),
  Zhang et al. (2020), Zscheischler et al. (2018);
* soil_degradation_model.py cites IPCC AR6 WG2 (2022), FAO GSP (2021), GLASOD (1991).

UNSOURCED: every numeric constant in the remaining rules, and the rule
interactions themselves.

## The documentation gap, stated plainly

There is no REFERENCES dict anywhere in the package. Two of the five classes
carry an inline comment citation; three do not, and four of the five have no
class docstring at all. The rule numbering (h01..h25) suggests a specification
that exists somewhere outside this repository and was never brought in.

This record therefore registers the family so the gap is visible and owned rather
than absent. It is `stub` because a scientific contribution with undocumented
coefficients is unfinished, not because the construction is wrong.

## Domain of validity

Monthly or daily climate normals, soil properties in the units each class
expects, and scenario projections. The rules are calibrated to the cited
assessments' resolution; a monthly rule applied to daily input, or a rule
transferred between agro-ecological zones, is outside what any of them was
estimated for, and nothing in the code records the resolution each rule was
fitted at.

## What would make this publishable

1. The rule specification behind the h-numbers, or a decision that the numbering
   is historical and to be replaced by named rules.
2. A citation per rule, or an explicit statement that a rule is heuristic.
3. Class docstrings for the four that lack them.
4. At least one worked case per rule with a hand-checkable expected value.
""",
    "hpheno_phenology": """
# Phenology detection from an NDVI series

Provenance: composite. The phenological metrics and the Savitzky-Golay method
are published; the detection sequence built on them is this project's.

## What it computes

From a smoothed NDVI series:

    smoothed = Savitzky-Golay(NDVI, window, polyorder)
    rate     = d(smoothed)/dt
    green-up / peak / senescence crossings of the rate
    from     = integral of NDVI above the seasonal baseline
    to       = integral between the crossings

## Why the environment-independence mattered

The module previously called `scipy.signal.savgol_filter` and, when scipy was
absent, fell back to `np.convolve(mode="same")` -- a centred MOVING AVERAGE. A
moving average has no derivative-preserving property, so every downstream
zero-crossing and `np.gradient` changed meaning depending on whether an optional
dependency was installed. The same code could report a different sowing date on two
machines with the same data.

The kernel is now computed directly from the pseudo-inverse of the window's
Vandermonde matrix, and the window is always valid and odd, so the two failure
paths are gone rather than guarded.

## Domain of validity

NDVI in [-1, 1] at a regular time step; a window that is short relative to the
phenological signal and long enough to suppress noise; a series long enough to
carry at least one full season. With fewer than 12 observations `validate_inputs`
fails, but `compute` does not call `validate_inputs`, so a short series is
silently smoothed.

## Coefficient status

SOURCED:
* the phenological metrics: Zhang, X. et al. (2003) Monitoring vegetation
  phenology with MODIS; White, J.C. et al. (2009) Derivation of phenological
  metrics from MODIS NDVI;
* the Savitzky-Golay filter: Savitzky & Golay (1964), via its polynomial-exactness
  property.

UNSOURCED: the default window of 11 points and polyorder of 3, neither tied to a
sampling interval or a crop.

## What is verified

* The kernel is the correct Savitzky-Golay polynomial filter, not a moving
  average: it reproduces a polynomial of the fitting order exactly, passes a
  constant and a linear signal through unchanged, and preserves the amplitude of
  a slow sinusoid. Those are the properties that define the method, and the tests
  assert them.
* The result is byte-identical whether or not scipy is installed, and the window
  is always valid and odd, so the two former failure paths are gone rather than
  guarded.

## What is not verified

* The default window of 11 points and polyorder of 3. They are not tied to the
  sampling interval or the crop, so the detection dates the method produces are
  only as good as an unexamined default.
* Every metric downstream of the crossings -- integrated area, phase, amplitude
  -- is asserted for behaviour but not against a published phenology record for a
  known site and season.

## Anchor cases

The tests assert the properties that define the method rather than a stored
number: a polynomial of the fitting order is reproduced exactly, a constant and a
linear signal pass through unchanged, and the result is byte-identical with scipy
absent.
""",
    "core_soil_health_score": """
# Soil health score (HyDroMa core)

Provenance: composite. The component optima are standard agronomic values; the
weighted combination is this project's.

## What it computes

    ph_score   = 100 if 6.0 <= pH <= 7.5 else max(0, 100 - |pH - 6.75|*15)
    om_score   = min(100, organic_matter_pct * 40)
    tex_score  = 100 / 70 / 40 by texture class band
    clay_score = 100 if 0.15 <= clay_fraction <= 0.35 else 60
    score = 0.25*ph + 0.30*om + 0.25*tex + 0.20*clay          [core/core.py:96]

## Attribution problem

The docstring says "Based on USDA Soil Quality Index". The USDA NRCS Soil Quality
Index (Andrews et al., 2002) is a real published method, but it is a
**principal-components** index, not a hand-weighted linear combination, and the
weights 0.25 / 0.30 / 0.25 / 0.20 appear nowhere in it. The attribution names a
standard that does not define this construction.

## Domain of validity

pH 0-14, organic matter 0-100 percent, clay fraction 0-1, and an integer texture
class. The pH term is linear away from 6.0-7.5 and floored at 0, so pH 3 and pH 4
score identically.

## Coefficient status

SOURCED (agronomic optima, used as component ranges): pH 6.0-7.5; organic matter
saturating at 2.5%; clay 15-35%.

UNSOURCED: the four weights; the 15 per pH unit in `ph_score`; the `* 40` in
`om_score`; the 60 fallback in `clay_score`.

## Two related constructions that must not be confused

A second, differently-constructed soil health score exists at
`engine/hydroma/wrapper.py:119-132`: a 50-base additive bonus scheme
(+20 neutral pH, +15 high organic matter, +5 each for in-range N, P, K). Same
intended quantity, different formula. Both are reachable from the API.

## Also in this file, and more serious

`rusle_soil_loss` in `core/core.py:273-276` multiplies the RUSLE product by a
default `calibration` of 0.10. RUSLE is `A = R K LS C P`; a blanket tenth is not
part of it, the parameter is not cited, and it is absent from the native kernel
(`erosion.cpp:19`), which implements the plain product. This is a published
quantity silently scaled by ten.

The same file's `estimate_carbon_sequestration_potential` applies
`method_potentials * climate_multiplier * texture_multiplier` using a 6x4 table of
unexplained multipliers (`no_till 0.3-0.8`, `biochar 2.0-5.0`, `tropical 1.3`,
`cold 0.5`, `clay 1.2` ... `sand 0.9`) attributed only to "IPCC-based factors".
A second, different set of climate multipliers appears in
`carbon/calculator.py:166-170` for the same concept.
""",
}
