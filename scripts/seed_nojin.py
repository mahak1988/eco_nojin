"""Idempotent seeder for the Nojin knowledge base (fixes D4).

Populates nojin_materials / nojin_soil_types / nojin_formulation_recipes from
the engine's canonical data package (engine.hydroma.biofertilizer.data).
Tables that already contain rows are left untouched.

Usage:
    python scripts/seed_nojin.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.hub import hub  # noqa: E402
from engine.hydroma.biofertilizer.data import FORMULATIONS, MATERIALS, SOIL_TYPES  # noqa: E402
from engine.hydroma.biofertilizer.models import (  # noqa: E402
    NojinFormulationRecipe,
    NojinMaterial,
    NojinSoilType,
)


def _rowify(model_cls, data: dict):
    cols = {c.name for c in model_cls.__table__.columns}
    return model_cls(**{k: v for k, v in data.items() if k in cols})


def main() -> int:
    Session = hub.get_session
    with Session() as db:
        n_soil = db.query(NojinSoilType).count()
        n_mat = db.query(NojinMaterial).count()
        n_rec = db.query(NojinFormulationRecipe).count()
        print(f"before: soils={n_soil} materials={n_mat} recipes={n_rec}")

        if n_mat == 0:
            for md in MATERIALS:
                db.add(_rowify(NojinMaterial, md))
            print(f"inserted materials: {len(MATERIALS)}")
        if n_soil == 0:
            soil_map: dict[str, int] = {}
            for sd in SOIL_TYPES:
                row = _rowify(NojinSoilType, sd)
                db.add(row)
                db.flush()
                soil_map[sd["soil_code"]] = row.id
            print(f"inserted soils: {len(SOIL_TYPES)}")
        else:
            soil_map = {s.soil_code: s.id for s in db.query(NojinSoilType).all()}
        if n_rec == 0:
            for fd in FORMULATIONS:
                fd = dict(fd)
                soil_code = fd.pop("soil_code", None)
                fd["soil_type_id"] = soil_map.get(soil_code)
                db.add(_rowify(NojinFormulationRecipe, fd))
            print(f"inserted recipes: {len(FORMULATIONS)}")
        db.commit()

    with Session() as verify:
        print(
            f"after: soils={verify.query(NojinSoilType).count()} "
            f"materials={verify.query(NojinMaterial).count()} "
            f"recipes={verify.query(NojinFormulationRecipe).count()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
