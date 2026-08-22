"""
Phase 12 Final Models Patch
===========================
هدف: حل قطعی ۲ مشکل باقی‌مانده با راه‌حل‌های علمی صحیح

1. H-Pheno: جایگزینی derivative-based با GDD (Growing Degree Days)
   - GDD = Σ(T_mean - T_base) for T_mean > T_base
   - Wheat typical: 1500-2000 GDD to maturity
   - LOS = GDD_to_maturity / average_daily_GDD
   
2. EPIA: Fix مقایسه temporal scales (daily vs weekly)
   - تقسیم rainfall بر 7 برای daily average

References:
- McMaster & Wilhelm (1997) "Growing degree-days: one equation, two interpretations"
- FAO-56 (Allen et al. 1998) Irrigation scheduling
"""
from pathlib import Path

ORCH = Path(r"D:\eco_nojin\sandbox\phase12_unified_orchestrator.py")
content = ORCH.read_text(encoding="utf-8")
original = content

# ==========================================================================
# PATCH 1: Replace H-Pheno with GDD-based phenology
# ==========================================================================

old_hpheno_block = '''        # H-Pheno
        try:
            from datetime import date, timedelta
            hpheno = self.HPheno()
            days = 365
            t = np.arange(days)
            # Region-specific seed
            region_seed = int(abs(ctx.lat * 100) + abs(ctx.lon * 100)) % 10000 + 100
            # Phase shift based on latitude (NH vs SH)
            phase_shift = int(60 if ctx.lat > 0 else 240)
            
            # Growing season length based on climate (warmer = shorter)
            # Wheat typical: 150-200 days, adjusted by temperature
            growing_season_length = int(np.clip(200 - ctx.climate.t_ann_mean * 2, 120, 240))
            
            # Build cleaner NDVI time series with realistic phenology
            rng2 = np.random.default_rng(region_seed)
            ndvi_ts = np.zeros(days)
            
            # Pre-season: bare soil (NDVI ~0.15)
            sos_day = phase_shift - growing_season_length // 3
            sos_day = sos_day % 365
            
            for d in range(days):
                day_in_cycle = (d - sos_day) % 365
                if day_in_cycle < 0:
                    day_in_cycle += 365
                
                if day_in_cycle < growing_season_length:
                    # In growing season: bell curve
                    progress = day_in_cycle / growing_season_length
                    # Smooth bell curve: 0 → peak (0.65) → 0
                    ndvi_base = 0.15 + 0.55 * np.sin(np.pi * progress)
                else:
                    # Out of season: bare soil
                    ndvi_base = 0.15
                
                ndvi_ts[d] = ndvi_base + rng2.normal(0, 0.02)  # low noise
            
            ndvi_ts = np.clip(ndvi_ts, 0.05, 0.9)
            dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(days)]
            hpheno_result = hpheno.compute(ndvi_ts, dates, dt_days=1.0)
            for k in ["sos", "pos", "eos"]:
                if hpheno_result.get(k):
                    hpheno_result[k] = hpheno_result[k].isoformat()'''

new_hpheno_block = '''        # H-Pheno — GDD-based approach (McMaster & Wilhelm 1997)
        # Replaces derivative-based approach that requires real Sentinel-2 data
        # Uses temperature data to estimate phenology via Growing Degree Days
        try:
            # Crop-specific parameters for wheat
            T_BASE = 5.0   # Base temperature for wheat (°C)
            T_OPT = 25.0   # Optimal temperature (°C)
            T_MAX = 35.0   # Maximum temperature (°C)
            # GDD to maturity (FAO typical for wheat: 1500-2000)
            # Adjusted by climate: warmer = shorter cycle
            GDD_TO_MATURITY = max(1200, 2000 - (ctx.climate.t_ann_mean - 15) * 40)
            
            # Build daily temperature series from monthly
            # Assume 30 days per month, linear interpolation within month
            days_in_year = 365
            daily_t_mean = np.zeros(days_in_year)
            for m_idx in range(12):
                t_mean_m = (ctx.climate.t_min_monthly[m_idx] + 
                            ctx.climate.t_max_monthly[m_idx]) / 2
                # Fill 30 days of this month
                start_day = m_idx * 30
                end_day = min(start_day + 30, days_in_year)
                daily_t_mean[start_day:end_day] = t_mean_m
            
            # Compute daily GDD
            daily_gdd = np.zeros(days_in_year)
            for d in range(days_in_year):
                t = daily_t_mean[d]
                if t < T_BASE:
                    daily_gdd[d] = 0.0
                elif t > T_MAX:
                    daily_gdd[d] = max(0, T_OPT - T_BASE)
                else:
                    daily_gdd[d] = min(t, T_OPT) - T_BASE
            
            avg_daily_gdd = float(np.mean(daily_gdd[daily_gdd > 0])) if np.any(daily_gdd > 0) else 0
            los_days = int(GDD_TO_MATURITY / max(avg_daily_gdd, 0.1)) if avg_daily_gdd > 0 else 0
            los_days = int(np.clip(los_days, 90, 300))  # realistic bounds
            
            # SOS: optimal planting time based on temperature
            # Wheat in NH: Oct-Nov (fall planting) or Feb-Mar (spring planting)
            if ctx.lat > 0:  # Northern Hemisphere
                sos_month = 10 if ctx.climate.t_ann_mean > 15 else 2  # fall vs spring wheat
            else:  # Southern Hemisphere
                sos_month = 4 if ctx.climate.t_ann_mean > 15 else 8
            
            from datetime import date, timedelta
            sos_date = date(2024, sos_month, 15)
            pos_date = sos_date + timedelta(days=los_days * 2 // 3)  # peak at 2/3
            eos_date = sos_date + timedelta(days=los_days)
            
            # BBCH stages (simplified)
            bbch_stages = {
                "BBCH_00_09": "Germination",
                "BBCH_10_19": "Leaf development",
                "BBCH_20_29": "Tillering",
                "BBCH_30_39": "Stem elongation",
                "BBCH_40_49": "Booting",
                "BBCH_50_59": "Heading",
                "BBCH_60_69": "Flowering",
                "BBCH_70_79": "Grain filling",
                "BBCH_80_89": "Ripening",
                "BBCH_90_99": "Senescence",
            }
            
            hpheno_result = {
                "method": "GDD-based (McMaster & Wilhelm 1997)",
                "sos": sos_date.isoformat(),
                "pos": pos_date.isoformat(),
                "eos": eos_date.isoformat(),
                "los_days": los_days,
                "gdd_to_maturity": float(GDD_TO_MATURITY),
                "avg_daily_gdd": avg_daily_gdd,
                "t_base_c": T_BASE,
                "crop": ctx.crop_type,
                "bbch_stages": bbch_stages,
            }'''

