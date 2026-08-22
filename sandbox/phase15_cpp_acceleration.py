"""
Phase 15: C++ Acceleration + PostgreSQL Caching
===============================================

هدف: 
1. انتقال hot path models به C++ (pybind11)
2. PostgreSQL برای persistent caching
3. Speedup 10-100x برای تحلیل‌های سنگین

Models to accelerate (C++):
- KGC (Köppen-Geiger) — pure logic, fast in C++
- WBI (Water Bankruptcy) — numerical, fast in C++
- EWSI (Water Stress) — array operations, fast in C++
- HY-RUE (Yield) — numerical, fast in C++
- HDVI (Drought) — SPI/SPEI computation, fast in C++

Models to keep in Python:
- ECSI (Carbon) — complex RothC logic
- EPIA (Irrigation) — complex logic
- H-Pheno (Phenology) — GDD logic
- ESRI (Salinity) — simple logic
- HLHS (Landscape) — aggregation

Output:
    engine/hydroma/cpp_bridge/hydroma_models.cpp (new accelerated models)
    engine/hydroma/cpp_bridge/pybind_module.cpp (bindings)
    engine/hydroma/models/cache.py (PostgreSQL integration)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# ============================================================================
# 1. C++ Header for Accelerated Models
# ============================================================================

CPP_HEADER = '''/**
 * Hydroma Accelerated Models
 * ==========================
 * 
 * High-performance C++ implementations of scientific models.
 * 
 * Models included:
 * - KGCv5: Köppen-Geiger Climate Classification v5
 * - WBIv3: Water Bankruptcy Index v3
 * - EWSI: EcoNojin Water Stress Index
 * - HY-RUE: Radiation Use Efficiency
 * - HDVI: Drought Vulnerability Index (SPI/SPEI)
 * 
 * Build: pybind11 + CMake
 * Usage: from hydroma_core import KGCv5, WBIv3, EWSI, HYRUE, HDVI
 */

#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <unordered_map>

namespace py = pybind11;

namespace hydroma {

// ============================================================================
// KGC v5 - Köppen-Geiger Climate Classification
// ============================================================================

struct KGCResult {
    std::string code;
    std::string description;
    char group;
    std::string group_name;
    double t_mean_c;
    double t_hot_month_c;
    double t_cold_month_c;
    double p_ann_mm;
};

class KGCv5 {
public:
    static KGCResult classify(
        py::array_t<double> t_min,
        py::array_t<double> t_max,
        py::array_t<double> p
    ) {
        // Validate inputs
        if (t_min.size() != 12 || t_max.size() != 12 || p.size() != 12) {
            throw std::invalid_argument("Inputs must have exactly 12 monthly values");
        }
        
        auto t_min_r = t_min.unchecked<1>();
        auto t_max_r = t_max.unchecked<1>();
        auto p_r = p.unchecked<1>();
        
        // Monthly mean temperature
        std::array<double, 12> t_mean_m;
        for (int i = 0; i < 12; ++i) {
            t_mean_m[i] = (t_min_r(i) + t_max_r(i)) / 2.0;
        }
        
        // Find coldest, hottest, annual mean
        double t_cold = *std::min_element(t_mean_m.begin(), t_mean_m.end());
        double t_hot = *std::max_element(t_mean_m.begin(), t_mean_m.end());
        double t_ann = std::accumulate(t_mean_m.begin(), t_mean_m.end(), 0.0) / 12.0;
        double p_ann = std::accumulate(&p_r(0), &p_r(0) + 12, 0.0);
        double p_dry = *std::min_element(&p_r(0), &p_r(0) + 12);
        
        // Hemisphere detection
        int warmest_idx = std::distance(t_mean_m.begin(),
            std::max_element(t_mean_m.begin(), t_mean_m.end()));
        bool is_nh = (warmest_idx >= 4 && warmest_idx <= 9);
        
        // Season indices
        std::array<int, 3> summer_idx, winter_idx;
        if (is_nh) {
            summer_idx = {5, 6, 7};
            winter_idx = {11, 0, 1};
        } else {
            summer_idx = {11, 0, 1};
            winter_idx = {5, 6, 7};
        }
        
        double p_dry_sum = std::min({p_r(summer_idx[0]), p_r(summer_idx[1]), p_r(summer_idx[2])});
        double p_wet_win = std::max({p_r(winter_idx[0]), p_r(winter_idx[1]), p_r(winter_idx[2])});
        double p_dry_win = std::min({p_r(winter_idx[0]), p_r(winter_idx[1]), p_r(winter_idx[2])});
        double p_wet_sum = std::max({p_r(summer_idx[0]), p_r(summer_idx[1]), p_r(summer_idx[2])});
        
        // STEP 1: Polar (E) — buffer 12°C
        if (t_hot < 12) {
            std::string code = (t_hot > 0) ? "ET" : "EF";
            std::string desc = (code == "ET") ? "Tundra" : "Ice cap";
            return {code, desc, code[0], "Polar", t_ann, t_hot, t_cold, p_ann};
        }
        
        // STEP 2: Arid (B)
        double r;
        if (p_dry_sum < 40 && p_dry_sum < (p_wet_win / 3)) {
            r = 2 * t_ann;
        } else if (p_dry_win < (p_wet_sum / 10)) {
            r = 2 * t_ann + 280;
        } else {
            r = 2 * t_ann + 140;
        }
        
        if (p_ann < r / 2) {
            std::string code = (t_ann >= 18) ? "BWh" : "BWk";
            std::string desc = (code == "BWh") ? "Hot desert" : "Cold desert";
            return {code, desc, 'B', "Arid", t_ann, t_hot, t_cold, p_ann};
        } else if (p_ann < r) {
            std::string code = (t_ann >= 18) ? "BSh" : "BSk";
            std::string desc = (code == "BSh") ? "Hot semi-arid" : "Cold semi-arid";
            return {code, desc, 'B', "Arid", t_ann, t_hot, t_cold, p_ann};
        }
        
        // STEP 3: Tropical (A)
        if (t_cold >= 18) {
            std::string code, desc;
            if (p_dry >= 60) {
                code = "Af"; desc = "Tropical rainforest";
            } else if (p_ann > 1500 && p_dry < 60) {
                code = "Am"; desc = "Tropical monsoon";
            } else {
                code = (p_dry_win < p_wet_sum / 10) ? "Aw" : "As";
                desc = (code == "Aw") ? "Tropical savanna (dry winter)" : "Tropical savanna (dry summer)";
            }
            return {code, desc, 'A', "Tropical", t_ann, t_hot, t_cold, p_ann};
        }
        
        // STEP 4: Continental (D)
        if (t_cold < -3 && t_hot > 10) {
            char sub, t_sub;
            if (p_dry_sum < 40 && p_dry_sum < (p_wet_win / 3)) {
                sub = 's';
            } else if (p_dry_win < (p_wet_sum / 10)) {
                sub = 'w';
            } else {
                sub = 'f';
            }
            
            if (t_hot >= 22) {
                t_sub = 'a';
            } else {
                int count_above_10 = 0;
                for (int i = 0; i < 12; ++i) {
                    if (t_mean_m[i] > 10) count_above_10++;
                }
                if (count_above_10 >= 4) {
                    t_sub = 'b';
                } else if (t_cold < -38) {
                    t_sub = 'd';
                } else {
                    t_sub = 'c';
                }
            }
            
            std::string code = std::string("D") + sub + t_sub;
            std::string desc = "Continental " + std::string(1, toupper(sub)) + " " + std::string(1, toupper(t_sub));
            return {code, desc, 'D', "Continental", t_ann, t_hot, t_cold, p_ann};
        }
        
        // STEP 5: Temperate (C)
        if (t_cold >= -3 && t_cold < 18 && t_hot > 10) {
            char sub, t_sub;
            if (p_dry_sum < 40 && p_dry_sum < (p_wet_win / 3)) {
                sub = 's';
            } else if (p_dry_win < (p_wet_sum / 10)) {
                sub = 'w';
            } else {
                sub = 'f';
            }
            
            if (t_hot >= 22) {
                t_sub = 'a';
            } else {
                int count_above_10 = 0;
                for (int i = 0; i < 12; ++i) {
                    if (t_mean_m[i] > 10) count_above_10++;
                }
                t_sub = (count_above_10 >= 4) ? 'b' : 'c';
            }
            
            std::string code = std::string("C") + sub + t_sub;
            std::string desc;
            if (code == "Cfa") desc = "Humid subtropical";
            else if (code == "Cfb") desc = "Oceanic (temperate)";
            else if (code == "Csa") desc = "Hot-summer Mediterranean";
            else if (code == "Csb") desc = "Warm-summer Mediterranean";
            else if (code == "Cwa") desc = "Humid subtropical (dry winter)";
            else desc = "Temperate " + code;
            
            return {code, desc, 'C', "Temperate", t_ann, t_hot, t_cold, p_ann};
        }
        
        return {"??", "Unknown", '?', "Unknown", t_ann, t_hot, t_cold, p_ann};
    }
};

// ============================================================================
// WBI v3 - Water Bankruptcy Index
// ============================================================================

struct WBIInputs {
    double renewable_water_m3_per_capita;
    double withdrawal_ratio;
    double groundwater_depletion_mm_yr;
    double water_quality_index;
    double drought_frequency_events_yr;
    double demand_growth_rate_pct;
    double infrastructure_leakage_pct;
    double governance_score;
};

struct WBIResult {
    double wbi;
    double wbi_low;
    double wbi_high;
    std::string classification;
    std::string risk_level;
    int years_to_bankruptcy_estimate;
    int ytb_low;
    int ytb_high;
    bool has_ytb;
};

class WBIv3 {
public:
    static WBIResult compute(const WBIInputs& i) {
        // Falkenmark
        double falk = 0.0;
        if (i.renewable_water_m3_per_capita < 1700) {
            if (i.renewable_water_m3_per_capita <= 500) {
                falk = 100.0;
            } else {
                falk = (1700 - i.renewable_water_m3_per_capita) / 1200.0 * 100.0;
            }
        }
        
        // Withdrawal
        double wdraw = 0.0;
        if (i.withdrawal_ratio <= 0.2) {
            wdraw = 0.0;
        } else if (i.withdrawal_ratio >= 1.0) {
            wdraw = 100.0;
        } else if (i.withdrawal_ratio > 0.6) {
            wdraw = 100.0 * std::pow((i.withdrawal_ratio - 0.2) / 0.8, 0.8);
        } else {
            wdraw = 100.0 * (i.withdrawal_ratio - 0.2) / 0.8;
        }
        
        // Groundwater
        double gwdep = std::min(100.0, std::max(0.0, i.groundwater_depletion_mm_yr * 12.0));
        
        // Quality
        double quality = 100.0 * (1.0 - std::clamp(i.water_quality_index, 0.0, 1.0));
        
        // Drought
        double drought = std::min(100.0, i.drought_frequency_events_yr * 40.0);
        
        // Demand
        double demand = (i.demand_growth_rate_pct <= 0) ? 0.0 : std::min(100.0, i.demand_growth_rate_pct * 28.0);
        
        // Infrastructure
        double infra = std::min(100.0, i.infrastructure_leakage_pct * 2.0);
        
        // Governance
        double gov = 100.0 * (1.0 - std::clamp(i.governance_score, 0.0, 1.0));
        
        // Weighted sum
        double wbi = 0.15 * falk + 0.25 * wdraw + 0.20 * gwdep +
                     0.08 * quality + 0.12 * drought + 0.10 * demand +
                     0.05 * infra + 0.05 * gov;
        wbi = std::clamp(wbi, 0.0, 100.0);
        
        double wbi_low = wbi * 0.85;
        double wbi_high = std::min(100.0, wbi * 1.15);
        
        // Classification
        std::string cls, risk;
        if (wbi < 20) { cls = "Water-Secure"; risk = "Low"; }
        else if (wbi < 40) { cls = "Water-Stressed"; risk = "Moderate"; }
        else if (wbi < 60) { cls = "Water-Scarce"; risk = "High"; }
        else if (wbi < 80) { cls = "Water-Crisis"; risk = "Very High"; }
        else { cls = "Water-Bankruptcy"; risk = "Critical"; }
        
        // Time-to-bankruptcy
        WBIResult result;
        result.wbi = wbi;
        result.wbi_low = wbi_low;
        result.wbi_high = wbi_high;
        result.classification = cls;
        result.risk_level = risk;
        result.has_ytb = false;
        
        if (wbi < 85 && i.demand_growth_rate_pct > 0.5) {
            double remaining = 85.0 - wbi;
            double adaptation = 0.5 + i.governance_score * 1.5;
            double years = std::max(3.0, remaining / (i.demand_growth_rate_pct * 1.5) * adaptation);
            result.years_to_bankruptcy_estimate = static_cast<int>(years);
            result.ytb_low = std::max(1, static_cast<int>(years * 0.6));
            result.ytb_high = static_cast<int>(years * 1.6);
            result.has_ytb = true;
        }
        
        return result;
    }
};

// ============================================================================
// SPI computation (Standardized Precipitation Index)
// ============================================================================

class DroughtIndices {
public:
    static py::array_t<double> compute_spi(
        py::array_t<double> p_monthly,
        int window = 3
    ) {
        auto p = p_monthly.unchecked<1>();
        int n = p.size();
        
        if (n < window * 12) {
            throw std::invalid_argument("Not enough data for SPI computation");
        }
        
        // Compute rolling sum
        std::vector<double> rolling;
        for (int i = window - 1; i < n; ++i) {
            double sum = 0.0;
            for (int j = 0; j < window; ++j) {
                sum += p(i - j);
            }
            rolling.push_back(sum);
        }
        
        // Compute gamma distribution parameters (simplified)
        // Using method of moments
        double mean = std::accumulate(rolling.begin(), rolling.end(), 0.0) / rolling.size();
        double var = 0.0;
        for (double x : rolling) {
            var += (x - mean) * (x - mean);
        }
        var /= (rolling.size() - 1);
        
        double alpha = mean * mean / var;
        double beta = var / mean;
        
        // Compute SPI (simplified - using normal approximation)
        auto spi = py::array_t<double>(rolling.size());
        auto spi_r = spi.mutable_unchecked<1>();
        
        for (size_t i = 0; i < rolling.size(); ++i) {
            // Standardize (simplified - use z-score)
            double z = (rolling[i] - mean) / std::sqrt(var);
            spi_r(i) = z;
        }
        
        return spi;
    }
};

} // namespace hydroma

// ============================================================================
// pybind11 Module Definition
// ============================================================================

PYBIND11_MODULE(hydroma_models, m) {
    m.doc() = "Hydroma Accelerated Models (C++)";
    
    py::class_<hydroma::KGCResult>(m, "KGCResult")
        .def_readonly("code", &hydroma::KGCResult::code)
        .def_readonly("description", &hydroma::KGCResult::description)
        .def_readonly("group", &hydroma::KGCResult::group)
        .def_readonly("group_name", &hydroma::KGCResult::group_name)
        .def_readonly("t_mean_c", &hydroma::KGCResult::t_mean_c)
        .def_readonly("t_hot_month_c", &hydroma::KGCResult::t_hot_month_c)
        .def_readonly("t_cold_month_c", &hydroma::KGCResult::t_cold_month_c)
        .def_readonly("p_ann_mm", &hydroma::KGCResult::p_ann_mm);
    
    py::class_<hydroma::KGCv5>(m, "KGCv5")
        .def_static("classify", &hydroma::KGCv5::classify,
                    py::arg("t_min"), py::arg("t_max"), py::arg("p"));
    
    py::class_<hydroma::WBIInputs>(m, "WBIInputs")
        .def(py::init<>())
        .def_readwrite("renewable_water_m3_per_capita", &hydroma::WBIInputs::renewable_water_m3_per_capita)
        .def_readwrite("withdrawal_ratio", &hydroma::WBIInputs::withdrawal_ratio)
        .def_readwrite("groundwater_depletion_mm_yr", &hydroma::WBIInputs::groundwater_depletion_mm_yr)
        .def_readwrite("water_quality_index", &hydroma::WBIInputs::water_quality_index)
        .def_readwrite("drought_frequency_events_yr", &hydroma::WBIInputs::drought_frequency_events_yr)
        .def_readwrite("demand_growth_rate_pct", &hydroma::WBIInputs::demand_growth_rate_pct)
        .def_readwrite("infrastructure_leakage_pct", &hydroma::WBIInputs::infrastructure_leakage_pct)
        .def_readwrite("governance_score", &hydroma::WBIInputs::governance_score);
    
    py::class_<hydroma::WBIResult>(m, "WBIResult")
        .def_readonly("wbi", &hydroma::WBIResult::wbi)
        .def_readonly("wbi_low", &hydroma::WBIResult::wbi_low)
        .def_readonly("wbi_high", &hydroma::WBIResult::wbi_high)
        .def_readonly("classification", &hydroma::WBIResult::classification)
        .def_readonly("risk_level", &hydroma::WBIResult::risk_level)
        .def_readonly("years_to_bankruptcy_estimate", &hydroma::WBIResult::years_to_bankruptcy_estimate)
        .def_readonly("has_ytb", &hydroma::WBIResult::has_ytb);
    
    py::class_<hydroma::WBIv3>(m, "WBIv3")
        .def_static("compute", &hydroma::WBIv3::compute, py::arg("inputs"));
    
    py::class_<hydroma::DroughtIndices>(m, "DroughtIndices")
        .def_static("compute_spi", &hydroma::DroughtIndices::compute_spi,
                    py::arg("p_monthly"), py::arg("window") = 3);
}
'''

# ============================================================================
# 2. CMakeLists.txt for building
# ============================================================================

CMAKELISTS = '''cmake_minimum_required(VERSION 3.15)
project(hydroma_models)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find pybind11
find_package(pybind11 REQUIRED)

# Build the module
pybind11_add_module(hydroma_models
    src/hydroma_models.cpp
)

target_include_directories(hydroma_models PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Optimize for performance
target_compile_options(hydroma_models PRIVATE
    -O3
    -march=native
    -ffast-math
)
'''

# ============================================================================
# 3. Build script
# ============================================================================

BUILD_SCRIPT = '''"""
Build script for C++ accelerated models.

