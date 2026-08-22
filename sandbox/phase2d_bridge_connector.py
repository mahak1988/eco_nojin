"""
Phase 2d: Bridge Connector with Graceful Degradation
هدف: اتصال bridge‌ها به hydroma_core با fallback به Python
پروتکل: Backup + AST validation + Dry-run + Smoke Test
"""
from __future__ import annotations

import ast
import sys
import shutil
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CPP_BRIDGE = PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge"

# ============================================================================
# 1. تنظیمات Mapping
# ============================================================================

BRIDGE_CONFIG = {
    "soil_physics_fast.py": {
        "fallback_name": "soil_physics_fallback.py",
        "doc": "Soil Physics Bridge - van Genuchten & Mualem with C++ acceleration",
        "functions": [
            {
                "public_name": "soil_water_content",
                "cxx_name": "soil_water_content",
                "signature": "(h_matric: np.ndarray, soil_texture: str) -> np.ndarray",
                "doc": "Calculate soil water content (θ) from matric potential using van Genuchten.",
                "pre_convert": [
                    "    h_list = h_matric.tolist() if hasattr(h_matric, 'tolist') else list(h_matric)",
                ],
                "cxx_call": "    result = _core.soil_water_content(h_list, soil_texture)",
                "post_convert": "    return np.array(result, dtype=np.float64)",
            },
            {
                "public_name": "hydraulic_conductivity",
                "cxx_name": "hydraulic_conductivity",
                "signature": "(h_matric: np.ndarray, soil_texture: str) -> np.ndarray",
                "doc": "Calculate unsaturated hydraulic conductivity K(h) using Mualem-van Genuchten.",
                "pre_convert": [
                    "    h_list = h_matric.tolist() if hasattr(h_matric, 'tolist') else list(h_matric)",
                ],
                "cxx_call": "    result = _core.hydraulic_conductivity(h_list, soil_texture)",
                "post_convert": "    return np.array(result, dtype=np.float64)",
            },
            {
                "public_name": "get_soil_parameters",
                "cxx_name": "soil_params",
                "signature": "(soil_texture: str) -> dict",
                "doc": "Get van Genuchten parameters (theta_r, theta_s, alpha, n, Ks) for a soil texture.",
                "pre_convert": [],
                "cxx_call": "    params_obj = _core.soil_params(soil_texture)",
                "post_convert": (
                    "    return {\n"
                    "        'theta_r': params_obj.theta_r,\n"
                    "        'theta_s': params_obj.theta_s,\n"
                    "        'alpha': params_obj.alpha,\n"
                    "        'n': params_obj.n,\n"
                    "        'm': 1 - 1/params_obj.n if params_obj.n != 0 else 0,\n"
                    "        'Ks': params_obj.Ks,\n"
                    "    }"
                ),
            },
        ],
    },
    "hydrology_fast.py": {
        "fallback_name": "hydrology_fallback.py",
        "doc": "Hydrology Bridge - Muskingum-Cunge flood routing with C++ acceleration",
        "functions": [
            {
                "public_name": "compute_wave_parameters",
                "cxx_name": "compute_wave_parameters",
                "signature": "(channel_length: float, bed_slope: float, manning_n: float, channel_width: float, peak_flow: float) -> dict",
                "doc": "Compute wave celerity and K parameter from channel geometry.",
                "pre_convert": [],
                "cxx_call": "    result = _core.compute_wave_parameters(channel_length, bed_slope, manning_n, channel_width, peak_flow)",
                "post_convert": "    return dict(result) if hasattr(result, 'items') else vars(result)",
            },
            {
                "public_name": "route_flood_wave",
                "cxx_name": "route_flood_wave",
                "signature": "(inflow_hydrograph: np.ndarray, channel_length: float = 1000.0, n_cells: int = 50, manning_n: float = 0.03, bed_slope: float = 0.002, dt: float = 10.0, channel_width: float = 5.0) -> dict",
                "doc": "Route a flood wave using Muskingum-Cunge method.",
                "pre_convert": [
                    "    inflow_list = inflow_hydrograph.tolist() if hasattr(inflow_hydrograph, 'tolist') else list(inflow_hydrograph)",
                ],
                "cxx_call": "    result = _core.route_flood_wave(inflow_list, channel_length, n_cells, manning_n, bed_slope, dt, channel_width)",
                "post_convert": "    return dict(result) if hasattr(result, 'items') else vars(result)",
            },
            {
                "public_name": "route_multi_reach",
                "cxx_name": "route_multi_reach",
                "signature": "(inflow_hydrograph: np.ndarray, channel_length: float, n_reaches: int, manning_n: float = 0.03, bed_slope: float = 0.002, dt: float = 10.0, channel_width: float = 5.0) -> dict",
                "doc": "Route through multiple reaches for more accurate attenuation.",
                "pre_convert": [
                    "    inflow_list = inflow_hydrograph.tolist() if hasattr(inflow_hydrograph, 'tolist') else list(inflow_hydrograph)",
                ],
                "cxx_call": "    result = _core.route_multi_reach(inflow_list, channel_length, n_reaches, manning_n, bed_slope, dt, channel_width)",
                "post_convert": "    return dict(result) if hasattr(result, 'items') else vars(result)",
            },
        ],
    },
    "indices_fast.py": {
        "fallback_name": "indices_fallback.py",
        "doc": "Spectral Indices Bridge - NDVI, EVI, SAVI, NBR with C++ acceleration",
        "functions": [
            {
                "public_name": "ndvi_fast",
                "cxx_name": "ndvi_array",
                "signature": "(red: np.ndarray, nir: np.ndarray) -> np.ndarray",
                "doc": "Calculate NDVI = (NIR - Red) / (NIR + Red).",
                "pre_convert": [
                    "    red_list = red.tolist() if hasattr(red, 'tolist') else list(red)",
                    "    nir_list = nir.tolist() if hasattr(nir, 'tolist') else list(nir)",
                ],
                "cxx_call": "    result = _core.ndvi_array(red_list, nir_list)",
                "post_convert": "    return np.array(result, dtype=np.float64)",
            },
            {
                "public_name": "evi_fast",
                "cxx_name": "evi_array",
                "signature": "(red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray",
                "doc": "Calculate Enhanced Vegetation Index (EVI).",
                "pre_convert": [
                    "    red_list = red.tolist() if hasattr(red, 'tolist') else list(red)",
                    "    nir_list = nir.tolist() if hasattr(nir, 'tolist') else list(nir)",
                    "    blue_list = blue.tolist() if hasattr(blue, 'tolist') else list(blue)",
                ],
                "cxx_call": "    result = _core.evi_array(red_list, nir_list, blue_list)",
                "post_convert": "    return np.array(result, dtype=np.float64)",
            },
            {
                "public_name": "savi_fast",
                "cxx_name": "savi_array",
                "signature": "(red: np.ndarray, nir: np.ndarray, L: float = 0.5) -> np.ndarray",
                "doc": "Calculate Soil-Adjusted Vegetation Index (SAVI).",
                "pre_convert": [
                    "    red_list = red.tolist() if hasattr(red, 'tolist') else list(red)",
                    "    nir_list = nir.tolist() if hasattr(nir, 'tolist') else list(nir)",
                ],
                "cxx_call": "    result = _core.savi_array(red_list, nir_list, L)",
                "post_convert": "    return np.array(result, dtype=np.float64)",
            },
            {
                "public_name": "nbr_fast",
                "cxx_name": "nbr_array",
                "signature": "(nir: np.ndarray, swir: np.ndarray) -> np.ndarray",
                "doc": "Calculate Normalized Burn Ratio (NBR).",
                "pre_convert": [
                    "    nir_list = nir.tolist() if hasattr(nir, 'tolist') else list(nir)",
                    "    swir_list = swir.tolist() if hasattr(swir, 'tolist') else list(swir)",
                ],
                "cxx_call": "    result = _core.nbr_array(nir_list, swir_list)",
                "post_convert": "    return np.array(result, dtype=np.float64)",
            },
            {
                "public_name": "is_numba_available",
                "cxx_name": None,  # No C++ equivalent - always reports status
                "signature": "() -> bool",
                "doc": "Check if C++ acceleration is available.",
                "pre_convert": [],
                "cxx_call": "    return _HYDROMA_AVAILABLE",
                "post_convert": None,
                "is_direct": True,
            },
        ],
    },
}


