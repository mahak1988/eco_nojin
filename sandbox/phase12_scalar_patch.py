"""
Phase 12 Scalar Patch: Fix _scalar for list type + H-Pheno improvement
======================================================================
ریشه مشکلات:
1. _scalar فقط np.ndarray را می‌شناسد، نه list (پس از _json_safe)
2. H-Pheno از synthetic data خیلی noisy استفاده می‌کند

این patch:
- _scalar را برای list هم فعال می‌کند
- H-Pheno را با synthetic cleaner NDVI بهبود می‌دهد
- EPIA recommendation string را اصلاح می‌کند
"""
from pathlib import Path

ORCH = Path(r"D:\eco_nojin\sandbox\phase12_unified_orchestrator.py")
content = ORCH.read_text(encoding="utf-8")
original = content

# ==========================================================================
# PATCH 1: Fix _scalar to handle list type
# ==========================================================================

old_scalar = '''def _scalar(val, default=0.0):
    """Extract scalar float from possibly-array value."""
    if val is None:
        return default
    if isinstance(val, np.ndarray):
        return float(np.mean(val)) if val.size > 0 else default
    if isinstance(val, (np.integer, np.floating)):
        return float(val)
    if isinstance(val, (int, float)):
        return float(val)
    return default'''

new_scalar = '''def _scalar(val, default=0.0):
    """Extract scalar float from possibly-array/list/scalar value."""
    if val is None:
        return default
    if isinstance(val, np.ndarray):
        return float(np.mean(val)) if val.size > 0 else default
    if isinstance(val, (list, tuple)):
        return float(np.mean(val)) if len(val) > 0 else default
    if isinstance(val, (np.integer, np.floating)):
        return float(val)
    if isinstance(val, (int, float)):
        return float(val)
    return default'''

if old_scalar in content:
    content = content.replace(old_scalar, new_scalar)
    print("✅ Patch 1: _scalar handles list type (fixes HY-RUE, HDVI, EPIA)")
else:
    print("ℹ️  Patch 1: Already applied")

# ==========================================================================
# PATCH 2: Improve H-Pheno synthetic data (cleaner curve)
# ==========================================================================

old_hpheno = '''            # Region-specific seed based on latitude+longitude for variety
            region_seed = int(abs(ctx.lat * 100) + abs(ctx.lon * 100)) % 10000 + 100
            # Shift phase based on latitude (NH vs SH growing seasons differ)
            phase_shift = int(60 if ctx.lat > 0 else 240)  # NH summer vs SH summer
            rng2 = np.random.default_rng(region_seed)
            ndvi_ts = 0.2 + 0.5 * np.sin(2 * np.pi * (t - phase_shift) / 365) + rng2.normal(0, 0.05, days)'''

new_hpheno = '''            # Region-specific seed
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
            
            ndvi_ts = np.clip(ndvi_ts, 0.05, 0.9)'''

if old_hpheno in content:
    content = content.replace(old_hpheno, new_hpheno)
    print("✅ Patch 2: H-Pheno with realistic bell-curve phenology (LOS ~150-200 days)")
else:
    print("ℹ️  Patch 2: Already applied")

# ==========================================================================
# PATCH 3: Print EPIA recommendation correctly (not the mm value)
# ==========================================================================

old_epia_print = '            print(f"  EPIA:    {result.epia.get(\'recommendation\', \'?\')}")'
new_epia_print = '''            epia_irr = _scalar(result.epia.get('irrigation_need_mm', 0))
            epia_days = result.epia.get('days_until_irrigation', '?')
            epia_stage = result.epia.get('crop_stage', '?')
            print(f"  EPIA:    Irrigate {epia_irr:.1f} mm in {epia_days} days ({epia_stage})")'''

if old_epia_print in content:
    content = content.replace(old_epia_print, new_epia_print)
    print("✅ Patch 3: EPIA print with mm and days")
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
    print("\n⚠️ No changes")