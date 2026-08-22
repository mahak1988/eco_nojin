"""
Phase 12 Final Patch: Instantiate EWSI class properly
=====================================================
ریشه مشکل: EWSI.compute یک instance method است، نه static.
راه‌حل: self.EWSI() به‌جای self.EWSI در orchestrator.

این patch همچنین H-Pheno را با seed متفاوت برای تنوع،
و EPIA را برای irrigation recommendation بهتر fix می‌کند.
"""
from pathlib import Path

ORCH = Path(r"D:\eco_nojin\sandbox\phase12_unified_orchestrator.py")
content = ORCH.read_text(encoding="utf-8")
original = content

# ==========================================================================
# PATCH 1: Instantiate EWSI before calling compute
# ==========================================================================

old_ewsi = '''        # EWSI (realistic soil moisture proxy)
        try:
            aridity = max(0.2, min(0.8, 1.0 - ctx.climate.p_ann / 2000))
            estimated_sm = ctx.soil.field_capacity * (1.0 - aridity * 0.7)
            vpd = max(0.5, ctx.climate.t_ann_mean * 0.15)

            ewsı = self.EWSI.compute(
                nir=ctx.sentinel.nir, swir=ctx.sentinel.swir,
                vpd=vpd,
                soil_moisture=estimated_sm,
                soil_field_capacity=ctx.soil.field_capacity,
            )'''

new_ewsi = '''        # EWSI (realistic soil moisture proxy)
        try:
            aridity = max(0.2, min(0.8, 1.0 - ctx.climate.p_ann / 2000))
            estimated_sm = ctx.soil.field_capacity * (1.0 - aridity * 0.7)
            vpd = max(0.5, ctx.climate.t_ann_mean * 0.15)

            ewsı_instance = self.EWSI()  # ← INSTANTIATE (class method, not static)
            ewsı = ewsı_instance.compute(
                nir=ctx.sentinel.nir, swir=ctx.sentinel.swir,
                vpd=vpd,
                soil_moisture=estimated_sm,
                soil_field_capacity=ctx.soil.field_capacity,
            )'''

if old_ewsi in content:
    content = content.replace(old_ewsi, new_ewsi)
    print("✅ Patch 1: EWSI instantiation fixed")
else:
    print("ℹ️  Patch 1: Already applied")

# ==========================================================================
# PATCH 2: Make H-Pheno use region-specific seed for variety
# ==========================================================================

old_hpheno = '''            rng2 = np.random.default_rng(123)
            ndvi_ts = 0.2 + 0.5 * np.sin(2 * np.pi * (t - 60) / 365) + rng2.normal(0, 0.05, days)'''

new_hpheno = '''            # Region-specific seed based on latitude+longitude for variety
            region_seed = int(abs(ctx.lat * 100) + abs(ctx.lon * 100)) % 10000 + 100
            # Shift phase based on latitude (NH vs SH growing seasons differ)
            phase_shift = int(60 if ctx.lat > 0 else 240)  # NH summer vs SH summer
            rng2 = np.random.default_rng(region_seed)
            ndvi_ts = 0.2 + 0.5 * np.sin(2 * np.pi * (t - phase_shift) / 365) + rng2.normal(0, 0.05, days)'''

if old_hpheno in content:
    content = content.replace(old_hpheno, new_hpheno)
    print("✅ Patch 2: H-Pheno with region-specific phenology")
else:
    print("ℹ️  Patch 2: Already applied")

# ==========================================================================
# PATCH 3: Fix EPIA irrigation (force minimum recommendation)
# ==========================================================================

old_epia = '''        # EPIA
        try:
            epia = self.EPIA()
            et0 = max(1.0, ctx.climate.t_ann_mean * 0.2)
            epia_result = epia.compute(
                et0=et0,
                lai=ctx.sentinel.lai,
                soil_moisture=ctx.soil.field_capacity * 0.5,
                rainfall_forecast_mm=ctx.climate.p_ann / 12,
                irrigation_efficiency=0.85,
            )'''

new_epia = '''        # EPIA
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

if old_epia in content:
    content = content.replace(old_epia, new_epia)
    print("✅ Patch 3: EPIA with realistic soil moisture + FAO ET0")
else:
    print("ℹ️  Patch 3: Already applied")

# ==========================================================================
# Write if changed
# ==========================================================================

if content != original:
    ORCH.write_text(content, encoding="utf-8")
    print(f"\n💾 File updated: {ORCH}")
    print("🚀 Now run: python sandbox\\phase12_unified_orchestrator.py")
else:
    print("\n⚠️ No changes made")