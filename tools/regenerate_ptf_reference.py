"""Regenerate the frozen Rosetta-3 PTF reference artifact (developer only).

This is a **build** tool, not a runtime module. It imports the optional
``rosetta-soil`` package (CC0-1.0, USDA-ARS) and numpy, both of which are dev
dependencies only and are deliberately absent from the engine runtime and from
the reader it produces (``engine/hydroma/soil/ptf_reference.py``). The engine
computation it feeds from (``engine.hydroma.soil.physics``) is read-only here:
nothing it touches is modified.

It rebuilds ``engine/hydroma/soil/ptf_reference.json`` deterministically from
the engine's own inputs and the installed Rosetta 3 model (code 5), then prints
the row count and a sha256 of the generated JSON. With ``--check`` it rebuilds in
memory (reusing the committed ``generated_at`` so the timestamp is not mistaken
for drift), compares byte-for-byte with the committed artifact, prints
``MATCH``/``DRIFT`` and exits non-zero on any difference -- so CI can prove the
committed artifact still equals a fresh Rosetta run and flag when it must be
regenerated.

Determinism: Rosetta 3's bootstrap ensembles are fixed resources and
numpy's reductions over them are reproducible, so two runs of this tool with the
same installed packages produce byte-identical JSON (given the same timestamp,
which ``--check`` holds fixed). Rosetta returns code 5 (all six inputs accepted)
for all twelve rows; a row that fell back to a weaker model would make this
artifact dishonest, so that is asserted rather than assumed.

Usage::

    python tools/regenerate_ptf_reference.py            # rewrite the artifact
    python tools/regenerate_ptf_reference.py --check    # verify, no write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# The engine is read-only here: the inputs to Rosetta are derived from the
# engine's own table and van Genuchten curve, and nothing is written back to it.
import numpy as np
from rosetta import rosetta

from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG, van_genuchten_theta

# --- fixed provenance and input-derivation constants -----------------------

ARTIFACT_ID = "PTF-REFERENCE-ROSETTA-3"
ARTIFACT_VERSION = "1.0.0"
GENERATOR_PATH = "tools/regenerate_ptf_reference.py"
PACKAGE = "rosetta-soil"
PACKAGE_VERSION = "0.3.2"
PACKAGE_LICENSE = "CC0-1.0 (USDA-ARS)"
ROSETTA_VERSION = 3  # Rosetta 3; code 5 is the best-available model it selects.
EXPECTED_MODEL_CODE = 5

#: Standard mineral particle density [g/cm3], turning the engine's own porosity
#: into the bulk density Rosetta wants (quartz-dominant value, as in the audit).
PARTICLE_DENSITY = 2.65

#: Heads corresponding to 33 kPa and 1500 kPa [cm of water] -- the definitions
#: Rosetta's th33 and th1500 inputs use.
HEAD_33_KPA_CM = 330.0
HEAD_1500_KPA_CM = 15000.0

#: Reference particle-size fractions for the twelve USDA textures as
#: (sand %, silt %, clay %): the engine's own reference compositions for its own
#: texture classes, taken from the divergence audit
#: (engine/hydroma/soil/tests/test_soil.py:700-713 and carried in
#: engine/tests/test_rosetta_ptf_reference.py ``_REFERENCE_COMPOSITIONS``).
REFERENCE_COMPOSITIONS: dict[str, tuple[float, float, float]] = {
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

INPUTS_DERIVATION = (
    "Sand/silt/clay percentages are the engine's own reference compositions for "
    "its twelve texture classes (see engine/tests/test_rosetta_ptf_reference.py "
    "_REFERENCE_COMPOSITIONS); bulk density = 2.65*(1-theta_s) from the engine "
    "table; theta_33/theta_1500 evaluated from the engine's own VG curve at "
    "330/15000 cm. The artifact therefore records Rosetta's prediction AT THE "
    "ENGINE'S OWN INPUTS, which is what the divergence audit measures -- it is "
    "not an independent USDA canonical table."
)

CITATION = (
    "Zhang & Schaap 2017, Journal of Hydrology 547:39-53 (Rosetta 3); "
    "Schaap et al. 2001, JH 251:163-176 (Rosetta 1)"
)

INPUT_COLUMNS = ["sand_pct", "silt_pct", "clay_pct", "bulk_density", "theta_33", "theta_1500"]
PARAMETER_KEYS = ["theta_r", "theta_s", "alpha", "n", "ks_cm_per_day"]

#: Decimals kept in the artifact. Enough that every judged parameter is stored to
#: well under the 1e-9 the parity test compares against, and small enough that
#: the file stays a lightweight reference.
ROUND_DECIMALS = 10

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "engine" / "hydroma" / "soil" / "ptf_reference.json"


def _rosetta_input_records() -> list[list[float]]:
    """The twelve Rosetta input records, derived from the engine's own table.

    Each record is ``[sand %, silt %, clay %, bulk density, theta_33,
    theta_1500]``, the order Rosetta expects. This mirrors
    ``engine/tests/test_rosetta_ptf_reference.py::_rosetta_input_records`` so the
    artifact and the parity test feed Rosetta identical inputs.
    """
    if set(REFERENCE_COMPOSITIONS) != set(SOIL_PARAMETERS_VG):
        extra_comp = sorted(set(REFERENCE_COMPOSITIONS) - set(SOIL_PARAMETERS_VG))
        extra_engine = sorted(set(SOIL_PARAMETERS_VG) - set(REFERENCE_COMPOSITIONS))
        raise RuntimeError(
            "reference compositions and the engine table disagree on textures: "
            f"only-in-compositions={extra_comp}, only-in-engine={extra_engine}"
        )
    records: list[list[float]] = []
    for texture in REFERENCE_COMPOSITIONS:
        entry = SOIL_PARAMETERS_VG[texture]
        sand, silt, clay = REFERENCE_COMPOSITIONS[texture]
        bulk_density = PARTICLE_DENSITY * (1.0 - entry["theta_s"])
        theta_33 = van_genuchten_theta(
            -HEAD_33_KPA_CM, entry["theta_r"], entry["theta_s"], entry["alpha"], entry["n"]
        )
        theta_1500 = van_genuchten_theta(
            -HEAD_1500_KPA_CM, entry["theta_r"], entry["theta_s"], entry["alpha"], entry["n"]
        )
        records.append([sand, silt, clay, bulk_density, theta_33, theta_1500])
    return records


def _round(value: float) -> float:
    return round(float(value), ROUND_DECIMALS)


def build_artifact(generated_at: str) -> dict:
    """Build the artifact document for a given ``generated_at`` timestamp.

    Deterministic in the data: the only caller-supplied field is the timestamp,
    so ``--check`` can hold it fixed to isolate real drift from the clock.
    """
    records = _rosetta_input_records()
    means, sds, codes = rosetta(ROSETTA_VERSION, records)
    means = np.asarray(means, dtype=float)
    sds = np.asarray(sds, dtype=float)
    codes = np.asarray(codes, dtype=int).ravel().tolist()

    bad = [i for i, code in enumerate(codes) if code != EXPECTED_MODEL_CODE]
    if bad:
        textures = list(REFERENCE_COMPOSITIONS)
        detail = ", ".join(f"{textures[i]}=code {codes[i]}" for i in bad)
        raise RuntimeError(
            "Rosetta did not reach model code "
            f"{EXPECTED_MODEL_CODE} (all six inputs accepted) for: {detail}. "
            "A weaker model would make the reference rows incomparable."
        )
    if not np.all(np.isfinite(means[:, :5])) or not np.all(np.isfinite(sds[:, :5])):
        raise RuntimeError("Rosetta returned a non-finite judged parameter.")

    textures: dict[str, dict] = {}
    for index, texture in enumerate(REFERENCE_COMPOSITIONS):
        record = records[index]
        mean = means[index]
        sd = sds[index]
        textures[texture] = {
            "inputs": {
                "sand_pct": _round(record[0]),
                "silt_pct": _round(record[1]),
                "clay_pct": _round(record[2]),
                "bulk_density": _round(record[3]),
                "theta_33": _round(record[4]),
                "theta_1500": _round(record[5]),
            },
            "mean": {key: _round(mean[col]) for col, key in enumerate(PARAMETER_KEYS)},
            "sd": {key: _round(sd[col]) for col, key in enumerate(PARAMETER_KEYS)},
        }

    return {
        "artifact_id": ARTIFACT_ID,
        "version": ARTIFACT_VERSION,
        "generated_at": generated_at,
        "generator": GENERATOR_PATH,
        "provenance": {
            "package": PACKAGE,
            "version": PACKAGE_VERSION,
            "license": PACKAGE_LICENSE,
            "model": "Rosetta 3",
            "model_code": EXPECTED_MODEL_CODE,
            "citation": CITATION,
            "inputs_derivation": INPUTS_DERIVATION,
            "columns": list(INPUT_COLUMNS),
        },
        "textures": textures,
    }


def serialize(artifact: dict) -> str:
    """Canonical byte-stable JSON text for the artifact (insertion-ordered)."""
    return json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def regenerate() -> tuple[dict, str]:
    """Build with the current UTC timestamp and write the artifact to disk."""
    artifact = build_artifact(_now_iso())
    text = serialize(artifact)
    ARTIFACT_PATH.write_bytes(text.encode("utf-8"))
    return artifact, sha256_of(text)


def check() -> int:
    """Rebuild in memory and compare against the committed artifact."""
    if not ARTIFACT_PATH.is_file():
        print(f"DRIFT: no committed artifact at {ARTIFACT_PATH}", file=sys.stderr)
        return 1
    committed_text = ARTIFACT_PATH.read_bytes().decode("utf-8")
    committed = json.loads(committed_text)
    # Reuse the committed timestamp so the clock cannot masquerade as drift.
    rebuilt_text = serialize(build_artifact(committed["generated_at"]))
    n_rows = len(committed.get("textures", {}))
    if rebuilt_text == committed_text:
        print(f"MATCH {n_rows} textures; sha256 {sha256_of(rebuilt_text)}")
        return 0
    print(
        f"DRIFT: regenerated artifact differs from {ARTIFACT_PATH} "
        f"({n_rows} committed rows). committed sha256 {sha256_of(committed_text)}, "
        f"regenerated sha256 {sha256_of(rebuilt_text)}. Run without --check to "
        "regenerate.",
        file=sys.stderr,
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="rebuild in memory and compare with the committed artifact; "
        "exit non-zero on drift without writing",
    )
    args = parser.parse_args(argv)

    if args.check:
        return check()

    artifact, digest = regenerate()
    n_rows = len(artifact["textures"])
    print(f"wrote {ARTIFACT_PATH}")
    print(f"rows {n_rows}")
    print(f"sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
