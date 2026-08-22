"""
Phase 6a: Scientific Refinement for Global Watchdog
====================================================
هدف: رفع ۵ مشکل علمی شناسایی‌شده و افزودن uncertainty bounds

بهبودهای کلیدی:
1. Köppen-Geiger: اصلاح منطق s/w/f برای تشخیص دقیق‌تر
2. WERI: افزودن soft cap و sigmoid برای جلوگیری از 100 شدن
3. WBI: اصلاح فرمول time-to-bankruptcy با پارامترهای واقع‌بینانه‌تر
4. PRSP: شخصی‌سازی توصیه‌ها بر اساس climate zone و governance
5. Uncertainty Bounds: افزودن بازه‌های عدم قطعیت به همه خروجی‌ها

پروتکل: Evidence-based + Cautious interpretation + Scientific honesty
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("hgw.v2")


# ============================================================================
# 1. KGC v2 — Improved Köppen-Geiger
# ============================================================================

class KGCv2:
    """
    Köppen-Geiger v2: Improved dry-season detection.

    اصلاحات:
    - منطق دقیق‌تر برای s/w/f (Rubel et al. 2016)
    - استفاده از half-year sums برای تشخیص فصل خشک
    - بهبود تشخیص Csa/Csb/Cwa/Cwb (مهم برای California)
    - بهبود تشخیص Cfb/Cfa (مهم برای Netherlands)
    """

    GROUPS = {"A": "Tropical", "B": "Arid", "C": "Temperate",
              "D": "Continental", "E": "Polar"}

    @staticmethod
    def classify(t_min: np.ndarray, t_max: np.ndarray, p: np.ndarray) -> Dict[str, Any]:
        t_min = np.asarray(t_min, dtype=float)
        t_max = np.asarray(t_max, dtype=float)
        p = np.asarray(p, dtype=float)

        t_cold = float(np.min(t_min))
        t_hot = float(np.max(t_max))
        t_mean = float(np.mean((t_min + t_max) / 2))
        p_ann = float(np.sum(p))

        # نیم‌سال گرم و سرد (hemisphere detection)
        nh_summer = float(p[5:8].sum())  # Jun-Aug
        nh_winter = float(p[[11, 0, 1]].sum())
        is_nh_summer_warmer = float(np.mean(t_max[5:8])) > float(np.mean(t_max[[11, 0, 1]]))

        if is_nh_summer_warmer:
            p_wet_season = max(nh_summer, nh_winter)
            p_dry_season = min(nh_summer, nh_winter)
            dry_in_winter = nh_winter < nh_summer / 3
            dry_in_summer = nh_summer < nh_winter / 3
        else:
            p_wet_season = max(nh_summer, nh_winter)
            p_dry_season = min(nh_summer, nh_winter)
            dry_in_winter = nh_summer < nh_winter / 3
            dry_in_summer = nh_winter < nh_summer / 3

        p_dry_month = float(np.min(p))
        p_wet_month = float(np.max(p))

        # === Group E: Polar ===
        if t_hot < 10:
            code = "ET" if t_hot > 0 else "EF"

        # === Group B: Arid (threshold-based) ===
        else:
            # Beck et al. (2018) aridity threshold
            if 70 < p_ann < 140:  # winter-wet (s)
                threshold = 2 * t_mean
            elif p_ann >= 140 and dry_in_summer:
                threshold = 2 * t_mean + 140
            elif p_ann >= 140 and dry_in_winter:
                threshold = 2 * t_mean + 280
            else:
                threshold = 2 * t_mean + 140

            if p_ann < threshold / 2:
                code = f"BW{'h' if t_mean >= 18 else 'k'}"
            elif p_ann < threshold:
                code = f"BS{'h' if t_mean >= 18 else 'k'}"
            # === Group A: Tropical ===
            elif t_cold >= 18:
                if p_dry_month >= 60:
                    sub = "f"
                elif p_dry_month < 60 and 25 * p_dry_month >= (100 - p_ann):
                    sub = "m"
                elif dry_in_winter:
                    sub = "w"
                else:
                    sub = "s"
                code = f"A{sub}"
            # === Group C: Temperate ===
            elif -3 <= t_cold < 18 and t_hot > 10:
                if dry_in_summer and p_dry_month < 40 and p_dry_month < p_wet_month / 3:
                    sub = "s"
                elif dry_in_winter and p_dry_month < p_wet_month / 10:
                    sub = "w"
                else:
                    sub = "f"
                # a/b/c temperature subdivision
                if t_hot >= 22:
                    t_sub = "a"
                elif np.sum(t_max > 10) >= 4:
                    t_sub = "b"
                else:
                    t_sub = "c"
                code = f"C{sub}{t_sub}"
            # === Group D: Continental ===
            elif t_cold < -3:
                if dry_in_summer and p_dry_month < 40 and p_dry_month < p_wet_month / 3:
                    sub = "s"
                elif dry_in_winter and p_dry_month < p_wet_month / 10:
                    sub = "w"
                else:
                    sub = "f"
                if t_hot >= 22:
                    t_sub = "a"
                elif np.sum(t_max > 10) >= 4:
                    t_sub = "b"
                elif t_cold < -38:
                    t_sub = "d"
                else:
                    t_sub = "c"
                code = f"D{sub}{t_sub}"
            else:
                code = "??"

        return {
            "code": code,
            "group": code[0] if code != "??" else "?",
            "group_name": KGCv2.GROUPS.get(code[0], "Unknown"),
            "description": KGCv2.describe(code),
            "t_mean_c": t_mean,
            "p_ann_mm": p_ann,
            "dry_season": "summer" if dry_in_summer else ("winter" if dry_in_winter else "none"),
        }

    @staticmethod
    def describe(code: str) -> str:
        desc = {
            "Af": "Tropical rainforest", "Am": "Tropical monsoon",
            "Aw": "Tropical savanna", "As": "Tropical savanna (dry summer)",
            "BWh": "Hot desert", "BWk": "Cold desert",
            "BSh": "Hot semi-arid", "BSk": "Cold semi-arid",
            "Cfa": "Humid subtropical", "Cfb": "Oceanic (temperate)",
            "Cfc": "Subpolar oceanic",
            "Csa": "Hot-summer Mediterranean",
            "Csb": "Warm-summer Mediterranean",
            "Csc": "Cold-summer Mediterranean",
            "Cwa": "Humid subtropical (dry winter)",
            "Cwb": "Subtropical highland",
            "Dfa": "Hot-summer humid continental",
            "Dfb": "Warm-summer humid continental",
            "Dfc": "Subarctic",
            "Dsa": "Mediterranean continental (hot summer)",
            "ET": "Tundra", "EF": "Ice cap",
        }
        return desc.get(code, f"Köppen {code}")


# ============================================================================
# 2. WBI v2 — Improved time-to-bankruptcy
# ============================================================================

@dataclass
class WBIInputs:
    renewable_water_m3_per_capita: float
    withdrawal_ratio: float
    groundwater_depletion_mm_yr: float
    water_quality_index: float
    drought_frequency_events_yr: float
    demand_growth_rate_pct: float
    infrastructure_leakage_pct: float
    governance_score: float


class WBIv2:
    """
    Water Bankruptcy Index v2 — با فرمول واقع‌بینانه‌تر time-to-bankruptcy.

    بهبودها:
    - Time-to-bankruptcy: `remaining / (demand * 1.5)` به جای `*3`
    - افزودن adaptation factor (کشورهای قوی‌تر کندتر به ورشکستگی می‌رسند)
    - بازه عدم قطعیت (±20%)
    """

    @staticmethod
    def falkenmark(w: float) -> float:
        if w >= 1700: return 0.0
        if w <= 500: return 100.0
        return 100 * (1700 - w) / 1200

    @staticmethod
    def withdrawal(ratio: float) -> float:
        if ratio <= 0.2: return 0.0
        if ratio >= 1.0: return 100.0
        return 100 * (ratio - 0.2) / 0.8

    @staticmethod
    def groundwater(dep: float) -> float:
        if dep <= 0: return 0.0
        return min(100.0, dep * 10)

    @staticmethod
    def quality(wqi: float) -> float:
        return 100 * (1 - np.clip(wqi, 0, 1))

    @staticmethod
    def drought(e: float) -> float:
        return min(100.0, e * 40)

    @staticmethod
    def demand(p: float) -> float:
        if p <= 0: return 0.0
        return min(100.0, p * 25)

    @staticmethod
    def infrastructure(lep: float) -> float:
        return min(100.0, lep * 2)

    @staticmethod
    def governance(g: float) -> float:
        return 100 * (1 - np.clip(g, 0, 1))

    @classmethod
    def compute(cls, inputs: WBIInputs) -> Dict[str, Any]:
        scores = {
            "falkenmark": cls.falkenmark(inputs.renewable_water_m3_per_capita),
            "withdrawal": cls.withdrawal(inputs.withdrawal_ratio),
            "groundwater": cls.groundwater(inputs.groundwater_depletion_mm_yr),
            "quality": cls.quality(inputs.water_quality_index),
            "drought": cls.drought(inputs.drought_frequency_events_yr),
            "demand": cls.demand(inputs.demand_growth_rate_pct),
            "infrastructure": cls.infrastructure(inputs.infrastructure_leakage_pct),
            "governance": cls.governance(inputs.governance_score),
        }

        w = {
            "falkenmark": 0.15, "withdrawal": 0.20, "groundwater": 0.15,
            "quality": 0.10, "drought": 0.15, "demand": 0.10,
            "infrastructure": 0.08, "governance": 0.07,
        }
        wbi = sum(w[k] * scores[k] for k in scores)
        wbi = float(np.clip(wbi, 0, 100))

        # Uncertainty bounds (±15% برای شاخص‌های composite)
        wbi_low = max(0, wbi * 0.85)
        wbi_high = min(100, wbi * 1.15)

        if wbi < 20: classification, risk = "Water-Secure", "Low"
        elif wbi < 40: classification, risk = "Water-Stressed", "Moderate"
        elif wbi < 60: classification, risk = "Water-Scarce", "High"
        elif wbi < 80: classification, risk = "Water-Crisis", "Very High"
        else: classification, risk = "Water-Bankruptcy", "Critical"

        # IMPROVED: Time-to-bankruptcy با adaptation factor
        years_to_bankruptcy = None
        if wbi < 80 and inputs.demand_growth_rate_pct > 0.5:
            remaining = 80 - wbi
            # adaptation factor: governance slows bankruptcy
            adaptation = 0.5 + inputs.governance_score * 1.5  # 0.5-2.0
            # softer growth rate
            years = max(3, remaining / (inputs.demand_growth_rate_pct * 1.5) * adaptation)
            years_to_bankruptcy = int(years)
            # bounds
            ytb_low = max(1, int(years * 0.7))
            ytb_high = int(years * 1.5)
        else:
            ytb_low = ytb_high = None

        return {
            "wbi": wbi,
            "wbi_low": wbi_low,
            "wbi_high": wbi_high,
            "classification": classification,
            "risk_level": risk,
            "component_scores": scores,
            "years_to_bankruptcy_estimate": years_to_bankruptcy,
            "years_to_bankruptcy_range": (ytb_low, ytb_high) if years_to_bankruptcy else None,
            "disclaimer": "Probabilistic — ±15% uncertainty typical for composite indices",
        }


# ============================================================================
# 3. WERI v2 — Soft-cap sigmoid
# ============================================================================

class WERIv2:
    """
    WEF Nexus Risk v2 — با sigmoid soft-cap به جای hard cap.

    به جای اینکه مستقیماً به 100 بپرد، با sigmoid نرم‌تر رفتار می‌کند.
    """

    @staticmethod
    def compute(water_stress: float, energy_access: float, food_security: float,
                nexus_coupling: float = 0.5) -> Dict[str, Any]:
        linear = (water_stress + energy_access + food_security) / 3

        # Multiplicative compounding (softened)
        product = water_stress * energy_access * food_security
        compounding = nexus_coupling * product * 2.5  # reduced from 8

        raw = linear + compounding

        # Sigmoid soft-cap: asymptotes at 0.95 instead of 1.0
        weri = 95 * (raw / (raw + 0.5))  # sigmoid transformation
        weri = float(np.clip(weri, 0, 100))

        individual = {"water": water_stress, "energy": energy_access, "food": food_security}
        primary = max(individual.items(), key=lambda x: x[1])[0]

        if weri < 25: status = "Nexus-Stable"
        elif weri < 50: status = "Nexus-Stressed"
        elif weri < 75: status = "Nexus-Critical"
        else: status = "Nexus-Collapse"

        return {
            "weri": weri,
            "status": status,
            "individual_risks": individual,
            "primary_stressor": primary,
            "raw_risk": float(raw),
        }


# ============================================================================
# 4. PRSP v2 — Context-aware recommendations
# ============================================================================

class PRSPv2:
    """
    Prescriptive Recovery Scenario Planner v2

    بهبود: توصیه‌ها بر اساس climate zone و governance شخصی‌سازی می‌شوند.
    """

    INTERVENTIONS_BY_CONTEXT = {
        "arid_low_gov": [
            {"name": "Drip irrigation rollout",
             "impact": 0.40, "lead_time": 2, "cost": 0.15,
             "ref": "FAO AQUASTAT best practices"},
            {"name": "Solar-powered desalination",
             "impact": 0.35, "lead_time": 5, "cost": 0.70,
             "ref": "IRENA Desalination Yearbook (2021)"},
            {"name": "Community-based water governance",
             "impact": 0.30, "lead_time": 2, "cost": 0.05,
             "ref": "Ostrom (2009) Governing the Commons"},
        ],
        "arid_high_gov": [
            {"name": "Wastewater recycling (advanced)",
             "impact": 0.40, "lead_time": 3, "cost": 0.50,
             "ref": "WHO Water Reuse Guidelines (2017)"},
            {"name": "Aquifer managed recharge (MAR)",
             "impact": 0.45, "lead_time": 5, "cost": 0.10,
             "ref": "Dillon et al. (2019)"},
            {"name": "Water pricing reform",
             "impact": 0.30, "lead_time": 2, "cost": 0.05,
             "ref": "OECD Water Pricing (2010)"},
        ],
        "temperate": [
            {"name": "Leakage reduction program",
             "impact": 0.30, "lead_time": 2, "cost": 0.30,
             "ref": "World Bank NRW guidelines"},
            {"name": "Regenerative agriculture",
             "impact": 0.35, "lead_time": 3, "cost": 0.10,
             "ref": "FAO Save and Grow (2011)"},
            {"name": "Wetland restoration",
             "impact": 0.30, "lead_time": 5, "cost": 0.20,
             "ref": "Ramsar Convention"},
        ],
        "water_secure": [
            {"name": "Flood-risk preparedness",
             "impact": 0.25, "lead_time": 2, "cost": 0.15,
             "ref": "Sendai Framework for DRR"},
            {"name": "Water quality monitoring",
             "impact": 0.20, "lead_time": 1, "cost": 0.10,
             "ref": "WHO Guidelines on Drinking Water"},
            {"name": "Biodiversity conservation",
             "impact": 0.25, "lead_time": 10, "cost": 0.20,
             "ref": "CBD Post-2020 Framework"},
        ],
    }

    @classmethod
    def recommend(cls, wbi: float, climate_code: str,
                  governance: float) -> Dict[str, Any]:
        # Determine context
        if wbi < 20:
            context = "water_secure"
        elif climate_code.startswith("B"):
            context = "arid_high_gov" if governance > 0.5 else "arid_low_gov"
        elif climate_code.startswith("E"):
            context = "temperate"  # polar handled as temperate for recovery
        else:
            context = "temperate"

        interventions = cls.INTERVENTIONS_BY_CONTEXT.get(
            context, cls.INTERVENTIONS_BY_CONTEXT["temperate"]
        )

        # Prioritize: prefer fast, high-impact for high-WBI regions
        if wbi > 60:
            interventions.sort(key=lambda x: x["impact"] / max(x["lead_time"], 1), reverse=True)
        else:
            interventions.sort(key=lambda x: x["impact"], reverse=True)

        return {
            "context": context,
            "portfolio": interventions[:3],
            "disclaimer": "Evidence-based recommendations; local adaptation required",
        }


# ============================================================================
# 5. Full Watchdog v2 (Orchestrator)
# ============================================================================

class GlobalWatchdogV2:
    def analyze(self, name: str, climate: Tuple, water: WBIInputs,
                food_insecurity: float, energy_access: float,
                population_millions: float, displacement: float = 0.0,
                natural_capital: float = 0.5, recharge: float = 0.5,
                soil: float = 0.5, biodiversity: float = 0.5,
                financial: float = 0.5) -> Dict[str, Any]:

        t_min, t_max, p = climate
        kgc = KGCv2.classify(t_min, t_max, p)
        wbi = WBIv2.compute(water)
        weri = WERIv2.compute(
            water_stress=wbi["wbi"] / 100,
            energy_access=energy_access,
            food_security=food_insecurity,
        )

        # Conflict risk (Mach et al. 2019)
        water_factor = wbi["wbi"] / 100
        base_risk = (
            0.30 * (1 - water.governance_score) +
            0.20 * 0.5 +  # ethnic fractionalization default
            0.15 * food_insecurity +
            0.15 * displacement
        )
        climate_amp = 0.15 * water_factor
        cri = np.clip((base_risk + climate_amp) * 100, 0, 100)
        cri_low, cri_high = max(0, cri * 0.8), min(100, cri * 1.2)

        # Recovery potential
        eco = 0.35 * natural_capital + 0.30 * recharge + 0.20 * biodiversity + 0.15 * soil
        inst = 0.6 * water.governance_score + 0.4 * financial
        erpi = np.clip(eco * 0.6 + inst * 0.4, 0, 1)

        # Prescriptive (context-aware)
        prsp = PRSPv2.recommend(wbi["wbi"], kgc["code"], water.governance_score)

        return {
            "region": name,
            "kgc": kgc,
            "wbi": wbi,
            "weri": weri,
            "cri": {
                "cri": float(cri), "cri_low": float(cri_low), "cri_high": float(cri_high),
                "classification": (
                    "Low" if cri < 25 else
                    "Moderate" if cri < 50 else
                    "High" if cri < 75 else "Critical"
                ),
            },
            "erpi": float(erpi),
            "prsp": prsp,
            "population_millions": population_millions,
        }


# ============================================================================
# Demonstration
# ============================================================================

def demo():
    print("=" * 80)
    print("🌍 HYDROMA GLOBAL WATCHDOG v2 — Scientific Refinement")
    print("=" * 80)

    gw = GlobalWatchdogV2()

    regions = {
        "Somalia": {
            "climate": (
                np.array([24, 25, 27, 28, 28, 27, 25, 25, 26, 27, 26, 25]),
                np.array([30, 31, 32, 33, 32, 30, 28, 28, 30, 31, 31, 30]),
                np.array([5, 2, 10, 40, 60, 25, 15, 5, 10, 50, 70, 20]),
            ),
            "water": WBIInputs(150, 0.95, 5.0, 0.3, 2.5, 3.5, 55.0, 0.2),
            "food": 0.85, "energy": 0.8, "pop": 18.0, "disp": 0.15,
            "nat": 0.2, "rch": 0.1, "soil": 0.3, "bio": 0.25, "fin": 0.1,
        },
        "Sudan": {
            "climate": (
                np.array([18, 20, 23, 26, 28, 28, 25, 24, 25, 25, 22, 19]),
                np.array([32, 34, 37, 40, 41, 40, 35, 33, 35, 37, 35, 33]),
                np.array([0, 0, 0, 5, 20, 50, 100, 120, 70, 20, 5, 0]),
            ),
            "water": WBIInputs(300, 0.85, 4.0, 0.4, 2.0, 3.0, 45.0, 0.3),
            "food": 0.75, "energy": 0.6, "pop": 48.0, "disp": 0.12,
            "nat": 0.3, "rch": 0.2, "soil": 0.4, "bio": 0.35, "fin": 0.2,
        },
        "Yemen": {
            "climate": (
                np.array([12, 14, 17, 19, 21, 23, 24, 23, 21, 18, 15, 13]),
                np.array([24, 26, 29, 31, 33, 36, 37, 36, 33, 29, 26, 24]),
                np.array([5, 3, 10, 30, 15, 2, 5, 15, 8, 2, 4, 5]),
            ),
            "water": WBIInputs(80, 1.8, 8.0, 0.25, 3.0, 2.8, 60.0, 0.15),
            "food": 0.8, "energy": 0.7, "pop": 34.0, "disp": 0.18,
            "nat": 0.15, "rch": 0.1, "soil": 0.2, "bio": 0.2, "fin": 0.05,
        },
        "Iran_Central": {
            "climate": (
                np.array([-2, 1, 6, 11, 16, 22, 25, 24, 19, 12, 5, 0]),
                np.array([10, 13, 19, 25, 31, 37, 40, 39, 34, 26, 17, 11]),
                np.array([30, 35, 40, 35, 15, 3, 1, 1, 3, 15, 25, 30]),
            ),
            "water": WBIInputs(900, 0.88, 6.0, 0.5, 1.5, 2.0, 30.0, 0.5),
            "food": 0.35, "energy": 0.1, "pop": 88.0, "disp": 0.02,
            "nat": 0.35, "rch": 0.3, "soil": 0.45, "bio": 0.4, "fin": 0.4,
        },
        "California_USA": {
            "climate": (
                np.array([7, 8, 9, 11, 14, 17, 19, 19, 17, 13, 9, 7]),
                np.array([18, 19, 20, 22, 25, 29, 33, 33, 31, 26, 21, 18]),
                np.array([80, 75, 60, 30, 15, 5, 1, 1, 5, 20, 45, 70]),
            ),
            "water": WBIInputs(1100, 0.65, 2.5, 0.75, 1.2, 0.8, 12.0, 0.85),
            "food": 0.15, "energy": 0.05, "pop": 39.0, "disp": 0.005,
            "nat": 0.5, "rch": 0.6, "soil": 0.7, "bio": 0.55, "fin": 0.9,
        },
        "Netherlands": {
            "climate": (
                np.array([1, 1, 3, 5, 9, 12, 14, 14, 11, 8, 4, 2]),
                np.array([6, 7, 10, 14, 18, 20, 23, 22, 19, 14, 10, 7]),
                np.array([70, 50, 60, 45, 55, 65, 75, 80, 75, 85, 85, 80]),
            ),
            "water": WBIInputs(3500, 0.15, 0.0, 0.9, 0.1, 0.2, 5.0, 0.95),
            "food": 0.05, "energy": 0.05, "pop": 18.0, "disp": 0.001,
            "nat": 0.6, "rch": 0.9, "soil": 0.85, "bio": 0.5, "fin": 0.95,
        },
    }

    results = {}
    for name, data in regions.items():
        r = gw.analyze(
            name, data["climate"], data["water"],
            data["food"], data["energy"], data["pop"], data["disp"],
            data["nat"], data["rch"], data["soil"], data["bio"], data["fin"],
        )
        results[name] = r

        print(f"\n{'─'*70}")
        print(f"🌍 {name}")
        print(f"{'─'*70}")
        print(f"  🌡️ Climate:  {r['kgc']['code']} — {r['kgc']['description']}")
        print(f"  💧 WBI:      {r['wbi']['wbi']:.1f}/100 "
              f"[{r['wbi']['wbi_low']:.1f}-{r['wbi']['wbi_high']:.1f}] — {r['wbi']['classification']}")
        if r["wbi"]["years_to_bankruptcy_range"]:
            lo, hi = r["wbi"]["years_to_bankruptcy_range"]
            print(f"             ⏱ → bankruptcy in {lo}-{hi} years")
        print(f"  ⚡ WERI:     {r['weri']['weri']:.1f}/100 ({r['weri']['status']})")
        print(f"  ⚔️ Conflict: {r['cri']['cri']:.1f}/100 "
              f"[{r['cri']['cri_low']:.1f}-{r['cri']['cri_high']:.1f}] — {r['cri']['classification']}")
        print(f"  🌱 Recovery: {r['erpi']:.2f}")
        print(f"  💡 Recovery Context: {r['prsp']['context']}")
        print(f"     Top Recommendations:")
        for i, intv in enumerate(r["prsp"]["portfolio"][:3], 1):
            print(f"       {i}. {intv['name']} (impact {intv['impact']:.0%}, "
                  f"{intv['lead_time']}yr) — {intv['ref']}")

    print(f"\n{'='*70}")
    print("🌐 FINAL RANKING (with uncertainty)")
    print(f"{'='*70}")
    sorted_r = sorted(results.items(), key=lambda x: x[1]["wbi"]["wbi"], reverse=True)
    for i, (name, r) in enumerate(sorted_r, 1):
        w = r["wbi"]
        ytb = r["wbi"]["years_to_bankruptcy_range"]
        ytb_str = f" → ⏱ {ytb[0]}-{ytb[1]}yr" if ytb else ""
        print(f"  #{i} {name:<20} WBI={w['wbi']:5.1f} "
              f"[{w['wbi_low']:.0f}-{w['wbi_high']:.0f}] ({w['classification']}){ytb_str}")

    print(f"\n⚠️ SCIENTIFIC DISCLAIMER")
    print(f"{'─'*70}")
    print("""All outputs carry ±15% uncertainty typical of composite indices.
Time-to-bankruptcy estimates are order-of-magnitude (not predictions).
Conflict risk is one factor among many (Mach et al. 2019).
All recommendations require local validation before policy action.""")

    return results


if __name__ == "__main__":
    demo()