#!/usr/bin/env python3
"""
Service Migration Script: Migrate services from direct engine.hydroma imports
to Engine Gateway access via services/_gateway_facade.py.

Usage:
    python tools/migrate_services_to_gateway.py --dry-run
    python tools/migrate_services_to_gateway.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Import mapping: old import -> new import
IMPORT_MAP: dict[str, str] = {
    # Soil chemistry
    "engine.hydroma.soil.chemistry": "calculate_cec, calculate_esp, calculate_sar",
    # Soil health
    "engine.hydroma.soil.health": "calculate_soil_health_index",
    # Soil pedotransfer
    "engine.hydroma.soil.pedotransfer": "estimate_soil_parameters",
    # Soil physics
    "engine.hydroma.soil.physics": "available_water_capacity, water_content_at, van_genuchten_theta",
    # Soil recommendations
    "engine.hydroma.soil.recommendations": "generate_recommendations",
    # Soil salinity
    "engine.hydroma.soil.salinity": "calculate_leaching_requirement, calculate_sodic_soil_amendment, classify_salinity",
    # Soil taxonomy
    "engine.hydroma.soil.taxonomy": "get_soil_taxonomy",
    # Soil texture
    "engine.hydroma.soil.texture": "TEXTURE_NAMES, classify_texture, is_clayey, is_sandy, is_silty, texture_triangle_coords",
    # Soil water retention
    "engine.hydroma.soil.water_retention": "calculate_water_retention_curve, get_vg_parameters",
    # Climate
    "engine.hydroma.climate.et_calculator": "calc_et0_hargreaves, calc_et0_penman_monteith, calc_extraterrestrial_radiation, ClimateData",
    "engine.hydroma.climate": "calc_et0_hargreaves, calc_et0_penman_monteith",
    # Carbon
    "engine.hydroma.carbon.calculator": "CarbonProjectType, calculate_carbon_sequestration, CarbonCalculator",
    # Economics
    "engine.hydroma.economics.analysis": "calculate_npv, calculate_payback",
    "engine.hydroma.economics.costing": "calculate_agricultural_cost",
    "engine.hydroma.economics.employment": "estimate_direct_employment",
    "engine.hydroma.economics.revenue": "calculate_agricultural_revenue",
    "engine.hydroma.economics.risk": "assess_market_price_risk, assess_yield_risk",
    "engine.hydroma.economics.roi": "calculate_financial_metrics",
    "engine.hydroma.economics": "calculate_npv, calculate_payback, calculate_agricultural_cost",
    # Irrigation
    "engine.hydroma.irrigation.scheduler": "calculate_application_depth, calculate_interval",
    # Watershed
    "engine.hydroma.watershed.calculator": "calculate_runoff, design_check_dam, design_contour_trench, design_half_moon, StructureType, design_watershed_structure",
    # Models
    "engine.hydroma.models": "EWSI, HYRUE, ECSI, HDVI, EPIA, ESRI, HLHS, HPheno",
    "engine.hydroma.models.ecsi": "ECSI",
    "engine.hydroma.models.hyrue": "HYRUE",
    "engine.hydroma.models.hlhs": "HLHS, LandscapeMetrics",
    "engine.hydroma.models.runoff_model": "RunoffCalculator, RunoffInput",
    "engine.hydroma.models.groundwater_model": "GroundwaterInput, GroundwaterModel",
    "engine.hydroma.groundwater.service": "AquiferType, GroundwaterInput, GroundwaterService",
    # Simulation
    "engine.hydroma.simulation.orchestrator": "SimulationOrchestrator, run_chain",
    "engine.hydroma.simulation.contracts": "ChainInputs",
    "engine.hydroma.simulation.runners.rothc_runner": "RothCRunner, temp_factor",
    "engine.hydroma.simulation.weather_source": "fetch_daily_weather, hargreaves_et0",
    "engine.hydroma.simulation.calibration": "ishigami, sensitivity_of_metric",
    "engine.hydroma.simulation.scenarios": "SCENARIOS",
    # MRV
    "engine.hydroma.mrv.metrics": "MRVMetrics, compute_dashboard",
    "engine.hydroma.mrv.qa": "validate_reading, validate_satellite_index",
    "engine.hydroma.mrv.schemas": "CitizenBatch, CitizenReport, IoTReading, SatelliteIndex",
    "engine.hydroma.mrv.satellite_cdse": "CdseConfig, CdseUnavailable, build_bbox, retrieve_ndvi",
    "engine.hydroma.mrv.iot_ingest": "parse_ttn_v3, persist_iot_reading, webhook_key_ok",
    "engine.hydroma.mrv": "satellite_cdse",
    # Plant neuro
    "engine.hydroma.plant_neuro": "PlantNeuroEngine, StressLevel, VOCProfile",
    # Materials
    "engine.hydroma.materials.compost_formulator": "CompostMaterial, calculate_mix_cn_ratio",
    # Wrapper
    "engine.hydroma.wrapper": "compute_erosion, apply_scenario",
    # CPP bindings
    "engine.hydroma.cpp_bridge": "_ARRAY_CPP_THRESHOLD, _NUMBA_AVAILABLE, backend_status, get_module",
    "engine.hydroma.cpp_bindings": "estimate_rainfall_erosivity, get_telemetry, is_cpp_available, ndvi_array, penman_monteith_et0, reset_telemetry, rusle_annual_soil_loss",
    # Analysis
    "engine.hydromy.analyses.topography_analysis": "TopographyAnalyzer, TopographyInput",
    # Calculations
    "engine.hydroma.calculations.crop_water_req_calc": "CropWaterReqInput, CropWaterRequirementCalculator",
    # Scenarios
    "engine.hydroma.scenarios.climate_scenarios": "apply_climate_change, get_climate_projection",
    "engine.hydroma.scenarios.crop_scenarios": "compare_crops, simulate_crop_yield",
    # Decision support
    "engine.hydroma.decision_support.recommender": "RecommenderEngine",
    # Climate adaptation
    "engine.hydroma.climate_adaptation.uncertainty_knowledge_engine": "UncertaintyAndKnowledgeEngine",
    "engine.hydroma.climate_adaptation.dynamic_stress_engine": "DynamicStressEngine",
    "engine.hydroma.climate_adaptation.seed_optimization_engine": "SeedOptimizationEngine",
    "engine.hydroma.climate_adaptation.soil_degradation_model": "SoilDegradationModel",
    "engine.hydroma.climate_adaptation.climate_adaptive_phenology": "ClimateAdaptivePhenology",
    # Data pipeline
    "engine.hydroma.data_pipeline": "get_pipeline",
    # Biofertilizer
    "engine.hydroma.biofertilizer.models": "NojinFormulationRecipe, NojinMaterial, NojinSoilType",
    "engine.hydroma.biofertilizer.data": "MATERIALS",
    "engine.hydroma.biofertilizer.advanced_calculator": "ScaleCalculator",
    # Water
    "engine.hydroma.water.quality": "water_quality_func",
    # Misc
    "engine.hydroma": "cpp_bindings",
}


def load_violations(json_path: str) -> list[dict]:
    """Load violations from import guard JSON output."""
    with open(json_path) as f:
        data = json.load(f)
    return data.get("violations", [])


def group_violations_by_file(violations: list[dict]) -> dict[str, list[dict]]:
    """Group violations by source file."""
    files: dict[str, list[dict]] = {}
    for v in violations:
        f = v["file"]
        if f not in files:
            files[f] = []
        files[f].append(v)
    return files


def migrate_file(file_path: str, violations: list[dict], dry_run: bool = True) -> bool:
    """Migrate a single file from direct imports to gateway facade imports.
    
    Returns True if file was modified (or would be in dry_run mode).
    """
    path = Path(file_path)
    if not path.exists():
        return False
    
    source = path.read_text(encoding="utf-8")
    original_source = source
    
    # Build a mapping of module -> imported names from violations
    module_imports: dict[str, list[str]] = {}
    for v in violations:
        module = v["module"]
        names = v.get("names", [])
        if module not in module_imports:
            module_imports[module] = []
        module_imports[module].extend(names)
    
    # Replace import statements
    for module, _names in module_imports.items():
        # Handle "from engine.hydroma.X import name1, name2"
        pattern = rf'^from {re.escape(module)} import (.+)$'
        
        def replace_import(match: re.Match) -> str:
            imported_names_str = match.group(1).strip()
            # Parse the imported names
            imported_names = [n.strip().rstrip(' as ').strip() for n in imported_names_str.split(',')]
            
            # Check which names are in our facade
            facade_names = []
            for name in imported_names:
                facade_names.append(name.split(' as ')[0].strip())
            
            if facade_names:
                names_str = ", ".join(facade_names)
                return f"from services._gateway_facade import {names_str}"
            return ""
        
        source = re.sub(pattern, replace_import, source, flags=re.MULTILINE)
    
    if source != original_source:
        if not dry_run:
            path.write_text(source, encoding="utf-8")
        return True
    
    return False


def main():
    parser = argparse.ArgumentParser(description="Migrate services to use gateway facade")
    parser.add_argument("--json", default="temp_imports_final.json", help="Path to import guard JSON")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes (overrides dry-run)")
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    violations = load_violations(args.json)
    files = group_violations_by_file(violations)
    
    print(f"Found {len(violations)} violations across {len(files)} files")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY'}")
    print()
    
    modified_count = 0
    for file_path, file_violations in sorted(files.items()):
        modified = migrate_file(file_path, file_violations, dry_run=dry_run)
        if modified:
            modified_count += 1
            action = "WOULD MODIFY" if dry_run else "MODIFIED"
            print(f"  {action}: {file_path} ({len(file_violations)} violations)")
    
    print()
    print(f"Total files: {len(files)}")
    print(f"Modified: {modified_count}")
    print(f"Unmodified: {len(files) - modified_count}")


if __name__ == "__main__":
    main()