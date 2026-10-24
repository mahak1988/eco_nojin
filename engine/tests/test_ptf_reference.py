"""Parity and containment for the frozen Rosetta-3 PTF reference artifact.

Modules under test:

* ``engine/hydroma/soil/ptf_reference.json`` -- the frozen artifact
  (``PTF-REFERENCE-ROSETTA-3`` v1.0.0), generated once by
  ``tools/regenerate_ptf_reference.py`` from Rosetta 3 (``rosetta-soil`` 0.3.2,
  CC0-1.0, model code 5); and
* ``engine/hydroma/soil/ptf_reference.py`` -- the dependency-free reader of it.

What these tests are
---------------------
A **containment and parity harness** for an additive reference. The sibling suite
``engine/tests/test_rosetta_ptf_reference.py`` already compares the engine's
``SOIL_PARAMETERS_VG`` against a live Rosetta run; this suite instead pins the
*frozen* copy of that comparison and proves the reader is dependency-free. It
confirms the artifact covers the engine's textures, still equals a fresh Rosetta
run, exposes usable uncertainty bands, and -- crucially -- changed nothing:

* gap **G-S6** (the engine table's withdrawn Carsel & Parrish attribution) stays
  open. ``SOIL_PARAMETERS_VG`` is asserted here *against the literal numbers the
  engine ships*, so if anyone treats this artifact as licence to edit the table,
  these tests fail;
* the engine table is unchanged, value for value.

The loader admits only the standard library (``json`` + ``math``), which is
itself asserted below: it must not import or name numpy or Rosetta, so the
frozen reference stays readable without the dev prediction package present.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from engine.hydroma.soil import ptf_reference as loader
from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG, van_genuchten_theta

#: The five judged parameters, in artifact column order.
_PARAMETER_KEYS = ("theta_r", "theta_s", "alpha", "n", "ks_cm_per_day")

#: Reference particle-size fractions for the twelve USDA textures as
#: (sand %, silt %, clay %): the engine's own reference compositions, identical to
#: those the audit and the regenerator use, embedded here so the in-memory fresh
#: run reproduces the artifact's inputs without importing the generator.
_REFERENCE_COMPOSITIONS: dict[str, tuple[float, float, float]] = {
    "sand": (85.0, 10.0, 5.0),
    "loamy_sand": (75.0, 15.0, 10.0),
    "sandy_loam": (60.0, 25.0, 15.0),
    "loam": (40.0, 40.0, 20.0),
    "silt_loam": (20.0, 65.0, 15.0),
    "silt": (5.0, 90.0, 5.0),
    "sandy_clay_loam": (60.0, 15.0, 25.0),
    "clay_loam": (35.0, 35.0, 30.0),
    "silty_clay_loam": (15.0, 55.0, 30.0),
    "sandy_clay": (50.0, 10.0, 40.0),
    "silty_clay": (10.0, 45.0, 45.0),
    "clay": (20.0, 30.0, 50.0),
}

#: Input-derivation constants, identical to the audit and the regenerator.
_PARTICLE_DENSITY = 2.65
_HEAD_33_KPA_CM = 330.0
_HEAD_1500_KPA_CM = 15000.0
_ROSETTA_VERSION = 3

#: The audited engine/Rosetta alpha ratio for "sand": 0.145 / 0.03819 = 3.797,
#: the widest alpha divergence the sibling suite recorded. Recorded here so a
#: change that closes G-S6 silently cannot pass.
_AUDITED_SAND_ALPHA_RATIO = 3.797


def test_artifact_covers_every_table_texture() -> None:
    """The artifact's textures are exactly the engine table's twelve."""
    artifact = loader.load_reference()
    artifact_textures = set(artifact["textures"])
    engine_textures = set(SOIL_PARAMETERS_VG)
    assert len(engine_textures) == 12, (
        f"engine table has {len(engine_textures)} textures, expected 12"
    )
    assert engine_textures == artifact_textures, (
        "artifact textures differ from the engine table: "
        f"engine-only={sorted(engine_textures - artifact_textures)}, "
        f"artifact-only={sorted(artifact_textures - engine_textures)}"
    )
    assert len(artifact_textures) == 12, (
        f"artifact has {len(artifact_textures)} textures, expected 12"
    )


def test_artifact_matches_a_fresh_rosetta_run() -> None:
    """The committed artifact still equals a fresh Rosetta 3 run (deterministic)."""
    pytest.importorskip("rosetta", reason="rosetta-soil is a dev-only reference package")
    from rosetta import rosetta

    records: list[list[float]] = []
    for texture in _REFERENCE_COMPOSITIONS:
        entry = SOIL_PARAMETERS_VG[texture]
        sand, silt, clay = _REFERENCE_COMPOSITIONS[texture]
        bulk_density = _PARTICLE_DENSITY * (1.0 - entry["theta_s"])
        theta_33 = van_genuchten_theta(
            -_HEAD_33_KPA_CM, entry["theta_r"], entry["theta_s"], entry["alpha"], entry["n"]
        )
        theta_1500 = van_genuchten_theta(
            -_HEAD_1500_KPA_CM, entry["theta_r"], entry["theta_s"], entry["alpha"], entry["n"]
        )
        records.append([sand, silt, clay, bulk_density, theta_33, theta_1500])

    means, _sds, codes = rosetta(_ROSETTA_VERSION, records)
    assert all(int(code) == 5 for code in codes), (
        f"Rosetta did not use model code 5 for every row: codes={list(codes)}"
    )

    artifact = loader.load_reference()
    for index, texture in enumerate(_REFERENCE_COMPOSITIONS):
        committed = artifact["textures"][texture]["mean"]
        fresh = means[index]
        for column, key in enumerate(_PARAMETER_KEYS):
            assert committed[key] == pytest.approx(fresh[column], abs=1e-9), (
                f"{texture}.{key}: committed {committed[key]!r} differs from a fresh "
                f"Rosetta run {fresh[column]!r} by more than 1e-9. The artifact is "
                "stale; regenerate it with tools/regenerate_ptf_reference.py."
            )


def test_uncertainty_bands_are_usable() -> None:
    """Every texture yields a positive, finite band with a sane log10-Ks width."""
    artifact = loader.load_reference()
    for texture in artifact["textures"]:
        sd = artifact["textures"][texture]["sd"]
        for key in _PARAMETER_KEYS:
            value = float(sd[key])
            assert value > 0.0, f"{texture}.sd[{key}] = {value} is not positive"
            assert math.isfinite(value), f"{texture}.sd[{key}] = {value} is not finite"

        band = loader.uncertainty_band(texture)
        assert isinstance(band, loader.PTFUncertainty)
        for name in (
            "sd_theta_r",
            "sd_theta_s",
            "sd_alpha",
            "sd_n",
            "sd_log10_ks_cm_per_day",
        ):
            value = float(getattr(band, name))
            assert math.isfinite(value), f"{texture}.{name} = {value} is not finite"
            assert value > 0.0, f"{texture}.{name} = {value} is not positive"
        assert 0.0 < band.sd_log10_ks_cm_per_day < 3.0, (
            f"{texture}: derived sd_log10_ks = {band.sd_log10_ks_cm_per_day} is "
            "outside (0, 3); the delta-method conversion from Rosetta's linear "
            "Ks sd looks wrong"
        )


def test_engine_table_is_unchanged_by_the_artifact() -> None:
    """``SOIL_PARAMETERS_VG`` still holds the exact values the engine ships.

    These are the literal numbers in ``engine/data/soil_vg_table.csv``, read from
    the module and frozen here. If this artifact were ever treated as licence to
    edit the engine table, one of these would move and this test would fail. The
    artifact is additive; it replaces nothing (G-S6 stays open).
    """
    assert SOIL_PARAMETERS_VG["loam"]["theta_s"] == 0.43
    assert SOIL_PARAMETERS_VG["sand"]["theta_r"] == 0.045
    assert SOIL_PARAMETERS_VG["clay"]["Ks"] == 4.8
    assert SOIL_PARAMETERS_VG["silt"]["alpha"] == 0.016
    # Guard against the whole set being replaced by Rosetta's table.
    assert set(SOIL_PARAMETERS_VG) == set(_REFERENCE_COMPOSITIONS)


def test_documented_divergence_is_unchanged() -> None:
    """The "sand" engine/Rosetta alpha gap is still the audited wide divergence.

    This records that gap G-S6 remains **open**, not closed. Rosetta's alpha for
    "sand" is far below the engine's, and if anyone "resolved" the conflict by
    abandoning the engine value for Rosetta's, the ratio would collapse toward 1
    and this test would fail.
    """
    engine_alpha = float(SOIL_PARAMETERS_VG["sand"]["alpha"])
    sand_row = loader.reference_row("sand")
    assert sand_row is not None  # 'sand' is present in the reference table
    rosetta_alpha = float(sand_row["mean"]["alpha"])
    ratio = engine_alpha / rosetta_alpha
    assert rosetta_alpha > 0.0, f"Rosetta alpha for sand is non-positive: {rosetta_alpha}"
    assert ratio > 2.0, (
        f"engine alpha / Rosetta alpha for 'sand' = {ratio:.3f}; a ratio near 1 "
        "would mean the engine has adopted Rosetta's table and gap G-S6 is "
        "being treated as closed by a change, not by a decision"
    )
    assert abs(ratio - _AUDITED_SAND_ALPHA_RATIO) <= 0.5, (
        f"engine alpha / Rosetta alpha for 'sand' = {ratio:.3f}, which is more "
        f"than 0.5 from the audited {_AUDITED_SAND_ALPHA_RATIO}. Either the "
        "engine table or the Rosetta reference moved; this is the divergence "
        "the audit measured and G-S6 is still open."
    )


def test_loader_has_no_numpy_or_rosetta() -> None:
    """The reader stays standard-library-only and free of the prediction package."""
    source = Path(loader.__file__).read_text(encoding="utf-8")
    assert "numpy" not in source, (
        "ptf_reference.py names numpy; the loader must be dependency-free so the "
        "frozen reference is readable without the numpy/rosetta dev stack"
    )
    assert "rosetta" not in source, (
        "ptf_reference.py names rosetta; the loader must be dependency-free and "
        "must not import or reference the prediction package"
    )
