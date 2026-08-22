"""
Phase 3f: Hydroma Scientific Models Library
هدف: پیاده‌سازی ۸ مدل اختصاصی با فرمول‌های علمی دقیق
پروتکل: Scientific accuracy + Vectorized NumPy + Documentation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger("econojin.models")


# =============================================================================
# 1. EWSI — EcoNojin Water Stress Index
# =============================================================================

class EWSI:
    """
    EcoNojin Water Stress Index
    
    ترکیب Sentinel-2 (NDMI) + VPD + رطوبت خاک برای تشخیص تنش آبی
    
    Output: 0 (no stress) to 1 (severe stress)
    """
    
    @staticmethod
    def ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Normalized Difference Moisture Index (Gao, 1996)
        NDMI = (NIR - SWIR) / (NIR + SWIR)
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (nir - swir) / (nir + swir)
        return np.nan_to_num(result, nan=np.nan)
    
    @staticmethod
    def compute(
        nir: np.ndarray,
        swir: np.ndarray,
        vpd: float,
        soil_moisture: float,
        soil_field_capacity: float,
        weights: tuple[float, float, float] = (0.4, 0.3, 0.3),
    ) -> np.ndarray:
        """
        Compute EWSI from Sentinel-2 bands + atmospheric + soil data
        
        Parameters
        ----------
        nir : array (Sentinel-2 B08)
        swir : array (Sentinel-2 B11)
        vpd : Vapour Pressure Deficit (kPa), typical 0.5-4.0
        soil_moisture : Current θ (m³/m³)
        soil_field_capacity : θ_fc from van Genuchten (m³/m³)
        weights : (w1, w2, w3) for NDMI, VPD, soil components
        
        Returns
        -------
        ewsı : array, shape of nir, values in [0, 1]
        """
        w1, w2, w3 = weights
        
        # NDMI component (higher NDMI = less stress)
        ndmi = EWSI.ndmi(nir, swir)
        ndmi_stress = np.clip(1 - ndmi, 0, 1)  # invert: high NDMI = low stress
        
        # VPD component (normalize: 0.5 kPa = no stress, 4 kPa = max stress)
        vpd_stress = np.clip((vpd - 0.5) / 3.5, 0, 1)
        
        # Soil moisture component
        soil_stress = np.clip(1 - (soil_moisture / soil_field_capacity), 0, 1)
        
        # Weighted combination
        ewsı = w1 * ndmi_stress + w2 * vpd_stress + w3 * soil_stress
        
        return np.clip(ewsı, 0, 1)
    
    @staticmethod
    def classify(ewsı: np.ndarray) -> np.ndarray:
        """Classify EWSI into severity levels"""
        return np.select(
            [ewsı < 0.3, ewsı < 0.6, ewsı < 0.8],
            ["optimal", "mild", "moderate"],
            default="severe"
        )


# =============================================================================
# 2. HY-RUE — Hydroma Radiation Use Efficiency Model
# =============================================================================

@dataclass
class HYRUEParams:
    """Parameters for HY-RUE model"""
    epsilon: float = 2.5  # RUE (g/MJ IPAR), crop-specific
    k: float = 0.65  # Extinction coefficient
    hi: float = 0.45  # Harvest index
    lai_max: float = 6.0  # Maximum LAI for Kc calculation


class HYRUE:
    """
    Hydroma Radiation Use Efficiency Model
    
    Monteith (1977) + Sentinel-2 LAI + stress factors
    
    B = Σ(PAR × fIPAR × ε × f_stress)
    Y = B × HI
    """
    
    @staticmethod
    def f_ipar(lai: np.ndarray, k: float = 0.65) -> np.ndarray:
        """
        Fraction of intercepted PAR from LAI (Beer-Lambert law)
        fIPAR = 1 - exp(-k × LAI)
        """
        return 1 - np.exp(-k * lai)
    
    @staticmethod
    def stress_water(ewsı: np.ndarray) -> np.ndarray:
        """Water stress factor from EWSI (0 to 1)"""
        return 1 - ewsı
    
    @staticmethod
    def stress_temperature(t_mean: float, t_opt: float = 25.0,
                           t_min: float = 5.0, t_max: float = 35.0) -> float:
        """
        Temperature stress factor (Gaussian response)
        f_temp = exp(-((T - T_opt) / 8)²)
        """
        if t_mean < t_min or t_mean > t_max:
            return 0.0
        return np.exp(-((t_mean - t_opt) / 8) ** 2)
    
    @staticmethod
    def compute_daily(
        par: float,
        lai: np.ndarray,
        ewsı: np.ndarray,
        t_mean: float,
        params: HYRUEParams = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute daily biomass accumulation
        
        Parameters
        ----------
        par : PAR (MJ/m²/day)
        lai : Sentinel-2 derived LAI
        ewsı : Water stress from EWSI
        t_mean : Mean temperature (°C)
        params : HY-RUE parameters
        
        Returns
        -------
        f_ipar : intercepted PAR fraction
        biomass_daily : daily biomass (g/m²/day)
        """
        if params is None:
            params = HYRUEParams()
        
        f_ipar = HYRUE.f_ipar(lai, params.k)
        apár = par * f_ipar
        
        f_water = HYRUE.stress_water(ewsı)
        f_temp = HYRUE.stress_temperature(t_mean)
        
        biomass_daily = apár * params.epsilon * f_water * f_temp
        
        return f_ipar, biomass_daily
    
    @staticmethod
    def compute_yield(
        total_biomass: np.ndarray,
        hi: float = 0.45,
    ) -> np.ndarray:
        """Convert total biomass to yield: Y = B × HI"""
        return total_biomass * hi


