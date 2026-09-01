import structlog

logger = structlog.get_logger()
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.climate_adaptive_phenology import (
    ClimateAdaptivePhenology)

def main():
    cap = ClimateAdaptivePhenology()

    # H05: فنولوژی پویا
    soil = [8.0, 8.5, 9.0, 9.5]
    r = cap.h05_dynamic_planting_day(280, soil, rain_onset_day_of_year=300)
    assert "planting_day_of_year" in r
    assert r["planting_day_of_year"] >= 280
    assert len(r["reasons"]) > 0

    # H06: خشکسالی ناگهانی
    vpd = [1.0, 1.2, 1.5, 1.9, 2.4, 3.0, 3.7]
    sm = [0.6, 0.55, 0.5, 0.42, 0.35, 0.28, 0.22, 0.17,
          0.13, 0.10, 0.08, 0.06, 0.05, 0.04]
    r2 = cap.h06_flash_drought_risk(vpd, sm, forecast_rain_mm_next_14d=2.0)
    assert 0.0 <= r2["risk_0_1"] <= 1.0
    assert r2["level"] in ("عادی", "پایش", "هشدار", "بحرانی")
    assert r2["risk_0_1"] >= 0.5  # شرایط تنش شدید

    # H07: ساعات سرمایی
    temps = [1.0, 2.0, 3.0, 5.0, 7.0, 9.0, 11.0, 13.0] * 100
    r3 = cap.h07_chilling_hours(temps)
    assert r3["chilling_units"] >= 0
    assert r3["hours_analyzed"] == 800

    # H24: تصحیح بلادرنگ
    r4 = cap.h24_realtime_correction(0.4, 0.6)
    assert 0.5 <= r4["correction_factor"] <= 1.5
    assert r4["correction_factor"] < 1.0  # عملکرد کمتر از پیش‌بینی

    # گزارش فصلی یکپارچه
    adv = cap.generate_season_advisory(
        last_frost_day=280, soil_temp_series=soil,
        vpd_7d=vpd, sm_14d=sm, forecast_rain=2.0,
        winter_temps=temps)
    assert "planting" in adv and "flash_drought" in adv and "chilling" in adv

    logger.info("ALL CAP TESTS PASSED (H05,H06,H07,H24)")

if __name__ == "__main__":
    main()