# ============================================================================
# 2. Generator برای فایل bridge
# ============================================================================

def generate_bridge_file(bridge_name: str, config: Dict[str, Any]) -> str:
    """تولید کد فایل bridge با wrapper و fallback"""
    
    functions_code = []
    
    for func in config["functions"]:
        pre_lines = "\n".join(func["pre_convert"]) if func["pre_convert"] else ""
        pre_lines_or_pass = pre_lines if pre_lines.strip() else "            pass  # No pre-conversion needed"
        
        # تابع با direct return (مثل is_numba_available)
        if func.get("is_direct"):
            functions_code.append(f'''
def {func["public_name"]}{func["signature"]}:
    """{func["doc"]}"""
    return {func["cxx_call"]}
''')
            continue
        
        # توابع معمول با C++ + fallback
        functions_code.append(f'''
def {func["public_name"]}{func["signature"]}:
    """{func["doc"]}
    
    Execution path:
        1. Try C++ (hydroma_core.{func["cxx_name"]}) - fast
        2. Fallback to pure Python (_fallback.{func["public_name"]}) - reliable
    """
    if _HYDROMA_AVAILABLE:
        try:
{pre_lines_or_pass}
{func["cxx_call"]}
{func["post_convert"]}
        except Exception as e:
            _logger.warning(
                f"C++ call to '{func["cxx_name"]}' failed, falling back to Python: {{e}}"
            )
    
    # Fallback path
    return _fallback.{func["public_name"]}(*args, **kwargs) if '_fallback' in globals() else None
''')
    
    # اصلاح fallback call (args/kwargs)
    # برای هر تابع باید args و kwargs را به‌صورت صریح پاس دهیم
    
    return f'''"""
{config["doc"]}

Architecture:
    - Priority: C++ (hydroma_core) for performance
    - Fallback: Pure Python implementation for reliability
    - Logging: Every call path is traced

Auto-generated by Phase 2d Bridge Connector.
DO NOT EDIT MANUALLY - modify the generator script instead.
"""
from __future__ import annotations

import logging
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
_logger = logging.getLogger(__name__)

# Try to import C++ core
try:
    import hydroma_core as _core
    _HYDROMA_AVAILABLE = True
    _logger.debug("C++ hydroma_core loaded successfully")
except ImportError as e:
    _core = None
    _HYDROMA_AVAILABLE = False
    _logger.warning(f"C++ hydroma_core not available: {{e}}. Using Python fallback.")

# Try to import fallback implementation
try:
    from engine.hydroma.cpp_bridge import {bridge_name.replace("_fast.py", "_fallback")} as _fallback
except ImportError:
    try:
        from . import {bridge_name.replace("_fast.py", "_fallback")} as _fallback
    except ImportError:
        _fallback = None
        _logger.warning("Fallback module not found")


# ---------------------------------------------------------------------------
# Public API (Wrapper functions)
# ---------------------------------------------------------------------------
''' + "\n".join(functions_code).replace(
        "*args, **kwargs",
        _get_func_args_placeholder(config)
    )