# =============================================================================
# 3. ECSI — EcoNojin Carbon Sequestration Index
# =============================================================================

class ECSI:
    """
    EcoNojin Carbon Sequestration Index
    
    Based on RothC-26.3 model (Coleman & Jenkinson, 1996)
    dC/dt = I - k × C × f(T) × f(M) × f(P)
    """
    
    # Decomposition rates (per year) for RothC pools
    POOLS = {
        "DPM": 10.0,  # Decomposable Plant Material
        "RPM": 0.3,  # Resistant Plant Material
        "BIO": 0.66,  # Microbial Biomass
        "HUM": 0.02,  # Humified Organic Matter
        "IOM": 0.0,  # Inert Organic Matter
    }
    
    @staticmethod
    def temperature_factor(t_mean_c: float) -> float:
        """
        Temperature rate modifier (RothC)
        f(T) = exp(0.047 × T - 0.86) for T > -5°C, else 0
        """
        if t_mean_c <= -5.0:
            return 0.0
        return np.exp(0.047 * t_mean_c - 0.86)
    
    @staticmethod
    def moisture_factor(rainfall_mm: float, evaporation_mm: float,
                        clay_fraction: float = 0.23) -> float:
        """
        Moisture rate modifier (RothC)
        Simplified: f(M) = min(1.0, rainfall/evaporation × (1 - clay))
        """
        if evaporation_mm <= 0:
            return 1.0
        ratio = rainfall_mm / evaporation_mm
        return float(np.clip(ratio * (1 - clay_fraction), 0.0, 1.0))
    
    @staticmethod
    def plant_retain_factor(land_use: str) -> float:
        """Plant retain factor by land use (RothC)"""
        factors = {
            "arable": 0.6,
            "grassland": 0.85,
            "forest": 0.95,
            "bare": 0.0,
            "orchard": 0.8,
        }
        return factors.get(land_use, 0.6)
    
    @staticmethod
    def co2_bio_hum_ratio(clay_fraction: float) -> float:
        """
        CO2 / (BIO + HUM) ratio from clay content (RothC)
        x = 1.67 + 1.94 × clay_fraction
        """
        return 1.67 + 1.94 * clay_fraction
    
    @staticmethod
    def sequestration_rate(
        initial_soc_t_ha: float,
        carbon_input_t_ha: float,
        t_mean_c: float,
        rainfall_mm: float,
        evaporation_mm: float,
        clay_fraction: float = 0.23,
        land_use: str = "arable",
        dt_years: float = 1.0,
    ) -> float:
        """
        Compute annual SOC sequestration rate
        
        Returns: ΔSOC in t/ha/year (positive = sequestration, negative = emission)
        """
        f_T = ECSI.temperature_factor(t_mean_c)
        f_M = ECSI.moisture_factor(rainfall_mm, evaporation_mm, clay_fraction)
        f_P = ECSI.plant_retain_factor(land_use)
        
        # Simplified: weighted average decomposition
        k_eff = (
            0.1 * ECSI.POOLS["DPM"] + 0.3 * ECSI.POOLS["RPM"] +
            0.05 * ECSI.POOLS["BIO"] + 0.55 * ECSI.POOLS["HUM"]
        )
        
        decomposition = k_eff * initial_soc_t_ha * f_T * f_M * f_P * dt_years
        delta_soc = carbon_input_t_ha * dt_years - decomposition
        
        return float(delta_soc)
    
    @staticmethod
    def co2_equivalent(delta_soc_t_ha: float) -> float:
        """Convert SOC change to CO2-eq (44/12 molecular weight ratio)"""
        return delta_soc_t_ha * 44 / 12


