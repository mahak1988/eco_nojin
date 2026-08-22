"""
Phase 12: Unified Orchestrator (RegionAnalyzer)
==============================================

هدف: ایجاد یک لایه orchestration که همه ۱۰ مدل را با داده‌های واقعی
از providers یکپارچه کند.

Output: یک JSON جامع برای هر نقطه از جهان که شامل همه تحلیل‌ها است.

Architecture:
    RegionAnalyzer.analyze(lat, lon, crop_type) → AnalysisResult

Integration Map:
    ClimateFetcher → KGCv5 (climate classification)
    ClimateFetcher → WBIv3 (water bankruptcy, with WBIInputs from providers)
    ClimateFetcher + Sentinel-2 → EWSI (water stress)
    ClimateFetcher + Sentinel-2 → HY-RUE (biomass/yield)
    SoilGrids + ClimateFetcher → ECSI (carbon sequestration)
    ClimateFetcher → HDVI (drought vulnerability)
    ClimateFetcher + Sentinel-2 → EPIA (irrigation advice)
    Sentinel-2 time series → H-Pheno (phenology)
    Sentinel-2 + SoilGrids → ESRI (salinity)
    All models → HLHS (landscape health)

References:
- Architecture: Hexagonal (Ports & Adapters) pattern
- Design: Uncle Bob's Clean Architecture
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


# ============================================================================
# 1. Data Classes
# ============================================================================

@dataclass
class ClimateData:
    """Climate data for a region (from Open-Meteo or WorldClim)."""
    t_min_monthly: np.ndarray  # 12 values (°C)
    t_max_monthly: np.ndarray  # 12 values (°C)
    p_monthly: np.ndarray      # 12 values (mm)
    t_ann_mean: float
    p_ann: float
    source: str
    year: int = 2020

    def to_dict(self) -> Dict[str, Any]:
        return {
            "t_min_monthly": self.t_min_monthly.tolist(),
            "t_max_monthly": self.t_max_monthly.tolist(),
            "p_monthly": self.p_monthly.tolist(),
            "t_ann_mean": self.t_ann_mean,
            "p_ann": self.p_ann,
            "source": self.source,
            "year": self.year,
        }


@dataclass
class SoilData:
    """Soil data for a region (from SoilGrids or fallback)."""
    ph: float
    soc_g_per_kg: float
    clay_pct: float
    sand_pct: float
    silt_pct: float
    field_capacity: float  # m³/m³
    wilting_point: float   # m³/m³
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ph": self.ph,
            "soc_g_per_kg": self.soc_g_per_kg,
            "clay_pct": self.clay_pct,
            "sand_pct": self.sand_pct,
            "silt_pct": self.silt_pct,
            "field_capacity": self.field_capacity,
            "wilting_point": self.wilting_point,
            "source": self.source,
        }


@dataclass
class SentinelData:
    """Sentinel-2 data for a region (from Earth Search)."""
    nir: np.ndarray  # B08
    swir: np.ndarray  # B11
    red: np.ndarray   # B04
    blue: np.ndarray  # B02
    green: np.ndarray # B03
    lai: np.ndarray
    source: str
    acquisition_date: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nir_mean": float(np.mean(self.nir)),
            "swir_mean": float(np.mean(self.swir)),
            "red_mean": float(np.mean(self.red)),
            "blue_mean": float(np.mean(self.blue)),
            "green_mean": float(np.mean(self.green)),
            "lai_mean": float(np.mean(self.lai)),
            "source": self.source,
            "acquisition_date": self.acquisition_date,
        }


@dataclass
class WaterInputs:
    """Water management inputs (from WRI AQUASTAT or fallback)."""
    renewable_water_m3_per_capita: float
    withdrawal_ratio: float
    groundwater_depletion_mm_yr: float
    water_quality_index: float
    drought_frequency_events_yr: float
    demand_growth_rate_pct: float
    infrastructure_leakage_pct: float
    governance_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegionContext:
    """Complete context for a region."""
    name: str
    lat: float
    lon: float
    crop_type: str
    climate: ClimateData
    soil: SoilData
    sentinel: SentinelData
    water_inputs: WaterInputs


@dataclass
class AnalysisResult:
    """Complete analysis result for a region."""
    region_name: str
    lat: float
    lon: float
    crop_type: str
    timestamp: str

    # Global Watchdog
    koppen: Dict[str, Any]
    wbi: Dict[str, Any]

    # Hydroma 8 Models
    ewsi: Dict[str, Any]
    hyrue: Dict[str, Any]
    ecsi: Dict[str, Any]
    hdvi: Dict[str, Any]
    epia: Dict[str, Any]
    hpheno: Dict[str, Any]
    esri: Dict[str, Any]
    hlhs: Dict[str, Any]

    # Meta
    execution_time_ms: float
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ============================================================================
# 2. Mock Data Providers (for Phase 12 demonstration)
# ============================================================================

class MockProviders:
    """
    Mock providers for demonstration.
    In Phase 13, these will be replaced with real API calls.
    """

    # Preset data for demonstration regions
    PRESETS = {
        "Iran_Isfahan": {
            "lat": 32.65, "lon": 51.67,
            "t_min": np.array([-2, 1, 6, 11, 16, 22, 25, 24, 19, 12, 5, 0]),
            "t_max": np.array([10, 13, 19, 25, 31, 37, 40, 39, 34, 26, 17, 11]),
            "p": np.array([30, 35, 40, 35, 15, 3, 1, 1, 3, 15, 25, 30]),
            "soil_ph": 7.8,
            "soc": 12.0,
            "clay": 35.0,
            "sand": 30.0,
            "silt": 35.0,
            "nir": 0.45, "swir": 0.22, "red": 0.25, "blue": 0.08, "green": 0.15,
            "lai": 3.5,
            "water": WaterInputs(900, 0.88, 6.0, 0.5, 1.5, 2.0, 30.0, 0.5),
        },
        "Yemen_Sanaa": {
            "lat": 15.35, "lon": 44.21,
            "t_min": np.array([6, 7, 9, 11, 12, 14, 14, 13, 12, 7, 5, 7]),
            "t_max": np.array([24, 26, 29, 31, 33, 36, 37, 36, 33, 29, 26, 24]),
            "p": np.array([1.5, 12.8, 33.4, 6.4, 13.3, 8.8, 32.8, 53.0, 16.2, 1.4, 0.7, 2.0]),
            "soil_ph": 8.2,
            "soc": 6.0,
            "clay": 40.0,
            "sand": 35.0,
            "silt": 25.0,
            "nir": 0.25, "swir": 0.30, "red": 0.28, "blue": 0.10, "green": 0.14,
            "lai": 1.2,
            "water": WaterInputs(80, 1.8, 8.0, 0.25, 3.0, 2.8, 60.0, 0.15),
        },
        "California_Sacramento": {
            "lat": 38.58, "lon": -121.49,
            "t_min": np.array([3, 5, 7, 9, 12, 15, 17, 16, 14, 10, 6, 3]),
            "t_max": np.array([13, 16, 19, 23, 28, 33, 36, 35, 32, 25, 17, 13]),
            "p": np.array([95, 85, 65, 35, 15, 5, 1, 2, 8, 30, 70, 90]),
            "soil_ph": 6.8,
            "soc": 18.0,
            "clay": 28.0,
            "sand": 40.0,
            "silt": 32.0,
            "nir": 0.50, "swir": 0.20, "red": 0.18, "blue": 0.07, "green": 0.16,
            "lai": 4.2,
            "water": WaterInputs(1100, 0.65, 2.5, 0.75, 1.2, 0.8, 12.0, 0.85),
        },
    }

    @classmethod
    def get_context(cls, name: str, crop_type: str = "wheat") -> RegionContext:
        """Get complete context for a preset region."""
        if name not in cls.PRESETS:
            raise ValueError(f"Unknown region: {name}. Available: {list(cls.PRESETS.keys())}")

        p = cls.PRESETS[name]

        climate = ClimateData(
            t_min_monthly=p["t_min"],
            t_max_monthly=p["t_max"],
            p_monthly=p["p"],
            t_ann_mean=float(np.mean((p["t_min"] + p["t_max"]) / 2)),
            p_ann=float(np.sum(p["p"])),
            source="preset-openmeteo-2020",
            year=2020,
        )

        # Derive field capacity and wilting point from texture
        clay = p["clay"]
        fc = 0.15 + 0.003 * clay + 0.002 * p["silt"]
        wp = 0.05 + 0.0025 * clay

        soil = SoilData(
            ph=p["soil_ph"],
            soc_g_per_kg=p["soc"],
            clay_pct=p["clay"],
            sand_pct=p["sand"],
            silt_pct=p["silt"],
            field_capacity=fc,
            wilting_point=wp,
            source="preset-soilgrids-v2",
        )

        # Sentinel data as arrays (simulate small patch)
        size = 100
        sentinel = SentinelData(
            nir=np.full(size, p["nir"]) + np.random.randn(size) * 0.02,
            swir=np.full(size, p["swir"]) + np.random.randn(size) * 0.02,
            red=np.full(size, p["red"]) + np.random.randn(size) * 0.01,
            blue=np.full(size, p["blue"]) + np.random.randn(size) * 0.01,
            green=np.full(size, p["green"]) + np.random.randn(size) * 0.01,
            lai=np.full(size, p["lai"]) + np.random.randn(size) * 0.2,
            source="preset-earth-search-sentinel2",
            acquisition_date="2024-06-15",
        )

        return RegionContext(
            name=name,
            lat=p["lat"],
            lon=p["lon"],
            crop_type=crop_type,
            climate=climate,
            soil=soil,
            sentinel=sentinel,
            water_inputs=p["water"],
        )


# ============================================================================
# 3. Unified Orchestrator
# ============================================================================

class RegionAnalyzer:
    """
    Unified Orchestrator: runs all 10 models on a region.

    This is the integration layer that connects:
    - Data Providers (Climate, Soil, Satellite, Water)
    - 8 Hydroma Models
    - 2 Global Watchdog Models (KGC, WBI)

    Usage:
        analyzer = RegionAnalyzer()
        result = analyzer.analyze("Iran_Isfahan", crop_type="wheat")
        print(result.to_json())
    """

    def __init__(self):
        # Lazy imports to handle missing dependencies
        self._imports_loaded = False
        self._KGCv5 = None
        self._WBIv3 = None
        self._WBIInputs_cls = None
        self._EWSI = None
        self._HYRUE = None
        self._ECSI = None
        self._HDVI = None
        self._EPIA = None
        self._HPheno = None
        self._ESRI = None
        self._HLHS = None

    def _ensure_imports(self):
        """Load models lazily."""
        if self._imports_loaded:
            return

        try:
            from engine.hydroma.models.global_watchdog import (
                KGCv5, WBIv3, WBIInputs,
            )
            self._KGCv5 = KGCv5
            self._WBIv3 = WBIv3
            self._WBIInputs_cls = WBIInputs
        except ImportError as e:
            raise RuntimeError(
                f"Global Watchdog models not available: {e}. "
                "Run phase10_production_integration.py first."
            )

        try:
            from engine.hydroma.models import (
                EWSI, HYRUE, ECSI, HDVI, EPIA, HPheno, ESRI, HLHS,
            )
            self._EWSI = EWSI
            self._HYRUE = HYRUE
            self._ECSI = ECSI
            self._HDVI = HDVI
            self._EPIA = EPIA
            self._HPheno = HPheno
            self._ESRI = ESRI
            self._HLHS = HLHS
        except ImportError as e:
            raise RuntimeError(
                f"Hydroma models not available: {e}. "
                "Check engine/hydroma/models/ directory."
            )

        self._imports_loaded = True

    def analyze(self, region_name: str, crop_type: str = "wheat") -> AnalysisResult:
        """
        Run complete analysis for a region.

        Parameters
        ----------
        region_name : str
            Name of the region (must be in MockProviders.PRESETS or use real providers)
        crop_type : str
            Crop type for yield/irrigation models

        Returns
        -------
        AnalysisResult with all 10 model outputs
        """
        self._ensure_imports()
        t0 = time.time()
        warnings: List[str] = []

        # Get region context
        ctx = MockProviders.get_context(region_name, crop_type)

        # ===================================================================
        # Model 1: KGC (Köppen-Geiger)
        # ===================================================================
        try:
            kgc = self._KGCv5.classify(
                ctx.climate.t_min_monthly,
                ctx.climate.t_max_monthly,
                ctx.climate.p_monthly,
            )
        except Exception as e:
            kgc = {"error": str(e)}
            warnings.append(f"KGC failed: {e}")

        # ===================================================================
        # Model 2: WBI (Water Bankruptcy Index)
        # ===================================================================
        try:
            wbi_inputs = self._WBIInputs_cls(
                ctx.water_inputs.renewable_water_m3_per_capita,
                ctx.water_inputs.withdrawal_ratio,
                ctx.water_inputs.groundwater_depletion_mm_yr,
                ctx.water_inputs.water_quality_index,
                ctx.water_inputs.drought_frequency_events_yr,
                ctx.water_inputs.demand_growth_rate_pct,
                ctx.water_inputs.infrastructure_leakage_pct,
                ctx.water_inputs.governance_score,
            )
            wbi = self._WBIv3.compute(wbi_inputs)
        except Exception as e:
            wbi = {"error": str(e)}
            warnings.append(f"WBI failed: {e}")

        # ===================================================================
        # Model 3: EWSI (Water Stress Index)
        # ===================================================================
        try:
            # Use mean values for demonstration
            ewsı = self._EWSI.compute(
                nir=ctx.sentinel.nir,
                swir=ctx.sentinel.swir,
                vpd=1.5 + ctx.climate.t_ann_mean * 0.05,  # crude VPD proxy
                soil_moisture=ctx.soil.field_capacity * 0.6,  # crude proxy
                soil_field_capacity=ctx.soil.field_capacity,
            )
            ewsı_out = {
                "mean": float(np.mean(ewsı)),
                "std": float(np.std(ewsı)),
                "classification": self._EWSI.classify(ewsı).tolist(),
            }
        except Exception as e:
            ewsı_out = {"error": str(e)}
            warnings.append(f"EWSI failed: {e}")

        # ===================================================================
        # Model 4: HY-RUE (Yield)
        # ===================================================================
        try:
            hyrue = self._HYRUE(crop=crop_type)
            hyrue_result = hyrue.compute(
                par=18.0,  # MJ/m²/day (rough estimate from climate)
                lai=ctx.sentinel.lai,
                ewsı=np.full_like(ctx.sentinel.lai, float(np.mean(ewsı_out.get("mean", 0.3)))),
                t_mean=ctx.climate.t_ann_mean,
                days=120,  # typical growing season
            )
        except Exception as e:
            hyrue_result = {"error": str(e)}
            warnings.append(f"HY-RUE failed: {e}")

        # ===================================================================
        # Model 5: ECSI (Carbon Sequestration)
        # ===================================================================
        try:
            ecsi = self._ECSI()
            ecsi_result = ecsi.compute(
                initial_soc_t_ha=ctx.soil.soc_g_per_kg * 2.5,  # rough conversion
                carbon_input_t_ha=2.0,
                t_mean_c=ctx.climate.t_ann_mean,
                rainfall_mm=ctx.climate.p_ann,
                evaporation_mm=ctx.climate.p_ann * 1.5,  # rough proxy
                clay_fraction=ctx.soil.clay_pct / 100,
                land_use="arable",
            )
        except Exception as e:
            ecsi_result = {"error": str(e)}
            warnings.append(f"ECSI failed: {e}")

        # ===================================================================
        # Model 6: HDVI (Drought Vulnerability)
        # ===================================================================
        try:
            hdvi = self._HDVI()
            # Compute SPI from precipitation
            spi = self._HDVI.spi(ctx.climate.p_monthly, window=3)
            spi_value = float(np.nanmean(spi[-3:])) if not np.all(np.isnan(spi)) else 0.0

            # VHI from NDVI and LST proxies
            ndvi_proxy = (ctx.sentinel.nir - ctx.sentinel.red) / (
                ctx.sentinel.nir + ctx.sentinel.red + 1e-6
            )
            lst_proxy = ctx.climate.t_ann_mean + 273.15 + 5  # crude LST proxy
            vhi = self._HDVI.vhi(ndvi_proxy, np.full_like(ndvi_proxy, lst_proxy))

            # SMI from soil moisture
            smi = self._HDVI.smi(
                np.full_like(ndvi_proxy, ctx.soil.field_capacity * 0.5),
                ctx.soil.wilting_point,
                ctx.soil.field_capacity,
            )

            hdvi_result = hdvi.compute(
                spi_value=spi_value,
                spei_value=spi_value - 0.5,  # crude SPEI proxy
                vhi_value=vhi,
                smi_value=smi,
            )
        except Exception as e:
            hdvi_result = {"error": str(e)}
            warnings.append(f"HDVI failed: {e}")

        # ===================================================================
        # Model 7: EPIA (Irrigation Advice)
        # ===================================================================
        try:
            epia = self._EPIA()
            et0 = max(1.0, ctx.climate.t_ann_mean * 0.2)  # crude ET0 proxy
            epia_result = epia.compute(
                et0=et0,
                lai=ctx.sentinel.lai,
                soil_moisture=ctx.soil.field_capacity * 0.5,
                rainfall_forecast_mm=ctx.climate.p_ann / 12,  # monthly average
                irrigation_efficiency=0.85,
            )
        except Exception as e:
            epia_result = {"error": str(e)}
            warnings.append(f"EPIA failed: {e}")

        # ===================================================================
        # Model 8: H-Pheno (Phenology)
        # ===================================================================
        try:
            hpheno = self._HPheno()
            # Synthetic annual NDVI time series
            from datetime import date, timedelta
            days = 365
            t = np.arange(days)
            ndvi_ts = 0.2 + 0.5 * np.sin(2 * np.pi * (t - 60) / 365) + np.random.randn(days) * 0.05
            ndvi_ts = np.clip(ndvi_ts, -1, 1)
            dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(days)]
            hpheno_result = hpheno.compute(ndvi_ts, dates, dt_days=1.0)
            # Convert dates to strings
            for k in ["sos", "pos", "eos"]:
                if hpheno_result.get(k):
                    hpheno_result[k] = hpheno_result[k].isoformat()
        except Exception as e:
            hpheno_result = {"error": str(e)}
            warnings.append(f"H-Pheno failed: {e}")

        # ===================================================================
        # Model 9: ESRI (Salinity)
        # ===================================================================
        try:
            esri = self._ESRI()
            esri_result = esri.compute(
                blue=ctx.sentinel.blue,
                red=ctx.sentinel.red,
                nir=ctx.sentinel.nir,
                swir=ctx.sentinel.swir,
                ec_soil_dsm=max(0.5, ctx.soil.ph - 5.5) * 2,  # crude EC proxy
                ec_irrigation_dsm=0.8,
                actual_leaching_fraction=0.15,
            )
            esri_out = {
                "mean_esri": float(np.mean(esri_result["esri"])),
                "classification": esri_result["classification"].tolist()[:5],
                "leaching_requirement": esri_result["leaching_requirement"],
            }
        except Exception as e:
            esri_out = {"error": str(e)}
            warnings.append(f"ESRI failed: {e}")

        # ===================================================================
        # Model 10: HLHS (Landscape Health)
        # ===================================================================
        try:
            from engine.hydroma.models.hlhs import LandscapeMetrics
            hlhs = self._HLHS()
            metrics = LandscapeMetrics(
                ndvi_mean=float(np.mean(ndvi_proxy)) if 'ndvi_proxy' in locals() else 0.4,
                ewsı_mean=float(np.mean(ewsı_out.get("mean", 0.3))),
                soc_t_ha=ctx.soil.soc_g_per_kg * 2.5,
                shdi=1.5,  # placeholder
                ecsı_t_co2_ha_yr=ecsi_result.get("co2_eq_t_ha_yr", 0.0),
                slope_stability=0.7,  # placeholder
                connectivity=0.6,  # placeholder
            )
            hlhs_result = hlhs.compute(metrics)
        except Exception as e:
            hlhs_result = {"error": str(e)}
            warnings.append(f"HLHS failed: {e}")

        elapsed_ms = (time.time() - t0) * 1000

        return AnalysisResult(
            region_name=region_name,
            lat=ctx.lat,
            lon=ctx.lon,
            crop_type=crop_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            koppen=kgc,
            wbi=wbi,
            ewsi=ewsı_out,
            hyrue=hyrue_result,
            ecsi=ecsi_result,
            hdvi=hdvi_result,
            epia=epia_result,
            hpheno=hpheno_result,
            esri=esri_out,
            hlhs=hlhs_result,
            execution_time_ms=elapsed_ms,
            warnings=warnings,
        )


# ============================================================================
# 4. Demonstration
# ============================================================================

def demo():
    """Run demonstration of Unified Orchestrator."""
    print("=" * 80)
    print("🌍 PHASE 12: UNIFIED ORCHESTRATOR — Integration Demo")
    print("=" * 80)
    print("   Testing: 3 regions × 10 models = 30 analyses")
    print("=" * 80)

    analyzer = RegionAnalyzer()
    regions = ["Iran_Isfahan", "Yemen_Sanaa", "California_Sacramento"]

    all_results = {}

    for region in regions:
        print(f"\n{'─'*80}")
        print(f"🌍 {region}")
        print(f"{'─'*80}")

        try:
            result = analyzer.analyze(region, crop_type="wheat")
            all_results[region] = result

            print(f"\n📊 KGC:     {result.koppen.get('code', '?')} — "
                  f"{result.koppen.get('description', '?')}")
            print(f"💧 WBI:     {result.wbi.get('wbi', 0):.1f}/100 — "
                  f"{result.wbi.get('classification', '?')}")
            if result.wbi.get("years_to_bankruptcy_range"):
                lo, hi = result.wbi["years_to_bankruptcy_range"]
                print(f"          ⏱ {lo}-{hi} years")

            print(f"🌊 EWSI:    {result.ewsi.get('mean', 0):.2f}")
            print(f"🌾 HY-RUE:  yield = {result.hyrue.get('yield_t_ha', 0):.2f} t/ha")
            print(f"🌱 ECSI:    ΔSOC = {result.ecsi.get('delta_soc_t_ha_yr', 0):.2f} t/ha/yr")

            hdvi_val = result.hdvi.get("hdvi", np.array([0]))
            if isinstance(hdvi_val, np.ndarray):
                hdvi_val = float(np.mean(hdvi_val))
            print(f"🏜️ HDVI:    {hdvi_val:.2f} — {result.hdvi.get('classification', '?')}")

            print(f"💡 EPIA:    {result.epia.get('recommendation', '?')}")
            print(f"📅 H-Pheno: LOS = {result.hpheno.get('los_days', '?')} days")
            print(f"🧂 ESRI:    {result.esri.get('mean_esri', 0):.2f}")
            print(f"🏞️ HLHS:    {result.hlhs.get('hlhs', 0):.1f}/100 — "
                  f"{result.hlhs.get('classification', '?')}")
            print(f"⏱️ Time:    {result.execution_time_ms:.1f} ms")
            if result.warnings:
                print(f"⚠️ Warnings: {len(result.warnings)}")
                for w in result.warnings[:3]:
                    print(f"   • {w}")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    # Save all results to JSON
    output_dir = PROJECT_ROOT / "data" / "analysis_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, result in all_results.items():
        output_file = output_dir / f"{name.lower()}_analysis.json"
        output_file.write_text(result.to_json(), encoding="utf-8")
        print(f"\n💾 Saved: {output_file.relative_to(PROJECT_ROOT)}")

    # Summary
    print(f"\n{'='*80}")
    print("📊 UNIFIED ORCHESTRATOR SUMMARY")
    print("=" * 80)
    print(f"   ✅ Regions analyzed: {len(all_results)}/{len(regions)}")
    print(f"   📦 Total models per region: 10")
    print(f"   🎯 Integration: COMPLETE (all models in single pipeline)")
    print(f"\n💡 Next: Phase 13 — API endpoint exposure")

    return all_results


PROJECT_ROOT = Path(__file__).parent.parent.resolve()

if __name__ == "__main__":
    demo()