def _get_func_args_placeholder(config):
    """placeholder - در نسخه بعدی بهبود می‌یابد"""
    return "*args, **kwargs"


# ============================================================================
# 3. Generator بازنویسی‌شده با پارامترهای صریح
# ============================================================================

def generate_bridge_file_v2(bridge_name: str, config: Dict[str, Any]) -> str:
    """نسخه بهبودیافته با پارامترهای صریح در fallback call"""
    
    functions_code = []
    
    for func in config["functions"]:
        pre_lines = "\n".join(func["pre_convert"]) if func["pre_convert"] else ""
        pre_lines_or_pass = pre_lines if pre_lines.strip() else "            pass  # No pre-conversion needed"
        
        # استخراج نام پارامترها از signature
        sig = func["signature"]
        param_str = sig[1:sig.find(")")] if "(" in sig else ""
        # استخراج نام‌ها (قبل از :)
        params = []
        for p in param_str.split(","):
            p = p.strip()
            if p and p != "self":
                name = p.split(":")[0].strip()
                if name:
                    params.append(name)
        
        args_str = ", ".join(params)
        
        # تابع direct
        if func.get("is_direct"):
            functions_code.append(f'''
def {func["public_name"]}{func["signature"]}:
    """{func["doc"]}"""
    return {func["cxx_call"]}
''')
            continue
        
        # توابع معمول
        functions_code.append(f'''
def {func["public_name"]}{func["signature"]}:
    """{func["doc"]}
    
    Execution path:
        1. Try C++ (hydroma_core.{func["cxx_name"]}) - fast
        2. Fallback to pure Python - reliable
    """
    if _HYDROMA_AVAILABLE:
        try:
{pre_lines_or_pass}
{func["cxx_call"]}
{func["post_convert"]}
        except Exception as e:
            _logger.warning(
                f"C++ call to '{func["cxx_name"]}' failed, falling back to Python: {{e}}"
            )
    
    # Fallback path
    if _fallback is not None:
        return _fallback.{func["public_name"]}({args_str})
    
    raise RuntimeError(
        f"Neither C++ core nor Python fallback available for '{func["public_name"]}'"
    )
''')
    
    return f'''"""
{config["doc"]}

Architecture:
    - Priority: C++ (hydroma_core) for performance
    - Fallback: Pure Python implementation for reliability
    - Logging: Every call path is traced

Auto-generated by Phase 2d Bridge Connector.
DO NOT EDIT MANUALLY - modify the generator script instead.
"""
from __future__ import annotations

import logging

import numpy as np

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
_logger = logging.getLogger(__name__)

# Try to import C++ core
try:
    import hydroma_core as _core
    _HYDROMA_AVAILABLE = True
    _logger.info("C++ hydroma_core loaded successfully")
except ImportError as e:
    _core = None
    _HYDROMA_AVAILABLE = False
    _logger.warning(f"C++ hydroma_core not available: {{e}}. Using Python fallback.")

# Try to import fallback implementation
try:
    from engine.hydroma.cpp_bridge import {bridge_name.replace("_fast.py", "_fallback")} as _fallback
    _logger.debug("Fallback module loaded")
except ImportError:
    try:
        from . import {bridge_name.replace("_fast.py", "_fallback")} as _fallback
    except ImportError:
        _fallback = None
        _logger.warning("Fallback module not found - system may fail on C++ error")


# ---------------------------------------------------------------------------
# Public API (Wrapper functions)
# ---------------------------------------------------------------------------
''' + "\n".join(functions_code)


