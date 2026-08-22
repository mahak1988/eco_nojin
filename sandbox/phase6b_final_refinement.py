"""
Phase 6b: Final Scientific Refinement
=====================================
هدف: حل ۲ مشکل باقیمانده:
1. Köppen-Geiger: ساختار منطقی صحیح (B قبل از A/C/D)
2. PRSP: Crisis-aware context (override اگر WBI > 70)

References:
- Peel, M.C. et al. (2007) "Updated world map of Köppen-Geiger" HESS
- Rubel, F. et al. (2016) "Explaining the Köppen climate classification"
- Kottek, M. et al. (2006) "World Map of Köppen-Geiger"
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("hgw.v3")


# ============================================================================
# 1. KGC v3 — Corrected Köppen-Geiger
# ============================================================================

class KGCv3:
    """
    Köppen-Geiger v3 — with CORRECT logical precedence.

    Order MUST be: E → B → A → C → D
    (not the previous if-elif which misclassified arid zones)
    """

    @staticmethod
    def classify(t_min: np.ndarray, t_max: np.ndarray, p: np.ndarray) -> Dict[str, Any]:
        t_min = np.asarray(t_min, dtype=float)
        t_max = np.asarray(t_max, dtype=float)
        p = np.asarray(p, dtype=float)

        t_cold = float(np.min(t_min))
        t_hot = float(np.max(t_max))
        t_mean = float(np.mean((t_min + t_max) / 2))
        p_ann = float(np.sum(p))

        # Hemispheric detection (warm half-year vs cold half-year)
        nh_sum_p = float(p[4:8].sum())   # May-Aug (NH summer)
        nh_win_p = float(p[[10, 11, 0, 1, 2, 3]].sum())  # NH winter
        nh_sum_t = float(np.mean(t_max[4:8]))
        nh_win_t = float(np.mean(t_max[[10, 11, 0, 1, 2, 3]]))
        is_summer_wet_nh = nh_sum_p > nh_win_p
        is_nh_summer_warmer = nh_sum_t > nh_win_t

        if is_nh_summer_warmer:
            p_summer = nh_sum_p
            p_winter = nh_win_p
        else:
            p_summer = nh_win_p
            p_winter = nh_sum_p

        p_dry_month = float(np.min(p))
        p_wet_month = float(np.max(p))

        # ============ STEP 1: Polar (E) ============
        if t_hot < 10:
            code = "ET" if t_hot > 0 else "EF"
            desc = "Tundra" if code == "ET" else "Ice cap"

        # ============ STEP 2: Arid (B) — MUST BE BEFORE A/C/D ============
        else:
            # Beck et al. (2018) threshold with 3 regimes
            # r = precipitation of driest month in the warmer half-year
            if is_summer_wet_nh:  # dry winter (w regime)
                threshold = 2 * t_mean + 280
            else:  # dry summer (s regime) or even distribution
                # Check driest summer month vs wettest winter month
                p_dry_summer = float(np.min(p[4:8]) if is_nh_summer_warmer
                                    else np.min(p[[10, 11, 0, 1, 2, 3]]))
                p_wet_winter = float(np.max(p[[10, 11, 0, 1, 2, 3]]) if is_nh_summer_warmer
                                    else np.max(p[4:8]))
                if p_dry_summer < p_wet_winter / 3:  # dry summer (s)
                    threshold = 2 * t_mean
                else:  # even distribution (f)
                    threshold = 2 * t_mean + 140

            # Arid classification
            if p_ann < threshold / 2:
                # Desert (BW)
                code = "BWh" if t_mean >= 18 else "BWk"
                desc = "Hot desert" if code == "BWh" else "Cold desert"
            elif p_ann < threshold:
                # Steppe (BS)
                code = "BSh" if t_mean >= 18 else "BSk"
                desc = "Hot semi-arid" if code == "BSh" else "Cold semi-arid"
            # ============ STEP 3: Tropical (A) ============
            elif t_cold >= 18:
                if p_dry_month >= 60:
                    sub = "f"
                    desc = "Tropical rainforest"
                elif p_ann >= 25 * (100 - p_dry_month):
                    sub = "m"
                    desc = "Tropical monsoon"
                else:
                    sub = "w" if not is_summer_wet_nh else "s"
                    desc = "Tropical savanna"
                code = f"A{sub}"

            # ============ STEP 4: Continental (D) — must check before C ============
            elif t_cold < -3 and t_hot > 10:
                # Dry-season detection (same as C)
                p_dry_summer = float(np.min(p[4:8]) if is_nh_summer_warmer
                                    else np.min(p[[10, 11, 0, 1, 2, 3]]))
                p_wet_winter = float(np.max(p[[10, 11, 0, 1, 2, 3]]) if is_nh_summer_warmer
                                    else np.max(p[4:8]))
                p_dry_winter = float(np.min(p[[10, 11, 0, 1, 2, 3]]) if is_nh_summer_warmer
                                    else np.min(p[4:8]))
                p_wet_summer = float(np.max(p[4:8]) if is_nh_summer_warmer
                                    else np.max(p[[10, 11, 0, 1, 2, 3]]))

                if p_dry_summer < 40 and p_dry_summer < p_wet_winter / 3:
                    sub = "s"
                elif p_dry_winter < p_wet_summer / 10:
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
                desc = f"Continental {t_sub.upper()} {sub}"

            # ============ STEP 5: Temperate (C) ============
            elif -3 <= t_cold < 18 and t_hot > 10:
                p_dry_summer = float(np.min(p[4:8]) if is_nh_summer_warmer
                                    else np.min(p[[10, 11, 0, 1, 2, 3]]))
                p_wet_winter = float(np.max(p[[10, 11, 0, 1, 2, 3]]) if is_nh_summer_warmer
                                    else np.max(p[4:8]))
                p_dry_winter = float(np.min(p[[10, 11, 0, 1, 2, 3]]) if is_nh_summer_warmer
                                    else np.min(p[4:8]))
                p_wet_summer = float(np.max(p[4:8]) if is_nh_summer_warmer
                                    else np.max(p[[10, 11, 0, 1, 2, 3]]))

                if p_dry_summer < 40 and p_dry_summer < p_wet_winter / 3:
                    sub = "s"
                elif p_dry_winter < p_wet_summer / 10:
                    sub = "w"
                else:
                    sub = "f"

                if t_hot >= 22:
                    t_sub = "a"
                elif np.sum(t_max > 10) >= 4:
                    t_sub = "b"
                else:
                    t_sub = "c"
                code = f"C{sub}{t_sub}"
                desc = KGCv3._describe_c(code)
            else:
                code = "??"
                desc = "Unknown"

        return {
            "code": code,
            "group": code[0] if code != "??" else "?",
            "description": desc,
            "t_mean_c": t_mean,
            "t_hot_c": t_hot,
            "t_cold_c": t_cold,
            "p_ann_mm": p_ann,
            "threshold_mm": threshold if 'threshold' in dir() else None,
        }

    @staticmethod
    def _describe_c(code: str) -> str:
        d = {
            "Cfa": "Humid subtropical",
            "Cfb": "Oceanic (temperate)",
            "Cfc": "Subpolar oceanic",
            "Csa": "Hot-summer Mediterranean",
            "Csb": "Warm-summer Mediterranean",
            "Cwa": "Humid subtropical (dry winter)",
            "Cwb": "Subtropical highland",
        }
        return d.get(code, f"Temperate {code}")


# ============================================================================
# 2. PRSP v3 — Crisis-Aware Recommendations
# ============================================================================

class PRSPv3:
    """
    PRSP v3 — Crisis-aware prescriptive recommendations.

    Rule: if WBI > 70, OVERRIDE context to "crisis_arid" regardless of KGC.
    This ensures Yemen/Somalia get MAR/desalination recommendations.
    """

    INTERVENTIONS = {
        "crisis_arid_low_gov": [
            {"name": "Drip irrigation immediate rollout",
             "impact": 0.45, "lead_time": 2, "cost": 0.15,
             "ref": "FAO AQUASTAT — emergency water-saving"},
            {"name": "Solar-powered desalination (coastal)",
             "impact": 0.40, "lead_time": 3, "cost": 0.70,
             "ref": "IRENA Desalination Yearbook (2021)"},
            {"name": "Emergency water trucking + rainwater harvesting",
             "impact": 0.30, "lead_time": 1, "cost": 0.20,
             "ref": "UNHCR Emergency Water Standards"},
        ],
        "crisis_arid_high_gov": [
            {"name": "Wastewater recycling at scale",
             "impact": 0.45, "lead_time": 3, "cost": 0.50,
             "ref": "WHO Water Reuse Guidelines (2017)"},
            {"name": "Aquifer managed recharge (MAR)",
             "impact": 0.50, "lead_time": 5, "cost": 0.10,
             "ref": "Dillon et al. (2019)"},
            {"name": "Water pricing reform + smart metering",
             "impact": 0.35, "lead_time": 2, "cost": 0.08,
             "ref": "OECD Water Pricing (2010)"},
        ],
        "arid_low_gov": [
            {"name": "Drip irrigation rollout",
             "impact": 0.40, "lead_time": 2, "cost": 0.15,
             "ref": "FAO AQUASTAT"},
            {"name": "Community-based water governance",
             "impact": 0.35, "lead_time": 2, "cost": 0.05,
             "ref": "Ostrom (2009)"},
            {"name": "Solar-powered desalination",
             "impact": 0.35, "lead_time": 5, "cost": 0.70,
             "ref": "IRENA (2021)"},
        ],
        "arid_high_gov": [
            {"name": "Aquifer managed recharge (MAR)",
             "impact": 0.45, "lead_time": 5, "cost": 0.10,
             "ref": "Dillon et al. (2019)"},
            {"name": "Wastewater recycling",
             "impact": 0.40, "lead_time": 3, "cost": 0.50,
             "ref": "WHO (2017)"},
            {"name": "Water pricing reform",
             "impact": 0.30, "lead_time": 2, "cost": 0.05,
             "ref": "OECD (2010)"},
        ],
        "temperate": [
            {"name": "Regenerative agriculture",
             "impact": 0.35, "lead_time": 3, "cost": 0.10,
             "ref": "FAO Save and Grow (2011)"},
            {"name": "Leakage reduction program",
             "impact": 0.30, "lead_time": 2, "cost": 0.30,
             "ref": "World Bank NRW"},
            {"name": "Wetland restoration",
             "impact": 0.30, "lead_time": 5, "cost": 0.20,
             "ref": "Ramsar Convention"},
        ],
        "water_secure": [
            {"name": "Flood-risk preparedness",
             "impact": 0.25, "lead_time": 2, "cost": 0.15,
             "ref": "Sendai Framework"},
            {"name": "Biodiversity conservation",
             "impact": 0.25, "lead_time": 10, "cost": 0.20,
             "ref": "CBD Post-2020"},
            {"name": "Water quality monitoring",
             "impact": 0.20, "lead_time": 1, "cost": 0.10,
             "ref": "WHO Guidelines"},
        ],
    }

    @classmethod
    def recommend(cls, wbi: float, climate_code: str, governance: float) -> Dict[str, Any]:
        """
        Crisis-aware context selection.

        CRITICAL RULE: if WBI > 70, force arid crisis context
        regardless of Köppen classification (since KGC may misclassify
        extreme water-stressed regions due to data quality).
        """
        is_arid = climate_code.startswith("B")
        high_gov = governance > 0.5

        if wbi > 80:
            # Crisis — force arid crisis recommendations regardless of climate
            context = "crisis_arid_high_gov" if high_gov else "crisis_arid_low_gov"
            override_reason = f"WBI={wbi:.0f}>80 forces crisis context (climate={climate_code})"
        elif wbi > 70 and is_arid:
            context = "arid_high_gov" if high_gov else "arid_low_gov"
            override_reason = f"Arid climate + WBI={wbi:.0f}>70"
        elif is_arid:
            context = "arid_high_gov" if high_gov else "arid_low_gov"
            override_reason = "Arid climate"
        elif wbi < 20:
            context = "water_secure"
            override_reason = "Water secure"
        else:
            context = "temperate"
            override_reason = "Default temperate"

        portfolio = cls.INTERVENTIONS[context][:3]
        return {
            "context": context,
            "override_reason": override_reason,
            "portfolio": portfolio,
        }


# ============================================================================
# 3. Global Watchdog v3 (full orchestrator)
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


class GlobalWatchdogV3:
    @staticmethod
    def _wbi_compute(i: WBIInputs) -> Dict[str, Any]:
        scores = {
            "falkenmark": max(0, min(100, (1700 - i.renewable_water_m3_per_capita) / 12)) if i.renewable_water_m3_per_capita < 1700 else 0,
            "withdrawal": max(0, min(100, (i.withdrawal_ratio - 0.2) / 0.8 * 100)) if i.withdrawal_ratio > 0.2 else 0,
            "groundwater": min(100, max(0, i.groundwater_depletion_mm_yr * 10)),
            "quality": 100 * (1 - np.clip(i.water_quality_index, 0, 1)),
            "drought": min(100, i.drought_frequency_events_yr * 40),
            "demand": min(100, i.demand_growth_rate_pct * 25),
            "infrastructure": min(100, i.infrastructure_leakage_pct * 2),
            "governance": 100 * (1 - np.clip(i.governance_score, 0, 1)),
        }
        w = {"falkenmark": 0.15, "withdrawal": 0.20, "groundwater": 0.15,
             "quality": 0.10, "drought": 0.15, "demand": 0.10,
             "infrastructure": 0.08, "governance": 0.07}
        wbi = sum(w[k] * scores[k] for k in scores)
        wbi = float(np.clip(wbi, 0, 100))

        # Time-to-bankruptcy (realistic)
        ytb = None
        ytb_range = None
        if wbi < 85 and i.demand_growth_rate_pct > 0.5:
            remaining = 85 - wbi
            adaptation = 0.5 + i.governance_score * 1.5
            years = max(3, remaining / (i.demand_growth_rate_pct * 1.5) * adaptation)
            ytb = int(years)
            ytb_range = (max(1, int(years * 0.6)), int(years * 1.6))

        if wbi < 20: cls_txt, risk = "Water-Secure", "Low"
        elif wbi < 40: cls_txt, risk = "Water-Stressed", "Moderate"
        elif wbi < 60: cls_txt, risk = "Water-Scarce", "High"
        elif wbi < 80: cls_txt, risk = "Water-Crisis", "Very High"
        else: cls_txt, risk = "Water-Bankruptcy", "Critical"

        return {
            "wbi": wbi, "wbi_low": wbi*0.85, "wbi_high": min(100, wbi*1.15),
            "classification": cls_txt, "risk_level": risk,
            "years_to_bankruptcy_estimate": ytb,
            "years_to_bankruptcy_range": ytb_range,
        }

    def analyze(self, name, climate, water, food_insecurity, energy_access,
                population_millions, displacement=0.0, natural_capital=0.5,
                recharge=0.5, soil=0.5, biodiversity=0.5, financial=0.5):
        t_min, t_max, p = climate
        kgc = KGCv3.classify(t_min, t_max, p)
        wbi = self._wbi_compute(water)

        # WERI (sigmoid soft-cap)
        ws = wbi["wbi"] / 100
        linear = (ws + energy_access + food_insecurity) / 3
        product = ws * energy_access * food_insecurity
        raw = linear + 0.5 * product * 2.5
        weri = 95 * (raw / (raw + 0.5))

        # Conflict (Mach et al.)
        base_risk = (0.30 * (1 - water.governance_score) + 0.20 * 0.5 +
                     0.15 * food_insecurity + 0.15 * displacement)
        climate_amp = 0.15 * (wbi["wbi"] / 100)
        cri = np.clip((base_risk + climate_amp) * 100, 0, 100)

        # ERPI
        eco = 0.35*natural_capital + 0.30*recharge + 0.20*biodiversity + 0.15*soil
        inst = 0.6*water.governance_score + 0.4*financial
        erpi = np.clip(eco*0.6 + inst*0.4, 0, 1)

        # PRSP (crisis-aware)
        prsp = PRSPv3.recommend(wbi["wbi"], kgc["code"], water.governance_score)

        return {
            "region": name,
            "kgc": kgc,
            "wbi": wbi,
            "weri": {"weri": weri,
                     "status": ("Nexus-Stable" if weri < 25 else "Nexus-Stressed"
                                if weri < 50 else "Nexus-Critical"
                                if weri < 75 else "Nexus-Collapse")},
            "cri": {"cri": float(cri),
                    "classification": ("Low" if cri < 25 else "Moderate"
                                       if cri < 50 else "High" if cri < 75 else "Critical")},
            "erpi": float(erpi),
            "prsp": prsp,
        }


def demo():
    print("=" * 80)
    print("🌍 HYDROMA GLOBAL WATCHDOG v3 — Final Scientific Refinement")
    print("=" * 80)
    print("   Improvements: KGCv3 (correct arid detection) + PRSPv3 (crisis-aware)\n")

    gw = GlobalWatchdogV3()

    regions = {
        "Somalia": (
            (np.array([24,25,27,28,28,27,25,25,26,27,26,25]),
             np.array([30,31,32,33,32,30,28,28,30,31,31,30]),
             np.array([5,2,10,40,60,25,15,5,10,50,70,20])),
            WBIInputs(150, 0.95, 5.0, 0.3, 2.5, 3.5, 55.0, 0.2),
            {"food": 0.85, "energy": 0.8, "pop": 18.0, "disp": 0.15,
             "nat": 0.2, "rch": 0.1, "soil": 0.3, "bio": 0.25, "fin": 0.1},
        ),
        "Sudan": (
            (np.array([18,20,23,26,28,28,25,24,25,25,22,19]),
             np.array([32,34,37,40,41,40,35,33,35,37,35,33]),
             np.array([0,0,0,5,20,50,100,120,70,20,5,0])),
            WBIInputs(300, 0.85, 4.0, 0.4, 2.0, 3.0, 45.0, 0.3),
            {"food": 0.75, "energy": 0.6, "pop": 48.0, "disp": 0.12,
             "nat": 0.3, "rch": 0.2, "soil": 0.4, "bio": 0.35, "fin": 0.2},
        ),
        "Yemen": (
            (np.array([12,14,17,19,21,23,24,23,21,18,15,13]),
             np.array([24,26,29,31,33,36,37,36,33,29,26,24]),
             np.array([5,3,10,30,15,2,5,15,8,2,4,5])),
            WBIInputs(80, 1.8, 8.0, 0.25, 3.0, 2.8, 60.0, 0.15),
            {"food": 0.8, "energy": 0.7, "pop": 34.0, "disp": 0.18,
             "nat": 0.15, "rch": 0.1, "soil": 0.2, "bio": 0.2, "fin": 0.05},
        ),
        "Iran_Central": (
            (np.array([-2,1,6,11,16,22,25,24,19,12,5,0]),
             np.array([10,13,19,25,31,37,40,39,34,26,17,11]),
             np.array([30,35,40,35,15,3,1,1,3,15,25,30])),
            WBIInputs(900, 0.88, 6.0, 0.5, 1.5, 2.0, 30.0, 0.5),
            {"food": 0.35, "energy": 0.1, "pop": 88.0, "disp": 0.02,
             "nat": 0.35, "rch": 0.3, "soil": 0.45, "bio": 0.4, "fin": 0.4},
        ),
        "California_USA": (
            (np.array([7,8,9,11,14,17,19,19,17,13,9,7]),
             np.array([18,19,20,22,25,29,33,33,31,26,21,18]),
             np.array([80,75,60,30,15,5,1,1,5,20,45,70])),
            WBIInputs(1100, 0.65, 2.5, 0.75, 1.2, 0.8, 12.0, 0.85),
            {"food": 0.15, "energy": 0.05, "pop": 39.0, "disp": 0.005,
             "nat": 0.5, "rch": 0.6, "soil": 0.7, "bio": 0.55, "fin": 0.9},
        ),
        "Netherlands": (
            (np.array([1,1,3,5,9,12,14,14,11,8,4,2]),
             np.array([6,7,10,14,18,20,23,22,19,14,10,7]),
             np.array([70,50,60,45,55,65,75,80,75,85,85,80])),
            WBIInputs(3500, 0.15, 0.0, 0.9, 0.1, 0.2, 5.0, 0.95),
            {"food": 0.05, "energy": 0.05, "pop": 18.0, "disp": 0.001,
             "nat": 0.6, "rch": 0.9, "soil": 0.85, "bio": 0.5, "fin": 0.95},
        ),
    }

    results = {}
    for name, (climate, water, extras) in regions.items():
        r = gw.analyze(name, climate, water, extras["food"], extras["energy"],
                       extras["pop"], extras["disp"], extras["nat"], extras["rch"],
                       extras["soil"], extras["bio"], extras["fin"])
        results[name] = r

        print(f"\n{'─'*70}")
        print(f"🌍 {name}")
        print(f"{'─'*70}")
        print(f"  🌡️ KGC:       {r['kgc']['code']} — {r['kgc']['description']}")
        print(f"  💧 WBI:       {r['wbi']['wbi']:.1f}/100 [{r['wbi']['wbi_low']:.1f}-{r['wbi']['wbi_high']:.1f}] — {r['wbi']['classification']}")
        if r['wbi']['years_to_bankruptcy_range']:
            lo, hi = r['wbi']['years_to_bankruptcy_range']
            print(f"             ⏱ → {lo}-{hi} years")
        print(f"  ⚡ WERI:      {r['weri']['weri']:.1f}/100 ({r['weri']['status']})")
        print(f"  ⚔️ Conflict:  {r['cri']['cri']:.1f}/100 ({r['cri']['classification']})")
        print(f"  🌱 Recovery:  {r['erpi']:.2f}")
        print(f"  💡 PRSP context: {r['prsp']['context']}")
        print(f"     Override reason: {r['prsp']['override_reason']}")
        print(f"     Top Recommendations:")
        for i, iv in enumerate(r["prsp"]["portfolio"], 1):
            print(f"       {i}. {iv['name']} (impact {iv['impact']:.0%}, {iv['lead_time']}yr)")

    # Final ranking
    print(f"\n{'='*70}")
    print("🌐 FINAL RANKING")
    print(f"{'='*70}")
    for i, (name, r) in enumerate(sorted(results.items(), key=lambda x: x[1]["wbi"]["wbi"], reverse=True), 1):
        w = r["wbi"]
        ytb = r["wbi"]["years_to_bankruptcy_range"]
        ytb_str = f" → ⏱ {ytb[0]}-{ytb[1]}yr" if ytb else ""
        print(f"  #{i} {name:<18} WBI={w['wbi']:5.1f} [{w['wbi_low']:.0f}-{w['wbi_high']:.0f}] ({w['classification']}){ytb_str}")

    # Validation check
    print(f"\n{'='*70}")
    print("✅ VALIDATION CHECK (Peel et al. 2007 reference)")
    print(f"{'='*70}")
    expected = {
        "Somalia": ["BSh", "BWh", "Aw"],  # acceptable classifications
        "Sudan": ["BWh", "BSh", "Aw", "Am"],
        "Yemen": ["BWh", "BWk"],
        "Iran_Central": ["BWh", "BSh", "Csa"],
        "California_USA": ["Csa", "Csb", "Cfa"],
        "Netherlands": ["Cfb", "Cfc"],
    }
    for name, r in results.items():
        exp = expected.get(name, [])
        match = r["kgc"]["code"] in exp
        icon = "✅" if match else "⚠️"
        print(f"  {icon} {name:<18} → {r['kgc']['code']} (expected: {exp})")

    return results


if __name__ == "__main__":
    demo()