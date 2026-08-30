import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.uncertainty_knowledge_engine import (
    UncertaintyAndKnowledgeEngine)

def main():
    engine = UncertaintyAndKnowledgeEngine()

    # H22: مونت‌کارلو
    r1 = engine.h22_monte_carlo_uncertainty(5.0, n_simulations=100)
    assert r1["p10_t_ha"] <= r1["p50_t_ha"] <= r1["p90_t_ha"]
    assert r1["coefficient_of_variation"] >= 0
    assert r1["confidence_level"] in ("بالا", "متوسط", "پایین")

    # H23: تلفیق داده
    r2 = engine.h23_multi_scale_fusion(4.5, 5.0, 4.8)
    assert r2["fused_value"] > 0
    assert r2["consistency_score"] >= 0
    assert r2["data_quality"] in ("بالا", "متوسط", "پایین")

    # H25: دانش بومی
    r3 = engine.h25_local_knowledge_integration(30, 0.7, 0.8, 0.6)
    assert 0.0 <= r3["knowledge_score"] <= 1.0
    assert r3["integration_weight"] >= 0.0

    # گزارش جامع
    report = engine.generate_uncertainty_report(5.0, 4.5, 5.0, 25, 0.7)
    assert "overall_reliability" in report
    assert 0.0 <= report["overall_reliability"]["overall_score"] <= 1.0

    print("ALL UNCERTAINTY & KNOWLEDGE TESTS PASSED (H22,H23,H25)")

if __name__ == "__main__":
    main()