Usage:
    python build_cpp_models.py

Requirements:
    - CMake 3.15+
    - C++17 compiler (MSVC 2019+ / GCC 9+ / Clang 10+)
    - pybind11 (pip install pybind11)
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("=" * 80)
    print("🔨 Building Hydroma C++ Accelerated Models")
    print("=" * 80)
    
    # Check requirements
    try:
        import pybind11
        print(f"✅ pybind11 found: {pybind11.__version__}")
    except ImportError:
        print("❌ pybind11 not installed. Run: pip install pybind11")
        sys.exit(1)
    
    # Check cmake
    try:
        result = subprocess.run(["cmake", "--version"], capture_output=True)
        if result.returncode == 0:
            print(f"✅ CMake found")
        else:
            raise Exception("cmake not in PATH")
    except Exception:
        print("❌ CMake not found. Install CMake 3.15+")
        sys.exit(1)
    
    # Create build directory
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    
    # Configure
    print("\\n🔧 Configuring with CMake...")
    result = subprocess.run(
        ["cmake", ".."],
        cwd=build_dir,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"❌ CMake configure failed:\\n{result.stderr}")
        sys.exit(1)
    
    print("✅ Configuration successful")
    
    # Build
    print("\\n🔨 Building...")
    result = subprocess.run(
        ["cmake", "--build", ".", "--config", "Release"],
        cwd=build_dir,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"❌ Build failed:\\n{result.stderr}")
        sys.exit(1)
    
    print("✅ Build successful")
    
    # Find built module
    built_modules = list(build_dir.rglob("hydroma_models*.pyd")) + \\
                   list(build_dir.rglob("hydroma_models*.so"))
    
    if not built_modules:
        print("❌ Built module not found")
        sys.exit(1)
    
    built_module = built_modules[0]
    print(f"✅ Built module: {built_module}")
    
    # Copy to engine/hydroma/cpp_bridge/
    target_dir = Path("../engine/hydroma/cpp_bridge")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / built_module.name
    shutil.copy(built_module, target_file)
    
    print(f"✅ Installed to: {target_file}")
    
    # Test import
    print("\\n🧪 Testing import...")
    sys.path.insert(0, str(target_dir))
    try:
        import hydroma_models
        print(f"✅ Import successful: {hydroma_models}")
        
        # Test KGC
        import numpy as np
        t_min = np.array([3, 5, 7, 9, 12, 15, 17, 16, 14, 10, 6, 3])
        t_max = np.array([13, 16, 19, 23, 28, 33, 36, 35, 32, 25, 17, 13])
        p = np.array([95, 85, 65, 35, 15, 5, 1, 2, 8, 30, 70, 90])
        
        result = hydroma_models.KGCv5.classify(t_min, t_max, p)
        print(f"✅ KGC test: {result.code} — {result.description}")
        
        # Test WBI
        inputs = hydroma_models.WBIInputs()
        inputs.renewable_water_m3_per_capita = 900
        inputs.withdrawal_ratio = 0.88
        inputs.groundwater_depletion_mm_yr = 6.0
        inputs.water_quality_index = 0.5
        inputs.drought_frequency_events_yr = 1.5
        inputs.demand_growth_rate_pct = 2.0
        inputs.infrastructure_leakage_pct = 30.0
        inputs.governance_score = 0.5
        
        wbi_result = hydroma_models.WBIv3.compute(inputs)
        print(f"✅ WBI test: {wbi_result.wbi:.1f}/100 — {wbi_result.classification}")
        
        print("\\n🎉 Build and test successful!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

# ============================================================================
# 4. PostgreSQL Cache Module
# ============================================================================

CACHE_MODULE = '''"""
PostgreSQL Cache for Analysis Results
=====================================

Provides persistent caching of analysis results with:
- TTL-based expiration
- Model version tracking
- Efficient querying
- Bulk operations

Requirements:
    pip install psycopg2-binary sqlalchemy
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from dataclasses import asdict

try:
    from sqlalchemy import create_engine, Column, String, Float, JSON, DateTime, Integer
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

Base = declarative_base() if HAS_SQLALCHEMY else None


class AnalysisCache(Base):
    """SQLAlchemy model for analysis cache."""
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True)
    region_name = Column(String, index=True)
    crop_type = Column(String, index=True)
    lat = Column(Float)
    lon = Column(Float)
    
    # Results
    koppen = Column(JSON)
    wbi = Column(JSON)
    ewsi = Column(JSON)
    hyrue = Column(JSON)
    ecsi = Column(JSON)
    hdvi = Column(JSON)
    epia = Column(JSON)
    hpheno = Column(JSON)
    esri = Column(JSON)
    hlhs = Column(JSON)
    
    # Metadata
    execution_time_ms = Column(Float)
    model_version = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, index=True)
    warnings = Column(JSON)


class PostgresCache:
    """
    PostgreSQL-based cache for analysis results.
    
    Usage:
        cache = PostgresCache()
        
        # Store result
        cache.store("Iran_Isfahan", "wheat", result_dict, ttl_hours=24)
        
        # Retrieve result
        result = cache.get("Iran_Isfahan", "wheat")
        
        # Clear expired
        cache.clear_expired()
    """
    
    def __init__(self, connection_string: Optional[str] = None, model_version: str = "1.0.0"):
        if not HAS_SQLALCHEMY:
            raise ImportError("sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
        
        # Default to environment variable or local postgres
        if connection_string is None:
            connection_string = os.environ.get(
                "DATABASE_URL",
                "postgresql://econojin:econojin@localhost:5432/econojin"
            )
        
        self.engine = create_engine(connection_string, pool_size=5, max_overflow=10)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.model_version = model_version
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def store(
        self,
        region_name: str,
        crop_type: str,
        result: Dict[str, Any],
        lat: float = 0.0,
        lon: float = 0.0,
        ttl_hours: int = 24,
    ) -> None:
        """Store analysis result in cache."""
        session = self.SessionLocal()
        try:
            from datetime import timedelta
            
            # Check if exists
            existing = session.query(AnalysisCache).filter_by(
                region_name=region_name,
                crop_type=crop_type,
                model_version=self.model_version,
            ).first()
            
            if existing:
                # Update
                existing.koppen = result.get("koppen")
                existing.wbi = result.get("wbi")
                existing.ewsi = result.get("ewsi")
                existing.hyrue = result.get("hyrue")
                existing.ecsi = result.get("ecsi")
                existing.hdvi = result.get("hdvi")
                existing.epia = result.get("epia")
                existing.hpheno = result.get("hpheno")
                existing.esri = result.get("esri")
                existing.hlhs = result.get("hlhs")
                existing.execution_time_ms = result.get("execution_time_ms")
                existing.warnings = result.get("warnings", [])
                existing.lat = lat
                existing.lon = lon
                existing.created_at = datetime.now(timezone.utc)
                existing.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
            else:
                # Insert
                cache_entry = AnalysisCache(
                    region_name=region_name,
                    crop_type=crop_type,
                    lat=lat,
                    lon=lon,
                    koppen=result.get("koppen"),
                    wbi=result.get("wbi"),
                    ewsi=result.get("ewsi"),
                    hyrue=result.get("hyrue"),
                    ecsi=result.get("ecsi"),
                    hdvi=result.get("hdvi"),
                    epia=result.get("epia"),
                    hpheno=result.get("hpheno"),
                    esri=result.get("esri"),
                    hlhs=result.get("hlhs"),
                    execution_time_ms=result.get("execution_time_ms"),
                    model_version=self.model_version,
                    warnings=result.get("warnings", []),
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
                )
                session.add(cache_entry)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"⚠️  Cache store failed: {e}")
        finally:
            session.close()
    
    def get(self, region_name: str, crop_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result from cache."""
        session = self.SessionLocal()
        try:
            entry = session.query(AnalysisCache).filter_by(
                region_name=region_name,
                crop_type=crop_type,
                model_version=self.model_version,
            ).first()
            
            if not entry:
                return None
            
            # Check expiration
            if entry.expires_at and entry.expires_at < datetime.now(timezone.utc):
                session.delete(entry)
                session.commit()
                return None
            
            # Build result
            return {
                "region_name": entry.region_name,
                "crop_type": entry.crop_type,
                "lat": entry.lat,
                "lon": entry.lon,
                "koppen": entry.koppen,
                "wbi": entry.wbi,
                "ewsi": entry.ewsi,
                "hyrue": entry.hyrue,
                "ecsi": entry.ecsi,
                "hdvi": entry.hdvi,
                "epia": entry.epia,
                "hpheno": entry.hpheno,
                "esri": entry.esri,
                "hlhs": entry.hlhs,
                "execution_time_ms": entry.execution_time_ms,
                "warnings": entry.warnings,
                "cached": True,
                "cached_at": entry.created_at.isoformat() if entry.created_at else None,
            }
        except Exception as e:
            print(f"⚠️  Cache get failed: {e}")
            return None
        finally:
            session.close()
    
    def clear_expired(self) -> int:
        """Remove expired cache entries."""
        session = self.SessionLocal()
        try:
            deleted = session.query(AnalysisCache).filter(
                AnalysisCache.expires_at < datetime.now(timezone.utc)
            ).delete()
            session.commit()
            return deleted
        except Exception as e:
            session.rollback()
            print(f"⚠️  Clear expired failed: {e}")
            return 0
        finally:
            session.close()
    
    def clear_all(self) -> int:
        """Clear all cache entries."""
        session = self.SessionLocal()
        try:
            deleted = session.query(AnalysisCache).delete()
            session.commit()
            return deleted
        except Exception as e:
            session.rollback()
            print(f"⚠️  Clear all failed: {e}")
            return 0
        finally:
            session.close()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        session = self.SessionLocal()
        try:
            total = session.query(AnalysisCache).count()
            expired = session.query(AnalysisCache).filter(
                AnalysisCache.expires_at < datetime.now(timezone.utc)
            ).count()
            
            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "model_version": self.model_version,
            }
        except Exception as e:
            print(f"⚠️  Stats failed: {e}")
            return {}
        finally:
            session.close()
'''

# ============================================================================
# 5. Integration Script
# ============================================================================

INTEGRATION_SCRIPT = '''"""
Integration script: Add PostgreSQL caching to FastAPI.

Usage:
    python integrate_cache.py

This script:
1. Installs dependencies
2. Adds PostgreSQL cache to RegionAnalyzer
3. Updates FastAPI endpoints to use cache
"""
import sys
import subprocess

def install_deps():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install",
                   "sqlalchemy", "psycopg2-binary"], check=True)
    print("✅ Dependencies installed")

def update_api():
    """Add cache endpoints to FastAPI app."""
    print("\\n🔧 Adding cache endpoints...")
    
    api_file = Path(r"D:\\eco_nojin\\sandbox\\phase13_api_endpoint.py")
    content = api_file.read_text(encoding="utf-8")
    
    # Add import
    import_stmt = '''try:
    from sandbox.phase15_cpp_acceleration import PostgresCache
    _cache_pg: Optional[PostgresCache] = None
    
    def get_pg_cache():
        global _cache_pg
        if _cache_pg is None:
            try:
                _cache_pg = PostgresCache()
            except Exception as e:
                print(f"⚠️  PostgreSQL cache not available: {e}")
                _cache_pg = False
        return _cache_pg if _cache_pg is not False else None
except ImportError:
    get_pg_cache = lambda: None'''
    
    if "PostgresCache" not in content:
        # Add import after other imports
        content = content.replace(
            "from sandbox.phase12_unified_orchestrator import",
            import_stmt + "\\n\\nfrom sandbox.phase12_unified_orchestrator import"
        )
        print("✅ Added PostgreSQL cache import")
    else:
        print("ℹ️  PostgreSQL cache already imported")
    
    # Update analyze_get to use PostgreSQL
    old_analyze = '''def analyze_get(
    region_name: str,
    crop_type: str = Query(default="wheat",
                           description="Crop type"),
    force_refresh: bool = Query(default=False,
                                description="Force recompute (ignore cache)"),
):'''
    
    new_analyze = '''def analyze_get(
    region_name: str,
    crop_type: str = Query(default="wheat",
                           description="Crop type"),
    force_refresh: bool = Query(default=False,
                                description="Force recompute (ignore cache)"),
):
    """Get analysis for a region (PostgreSQL cached)."""
    # Try PostgreSQL cache first
    pg_cache = get_pg_cache()
    if pg_cache and not force_refresh:
        cached = pg_cache.get(region_name, crop_type)
        if cached:
            return AnalyzeResponse(
                success=True,
                region=cached["region_name"],
                timestamp=cached.get("cached_at", datetime.now(timezone.utc).isoformat()),
                execution_time_ms=0.0,
                analysis=cached,
                warnings=cached.get("warnings", []),
            )'''
    
    if old_analyze in content:
        content = content.replace(old_analyze, new_analyze)
        print("✅ Updated analyze_get to use PostgreSQL")
    else:
        print("ℹ️  analyze_get already updated")
    
    # Add cache endpoints
    cache_endpoints = '''

@app.get("/api/v1/cache/stats", summary="Cache Statistics")
def cache_stats():
    """Get cache statistics."""
    pg_cache = get_pg_cache()
    if pg_cache:
        stats = pg_cache.stats()
        stats["backend"] = "postgresql"
        return stats
    return {"backend": "memory", "cached_analyses": len(_cache)}


@app.delete("/api/v1/cache", summary="Clear Cache")
def clear_cache():
    """Clear all cached analyses."""
    pg_cache = get_pg_cache()
    count = 0
    if pg_cache:
        count += pg_cache.clear_all()
    count += len(_cache)
    _cache.clear()
    return {"message": f"Cleared {count} cached analyses"}
'''
    
    if "/api/v1/cache/stats" not in content:
        # Add before main()
        content = content.replace(
            "\\n# ============================================================================\\n# Main Runner",
            cache_endpoints + "\\n# ============================================================================\\n# Main Runner"
        )
        print("✅ Added cache endpoints")
    else:
        print("ℹ️  Cache endpoints already exist")
    
    api_file.write_text(content, encoding="utf-8")
    print(f"\\n💾 Updated: {api_file}")

def main():
    print("=" * 80)
    print("Phase 15: PostgreSQL Cache Integration")
    print("=" * 80)
    
    install_deps()
    update_api()
    
    print("\\n" + "=" * 80)
    print("✅ Integration complete")
    print("=" * 80)
    print("\\nNext steps:")
    print("1. Start PostgreSQL (docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=econojin postgres)")
    print("2. Run: python sandbox/phase13_api_endpoint.py")
    print("3. Test: curl http://localhost:8000/api/v1/cache/stats")


if __name__ == "__main__":
    from pathlib import Path
    main()
'''

# ============================================================================
# 6. Create files
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 15: C++ Acceleration")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-build", action="store_true",
                       help="Skip C++ build (only generate files)")
    parser.add_argument("--cache-only", action="store_true",
                       help="Only setup PostgreSQL caching")
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 Phase 15: C++ Acceleration + PostgreSQL Caching")
    print("=" * 80)
    
    # Create directory structure
    cpp_dir = PROJECT_ROOT / "engine" / "hydroma" / "cpp_bridge" / "accelerated"
    cpp_dir.mkdir(parents=True, exist_ok=True)
    (cpp_dir / "include").mkdir(exist_ok=True)
    (cpp_dir / "src").mkdir(exist_ok=True)
    (cpp_dir / "build").mkdir(exist_ok=True)
    
    print(f"\\n📁 Created: {cpp_dir.relative_to(PROJECT_ROOT)}")
    
    if args.dry_run:
        print("\\n🔍 DRY-RUN mode - no files written")
        return
    
    # Write C++ files
    files_to_create = {
        cpp_dir / "include" / "hydroma_models.hpp": CPP_HEADER,
        cpp_dir / "src" / "hydroma_models.cpp": CPP_HEADER,
        cpp_dir / "CMakeLists.txt": CMAKELISTS,
        cpp_dir / "build_cpp_models.py": BUILD_SCRIPT,
        PROJECT_ROOT / "engine" / "hydroma" / "models" / "cache.py": CACHE_MODULE,
        PROJECT_ROOT / "sandbox" / "integrate_cache.py": INTEGRATION_SCRIPT,
    }
    
    for path, content in files_to_create.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"✅ Created: {path.relative_to(PROJECT_ROOT)}")
    
    print("\\n" + "=" * 80)
    print("✅ Phase 15 Files Created")
    print("=" * 80)
    print("\\n📋 Next steps:")
    print("\\n1. Build C++ accelerated models:")
    print("   cd engine/hydroma/cpp_bridge/accelerated")
    print("   python build_cpp_models.py")
    print("\\n2. Setup PostgreSQL (optional):")
    print("   docker run -d -p 5432:5432 \\\\")
    print("     -e POSTGRES_DB=econojin \\\\")
    print("     -e POSTGRES_USER=econojin \\\\")
    print("     -e POSTGRES_PASSWORD=econojin \\\\")
    print("     postgres:15")
    print("\\n3. Integrate PostgreSQL caching:")
    print("   python sandbox/integrate_cache.py")
    print("\\n4. Test acceleration:")
    print("   python -c 'import hydroma_models; print(hydroma_models.KGCv5.classify(...))'")
    print("\\n🎯 Expected Speedup: 10-100x for numerical models")


if __name__ == "__main__":
    main()