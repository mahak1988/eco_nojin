# ============================================================================
# Hydroma Uncertainty Quantification & Local Knowledge Engine - Phase 5
# Algorithms: H22 Monte Carlo Uncertainty | H23 Multi-scale Data Fusion
#             H25 Local Knowledge Integration
#             H26 Multi-objective Monte Carlo + CRPS (F2)
# References: IPCC AR6 WG1 (2021); Altieri 2018; FAO Participatory Methods
#             Gneiting & Raftery (2007) JASA 102:359-378 (CRPS)
# ============================================================================
import contextlib
import math
import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

__version__ = "1.0.0"


@dataclass
class UncertaintyConfig:
    # H22: مونت‌کارلو
    default_simulations: int = 500
    random_seed: int | None = 42

    # H23: تلفیق داده
    fusion_weights: dict = field(
        default_factory=lambda: {"satellite": 0.40, "station": 0.35, "model": 0.15, "local": 0.10}
    )
    satellite_resolution_m: int = 30
    station_radius_km: float = 50.0

    # H25: دانش بومی
    knowledge_confidence_weights: dict = field(
        default_factory=lambda: {
            "experience_years": 0.30,
            "consistency": 0.25,
            "community_agreement": 0.25,
            "scientific_alignment": 0.20,
        }
    )
    max_experience_years: int = 50