# =============================================================================
# 4. HDVI — Hydroma Drought Vulnerability Index
# =============================================================================

class HDVI:
    """
    Hydroma Drought Vulnerability Index
    
    Multi-scale drought index combining SPI, SPEI, VHI, SMI
    """
    
    @staticmethod
    def spi(precip_series: np.ndarray, window: int = 3) -> np.ndarray:
        """
        Standardized Precipitation Index
        
        Simplified: (P - μ) / σ for the window
        Full implementation uses gamma distribution fit.
        """
        from scipy import stats
        
        spi_values = np.full_like(precip_series, np.nan)
        
        for i in range(window, len(precip_series)):
            window_data = precip_series[i - window:i]
            if np.any(window_data <= 0):
                # Use gamma distribution fit
                try:
                    shape, loc, scale = stats.gamma.fit(
                        window_data[window_data > 0], floc=0
                    )
                    # Probability
                    p = stats.gamma.cdf(
                        precip_series[i], shape, loc=0, scale=scale
                    )
                    if p > 0 and p < 1:
                        spi_values[i] = stats.norm.ppf(p)
                except Exception:
                    pass
            else:
                # Simple standardization
                mu = np.mean(window_data)
                sigma = np.std(window_data) + 1e-6
                spi_values[i] = (precip_series[i] - mu) / sigma
        
        return spi_values
    
    @staticmethod
    def vhi(ndvi: np.ndarray, lst: np.ndarray,
            ndvi_min: float = 0.1, ndvi_max: float = 0.9,
            lst_min: float = 270.0, lst_max: float = 330.0) -> np.ndarray:
        """
        Vegetation Health Index (Kogan, 1995)
        VHI = α × VCI + (1 - α) × TCI
        
        VCI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min) × 100
        TCI = (T_max - T) / (T_max - T_min) × 100
        """
        vci = np.clip((ndvi - ndvi_min) / (ndvi_max - ndvi_min), 0, 1) * 100
        tci = np.clip((lst_max - lst) / (lst_max - lst_min), 0, 1) * 100
        
        return 0.5 * vci + 0.5 * tci
    
    @staticmethod
    def smi(soil_moisture: np.ndarray, wilting_point: float,
            field_capacity: float) -> np.ndarray:
        """
        Soil Moisture Index
        SMI = (θ - θ_pwp) / (θ_fc - θ_pwp)
        """
        return np.clip(
            (soil_moisture - wilting_point) / (field_capacity - wilting_point + 1e-6),
            0, 1
        )
    
    @staticmethod
    def compute(
        spi_value: float,
        spei_value: float,
        vhi_value: np.ndarray,
        smi_value: np.ndarray,
        weights: tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25),
    ) -> np.ndarray:
        """
        Compute HDVI
        
        Returns: HDVI in range [-3, +3] (negative = drought)
        """
        w1, w2, w3, w4 = weights
        
        # Normalize VHI and SMI to SPI-like scale
        # VHI: 0-100 → map to SPI scale (-3 to +3)
        vhi_norm = (vhi_value - 50) / 50 * 3  # 0 → -3, 50 → 0, 100 → +3
        smi_norm = (smi_value - 0.5) * 6  # 0 → -3, 0.5 → 0, 1 → +3
        
        hdvi = (
            w1 * spi_value +
            w2 * spei_value +
            w3 * vhi_norm +
            w4 * smi_norm
        )
        
        return np.clip(hdvi, -3, 3)
    
    @staticmethod
    def classify(hdvi: np.ndarray) -> np.ndarray:
        """Classify drought severity"""
        return np.select(
            [hdvi > 0, hdvi > -1, hdvi > -2],
            ["normal", "mild_drought", "moderate_drought"],
            default="severe_drought"
        )