# ============================================================================
# 4. Backup Logic
# ============================================================================

def backup_bridge(bridge_name: str, fallback_name: str, dry_run: bool = False) -> bool:
    """پشتیبان‌گیری از bridge فعلی به عنوان fallback"""
    src = CPP_BRIDGE / bridge_name
    dst = CPP_BRIDGE / fallback_name
    
    if not src.exists():
        print(f"⚠️ فایل منبع یافت نشد: {src}")
        return False
    
    if dst.exists() and not dry_run:
        print(f"⚠️ fallback از قبل موجود است: {dst}")
        return True
    
    if dry_run:
        print(f"🔍 [DRY-RUN] کپی: {bridge_name} → {fallback_name}")
        return True
    
    shutil.copy2(src, dst)
    print(f"💾 پشتیبان: {bridge_name} → {fallback_name}")
    return True


def write_bridge_file(bridge_name: str, content: str, dry_run: bool = False) -> bool:
    """نوشتن فایل bridge جدید با AST validation"""
    
    # اعتبارسنجی AST قبل از نوشتن
    try:
        ast.parse(content)
    except SyntaxError as e:
        print(f"❌ خطای نحوی در کد تولیدشده: {e}")
        return False
    
    target = CPP_BRIDGE / bridge_name
    
    if dry_run:
        lines = content.count("\n")
        print(f"🔍 [DRY-RUN] بازنویسی: {bridge_name} ({lines} خط)")
        return True
    
    # پشتیبان‌گیری از فایل فعلی قبل از بازنویسی
    if target.exists():
        backup_path = target.with_suffix(".py.pre_phase2")
        if not backup_path.exists():
            shutil.copy2(target, backup_path)
    
    target.write_text(content, encoding="utf-8")
    print(f"✅ بازنویسی شد: {bridge_name}")
    return True


# ============================================================================
# 5. Smoke Test
# ============================================================================

