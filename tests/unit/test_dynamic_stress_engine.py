import structlog

logger = structlog.get_logger()
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.hydroma.climate_adaptation.dynamic_stress_engine import (
    DynamicStressEngine, vpd_kpa)

def main():
    e = DynamicStressEngine()
    # H01
    assert e.h01_effective_rain_mm(0.0) == 0.0
    d10 = e.h01_intensity_discount(10.0)
    d80 = e.h01_intensity_discount(80.0)
    assert d80 < d10, "H01: discount must decrease with intensity"
    # H02
    assert e.h02_night_penalty(10.0) == 0.0
    assert 0.0 < e.h02_night_penalty(20.0) <= 0.30
    # H03
    v = vpd_kpa(40.0, 25.0, 30.0)
    assert e.h03_et_correction_factor(v) > 1.0
    assert e.h03_et_correction_factor(1.0) == 1.0
    # H04
    ks = [e.h04_heat_ks(t) for t in range(25, 46)]
    assert all(a >= b for a, b in zip(ks, ks[1:])), "H04 must be monotonic decreasing"
    assert abs(e.h04_heat_ks(35.0) - 0.5) < 1e-9
    # H08
    assert e.h08_combined_ks(0.5, 0.5, 1.0, True) < e.h08_combined_ks(0.5, 0.5, 1.0, False)
    logger.info("ALL DSE TESTS PASSED (H01,H02,H03,H04,H08)")

if __name__ == "__main__":
    main()