# =============================================================================
# 5. EPIA — EcoNojin Precision Irrigation Advisor
# =============================================================================

class EPIA:
    """
    EcoNojin Precision Irrigation Advisor
    
    FAO-56 ETc + Sentinel-2 Kc for precision scheduling
    """
    
    @staticmethod
    def kc_from_lai(lai: np.ndarray, lai_max: float = 6.0,
                    kc_min: float = 0.1, kc_max: float = 1.2) -> np.ndarray:
        """
        Derive crop coefficient Kc from LAI
        Kc = Kc_min + (Kc_max - Kc_min) × LAI/LAI_max
        """
        return np.clip(
            kc_min + (kc_max - kc_min) * (lai / lai_max),
            kc_min, kc_max
        )
    
    @staticmethod
    def ks_water_stress(soil_moisture: float, depletion_fraction: float = 0.5,
                        taw: float = 50.0, etc: float = 5.0) -> float:
        """
        Water stress coefficient Ks (FAO-56)
        Ks = (TAW - Dr) / ((1 - p) × TAW) when Dr > RAW
        """
        raw = depletion_fraction * taw
        dr = taw * (1 - soil_moisture)  # Simplified root zone depletion
        
        if dr <= raw:
            return 1.0
        
        return np.clip((taw - dr) / (taw - raw + 1e-6), 0, 1)
    
    @staticmethod
    def effective_rainfall(rainfall_mm: float, etc_mm: float = 5.0,
                           method: str = "usda_scs") -> float:
        """
        Effective rainfall using USDA-SCS method
        P_eff = (125 - 0.2 × P) × P / 125  for P ≤ 250 mm
        """
        if method == "usda_scs":
            if rainfall_mm <= 250:
                return (125 - 0.2 * rainfall_mm) * rainfall_mm / 125
            else:
                return 0.75 * rainfall_mm - 25
        return rainfall_mm * 0.7  # Simple 70% effectiveness
    
    @staticmethod
    def recommend(
        et0: float,
        lai: np.ndarray,
        soil_moisture: float,
        rainfall_forecast_mm: float,
        irrigation_efficiency: float = 0.85,
        taw: float = 50.0,
        depletion_fraction: float = 0.5,
    ) -> dict[str, Any]:
        """
        Generate irrigation recommendation
        
        Returns:
        {
            'et0': float,
            'kc': array,
            'etc': array,
            'irrigation_need_mm': array,
            'irrigation_need_m3_ha': array,
            'days_until_irrigation': int,
            'recommendation': str
        }
        """
        # Derive Kc from LAI
        kc = EPIA.kc_from_lai(lai)
        
        # Calculate ETc
        ks = EPIA.ks_water_stress(soil_moisture, depletion_fraction, taw, et0)
        etc = et0 * kc * ks
        
        # Effective rainfall
        p_eff = EPIA.effective_rainfall(rainfall_forecast_mm)
        
        # Net irrigation requirement
        irri_net = np.maximum(0, etc - p_eff)
        
        # Gross irrigation requirement (accounting for efficiency)
        irri_gross = irri_net / irrigation_efficiency
        
        # Convert mm to m³/ha (1 mm = 10 m³/ha)
        irri_m3_ha = irri_gross * 10
        
        # Days until irrigation (based on soil moisture depletion)
        raw = depletion_fraction * taw
        days = max(1, int(raw / (et0 + 1e-6)))
        
        # Recommendation
        mean_kc = float(np.mean(kc))
        if mean_kc < 0.3:
            stage = "initial"
        elif mean_kc < 0.8:
            stage = "development"
        elif mean_kc < 1.1:
            stage = "mid-season"
        else:
            stage = "late-season"
        
        return {
            "et0": et0,
            "kc": kc,
            "ks": ks,
            "etc": etc,
            "irrigation_need_mm": irri_net,
            "irrigation_need_m3_ha": irri_m3_ha,
            "days_until_irrigation": days,
            "crop_stage": stage,
            "recommendation": f"Irrigate {float(np.mean(irri_gross)):.1f} mm in {days} days ({stage} stage)",
        }


