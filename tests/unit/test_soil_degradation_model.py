import structlog

logger = structlog.get_logger()
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.soil_degradation_model import (
    SoilDegradationModel)

def main():
    model = SoilDegradationModel()

    # H09: ظرفیت آب پویا
    r1 = model.h09_dynamic_awc(150.0, soc_current_pct=3.0)
    assert r1["awc_adjusted_mm_m"] > r1["awc_base_mm_m"]  # افزایش با افزایش SOC
    r1_low = model.h09_dynamic_awc(150.0, soc_current_pct=0.5)
    assert r1_low["awc_adjusted_mm_m"] < r1["awc_adjusted_mm_m"]  # کاهش با کاهش SOC

    # H10: فرسایش
    r2 = model.h10_root_depth_decay(100.0, 15.0, 10)
    assert r2["effective_root_depth_cm"] < 100.0
    assert r2["depth_loss_percent"] > 0

    # H11: شوری
    r3 = model.h11_salinity_trend(1.0, 0.2, 10)
    assert r3["ec_projected_ds_m"] > 1.0
    assert r3["estimated_yield_impact_percent"] >= 0

    # H12: تراکم
    r4 = model.h12_compaction_adjusted_ksat(20.0, 0.3)
    assert r4["ksat_adjusted_mm_h"] < r4["ksat_original_mm_h"]
    assert r4["reduction_percent"] == 30.0

    # H13: حاصلخیزی
    r5 = model.h13_soil_fertility_index(2.5, 0.2, 40.0, 250.0, 7.0, 0.6)
    assert 0.0 <= r5["fertility_index"] <= 1.0
    assert len(r5["component_scores"]) == 6

    # H14: فرونشست
    r6 = model.h14_subsidence_risk(500.0, 50.0, "clay")
    assert r6["subsidence_rate_mm_per_year"] >= 0
    assert r6["risk_level"] in ("کم", "متوسط", "شدید", "بحرانی")

    # گزارش یکپارچه
    report = model.generate_degradation_report(
        soc_pct=2.0, erosion_rate_t_ha_yr=10.0, ec_ds_m=2.0,
        ksat_mm_h=20.0, groundwater_extraction_mm_yr=300.0, soil_type="loam")
    assert "overall_sustainability_score" in report
    assert 0 <= report["overall_sustainability_score"]["overall_score"] <= 100

    logger.info("ALL SOIL DEGRADATION TESTS PASSED (H09-H14)")

if __name__ == "__main__":
    main()
