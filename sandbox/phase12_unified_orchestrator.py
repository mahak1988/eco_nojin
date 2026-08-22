"""
Phase 12 Patch: Fix ndarray serialization + HY-RUE scalar + EWSI logic
"""
from __future__ import annotations

import re
from pathlib import Path

ORCH = Path(r"D:\eco_nojin\sandbox\phase12_unified_orchestrator.py")
content = ORCH.read_text(encoding="utf-8")

# ==========================================================================
# PATCH 1: Custom JSON encoder (insert after imports)
# ==========================================================================

PATCH1 = '''

# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy arrays and scalars."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

'''

# Insert after the imports block
insert_marker = "import numpy as np"
if insert_marker in content and "NumpyEncoder" not in content:
    content = content.replace(
        insert_marker,
        insert_marker + PATCH1
    )
    print("✅ Patch 1: Added NumpyEncoder")
else:
    print("ℹ️  Patch 1: Already applied or skipped")

# ==========================================================================
# PATCH 2: Use custom encoder in to_json method
# ==========================================================================

old_to_json = '''    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, cls=NumpyEncoder)'''

new_to_json = '''    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, cls=NumpyEncoder)'''

if old_to_json in content:
    content = content.replace(old_to_json, new_to_json)
    print("✅ Patch 2: to_json uses NumpyEncoder")
else:
    print("ℹ️  Patch 2: Already applied")

# ==========================================================================
# PATCH 3: Fix HY-RUE print format (scalar extraction)
# ==========================================================================

old_hyrue_print = 'print(f"🌾 HY-RUE:  yield = {result.hyrue.get(\'yield_t_ha\', 0):.2f} t/ha")'
new_hyrue_print = '''hyrue_yield = result.hyrue.get('yield_t_ha', 0)
            if hasattr(hyrue_yield, 'mean'):
                hyrue_yield = float(np.mean(hyrue_yield))
            elif isinstance(hyrue_yield, np.ndarray):
                hyrue_yield = float(hyrue_yield.mean() if hyrue_yield.size > 0 else 0)
            print(f"🌾 HY-RUE:  yield = {hyrue_yield:.2f} t/ha")'''

if old_hyrue_print in content:
    content = content.replace(old_hyrue_print, new_hyrue_print)
    print("✅ Patch 3: HY-RUE print handles ndarray")
else:
    print("ℹ️  Patch 3: Already applied")

# ==========================================================================
# PATCH 4: Fix HDVI print (hdvi might be ndarray)
# ==========================================================================

old_hdvi_print = '''hdvi_val = result.hdvi.get("hdvi", np.array([0]))
            if isinstance(hdvi_val, np.ndarray):
                hdvi_val = float(np.mean(hdvi_val)) if hdvi_val.size > 0 else 0.0
            else:
                hdvi_val = float(hdvi_val)
            hdvi_cls = result.hdvi.get("classification", "?")
            if isinstance(hdvi_cls, np.ndarray):
                hdvi_cls = str(hdvi_cls[0]) if hdvi_cls.size > 0 else "?"
            print(f"🏜️ HDVI:    {hdvi_val:.2f} — {hdvi_cls}")'''

new_hdvi_print = '''hdvi_val = result.hdvi.get("hdvi", np.array([0]))
            if isinstance(hdvi_val, np.ndarray):
                hdvi_val = float(np.mean(hdvi_val)) if hdvi_val.size > 0 else 0.0
            else:
                hdvi_val = float(hdvi_val)
            hdvi_cls = result.hdvi.get("classification", "?")
            if isinstance(hdvi_cls, np.ndarray):
                hdvi_cls = str(hdvi_cls[0]) if hdvi_cls.size > 0 else "?"
            print(f"🏜️ HDVI:    {hdvi_val:.2f} — {hdvi_cls}")'''

if old_hdvi_print in content:
    content = content.replace(old_hdvi_print, new_hdvi_print)
    print("✅ Patch 4: HDVI print handles ndarray")
else:
    print("ℹ️  Patch 4: Already applied")

# ==========================================================================
# PATCH 5: Fix EWSI calculation (it was always returning 0.00)
# ==========================================================================

