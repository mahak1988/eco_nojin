import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.seed_optimization_engine import (
    SeedOptimizationEngine)

def main():
    engine = SeedOptimizationEngine()

    # H15: تطبیق ژنوتیپ-محیط
    tolerances = {"drought": 0.8, "heat": 0.7, "salinity": 0.5,
                  "frost": 0.6, "waterlogging": 0.4}
    stresses = {"drought": 0.6, "heat": 0.7, "salinity": 0.3,
                "frost": 0.4, "waterlogging": 0.2}
    r1 = engine.h15_gxe_matching(tolerances, stresses)
    assert 0.0 <= r1["gxe_score"] <= 1.0
    assert r1["classification"] in ("تطبیق عالی", "تطبیق خوب", "تطبیق متوسط", "تطبیق ضعیف")

    # H16: سازگاری میدانی
    r2 = engine.h16_field_hardiness(0.6, 0.7, 0.5)
    assert 0.0 <= r2["hardiness_score"] <= 1.0
    assert 0.0 <= r2["survival_probability_percent"] <= 100.0

    # H17: مقاومت بومی
    r3 = engine.h17_native_resilience(30, 0.7, 0.6, 0.5)
    assert 0.0 <= r3["native_resilience_index"] <= 1.0

    # H18: بهینه‌ساز دوره رشد
    r4 = engine.h18_growth_duration_optimizer(180, 200, 150, 160)
    assert r4["optimal_duration_days"] >= 60
    assert r4["recommended_variety_type"] in ("زودرس", "میان‌رس", "دیررس")

    # H19: آسیب‌پذیری ژنتیکی
    r5 = engine.h19_genetic_vulnerability(0.3, 70.0, 2)
    assert 0.0 <= r5["vulnerability_index"] <= 1.0
    assert r5["risk_level"] in ("کم", "متوسط", "شدید", "بحرانی")

    # H20: تطبیق اکولوژیک
    r6 = engine.h20_ecozone_matching(0.8, 0.7, 0.9, 0.6)
    assert 0.0 <= r6["ecozone_match_score"] <= 1.0

    # H21: میکروبیوم
    r7 = engine.h21_microbiome_compatibility(2.5, 7.0, 0.6, 0.5)
    assert 0.0 <= r7["microbiome_score"] <= 1.0
    assert isinstance(r7["inoculation_recommended"], bool)

    # گزارش یکپارچه
    advisory = engine.generate_seed_advisory(
        tolerances, stresses,
        is_tissue_culture=True,
        local_adaptation_years=25,
        genetic_diversity=0.4,
        soil_params={"soc_pct": 1.8, "ph": 7.2, "biology_index": 0.5, "organic_input": 0.4})
    assert "overall_seed_suitability" in advisory
    assert 0.0 <= advisory["overall_seed_suitability"]["overall_score"] <= 1.0

    print("ALL SEED OPTIMIZATION TESTS PASSED (H15-H21)")

if __name__ == "__main__":
    main()
