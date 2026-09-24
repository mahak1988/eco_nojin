#!/usr/bin/env python3
"""
Seed tool registry from innovation_registry.json (25 algorithms H01-H25)
and services/models/registry.py (22 scientific models).
Run after Phase 2 migration.
"""

import json
from pathlib import Path

from database.hub import hub
from database.models import ToolRegistryEntry

INNOVATION_REGISTRY = Path("docs/hydroma/innovation_registry.json")


# Domain mapping for algorithms
ALGO_DOMAIN_MAP = {
    "H01": "climate",
    "H02": "climate",
    "H03": "climate",
    "H04": "climate",
    "H05": "climate",
    "H06": "climate",
    "H07": "climate",
    "H08": "climate",
    "H09": "soil",
    "H10": "soil",
    "H11": "soil",
    "H12": "soil",
    "H13": "soil",
    "H14": "water",
    "H15": "seed",
    "H16": "seed",
    "H17": "seed",
    "H18": "seed",
    "H19": "seed",
    "H20": "seed",
    "H21": "seed",
    "H22": "modeling",
    "H23": "modeling",
    "H24": "modeling",
    "H25": "social",
}

# Category mapping for algorithms
ALGO_CATEGORY_MAP = {
    "H01": "algorithm",
    "H02": "algorithm",
    "H03": "algorithm",
    "H04": "algorithm",
    "H05": "algorithm",
    "H06": "algorithm",
    "H07": "algorithm",
    "H08": "algorithm",
    "H09": "algorithm",
    "H10": "algorithm",
    "H11": "algorithm",
    "H12": "algorithm",
    "H13": "algorithm",
    "H14": "algorithm",
    "H15": "algorithm",
    "H16": "algorithm",
    "H17": "algorithm",
    "H18": "algorithm",
    "H19": "algorithm",
    "H20": "algorithm",
    "H21": "algorithm",
    "H22": "model",
    "H23": "service",
    "H24": "service",
    "H25": "service",
}

# Phase mapping from innovation_registry.json
ALGO_PHASE_MAP = {
    "H01": 1,
    "H02": 1,
    "H03": 1,
    "H04": 1,
    "H08": 1,
    "H05": 2,
    "H06": 2,
    "H07": 2,
    "H24": 2,
    "H09": 3,
    "H10": 3,
    "H11": 3,
    "H12": 3,
    "H13": 3,
    "H14": 3,
    "H15": 4,
    "H16": 4,
    "H17": 4,
    "H18": 4,
    "H19": 4,
    "H20": 4,
    "H21": 4,
    "H22": 5,
    "H23": 5,
    "H25": 5,
}

# Fidelity mapping
ALGO_FIDELITY_MAP = {
    "H01": "official",  # FAO-based
    "H02": "official",  # Zhang et al.
    "H03": "official",  # Yuan et al.
    "H04": "official",  # CMIP6
    "H05": "official",  # Luedeling
    "H06": "official",  # Yuan et al. flash drought
    "H07": "official",  # Luedeling chilling
    "H08": "official",  # Zscheischler compound events
    "H09": "official",  # SOC-AWC
    "H10": "official",  # Erosion-RD
    "H11": "official",  # Salinity trend
    "H12": "official",  # Compaction
    "H13": "official",  # Soil biology
    "H14": "official",  # Land subsidence
    "H15": "official",  # GxE seed matching
    "H16": "official",  # Field hardiness
    "H17": "official",  # Native resilience
    "H18": "official",  # Growth duration optimizer
    "H19": "official",  # Genetic vulnerability
    "H20": "official",  # Ecozone matching
    "H21": "official",  # Microbiome
    "H22": "model",  # Monte Carlo
    "H23": "service",  # Multi-scale fusion
    "H24": "service",  # Real-time correction
    "H25": "service",  # Local knowledge
}


def load_innovation_registry():
    """Load and parse innovation_registry.json."""
    with open(INNOVATION_REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def load_models_registry():
    """Load the 22 scientific models from services.models.registry."""
    # Import dynamically to avoid circular imports
    import sys

    sys.path.insert(0, "D:/eco_nojin")
    from services.models.registry import REGISTRY

    return REGISTRY


def seed_tool_registry():
    """Seed tool registry from innovation registry and models registry."""
    # Load innovation registry
    innovation = load_innovation_registry()
    failures = {f["id"]: f for f in innovation.get("failures", [])}
    algorithms = {a["code"]: a for a in innovation.get("algorithms", [])}

    # Load models registry
    models_registry = load_models_registry()

    inserted = 0
    skipped = 0

    with hub.get_session() as session:
        # --- Seed algorithms (H01-H25) ---
        print("Seeding algorithms from innovation_registry.json...")
        for algo_id, algo in algorithms.items():
            tool_id = algo_id  # H01, H02, etc.

            # Check if already exists
            existing = (
                session.query(ToolRegistryEntry)
                .filter(ToolRegistryEntry.tool_id == tool_id)
                .first()
            )

            if existing:
                print(f"  Already exists: {tool_id}")
                skipped += 1
                continue

            failure = failures.get(algo_id, {})

            tool = ToolRegistryEntry(
                tool_id=tool_id,
                name_fa=algo.get("name_fa", ""),
                name_en=algo.get("name_en", ""),
                domain=ALGO_DOMAIN_MAP.get(algo_id, "modeling"),
                category=ALGO_CATEGORY_MAP.get(algo_id, "algorithm"),
                fidelity=ALGO_FIDELITY_MAP.get(algo_id, "official"),
                reference=algo.get("advantage", ""),
                description=failure.get("evidence", "") + " Impact: " + failure.get("impact", ""),
                formula=algo.get("formula", ""),
                service_slug=f"algorithms/{algo_id.lower()}",
                endpoint_path=f"/api/v1/science/algorithms/{algo_id.lower()}",
                phase=ALGO_PHASE_MAP.get(algo_id),
                is_active=True,
            )
            session.add(tool)
            inserted += 1
            print(f"  Inserted: {tool_id} - {algo.get('name_en', '')[:50]}")

        # --- Seed scientific models (22 models) ---
        print("\nSeeding scientific models from services.models.registry...")
        for model_spec in models_registry:
            tool_id = f"M{model_spec.slug.upper()}"

            # Check if already exists
            existing = (
                session.query(ToolRegistryEntry)
                .filter(ToolRegistryEntry.tool_id == tool_id)
                .first()
            )

            if existing:
                print(f"  Already exists: {tool_id}")
                skipped += 1
                continue

            # Determine domain from model domain
            domain_map = {
                "climate": "climate",
                "water": "water",
                "crop": "crop",
                "carbon": "carbon",
                "soil": "soil",
            }

            tool = ToolRegistryEntry(
                tool_id=tool_id,
                name_fa=model_spec.name_fa,
                name_en=model_spec.name_en,
                domain=domain_map.get(model_spec.domain, "modeling"),
                category="model",
                fidelity=model_spec.fidelity,
                reference=model_spec.reference,
                description=model_spec.description,
                service_slug=f"models/{model_spec.slug}",
                endpoint_path=f"/api/v1/models/{model_spec.slug}/run",
                phase=None,  # Scientific models are cross-cutting
                is_active=True,
            )
            session.add(tool)
            inserted += 1
            print(f"  Inserted: {tool_id} - {model_spec.name_en[:50]}")

        print(f"\nDone! Inserted: {inserted}, Skipped: {skipped}")


if __name__ == "__main__":
    seed_tool_registry()
