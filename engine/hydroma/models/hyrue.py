"""
HY-RUE — Hydroma Radiation Use Efficiency Model

Based on Monteith (1977) with satellite LAI retrieval.

    B_daily = PAR * f_IPAR(LAI) * epsilon * f_water(EWSI) * f_temp(T)
    B_total = B_daily * days          (scalar mode: constant-conditions estimate)
    B_total = sum(B_daily)            (seasonal mode: daily integration over arrays)
    Y       = B_total * HI

Two calling modes:

Scalar mode (daily estimate): par is a scalar. days multiplies the result.
This is a constant-conditions approximation: it assumes identical LAI, water,
and temperature for the whole period. It is fast but overstates seasonal
totals when conditions vary seasonally.

Seasonal mode (temporal integration): par is an array (one value per day)
alongside array lai, ewsi, and t_mean of matching length. The model computes
per-day biomass and sums the daily values into a seasonal total. This is the
physically correct way to accumulate biomass over a growing season.

REFERENCE: Monteith (1977), Steduto et al. (2009)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, ClassVar

import numpy as np

from .base import ScientificModel, ValidationResult, relative_error_of, validate_finite


@dataclass
class HYRUEParams:
    """پارامترهای مدل HY-RUE"""

    epsilon: float = 2.5  # RUE (g/MJ IPAR)
    # `k` is the light-extinction coefficient of Beer-Lambert, conventionally
    # 0.46-0.75 depending on canopy and row spacing; 0.65 sits in that band but
    # the specific value is a choice, not a derivation, and Monteith (1977)
    # does not fix it.
    k: float = 0.65
    hi: float = 0.45  # Harvest index
    # Maximum canopy LAI fed to the light-interception curve. This IS wired
    # now: `f_ipar` clips the canopy at this value before the Beer-Lambert
    # exponential, so a LAI above it no longer increases interception (a
    # denser-than-`lai_max` canopy is physically impossible). It was formerly
    # a recorded defect (declared but never read).
    lai_max: float = 6.0
    t_opt: float = 25.0  # Optimal temperature (°C)
    # RECORDED DEFECT: the Gaussian width is hard-coded to 8 in
    # `stress_temperature` and cannot be set per crop. Steduto et al. (2009)
    # (AquaCrop) parameterise the temperature stress by explicit cardinal
    # temperatures per crop rather than by a Gaussian width, so the three
    # values below have no source and the width has nowhere to live.
    t_min: float = 5.0
    t_max: float = 35.0

    # Crop-specific presets. They supply only epsilon, hi and t_opt, which
    # means k, t_min, t_max and lai_max fall back to the unsourced generic
    # values above for every crop. A wheat canopy and a maize canopy are given
    # the same extinction coefficient and the same thermal window.
    CROP_PRESETS: ClassVar[dict[str, Any]] = {
        "wheat": {"epsilon": 2.2, "hi": 0.45, "t_opt": 20.0},
        "maize": {"epsilon": 3.3, "hi": 0.50, "t_opt": 25.0},
        "rice": {"epsilon": 2.2, "hi": 0.45, "t_opt": 28.0},
        "potato": {"epsilon": 2.8, "hi": 0.75, "t_opt": 18.0},
    }

    @classmethod
    def for_crop(cls, crop_name: str) -> HYRUEParams:
        presets = cls.CROP_PRESETS.get(crop_name.lower())
        if presets:
            return cls(**presets)
        return cls()


class HYRUE(ScientificModel):
    """Hydroma Radiation Use Efficiency Model.

    Supports two modes via :meth:`compute`:

    * **Scalar mode** -- ``par`` is a scalar; ``days`` multiplies the result
      (constant-conditions estimate).
    * **Seasonal mode** -- ``par`` is an array of daily values alongside
      matching-length arrays for ``lai``, ``ewsi``, ``t_mean``; daily biomass
      is computed per day and **summed** into the seasonal total.
    """

    name = "HY-RUE"
    version = "2.0.0"
    description = "Radiation Use Efficiency with satellite LAI; supports daily integration"

    #: The RUE form and Beer-Lambert interception are Monteith's. The Gaussian
    #: width, the crop presets, the unsourced thermal window and the
    #: `days`-as-multiplier treatment are this project's own.
    PROVENANCE: ClassVar[str] = "composite"

    REFERENCES: ClassVar[dict[str, str]] = {
        "Monteith1977": "Monteith, J.L. (1977). Climate and the efficiency of crop production in Britain. Phil Trans R Soc B, 281, 277-294.",
        "Steduto2009": "Steduto et al. (2009). AquaCrop-The FAO crop model. Agronomy Journal, 101(3), 426-437.",
    }

    def __init__(self, params: HYRUEParams | None = None, crop: str | None = None, **config):
        super().__init__(**config)
        if params is not None:
            # Explicit parameters win.  They are a complete, self-consistent
            # parameter set, and a caller that supplies them is evaluating a
            # specific model (e.g. a calibrated or frozen one) rather than
            # asking for a crop preset.  Letting the crop preset override
            # them would silently discard the caller's values -- the defect
            # that made a calibrated model evaluate as the uncalibrated
            # default.
            self.params = params
        elif crop:
            self.params = HYRUEParams.for_crop(crop)
        else:
            # Generic, crop-neutral default. The Gaussian thermal response is
            # centred on t_opt = 25 degC, so for temperatures below 25 degC
            # WARMING INCREASES predicted yield. That is an artifact of the
            # crop-neutral default, not a validated or generally true crop
            # response (wheat etc. decline with warming once past their own,
            # lower optimum). The default path is therefore flagged rather than
            # trusted: pass a crop for the crop-specific optimum, e.g.
            # HYRUE(crop="wheat") or HYRUE(params=HYRUEParams(...)) with an
            # explicit t_opt.
            warnings.warn(
                "HYRUE() built with generic crop-neutral defaults (t_opt=25 C). "
                "Below 25 C this default can make warming INCREASE predicted "
                "yield, which is a default artifact, not a validated crop "
                "response. Pass a crop (HYRUE(crop='wheat')) or explicit "
                "HYRUEParams for a crop-specific thermal response.",
                stacklevel=2,
            )
            self.params = HYRUEParams()

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def validate_inputs(  # type: ignore[override]
        self, par, lai, ewsi, t_mean, days: int = 1
    ) -> tuple[bool, list[str]]:
        errors = validate_finite(
            "HYRUE",
            {"par": par, "lai": lai, "ewsi": ewsi, "t_mean": t_mean, "days": days},
        )

        if errors:
            return False, errors
        # --- Reject empty arrays (no data to compute) ---
        par_arr = np.asarray(par, dtype=float) if not np.isscalar(par) else par
        lai_arr = np.asarray(lai, dtype=float) if not np.isscalar(lai) else np.asarray([lai])
        ewsi_arr = np.asarray(ewsi, dtype=float) if not np.isscalar(ewsi) else np.asarray([ewsi])
        t_scalar_or_arr = np.asarray(t_mean, dtype=float) if not np.isscalar(t_mean) else None

        if np.ndim(par_arr) > 0 and par_arr.size == 0:
            errors.append("par array must not be empty")
        if lai_arr.size == 0:
            errors.append("lai array must not be empty")
        if ewsi_arr.size == 0:
            errors.append("ewsi array must not be empty")
        if t_scalar_or_arr is not None and t_scalar_or_arr.size == 0:
            errors.append("t_mean array must not be empty")

        if errors:
            return False, errors
        # --- PAR range (scalar or array) ---
        if np.any((par_arr < 0) | (par_arr > 50)):
            errors.append(f"PAR {par} MJ/m² out of range [0, 50]")
        # --- LAI range ---
        if np.any((lai_arr < 0) | (lai_arr > 10)):
            errors.append("LAI out of range [0, 10]")
        # --- EWSI range ---
        if np.any((ewsi_arr < 0) | (ewsi_arr > 1)):
            errors.append("EWSI out of range [0, 1]")
        # --- Temperature range (scalar or array) ---
        t_arr = t_scalar_or_arr if t_scalar_or_arr is not None else t_mean
        if np.any((t_arr < -10) | (t_arr > 50)):
            errors.append(f"Temperature {t_mean}°C out of range [-10, 50]")
        # `days` is accepted by `compute` and multiplies the whole result in
        # scalar mode, but `validate_inputs` did not declare it, so
        # `compute_checked` filtered it out and
        # `compute_checked(model, ..., days=-5)` returned a negative
        # total biomass from a validated call. It is validated here now.
        if isinstance(days, bool) or not isinstance(days, (int, np.integer)):
            errors.append(f"days must be an integer, got {days!r}")
        elif not (1 <= days <= 366):
            errors.append(f"days {days} out of range [1, 366]")
        # --- Array length consistency ---
        # When par is an array (seasonal mode), lai, ewsi and t_mean must
        # be arrays or scalars of compatible shape. NumPy broadcasting
        # handles scalars, but mismatched array lengths must not be silently
        # truncated or padded.
        if np.ndim(par_arr) > 0:
            par_len = par_arr.size
            for name, arr in [("lai", lai_arr), ("ewsi", ewsi_arr)]:
                if np.ndim(arr) > 0 and arr.size != par_len:
                    errors.append(
                        f"{name} array length {arr.size} does not match par length {par_len}"
                    )
            if t_scalar_or_arr is not None and np.ndim(t_scalar_or_arr) > 0:
                if t_scalar_or_arr.size != par_len:
                    errors.append(
                        f"t_mean array length {t_scalar_or_arr.size} does not match par length {par_len}"
                    )
        return len(errors) == 0, errors

    @staticmethod
    def f_ipar(lai: np.ndarray, k: float = 0.65, lai_max: float | None = None) -> np.ndarray:
        """Fraction of intercepted PAR (Beer-Lambert).

        ``lai_max``, when given, caps the canopy before the extinction curve:
        a LAI above it no longer increases interception. This is where
        ``HYRUEParams.lai_max`` is consumed (previously a dead parameter). When
        omitted the historical [0, 20] guard is used, so the two-argument call
        ``f_ipar(lai, k)`` is unchanged.
        """
        canopy = np.clip(lai, 0, lai_max) if lai_max is not None else np.clip(lai, 0, 20)
        return 1 - np.exp(-k * canopy)

    @staticmethod
    def stress_temperature(
        t_mean: float, t_opt: float = 25.0, t_min: float = 5.0, t_max: float = 35.0
    ) -> float:
        """Temperature stress factor (Gaussian response).

        The Gaussian width of 8 °C is hard-coded and has no source; see
        ``HYRUEParams``. A per-crop thermal response is what Steduto et al.
        (2009) parameterise, by explicit cardinal temperatures rather than a
        width, so the number here is a platform choice. ``t_min`` and
        ``t_max`` are an explicit cutoff: a Gaussian never reaches zero, so
        without them a plant at 60 °C reports a small non-zero stress factor
        rather than no growth.
        """
        if t_mean < t_min or t_mean > t_max:
            return 0.0
        return float(np.exp(-(((t_mean - t_opt) / 8) ** 2)))

    def compute_daily(
        self,
        par,
        lai,
        ewsi,
        t_mean,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute per-day biomass for the given inputs.

        ``par`` and ``t_mean`` may each be a scalar or a 1-D array. ``lai`` and
        ``ewsi`` may be scalars, 1-D arrays, or Python lists. All numeric
        arrays are broadcast together, so a call with N-element arrays returns
        N daily biomass values -- one per day.

        A scalar ``t_mean`` (with array ``lai``/``ewsi``) applies that
        temperature to every day. A scalar ``par`` applies that PAR to every
        day.
        """
        lai_arr = np.asarray(lai, dtype=float)
        ewsi_arr = np.asarray(ewsi, dtype=float)
        par_arr = np.asarray(par, dtype=float) if not np.isscalar(par) or isinstance(par, np.ndarray) else par
        t_arr = np.asarray(t_mean, dtype=float) if not np.isscalar(t_mean) or isinstance(t_mean, np.ndarray) else t_mean

        f_ipar = self.f_ipar(lai_arr, self.params.k, self.params.lai_max)
        # EWSI (Evapotranspiration Water Stress Index) is a STRESS index in
        # [0, 1] where 0 = no water stress and 1 = severe stress (see
        # engine/hydroma/models/ewsi.py and the EWSI_INTERPRETATION table:
        # 0.0-0.2 well-watered ... 0.8-1.0 severe stress). The water multiplier
        # is therefore its complement: f_water = 1 - EWSI, so f_water = 1 means
        # no stress and 0 means complete water limitation.
        f_water = 1 - ewsi_arr

        t_min_arr = self.params.t_min
        t_max_arr = self.params.t_max
        t_as_arr = np.asarray(t_arr) if np.ndim(t_arr) > 0 else t_arr
        t_above = t_as_arr > t_max_arr
        t_below = t_as_arr < t_min_arr
        t_clipped = np.where(t_below | t_above, self.params.t_opt, t_as_arr)
        f_temp = np.exp(-(((t_clipped - self.params.t_opt) / 8) ** 2))
        f_temp = np.where(t_below | t_above, 0.0, f_temp)

        apár = par_arr * f_ipar
        biomass = apár * self.params.epsilon * f_water * f_temp

        return f_ipar, biomass

    def compute(  # type: ignore[override]
        self,
        par,
        lai: np.ndarray,
        ewsi: np.ndarray,
        t_mean,
        days: int = 1,
    ) -> dict[str, Any]:
        """Compute biomass and yield.

        Three calling modes are supported, distinguished by whether ``par``
        is an array and whether ``days`` is greater than one:

        **Daily mode:** ``par`` is a scalar and ``days == 1`` (the default).
        ``lai``, ``ewsi``, ``t_mean`` may be scalars or same-length arrays;
        when arrays are given the model evaluates one day per element (scalar
        ``par`` is broadcast to every day). The result carries a per-day
        biomass array and, if the broadcast produced more than one day, a
        scalar total that is the sum of those daily values — NOT a
        multiplication by ``days``.

        **Seasonal mode:** ``par`` is an array (one value per day) alongside
        array ``lai``, ``ewsi``, and ``t_mean`` of matching length. The model
        computes per-day biomass and **sums** the daily values into a seasonal
        total. This is the physically correct way to accumulate biomass over a
        growing season: each day contributes its own light, stress, and
        temperature.

        **Legacy constant-conditions mode:** ``par`` is a scalar and
        ``days > 1``. The model assumes identical LAI, water, and temperature
        for the entire period and multiplies the single-day biomass by
        ``days``. This is a fast approximation that overstates seasonal totals
        when conditions vary — prefer Seasonal mode when daily data is
        available.

        WHAT THIS COMPUTES, PRECISELY:

            f_IPAR  = 1 - exp(-k * min(LAI, lai_max))     (Beer-Lambert)
            f_water = 1 - EWSI
            f_temp  = exp(-((T - T_opt) / 8) ** 2)         (Gaussian)
            B_day   = PAR * f_IPAR * epsilon * f_water * f_temp

        Daily mode (par scalar, days == 1):
            B_total = sum(B_day)         # sum of per-day broadcast values
            Y       = B_total * HI / 100  # g/m² -> t/ha

        Seasonal mode (par array):
            B_total = sum(B_day)
            Y       = B_total * HI / 100

        Legacy mode (par scalar, days > 1):
            B_total = daily_biomass * days
            Y       = B_total * HI / 100

        EWSI semantics: EWSI (Evipotranspiration Water Stress Index,
        ``engine/hydroma/models/ewsi.py``) is a STRESS index in [0, 1] where
        0 = no water stress and 1 = severe water stress. ``f_water`` is its
        complement ``1 - EWSI``, so ``f_water = 1`` means the crop was fully
        water-supplied (EWSI = 0) and ``f_water = 0`` means total water
        limitation (EWSI = 1).

        WARNING: legacy mode with ``days > 1`` assumes constant conditions
        (LAI, water, temperature) for the entire period. A real growing season
        sees LAI rise from near zero, peak, and senesce; multiplying a single-
        day figure by the season length overstates seasonal biomass.
        Prefer seasonal mode (array ``par``) when daily data is available.
        """
        f_ipar, daily_biomass = self.compute_daily(par, lai, ewsi, t_mean)

        if np.ndim(par) > 0:
            # Seasonal mode: par is a daily array, so sum daily biomass.
            total_biomass = float(np.sum(daily_biomass))
            yield_value = total_biomass * self.params.hi
            return {
                "computation_mode": "seasonal",
                "f_ipar": np.asarray(f_ipar).tolist(),
                "daily_biomass_g_m2": np.asarray(daily_biomass).tolist(),
                "total_biomass_g_m2": total_biomass,
                "yield_g_m2": float(yield_value),
                "yield_t_ha": float(yield_value) / 100,
                "season_length_days": int(np.asarray(par).size),
            }

        # Scalar par: decide between daily (days==1) and legacy (days>1).
        if days > 1:
            # Legacy constant-conditions mode: multiply single-day biomass
            # by days. This overstates seasonal totals when conditions vary.
            total_biomass = daily_biomass * days
            yield_value = total_biomass * self.params.hi
            return {
                "computation_mode": "legacy_constant",
                "f_ipar": np.asarray(f_ipar).tolist(),
                "daily_biomass_g_m2": np.asarray(daily_biomass).tolist(),
                "total_biomass_g_m2": total_biomass,
                "yield_g_m2": yield_value,
                "yield_t_ha": yield_value / 100,
                "assumed_days": days,
                "warning": (
                    "Legacy constant-conditions mode: biomass assumes identical "
                    "LAI, water, and temperature for all days. Use seasonal "
                    "mode (array par) for physiologically correct integration."
                ),
            }

        # Daily mode (days == 1): par is scalar.
        # When all inputs are scalar, daily_biomass is a scalar — a single
        # day's biomass. When lai/ewsi/t_mean are arrays, daily_biomass is
        # an array of per-day values (constant PAR broadcast to each day).
        # The latter is NOT summed — each day is evaluated independently.
        if np.ndim(daily_biomass) > 0:
            # Daily series with constant scalar PAR: per-day results.
            # yield_t_ha is an array (one per day) to preserve backward
            # compatibility with reduce: last in the YAML validation cases.
            yield_per_day = daily_biomass * self.params.hi
            return {
                "computation_mode": "daily_series",
                "f_ipar": np.asarray(f_ipar).tolist(),
                "daily_biomass_g_m2": np.asarray(daily_biomass).tolist(),
                "total_biomass_g_m2": np.asarray(daily_biomass),  # not a sum, per-day
                "yield_g_m2": yield_per_day,  # array, one per day
                "yield_t_ha": yield_per_day / 100,  # array, one per day
                "n_days_evaluated": int(np.asarray(daily_biomass).size),
                "constant_par": float(par),  # the scalar PAR applied to each day
            }

        # Pure scalar (single day, all inputs scalar): daily_biomass is scalar.
        total_biomass = float(daily_biomass)
        yield_value = total_biomass * self.params.hi
        return {
            "computation_mode": "daily",
            "f_ipar": float(f_ipar),
            "daily_biomass_g_m2": total_biomass,
            "total_biomass_g_m2": total_biomass,
            "yield_g_m2": float(yield_value),
            "yield_t_ha": float(yield_value) / 100,
            "n_days_evaluated": 1,
        }

    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.2,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["yield_t_ha"]))

        relative_error = relative_error_of(computed_value, reference_output)

        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="Yield (t/ha)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