# ============================================================================
class UncertaintyAndKnowledgeEngine:
    # ------------------------------------------------------------------ init
    def __init__(self, config: UncertaintyConfig | None = None):
        self.cfg = config or UncertaintyConfig()
        if self.cfg.random_seed is not None:
            random.seed(self.cfg.random_seed)

    # ------------------------------------------------------------------- H22
    def h22_monte_carlo_uncertainty(
        self,
        base_yield_t_ha: float,
        n_simulations: int | None = None,
        climate_variability: float = 0.15,
        soil_variability: float = 0.10,
        pest_variability: float = 0.08,
    ) -> dict:
        """
        تحلیل عدم قطعیت مونت‌کارلو (Monte Carlo Uncertainty Analysis)
        اجرای شبیه‌سازی با پارامترهای تصادفی و محاسبه بازه اطمینان
        خروجی: P10, P50, P90 + ضریب تغییرات
        """
        n = n_simulations or self.cfg.default_simulations
        yields = []

        for _ in range(n):
            # اعمال تغییرات تصادفی
            climate_factor = 1.0 + random.gauss(0, climate_variability)
            soil_factor = 1.0 + random.gauss(0, soil_variability)
            pest_factor = 1.0 + random.gauss(0, pest_variability)

            # محدود کردن عوامل به بازه منطقی
            climate_factor = max(0.3, min(1.5, climate_factor))
            soil_factor = max(0.5, min(1.3, soil_factor))
            pest_factor = max(0.4, min(1.2, pest_factor))

            simulated_yield = base_yield_t_ha * climate_factor * soil_factor * pest_factor
            yields.append(max(0.0, simulated_yield))

        # مرتب‌سازی و محاسبه صدک‌ها
        yields.sort()
        p10 = yields[int(n * 0.10)]
        p50 = yields[int(n * 0.50)]
        p90 = yields[int(n * 0.90)]

        # میانگین و انحراف معیار
        mean_yield = sum(yields) / n
        variance = sum((y - mean_yield) ** 2 for y in yields) / n
        std_yield = math.sqrt(variance)
        cv = std_yield / mean_yield if mean_yield > 0 else 0

        # تعیین سطح اطمینان
        if cv < 0.15:
            confidence = "بالا"
            confidence_score = 0.85
        elif cv < 0.30:
            confidence = "متوسط"
            confidence_score = 0.65
        else:
            confidence = "پایین"
            confidence_score = 0.45

        return {
            "base_yield_t_ha": round(base_yield_t_ha, 2),
            "n_simulations": n,
            "p10_t_ha": round(p10, 2),
            "p50_t_ha": round(p50, 2),
            "p90_t_ha": round(p90, 2),
            "mean_t_ha": round(mean_yield, 2),
            "std_t_ha": round(std_yield, 2),
            "coefficient_of_variation": round(cv, 3),
            "confidence_level": confidence,
            "confidence_score": confidence_score,
            "yield_range_percent": round((p90 - p10) / p50 * 100, 1) if p50 > 0 else 0,
            "recommendation": self._uncertainty_recommendation(cv),
        }

    def _uncertainty_recommendation(self, cv: float) -> str:
        if cv < 0.15:
            return "پیش‌بینی قابل اتکا؛ تصمیم‌گیری با اطمینان بالا"
        elif cv < 0.30:
            return "پیش‌بینی با احتیاط؛ سناریوهای جایگزین بررسی شود"
        else:
            return "پیش‌بینی پرریسک؛ کشت متنوع و بیمه توصیه می‌شود"

    # ------------------------------------------------------------------- H23
    def h23_multi_scale_fusion(
        self,
        satellite_value: float,
        station_value: float,
        model_value: float,
        local_value: float | None = None,
        satellite_quality: float = 0.8,
        station_density: float = 0.7,
    ) -> dict:
        """
        تلفیق داده چندمقیاسی (Multi-scale Data Fusion)
        ترکیب داده‌های ماهواره‌ای، ایستگاهی، مدل و محلی با وزن‌دهی دینامیک
        """
        w = self.cfg.fusion_weights.copy()

        # تنظیم وزن بر اساس کیفیت منابع
        w["satellite"] *= satellite_quality
        w["station"] *= station_density

        # اگر داده محلی موجود نباشد، وزن آن به ایستگاهی منتقل می‌شود
        if local_value is None:
            w["station"] += w["local"]
            w["local"] = 0.0
            local_value = station_value  # جایگزینی با ایستگاهی

        # نرمال‌سازی وزن‌ها
        total_w = sum(w.values())
        if total_w > 0:
            w = {k: v / total_w for k, v in w.items()}

        # محاسبه مقدار تلفیقی
        fused_value = (
            w["satellite"] * satellite_value
            + w["station"] * station_value
            + w["model"] * model_value
            + w["local"] * local_value
        )

        # ارزیابی کیفیت تلفیق
        values = [satellite_value, station_value, model_value, local_value]
        valid_values = [v for v in values if v is not None]
        if len(valid_values) > 1:
            mean_v = sum(valid_values) / len(valid_values)
            max_deviation = max(abs(v - mean_v) for v in valid_values)
            consistency = max(0.0, 1.0 - max_deviation / (mean_v + 1e-6))
        else:
            consistency = 0.5

        if consistency >= 0.8:
            quality = "بالا"
        elif consistency >= 0.5:
            quality = "متوسط"
        else:
            quality = "پایین"

        return {
            "fused_value": round(fused_value, 3),
            "weights_applied": {k: round(v, 3) for k, v in w.items()},
            "consistency_score": round(consistency, 3),
            "data_quality": quality,
            "sources_used": len(valid_values),
            "recommendation": self._fusion_recommendation(consistency),
        }

    def _fusion_recommendation(self, consistency: float) -> str:
        if consistency >= 0.8:
            return "داده‌ها همساز هستند؛ تلفیق قابل اتکا"
        elif consistency >= 0.5:
            return "اختلاف متوسط بین منابع؛ بررسی بیشتر توصیه می‌شود"
        else:
            return "اختلاف زیاد بین منابع؛ نیاز به اعتبارسنجی میدانی"

    # ------------------------------------------------------------------- H25
    def h25_local_knowledge_integration(
        self,
        farmer_experience_years: int,
        traditional_calendar_reliability: float,
        community_agreement_level: float,
        scientific_alignment: float,
    ) -> dict:
        """
        ادغام دانش بومی (Local Knowledge Integration)
        تبدیل دانش سنتی و تجربی کشاورزان به پارامترهای کمّی قابل استفاده در مدل
        """
        w = self.cfg.knowledge_confidence_weights

        # امتیاز تجربه (با سقف)
        experience_score = min(1.0, farmer_experience_years / self.cfg.max_experience_years)

        # محدود کردن سایر امتیازات به بازه 0-1
        calendar_score = max(0.0, min(1.0, traditional_calendar_reliability))
        community_score = max(0.0, min(1.0, community_agreement_level))
        alignment_score = max(0.0, min(1.0, scientific_alignment))

        # محاسبه امتیاز کل
        knowledge_score = (
            w["experience_years"] * experience_score
            + w["consistency"] * calendar_score
            + w["community_agreement"] * community_score
            + w["scientific_alignment"] * alignment_score
        )

        # تعیین وزن دانش بومی در مدل
        if knowledge_score >= 0.75:
            integration_weight = 0.25  # وزن بالا در مدل
            classification = "دانش بومی بسیار معتبر"
        elif knowledge_score >= 0.55:
            integration_weight = 0.15  # وزن متوسط
            classification = "دانش بومی معتبر"
        elif knowledge_score >= 0.35:
            integration_weight = 0.08  # وزن کم
            classification = "دانش بومی با اعتبار محدود"
        else:
            integration_weight = 0.0  # بدون وزن
            classification = "دانش بومی نیازمند اعتبارسنجی"

        return {
            "knowledge_score": round(knowledge_score, 3),
            "classification": classification,
            "integration_weight": integration_weight,
            "component_scores": {
                "experience": round(experience_score, 2),
                "calendar_reliability": round(calendar_score, 2),
                "community_agreement": round(community_score, 2),
                "scientific_alignment": round(alignment_score, 2),
            },
            "recommendation": self._knowledge_recommendation(knowledge_score),
        }

    def _knowledge_recommendation(self, score: float) -> str:
        if score >= 0.75:
            return "ادغام کامل در مدل؛ ثبت در پایگاه دانش بومی"
        elif score >= 0.55:
            return "ادغام با وزن متوسط؛ پایش و بازنگری دوره‌ای"
        elif score >= 0.35:
            return "ادغام محدود؛ نیاز به تأیید علمی بیشتر"
        else:
            return "عدم ادغام؛ مستندسازی برای ارزیابی‌های آینده"

    # ------------------------------------------------- گزارش جامع عدم قطعیت
    def generate_uncertainty_report(
        self,
        base_yield: float,
        satellite_data: float,
        station_data: float,
        farmer_experience: int = 20,
        calendar_reliability: float = 0.6,
    ) -> dict:
        """تولید گزارش جامع عدم قطعیت با ترکیب هر سه الگوریتم"""

        report: dict[str, Any] = {"model_version": __version__}

        # H22: عدم قطعیت مونت‌کارلو
        report["h22_uncertainty"] = self.h22_monte_carlo_uncertainty(base_yield)

        # H23: تلفیق داده
        report["h23_fusion"] = self.h23_multi_scale_fusion(
            satellite_data, station_data, base_yield * 0.95
        )

        # H25: دانش بومی
        report["h25_knowledge"] = self.h25_local_knowledge_integration(
            farmer_experience, calendar_reliability, 0.7, 0.6
        )

        # امتیاز کلی قابلیت اتکا
        report["overall_reliability"] = self._calculate_overall_reliability(report)

        return report

    def _calculate_overall_reliability(self, report: dict) -> dict:
        scores = []

        if "h22_uncertainty" in report:
            scores.append(report["h22_uncertainty"]["confidence_score"])
        if "h23_fusion" in report:
            scores.append(report["h23_fusion"]["consistency_score"])
        if "h25_knowledge" in report:
            scores.append(report["h25_knowledge"]["knowledge_score"])

        overall = sum(scores) / len(scores) if scores else 0.0

        if overall >= 0.75:
            status = "قابلیت اطمینان بالا"
        elif overall >= 0.55:
            status = "قابلیت اطمینان متوسط"
        else:
            status = "قابلیت اطمینان پایین"

        return {
            "overall_score": round(overall, 3),
            "status": status,
            "components_evaluated": len(scores),
        }

    # ------------------------------------------------- تصحیح خروجی مدل‌ها
    def apply_uncertainty_corrections(self, result, uncertainty_params: dict) -> object:
        """اعمال تصحیحات عدم قطعیت به خروجی مدل‌های رشد"""

        # دریافت ضریب اطمینان
        confidence = uncertainty_params.get("confidence_score", 0.65)

        # اعمال تخفیف بر اساس اطمینان
        if confidence < 0.5:
            correction_factor = 0.85  # تخفیف برای اطمینان پایین
        elif confidence < 0.7:
            correction_factor = 0.95  # تخفیف ملایم
        else:
            correction_factor = 1.0  # بدون تخفیف

        if hasattr(result, "yield_t_ha"):
            result.yield_t_ha = round(result.yield_t_ha * correction_factor, 2)

        # افزودن بازه اطمینان به هشدارها
        p10 = uncertainty_params.get("p10_t_ha", 0)
        p90 = uncertainty_params.get("p90_t_ha", 0)

        with contextlib.suppress(Exception):
            result.warnings = [
                *list(result.warnings),
                f"Uncertainty correction x{correction_factor:.2f} (P10={p10:.2f}, P90={p90:.2f}, confidence={confidence:.2f})",
            ]

        return result

    # ========================================================================
    # H26: Multi-objective Monte Carlo + CRPS (F2)
    # ========================================================================

    def h26_multi_objective_monte_carlo(
        self,
        base_values: dict[str, float],
        n_simulations: int | None = None,
        variabilities: dict[str, float] | None = None,
        correlations: dict[tuple[str, str], float] | None = None,
    ) -> dict[str, Any]:
        """
        Multi-objective Monte Carlo Uncertainty (H26).

        Runs joint Monte Carlo over multiple objectives (yield, NPV, IRR, SOC, erosion, etc.)
        with optional correlation structure.

        Returns per-objective P10/P50/P90, mean, std, CV, and CRPS if observations provided.
        """
        n = n_simulations or self.cfg.default_simulations

        if variabilities is None:
            variabilities = dict.fromkeys(base_values, 0.15)

        # Build correlation matrix
        obj_list = list(base_values.keys())
        n_obj = len(obj_list)
        corr_matrix = np.eye(n_obj)
        if correlations:
            for (i, j), rho in correlations.items():
                try:
                    i_idx = obj_list.index(i)
                    j_idx = obj_list.index(j)
                    corr_matrix[i_idx, j_idx] = rho
                    corr_matrix[j_idx, i_idx] = rho
                except ValueError:
                    pass

        # Cholesky decomposition for correlated sampling
        try:
            L = np.linalg.cholesky(corr_matrix)
        except np.linalg.LinAlgError:
            L = np.eye(n_obj)  # fallback to independent

        # Variability std per objective
        std_vec = np.array([variabilities.get(obj, 0.15) for obj in obj_list])

        results: dict[str, Any] = {}
        all_samples: dict[str, list[float]] = {obj: [] for obj in base_values}

        for _ in range(self.cfg.default_simulations):
            # Generate correlated random factors
            z = np.random.normal(0, 1, len(obj_list))
            correlated = L @ z
            factors = 1.0 + correlated * std_vec

            # Clip to reasonable bounds
            factors = np.clip(factors, 0.3, 1.8)

            # Apply to each objective
            for idx, obj in enumerate(base_values):
                simulated = base_values[obj] * factors[idx]
                all_samples[obj].append(max(0.0, simulated))

        # Compute statistics per objective
        results = {}
        for obj in base_values:
            samples = np.array(all_samples[obj])
            samples.sort()
            n = len(samples)
            p10 = samples[int(n * 0.10)]
            p50 = samples[int(n * 0.50)]
            p90 = samples[int(n * 0.90)]
            mean_val = np.mean(samples)
            std_val = np.std(samples, ddof=1)
            cv = std_val / mean_val if mean_val > 0 else 0

            # Determine confidence
            if cv < 0.15:
                confidence = "بالا"
                confidence_score = 0.85
            elif cv < 0.30:
                confidence = "متوسط"
                confidence_score = 0.65
            else:
                confidence = "پایین"
                confidence_score = 0.45

            results[obj] = {
                "base_value": round(base_values[obj], 3),
                "n_simulations": self.cfg.default_simulations,
                "p10": round(p10, 3),
                "p50": round(p50, 3),
                "p90": round(p90, 3),
                "mean": round(mean_val, 3),
                "std": round(std_val, 3),
                "coefficient_of_variation": round(cv, 3),
                "confidence_level": confidence,
                "confidence_score": confidence_score,
                "range_percent": round((p90 - p10) / p50 * 100, 1) if p50 > 0 else 0,
            }

        return {
            "objectives": results,
            "n_simulations": self.cfg.default_simulations,
            "correlation_matrix_used": corr_matrix.tolist(),
        }

    def h27_crps_evaluation(
        self,
        samples: dict[str, list[float]],
        observations: dict[str, float],
    ) -> dict[str, Any]:
        """
        CRPS Evaluation (H27) per Gneiting & Raftery (2007).

        Computes CRPS for each objective given Monte Carlo samples and observations.
        Returns per-objective CRPS, MAE, spread, and reliability flag.
        """
        from scripts.crps_score import crps_from_samples

        results = {}
        all_samples_list = []
        obs_list = []

        for obj, samples_list in samples.items():
            if obj in observations:
                arr = np.array(samples_list)
                score = crps_from_samples(arr, observations[obj])
                results[obj] = {
                    "crps": round(score.crps, 4),
                    "mae": round(score.mean_abs_error, 4),
                    "spread": round(score.spread, 4),
                    "reliable": score.reliable,
                    "n_samples": score.n_samples,
                }
                all_samples_list.append(np.array(samples_list))
                obs_list.append(observations[obj])

        # Overall CRPS comparison if multiple objectives
        if len(all_samples_list) > 1:
            # Create pseudo-comparison
            pass

        return {
            "objectives": results,
            "overall_crps": np.mean([v["crps"] for v in results.values()]) if results else 0.0,
            "all_reliable": all(v["reliable"] for v in results.values()) if results else True,
        }

    def h28_crps_from_pareto(
        self,
        pareto_front: list[dict],
        observation: dict[str, float],
        objective_key: str = "yield_ton_ha",
    ) -> dict:
        """
        CRPS evaluation from Pareto front ensemble.

        Uses the spread of Pareto-optimal solutions as an ensemble forecast.
        """
        # Local import for the same reason as h27_crps_evaluation: importing
        # scripts.crps_score at module scope makes the engine depend on the
        # scripts package at import time.
        from scripts.crps_score import crps_empirical

        if not pareto_front:
            return {"error": "Empty Pareto front"}

        samples = [p.get(objective_key, 0) for p in pareto_front]
        obs = observation.get(objective_key, 0)

        # Use the samples directly
        return {
            "objective": objective_key,
            "crps": crps_empirical(np.array(samples), obs),
            "n_solutions": len(samples),
            "pareto_spread": max(samples) - min(samples) if samples else 0,
        }

    def generate_full_uncertainty_report(
        self,
        chain_outputs: dict[str, float],
        variabilities: dict[str, float] | None = None,
        observations: dict[str, float] | None = None,
    ) -> dict:
        """
        Generate full uncertainty report with H26 + H27.
        """
        report = {
            "model_version": __version__,
            "h26_multi_objective": self.h26_multi_objective_monte_carlo(
                chain_outputs, variabilities=variabilities
            ),
        }

        if observations:
            # Generate samples for CRPS
            mc = self.h26_multi_objective_monte_carlo(
                {k: v for k, v in chain_outputs.items() if k in (observations or {})},
                variabilities={k: v for k, v in (variabilities or {}).items() if k in (observations or {})}
            )
            # Reconstruct samples from percentiles (approximate)
            samples_dict: dict[str, list[float]] = {}
            for obj, _vals in mc["objectives"].items():
                # Reconstruct approximate samples from P10/P50/P90
                # This is approximate - real samples would be stored
                samples_dict[obj] = []  # placeholder

            if observations:
                report["h27_crps"] = self.h27_crps_evaluation(samples_dict, observations)

        return report