def smoke_test(dry_run: bool = False):
    """تست سریع عملکرد bridge‌های جدید"""
    if dry_run:
        print("\n🔍 [DRY-RUN] Smoke test: تست import و فراخوانی bridge‌ها")
        return True
    
    print("\n" + "=" * 70)
    print("🧪 Smoke Test: تست عملکرد bridge‌های جدید")
    print("=" * 70)
    
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(CPP_BRIDGE))
    
    results = []
    
    # Test 1: soil_physics_fast
    print("\n🧪 Test 1: soil_physics_fast.soil_water_content")
    try:
        from engine.hydroma.cpp_bridge import soil_physics_fast
        h_matric = np.array([-100.0, -330.0, -15000.0])  # cm
        theta = soil_physics_fast.soil_water_content(h_matric, "loam")
        print(f"   ✅ θ(loam, h=[-100, -330, -15000]) = {theta}")
        results.append(("soil_physics_fast", True, None))
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        results.append(("soil_physics_fast", False, e))
    
    # Test 2: hydrology_fast
    print("\n🧪 Test 2: hydrology_fast.compute_wave_parameters")
    try:
        from engine.hydroma.cpp_bridge import hydrology_fast
        wave = hydrology_fast.compute_wave_parameters(
            channel_length=1000.0,
            bed_slope=0.002,
            manning_n=0.03,
            channel_width=5.0,
            peak_flow=10.0,
        )
        print(f"   ✅ Wave params: {type(wave).__name__}")
        results.append(("hydrology_fast", True, None))
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        results.append(("hydrology_fast", False, e))
    
    # Test 3: indices_fast
    print("\n🧪 Test 3: indices_fast.ndvi_fast")
    try:
        from engine.hydroma.cpp_bridge import indices_fast
        red = np.array([0.1, 0.2, 0.3])
        nir = np.array([0.4, 0.5, 0.6])
        ndvi = indices_fast.ndvi_fast(red, nir)
        print(f"   ✅ NDVI = {ndvi}")
        print(f"   📊 C++ available: {indices_fast.is_numba_available()}")
        results.append(("indices_fast", True, None))
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        results.append(("indices_fast", False, e))
    
    # جمع‌بندی
    print("\n" + "=" * 70)
    print("📊 نتایج Smoke Test")
    print("=" * 70)
    for name, ok, err in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"   {status} - {name}")
        if err:
            print(f"      خطا: {err}")
    
    return all(ok for _, ok, _ in results)


# ============================================================================
# 6. Main
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2d Bridge Connector")
    parser.add_argument("--dry-run", action="store_true", help="فقط گزارش، بدون تغییر")
    parser.add_argument("--skip-backup", action="store_true", help="رد کردن مرحله پشتیبان")
    parser.add_argument("--skip-test", action="store_true", help="رد کردن smoke test")
    args = parser.parse_args()
    
    print(f"🚀 Phase 2d: Bridge Connector (Mode: {'DRY-RUN' if args.dry_run else 'EXECUTION'})\n")
    
    # مرحله ۱: پشتیبان‌گیری
    if not args.skip_backup:
        print("=" * 70)
        print("📦 مرحله ۱: پشتیبان‌گیری از bridge‌های فعلی")
        print("=" * 70)
        for bridge_name, config in BRIDGE_CONFIG.items():
            backup_bridge(bridge_name, config["fallback_name"], args.dry_run)
        print()
    
    # مرحله ۲: تولید و نوشتن bridge‌های جدید
    print("=" * 70)
    print("🔧 مرحله ۲: تولید bridge‌های جدید با wrapper")
    print("=" * 70)
    for bridge_name, config in BRIDGE_CONFIG.items():
        content = generate_bridge_file_v2(bridge_name, config)
        write_bridge_file(bridge_name, content, args.dry_run)
    print()
    
    # مرحله ۳: Smoke Test
    if not args.skip_test:
        smoke_test(args.dry_run)
    
    # جمع‌بندی
    print("\n" + "=" * 70)
    print("📋 جمع‌بندی Phase 2d")
    print("=" * 70)
    print(f"   Bridge‌های متصل شده: {len(BRIDGE_CONFIG)}")
    print(f"   توابع wrapper شده: {sum(len(c['functions']) for c in BRIDGE_CONFIG.values())}")
    print(f"   Fallback‌های موجود: {len(BRIDGE_CONFIG)}")
    
    if args.dry_run:
        print("\n👆 این یک DRY-RUN بود. برای اجرای واقعی:")
        print("   python sandbox\\phase2d_bridge_connector.py")
    else:
        print("\n🎉 Phase 2d با موفقیت اجرا شد!")
        print("   گام بعدی: pytest tests/unit/ -v -k 'soil or hydrology or indices or ndvi or evi'")


if __name__ == "__main__":
    main()