if old_hpheno_block in content:
    content = content.replace(old_hpheno_block, new_hpheno_block)
    print("✅ Patch 1: H-Pheno replaced with GDD-based phenology (McMaster 1997)")
else:
    print("ℹ️  Patch 1: Already applied or structure differs")

# ==========================================================================
# PATCH 2: Fix EPIA - daily vs weekly rainfall comparison
# ==========================================================================

old_epia_compute = '''        # EPIA
        try:
            epia = self.EPIA()
            # FAO-56 reference ET0 (Hargreaves simplified)
            et0 = max(2.0, ctx.climate.t_ann_mean * 0.17 + 0.5)
            # Use realistic soil moisture (depleted, not at half field capacity)
            # If water-stressed region, soil is likely below field capacity
            current_sm = ctx.soil.field_capacity * (0.3 if ctx.climate.p_ann < 400 else 0.6)
            # Next 7-day forecast: conservative (low rainfall for arid)
            weekly_rain = ctx.climate.p_ann / 52  # weekly average
            epia_result = epia.compute(
                et0=et0,
                lai=ctx.sentinel.lai,
                soil_moisture=current_sm,
                rainfall_forecast_mm=weekly_rain,
                irrigation_efficiency=0.85,
            )'''

new_epia_compute = '''        # EPIA
        try:
            epia = self.EPIA()
            # FAO-56 reference ET0 (Hargreaves simplified)
            et0 = max(2.0, ctx.climate.t_ann_mean * 0.17 + 0.5)
            # Realistic soil moisture: depleted based on aridity
            current_sm = ctx.soil.field_capacity * (0.3 if ctx.climate.p_ann < 400 else 0.6)
            # DAILY rainfall forecast (not weekly!) - crucial for correct calculation
            daily_rain = ctx.climate.p_ann / 365
            # Apply effective rainfall coefficient (70% effective)
            effective_daily_rain = daily_rain * 0.7
            epia_result = epia.compute(
                et0=et0,
                lai=ctx.sentinel.lai,
                soil_moisture=current_sm,
                rainfall_forecast_mm=effective_daily_rain,  # DAILY now
                irrigation_efficiency=0.85,
            )'''

if old_epia_compute in content:
    content = content.replace(old_epia_compute, new_epia_compute)
    print("✅ Patch 2: EPIA daily rainfall fix (critical)")
else:
    print("ℹ️  Patch 2: Already applied")

# ==========================================================================
# PATCH 3: Update H-Pheno print to show GDD info
# ==========================================================================

old_hpheno_print = '            print(f"  H-Pheno: LOS = {result.hpheno.get(\'los_days\', \'?\')} days")'

new_hpheno_print = '''            los = result.hpheno.get('los_days', '?')
            gdd = result.hpheno.get('gdd_to_maturity', '?')
            method = result.hpheno.get('method', '?')
            print(f"  H-Pheno: LOS = {los} days, GDD = {gdd} ({method})")'''

if old_hpheno_print in content:
    content = content.replace(old_hpheno_print, new_hpheno_print)
    print("✅ Patch 3: H-Pheno print with GDD info")
else:
    print("ℹ️  Patch 3: Already applied")

# ==========================================================================
# Write
# ==========================================================================

if content != original:
    ORCH.write_text(content, encoding="utf-8")
    print(f"\n💾 Updated: {ORCH}")
    print("🚀 Run: python sandbox\\phase12_unified_orchestrator.py")
else:
    print("\n⚠️ No changes made")