"""
Nojin Database Population Script
==================================
Populates the database with:
- 43 scientifically-documented materials
- 10 soil types with characteristics
- 10 formulation recipes for different soils

All inserts are idempotent (safe to run multiple times).

Run: python populate_nojin_database.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(r"D:\eco_nojin")
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 80)
print("🌱 NOJIN DATABASE POPULATION")
print("=" * 80)
print(f"📅 {datetime.now().isoformat()}")

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Verify database and create tables
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 1: Verifying database connectivity...")

try:
    from database import engine, SessionLocal
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

print("\n📋 Step 2: Creating tables if they don't exist...")

try:
    from engine.hydroma.biofertilizer.models import (
        Base,
        NojinMaterial,
        NojinSoilType,
        NojinFormulationRecipe,
        NojinMaterialComposition,
        NojinApplicationGuide,
        NojinCostBenefit,
        NojinWaterSaving,
    )
    
    Base.metadata.create_all(engine)
    print("✅ All tables created/verified")
except Exception as e:
    print(f"❌ Table creation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Load data
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 3: Loading materials data...")

try:
    from engine.hydroma.biofertilizer.data.materials_data import (
        MATERIALS,
        SOIL_TYPES,
        FORMULATIONS,
    )
    
    print(f"✅ Loaded {len(MATERIALS)} materials")
    print(f"✅ Loaded {len(SOIL_TYPES)} soil types")
    print(f"✅ Loaded {len(FORMULATIONS)} formulations")
except Exception as e:
    print(f"❌ Data loading error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Populate materials
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 4: Populating materials...")

session = SessionLocal()

materials_added = 0
materials_updated = 0
materials_skipped = 0

# Fields to map from data to model
material_fields = [
    "material_code", "common_name", "scientific_name", "category",
    "nitrogen_pct", "phosphorus_pct", "potassium_pct",
    "calcium_pct", "magnesium_pct", "sulfur_pct",
    "carbon_pct", "organic_matter_pct",
    "cn_ratio", "ph", "ec_dsm_m", "cec_cmol_kg",
    "bulk_density_kg_m3", "water_retention_pct", "porosity_pct", "surface_area_m2_g",
    "release_rate", "persistence_years",
    "application_rate_kg_ha_min", "application_rate_kg_ha_max",
    "cost_per_ton_usd", "availability", "source_regions",
    "overuse_risks", "incompatibilities", "safety_notes",
    "historical_use", "modern_research", "benefits", "limitations",
    "is_proprietary", "is_locally_available", "is_suitable_for_arid", "arid_priority_score",
]

print("\n  🌱 Inserting/Updating 43 materials:")
print("-" * 70)

for mat_data in MATERIALS:
    try:
        code = mat_data["material_code"]
        
        # Check if exists
        existing = session.query(NojinMaterial).filter_by(material_code=code).first()
        
        # Build kwargs (only valid fields)
        kwargs = {}
        for field in material_fields:
            if field in mat_data and mat_data[field] is not None:
                kwargs[field] = mat_data[field]
        
        if existing:
            # Update existing record
            for key, value in kwargs.items():
                setattr(existing, key, value)
            materials_updated += 1
            print(f"  🔄 Updated: {code:10s} | {mat_data['common_name']}")
        else:
            # Create new record
            material = NojinMaterial(**kwargs)
            session.add(material)
            materials_added += 1
            print(f"  ✅ Added:   {code:10s} | {mat_data['common_name']}")
    
    except Exception as e:
        materials_skipped += 1
        print(f"  ❌ Error {code}: {e}")

session.commit()

print(f"\n📊 Materials summary:")
print(f"   ✅ Added: {materials_added}")
print(f"   🔄 Updated: {materials_updated}")
print(f"   ⚠️  Skipped: {materials_skipped}")

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Populate soil types
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 5: Populating soil types...")

soil_fields = [
    "soil_code", "soil_name", "soil_category", "texture",
    "typical_ph_min", "typical_ph_max",
    "typical_om_pct", "typical_cec_cmol_kg",
    "water_holding_capacity", "drainage",
    "common_problems", "nutrient_deficiencies",
    "common_regions",
]

soils_added = 0
soils_updated = 0

print("\n  🌍 Inserting/Updating 10 soil types:")
print("-" * 70)

for soil_data in SOIL_TYPES:
    try:
        code = soil_data["soil_code"]
        existing = session.query(NojinSoilType).filter_by(soil_code=code).first()
        
        kwargs = {k: soil_data.get(k) for k in soil_fields if k in soil_data}
        
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            soils_updated += 1
            print(f"  🔄 Updated: {code:10s} | {soil_data['soil_name']}")
        else:
            soil = NojinSoilType(**kwargs)
            session.add(soil)
            soils_added += 1
            print(f"  ✅ Added:   {code:10s} | {soil_data['soil_name']}")
    except Exception as e:
        print(f"  ❌ Error {soil_data.get('soil_code')}: {e}")

session.commit()

print(f"\n📊 Soil types summary:")
print(f"   ✅ Added: {soils_added}")
print(f"   🔄 Updated: {soils_updated}")

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Populate formulations
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 6: Populating formulation recipes...")

formulations_added = 0
formulations_updated = 0

print("\n  🧪 Inserting/Updating 10 formulations:")
print("-" * 70)

for form_data in FORMULATIONS:
    try:
        code = form_data["recipe_code"]
        soil_code = form_data["soil_code"]
        
        # Find soil_type_id
        soil = session.query(NojinSoilType).filter_by(soil_code=soil_code).first()
        if not soil:
            print(f"  ⚠️  Skipped {code}: soil {soil_code} not found")
            continue
        
        existing = session.query(NojinFormulationRecipe).filter_by(recipe_code=code).first()
        
        # Parse material_composition JSON if it's a string
        composition = form_data.get("material_composition", {})
        if isinstance(composition, str):
            composition = json.loads(composition)
        
        kwargs = {
            "recipe_code": code,
            "recipe_name": form_data.get("recipe_name"),
            "soil_type_id": soil.id,
            "area_min_ha": form_data.get("area_min_ha", 0.1),
            "area_max_ha": form_data.get("area_max_ha", 1000.0),
            "material_composition": composition,
            "total_kg_per_ha": form_data.get("total_kg_per_ha"),
            "estimated_cost_usd_per_ha": form_data.get("estimated_cost_usd_per_ha"),
            "cn_ratio_final": form_data.get("cn_ratio_final"),
            "om_increase_pct": form_data.get("om_increase_pct"),
            "water_saving_pct": form_data.get("water_saving_pct"),
            "yield_increase_pct": form_data.get("yield_increase_pct"),
            "restoration_years": form_data.get("restoration_years"),
            "application_timing": form_data.get("application_timing"),
            "application_method": form_data.get("application_method"),
            "frequency_per_year": form_data.get("frequency_per_year"),
            "traditional_technique": form_data.get("traditional_technique"),
            "integration_notes": form_data.get("integration_notes"),
        }
        
        if existing:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(existing, key, value)
            formulations_updated += 1
            print(f"  🔄 Updated: {code:15s} | {form_data.get('recipe_name', '')}")
        else:
            recipe = NojinFormulationRecipe(**kwargs)
            session.add(recipe)
            formulations_added += 1
            print(f"  ✅ Added:   {code:15s} | {form_data.get('recipe_name', '')}")
    except Exception as e:
        print(f"  ❌ Error {form_data.get('recipe_code')}: {e}")
        import traceback
        traceback.print_exc()

session.commit()

print(f"\n📊 Formulations summary:")
print(f"   ✅ Added: {formulations_added}")
print(f"   🔄 Updated: {formulations_updated}")

# ═══════════════════════════════════════════════════════════════════
# STEP 6: Verify final state
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 7: Verifying database state...")

print("\n" + "=" * 80)
print("📊 FINAL DATABASE STATE")
print("=" * 80)

# Count materials
mat_count = session.query(NojinMaterial).count()
print(f"\n🧪 Materials: {mat_count}")
print("-" * 70)

# Group by category
from sqlalchemy import func
categories = session.query(
    NojinMaterial.category,
    func.count(NojinMaterial.id)
).group_by(NojinMaterial.category).all()

for cat, count in categories:
    print(f"  • {cat:25s}: {count} materials")

# List arid-priority materials
print(f"\n🏜️  Top Arid-Priority Materials (score >= 9):")
print("-" * 70)
arid_materials = session.query(NojinMaterial).filter(
    NojinMaterial.arid_priority_score >= 9
).order_by(NojinMaterial.arid_priority_score.desc()).all()

for m in arid_materials:
    print(f"  ⭐ {m.material_code:10s} | {m.common_name:35s} | Score: {m.arid_priority_score}")

# Count soil types
soil_count = session.query(NojinSoilType).count()
print(f"\n🌍 Soil Types: {soil_count}")
print("-" * 70)

soils = session.query(NojinSoilType).order_by(NojinSoilType.soil_code).all()
for s in soils:
    print(f"  • {s.soil_code:10s} | {s.soil_name:35s} | {s.soil_category}")

# Count formulations
form_count = session.query(NojinFormulationRecipe).count()
print(f"\n🧪 Formulation Recipes: {form_count}")
print("-" * 70)

formulations = session.query(NojinFormulationRecipe).order_by(
    NojinFormulationRecipe.recipe_code
).all()

for f in formulations:
    soil = session.query(NojinSoilType).get(f.soil_type_id)
    soil_name = soil.soil_name if soil else "Unknown"
    cost = f.estimated_cost_usd_per_ha or 0
    years = f.restoration_years or 0
    water = f.water_saving_pct or 0
    print(f"  • {f.recipe_code:15s} | {soil_name:30s} | ${cost:5.0f}/ha | {years:.1f}yr | {water:.0f}% water")

session.close()

# ═══════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("✅ DATABASE POPULATION COMPLETE")
print("=" * 80)

print(f"""
📊 Summary:
  🧪 Materials:        {mat_count:3d} (target: 43)
  🌍 Soil Types:       {soil_count:3d} (target: 10)
  🧪 Formulations:     {form_count:3d} (target: 10)
  
  ➕ Added this run:
     Materials:     {materials_added}
     Soil types:    {soils_added}
     Formulations:  {formulations_added}
  
  🔄 Updated this run:
     Materials:     {materials_updated}
     Soil types:    {soils_updated}
     Formulations:  {formulations_updated}

🎯 Next steps:
  1. Build advanced calculator: python build_nojin_calculator_advanced.py
  2. Build API endpoints: python build_nojin_api.py
  3. Build tests: python build_nojin_tests.py

🌟 Achievement Unlocked:
  2.5 billion people in arid regions now have scientifically-backed
  soil restoration formulations in the database!
""")