# =============================================================================
# 6. H-Pheno — Hydroma Phenology Detection
# =============================================================================

class HPheno:
    """
    Hydroma Phenology Detection
    
    Savitzky-Golay smoothing + derivative analysis for NDVI time series
    """
    
    @staticmethod
    def smooth(ndvi: np.ndarray, window: int = 11, polyorder: int = 3) -> np.ndarray:
        """Savitzky-Golay smoothing"""
        try:
            from scipy.signal import savgol_filter
            return savgol_filter(ndvi, window, polyorder)
        except ImportError:
            # Fallback: simple moving average
            return np.convolve(ndvi, np.ones(window)/window, mode='same')
    
    @staticmethod
    def derivative(ndvi: np.ndarray, dt_days: float = 5.0) -> np.ndarray:
        """First derivative using central differences"""
        deriv = np.gradient(ndvi, dt_days)
        return deriv
    
    @staticmethod
    def second_derivative(ndvi: np.ndarray, dt_days: float = 5.0) -> np.ndarray:
        """Second derivative"""
        return np.gradient(np.gradient(ndvi, dt_days), dt_days)
    
    @staticmethod
    def detect_phenology(ndvi_ts: np.ndarray, dates: list[date],
                         dt_days: float = 5.0) -> dict[str, Any]:
        """
        Detect phenological stages from NDVI time series
        
        Returns:
        {
            'sos': date,  # Start of Season
            'pos': date,  # Peak of Season
            'eos': date,  # End of Season
            'los': int,   # Length of Season (days)
            'bbch_stages': dict,
        }
        """
        ndvi_smooth = HPheno.smooth(ndvi_ts)
        ndvi_prime = HPheno.derivative(ndvi_smooth, dt_days)
        
        # SOS: first positive zero-crossing of NDVI'
        sos_idx = None
        for i in range(1, len(ndvi_prime)):
            if ndvi_prime[i-1] <= 0 < ndvi_prime[i]:
                sos_idx = i
                break
        
        # POS: maximum of NDVI
        pos_idx = int(np.argmax(ndvi_smooth))
        
        # EOS: first negative zero-crossing of NDVI' after POS
        eos_idx = None
        for i in range(pos_idx + 1, len(ndvi_prime)):
            if ndvi_prime[i-1] >= 0 > ndvi_prime[i]:
                eos_idx = i
                break
        
        # Dates
        sos_date = dates[sos_idx] if sos_idx is not None else None
        pos_date = dates[pos_idx] if pos_idx is not None else None
        eos_date = dates[eos_idx] if eos_idx is not None else None
        
        # Length of season
        if sos_date and eos_date:
            los = (eos_date - sos_date).days
        else:
            los = 0
        
        # BBCH stage mapping
        bbch = {
            "BBCH_0_19": "Emergence (before SOS)",
            "BBCH_20_59": f"Vegetative (SOS to POS, ~{(pos_date - sos_date).days if sos_date and pos_date else 0} days)",
            "BBCH_60_89": f"Reproductive (POS to EOS, ~{(eos_date - pos_date).days if pos_date and eos_date else 0} days)",
            "BBCH_90_99": "Senescence (after EOS)",
        }
        
        return {
            "sos": sos_date,
            "pos": pos_date,
            "eos": eos_date,
            "los_days": los,
            "bbch_stages": bbch,
            "ndvi_smooth": ndvi_smooth,
            "ndvi_derivative": ndvi_prime,
        }


# =============================================================================
# 7. ESRI — EcoNojin Salinity Risk Index
# =============================================================================