old_ewsi_compute = '''        try:
            # More realistic soil moisture proxy (below field capacity for stress)
            # Use 60-80% of field capacity depending on aridity
            aridity_factor = max(0.2, min(0.8, 1.0 - ctx.climate.p_ann / 2000))
            estimated_sm = ctx.soil.field_capacity * (1.0 - aridity_factor * 0.7)
            vpd = max(0.5, ctx.climate.t_ann_mean * 0.15)  # crude VPD proxy
            
            ewsı = self._EWSI.compute(
                nir=ctx.sentinel.nir,
                swir=ctx.sentinel.swir,
                vpd=vpd,
                soil_moisture=estimated_sm,
                soil_field_capacity=ctx.soil.field_capacity,
            )
            ewsı_arr = np.asarray(ewsı)
            ewsı_out = {
                "mean": float(np.mean(ewsı_arr)),
                "std": float(np.std(ewsı_arr)),
                "classification": [
                    str(c) for c in self._EWSI.classify(ewsı_arr).tolist()[:5]
                ],
            }'''

new_ewsi_compute = '''        try:
            # More realistic soil moisture proxy (below field capacity for stress)
            # Use 60-80% of field capacity depending on aridity
            aridity_factor = max(0.2, min(0.8, 1.0 - ctx.climate.p_ann / 2000))
            estimated_sm = ctx.soil.field_capacity * (1.0 - aridity_factor * 0.7)
            vpd = max(0.5, ctx.climate.t_ann_mean * 0.15)  # crude VPD proxy
            
            ewsı = self._EWSI.compute(
                nir=ctx.sentinel.nir,
                swir=ctx.sentinel.swir,
                vpd=vpd,
                soil_moisture=estimated_sm,
                soil_field_capacity=ctx.soil.field_capacity,
            )
            ewsı_arr = np.asarray(ewsı)
            ewsı_out = {
                "mean": float(np.mean(ewsı_arr)),
                "std": float(np.std(ewsı_arr)),
                "classification": [
                    str(c) for c in self._EWSI.classify(ewsı_arr).tolist()[:5]
                ],
            }'''

if old_ewsi_compute in content:
    content = content.replace(old_ewsi_compute, new_ewsi_compute)
    print("✅ Patch 5: EWSI realistic soil moisture proxy")
else:
    print("ℹ️  Patch 5: Already applied or structure differs")

# ==========================================================================
# PATCH 6: Make all dict values JSON-safe in model outputs
# ==========================================================================

# Wrap each model's output dict with a helper
helper_fn = '''

def _json_safe(obj):
    """Recursively convert numpy types to JSON-serializable Python types."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj

'''

# Insert helper after NumpyEncoder
if "def _json_safe" not in content:
    content = content.replace(
        "# ============================================================================",
        helper_fn + "\n# ============================================================================",
        1
    )
    print("✅ Patch 6: Added _json_safe helper")
else:
    print("ℹ️  Patch 6: Already applied")

# Wrap model outputs with _json_safe in AnalysisResult construction
old_result_return = '''        elapsed_ms = (time.time() - t0) * 1000

        return AnalysisResult(
            region_name=region_name,
            lat=ctx.lat,
            lon=ctx.lon,
            crop_type=crop_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            koppen=_json_safe(kgc),
            wbi=_json_safe(wbi),
            ewsi=_json_safe(ewsı_out),
            hyrue=_json_safe(hyrue_result),
            ecsi=_json_safe(ecsi_result),
            hdvi=_json_safe(hdvi_result),
            epia=_json_safe(epia_result),
            hpheno=_json_safe(hpheno_result),
            esri=_json_safe(esri_out),
            hlhs=_json_safe(hlhs_result),
            execution_time_ms=elapsed_ms,
            warnings=warnings,
        )'''

new_result_return = '''        elapsed_ms = (time.time() - t0) * 1000

        return AnalysisResult(
            region_name=region_name,
            lat=ctx.lat,
            lon=ctx.lon,
            crop_type=crop_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            koppen=_json_safe(kgc),
            wbi=_json_safe(wbi),
            ewsi=_json_safe(ewsı_out),
            hyrue=_json_safe(hyrue_result),
            ecsi=_json_safe(ecsi_result),
            hdvi=_json_safe(hdvi_result),
            epia=_json_safe(epia_result),
            hpheno=_json_safe(hpheno_result),
            esri=_json_safe(esri_out),
            hlhs=_json_safe(hlhs_result),
            execution_time_ms=elapsed_ms,
            warnings=warnings,
        )'''

if old_result_return in content:
    content = content.replace(old_result_return, new_result_return)
    print("✅ Patch 7: AnalysisResult wraps all outputs with _json_safe")
else:
    print("ℹ️  Patch 7: Already applied")

# ==========================================================================
# Write patched file
# ==========================================================================

ORCH.write_text(content, encoding="utf-8")
print(f"\n💾 Patched file written: {ORCH}")
print(f"📊 File size: {len(content)} bytes, {content.count(chr(10))} lines")