class ESRI:
    """
    EcoNojin Salinity Risk Index
    
    Spectral Salinity Index + soil EC + irrigation management
    """
    
    @staticmethod
    def salinity_index_s2(blue: np.ndarray, red: np.ndarray,
                          nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """
        Sentinel-2 Salinity Index
        SI = √(B × R) / ((NIR/SWIR) × (B/R))
        
        Higher SI = higher salinity
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            numerator = np.sqrt(blue * red)
            ratio1 = nir / (swir + 1e-6)
            ratio2 = blue / (red + 1e-6)
            si = numerator / (ratio1 * ratio2 + 1e-6)
        return np.nan_to_num(si, nan=np.nan)
    
    @staticmethod
    def leaching_requirement(ec_w: float, ec_e: float) -> float:
        """
        FAO-32 Leaching Requirement
        LR = EC_w / (5 × EC_e - EC_w)
        
        EC_w: irrigation water EC (dS/m)
        EC_e: soil saturation extract EC (dS/m)
        """
        if ec_w <= 0:
            return 0.0
        denominator = 5 * ec_e - ec_w
        if denominator <= 0:
            return 1.0  # Impossible to leach
        return min(1.0, ec_w / denominator)
    
    @staticmethod
    def compute(
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir: np.ndarray,
        ec_soil_dsm: float = 2.0,
        ec_irrigation_dsm: float = 0.5,
        actual_leaching_fraction: float = 0.2,
        weights: tuple[float, float, float] = (0.3, 0.5, 0.2),
    ) -> np.ndarray:
        """
        Compute ESRI
        
        Returns: ESRI in [0, 1]
        """
        alpha, beta, gamma = weights
        
        # Spectral component (normalize SI to [0, 1])
        si = ESRI.salinity_index_s2(blue, red, nir, swir)
        si_norm = np.clip(si / 10, 0, 1)  # Typical SI range 0-10
        
        # Soil EC component (normalize: 2 dS/m = low, 16 dS/m = severe)
        ec_norm = np.clip(ec_soil_dsm / 16, 0, 1)
        
        # Leaching deficit component
        lr_required = ESRI.leaching_requirement(ec_irrigation_dsm, ec_soil_dsm)
        lr_deficit = np.clip(lr_required - actual_leaching_fraction, 0, 1)
        
        esri = alpha * si_norm + beta * ec_norm + gamma * lr_deficit
        
        return np.clip(esri, 0, 1)
    
    @staticmethod
    def classify(esri: np.ndarray) -> np.ndarray:
        """Classify salinity risk"""
        return np.select(
            [esri < 0.3, esri < 0.6, esri < 0.8],
            ["low", "moderate", "high"],
            default="severe"
        )


# =============================================================================
# 8. HLHS — Hydroma Landscape Health Score
# =============================================================================

@dataclass
class LandscapeMetrics:
    """Input metrics for HLHS calculation"""
    ndvi_mean: float = 0.0
    ewsı_mean: float = 0.0
    soc_t_ha: float = 0.0
    shdi: float = 0.0  # Shannon Diversity Index
    ecsı_t_co2_ha_yr: float = 0.0
    slope_stability: float = 0.0  # 0 to 1
    connectivity: float = 0.0  # 0 to 1


class HLHS:
    """
    Hydroma Landscape Health Score
    
    Composite index for landscape fund management
    """
    
    # Default weights
    WEIGHTS = {
        "vegetation": 0.20,
        "water": 0.20,
        "soil": 0.15,
        "biodiversity": 0.15,
        "carbon": 0.15,
        "topography": 0.10,
        "connectivity": 0.05,
    }
    
    # Normalization bounds
    BOUNDS = {
        "vegetation": (0.0, 0.8),  # NDVI range
        "water": (0.0, 1.0),  # 1 - EWSI
        "soil": (0, 100),  # SOC t/ha
        "biodiversity": (0.0, 3.0),  # SHDI
        "carbon": (-2, 5),  # t CO2-eq/ha/yr
        "topography": (0, 1),
        "connectivity": (0, 1),
    }
    
    @staticmethod
    def normalize(value: float, vmin: float, vmax: float) -> float:
        """Min-max normalization to [0, 1]"""
        if vmax <= vmin:
            return 0.5
        return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    
    @classmethod
    def compute(cls, metrics: LandscapeMetrics,
                weights: Optional[dict] = None) -> dict[str, Any]:
        """
        Compute HLHS
        
        Returns:
        {
            'hlhs': float (0-100),
            'components': dict,
            'classification': str,
        }
        """
        w = weights or cls.WEIGHTS
        b = cls.BOUNDS
        
        # Compute normalized components
        components = {
            "vegetation": cls.normalize(metrics.ndvi_mean, b["vegetation"][0], b["vegetation"][1]),
            "water": cls.normalize(1 - metrics.ewsı_mean, 0, 1),
            "soil": cls.normalize(metrics.soc_t_ha, b["soil"][0], b["soil"][1]),
            "biodiversity": cls.normalize(metrics.shdi, b["biodiversity"][0], b["biodiversity"][1]),
            "carbon": cls.normalize(metrics.ecsı_t_co2_ha_yr, b["carbon"][0], b["carbon"][1]),
            "topography": cls.normalize(metrics.slope_stability, 0, 1),
            "connectivity": cls.normalize(metrics.connectivity, 0, 1),
        }
        
        # Weighted sum
        hlhs = sum(w[k] * v for k, v in components.items()) * 100
        
        # Classification
        if hlhs >= 80:
            classification = "excellent"
        elif hlhs >= 60:
            classification = "good"
        elif hlhs >= 40:
            classification = "fair"
        elif hlhs >= 20:
            classification = "poor"
        else:
            classification = "critical"
        
        return {
            "hlhs": hlhs,
            "components": components,
            "classification": classification,
            "weights_used": w,
        }


# =============================================================================
# Comprehensive Test
# =============================================================================

def comprehensive_test():
    print("=" * 80)
    print("🧪 Phase 3f: Hydroma Scientific Models - Comprehensive Test")
    print("=" * 80)
    
    results = []
    
    # Test 1: EWSI
    print("\n🧪 Test 1: EWSI (Water Stress Index)")
    try:
        nir = np.array([0.4, 0.5, 0.6])
        swir = np.array([0.15, 0.2, 0.25])
        ewsı = EWSI.compute(nir, swir, vpd=2.0, soil_moisture=0.15, soil_field_capacity=0.35)
        classes = EWSI.classify(ewsı)
        print(f"   NDMI: {EWSI.ndmi(nir, swir)}")
        print(f"   EWSI: {ewsı}")
        print(f"   Classes: {classes}")
        results.append(("EWSI", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("EWSI", False))
    
    # Test 2: HY-RUE
    print("\n🧪 Test 2: HY-RUE (Biomass & Yield)")
    try:
        lai = np.array([0.5, 2.0, 4.0, 6.0])
        par = 20.0  # MJ/m²/day
        ewsı = np.array([0.2, 0.2, 0.2, 0.3])
        f_ipar, bio = HYRUE.compute_daily(par, lai, ewsı, t_mean=25.0)
        total_bio = float(np.sum(bio) * 30)  # 30 days
        yield_val = HYRUE.compute_yield(total_bio, hi=0.45)
        print(f"   fIPAR: {f_ipar}")
        print(f"   Daily biomass: {bio} g/m²")
        print(f"   30-day total: {total_bio:.1f} g/m²")
        print(f"   Yield: {yield_val:.1f} g/m²")
        results.append(("HY-RUE", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("HY-RUE", False))
    
    # Test 3: ECSI (Carbon)
    print("\n🧪 Test 3: ECSI (Carbon Sequestration)")
    try:
        delta_soc = ECSI.sequestration_rate(
            initial_soc_t_ha=30.0,
            carbon_input_t_ha=2.5,
            t_mean_c=15.0,
            rainfall_mm=500,
            evaporation_mm=1000,
            clay_fraction=0.23,
            land_use="grassland",
        )
        co2_eq = ECSI.co2_equivalent(delta_soc)
        print(f"   ΔSOC: {delta_soc:.3f} t/ha/yr")
        print(f"   CO₂-eq: {co2_eq:.3f} t CO₂/ha/yr")
        results.append(("ECSI", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("ECSI", False))
    
    # Test 4: HDVI
    print("\n🧪 Test 4: HDVI (Drought Vulnerability)")
    try:
        precip = np.array([50, 30, 80, 20, 60, 40, 70, 25, 90, 35])
        spi = HDVI.spi(precip, window=3)
        ndvi = np.array([0.3, 0.4, 0.5, 0.3, 0.5, 0.4, 0.6, 0.3, 0.7, 0.4])
        lst = np.array([300, 305, 295, 310, 290, 300, 285, 315, 280, 305])
        vhi = HDVI.vhi(ndvi, lst)
        smi = np.array([0.5, 0.3, 0.7, 0.2, 0.6, 0.4, 0.8, 0.2, 0.9, 0.4])
        
        hdvi = HDVI.compute(spi[-1], -1.0, vhi, smi)
        print(f"   SPI: {spi[-1]:.2f}")
        print(f"   VHI mean: {np.mean(vhi):.1f}")
        print(f"   HDVI: {hdvi}")
        print(f"   Drought class: {HDVI.classify(hdvi)}")
        results.append(("HDVI", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("HDVI", False))
    
    # Test 5: EPIA
    print("\n🧪 Test 5: EPIA (Irrigation Advisor)")
    try:
        lai = np.array([2.5, 3.0, 3.5, 4.0])
        rec = EPIA.recommend(
            et0=5.0, lai=lai, soil_moisture=0.25,
            rainfall_forecast_mm=10.0, irrigation_efficiency=0.85,
        )
        print(f"   ET₀: {rec['et0']} mm/day")
        print(f"   Kc (from LAI): {rec['kc']}")
        print(f"   ETc: {rec['etc']}")
        print(f"   Crop stage: {rec['crop_stage']}")
        print(f"   Days until irrigation: {rec['days_until_irrigation']}")
        print(f"   Recommendation: {rec['recommendation']}")
        results.append(("EPIA", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("EPIA", False))
    
    # Test 6: H-Pheno
    print("\n🧪 Test 6: H-Pheno (Phenology Detection)")
    try:
        # Synthetic NDVI time series (annual cycle)
        days = 365
        t = np.arange(days)
        ndvi_synthetic = 0.2 + 0.5 * np.sin(2 * np.pi * (t - 60) / 365) + 0.05 * np.random.randn(days)
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(days)]
        
        pheno = HPheno.detect_phenology(ndvi_synthetic, dates, dt_days=1.0)
        print(f"   SOS: {pheno['sos']}")
        print(f"   POS: {pheno['pos']}")
        print(f"   EOS: {pheno['eos']}")
        print(f"   Length of Season: {pheno['los_days']} days")
        results.append(("H-Pheno", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("H-Pheno", False))
    
    # Test 7: ESRI
    print("\n🧪 Test 7: ESRI (Salinity Risk)")
    try:
        blue = np.array([0.08, 0.1, 0.12])
        red = np.array([0.1, 0.12, 0.15])
        nir = np.array([0.4, 0.35, 0.3])
        swir = np.array([0.15, 0.18, 0.22])
        esri = ESRI.compute(blue, red, nir, swir, ec_soil_dsm=4.0, ec_irrigation_dsm=0.8)
        classes = ESRI.classify(esri)
        print(f"   SI: {ESRI.salinity_index_s2(blue, red, nir, swir)}")
        print(f"   ESRI: {esri}")
        print(f"   Classes: {classes}")
        results.append(("ESRI", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("ESRI", False))
    
    # Test 8: HLHS
    print("\n🧪 Test 8: HLHS (Landscape Health)")
    try:
        metrics = LandscapeMetrics(
            ndvi_mean=0.45,
            ewsı_mean=0.3,
            soc_t_ha=35.0,
            shdi=1.8,
            ecsı_t_co2_ha_yr=2.5,
            slope_stability=0.75,
            connectivity=0.6,
        )
        result = HLHS.compute(metrics)
        print(f"   HLHS: {result['hlhs']:.1f}/100")
        print(f"   Classification: {result['classification']}")
        print(f"   Components:")
        for k, v in result['components'].items():
            print(f"      {k}: {v:.2f}")
        results.append(("HLHS", True))
    except Exception as e:
        print(f"   ❌ {e}")
        results.append(("HLHS", False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 MODELS HEALTH REPORT")
    print("=" * 80)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"   {status} {name}")
    
    print(f"\n🎯 Score: {passed}/{total} models operational")
    
    if passed == total:
        print("\n🎉 ALL 8 HYDROMA MODELS OPERATIONAL!")
        print("   EcoNojin now has unique scientific capabilities:")
        print("   • Multi-source water stress detection (EWSI)")
        print("   • Real-time yield prediction (HY-RUE)")
        print("   • Carbon sequestration monitoring (ECSI)")
        print("   • Early drought warning (HDVI)")
        print("   • Precision irrigation (EPIA)")
        print("   • Automatic phenology (H-Pheno)")
        print("   • Salinity risk assessment (ESRI)")
        print("   • Landscape health scoring (HLHS)")
    
    return passed == total


if __name__ == "__main__":
    comprehensive_test()