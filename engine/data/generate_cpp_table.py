"""Generators that project the shared data files into the other backends.

The engine keeps one copy of each parameter table in ``engine/data``. The C++
kernel cannot read a CSV at run time, so its table is generated from the same
source. This module is the only sanctioned way to change that table: edit the
CSV, regenerate, and let the tests prove the copies still agree.

    python -m engine.data.generate_cpp_table          # rewrite soil.cpp
    python -m engine.data.generate_cpp_table --check  # fail if stale

Why the C++ table is checked rather than trusted
-------------------------------------------------
A generator nobody runs becomes a fifth copy. ``--check`` is what makes the
relationship enforced: CI runs it, and a hand edit to ``soil.cpp`` fails the
build rather than quietly diverging.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from engine.data.soil_table import FINENESS_ORDER, SOIL_PARAMETERS

REPO_ROOT = Path(__file__).resolve().parents[2]
SOIL_CPP = REPO_ROOT / "engine" / "cpp_core" / "src" / "soil.cpp"

_HEADER = """// GENERATED FILE - do not edit by hand.
// Source of truth: engine/data/soil_vg_table.csv
// Regenerate with: python -m engine.data.generate_cpp_table
//
// Units: Ks is cm/hr here because the compiled kernel has always used it;
// the CSV stores cm/day. That conversion is the only difference for six of the
// seven rows this file carried before consolidation.
//
// Provenance: design assumption, unverified. The former Carsel & Parrish (1988)
// attribution is withdrawn because the Ks column is not monotone in texture
// fineness at two rows. Clay and sandy_clay_loam are marked disputed in the CSV.
// See engine/data/SOIL_TABLE_CONFLICTS.md.
constexpr TextureEntry kTextures[] = {"""

_COMMENT_ABOVE_TABLE = """// Parameters are generated from engine/data/soil_vg_table.csv, which every
// backend shares. The Carsel & Parrish (1988) attribution formerly quoted here
// is withdrawn: see engine/data/SOIL_TABLE_CONFLICTS.md."""

_LEGACY_COMMENT = (
    "// Typical parameters from Carsel & Parrish (1988) / Rosetta pedotransfer,\n"
    "// matching engine/hydroma/cpp_bridge/soil_physics_fast.py exactly."
)


def _number(value: float) -> str:
    """Shortest exact-enough form, so the diff stays readable."""
    text = f"{value:.10g}"
    return text


def render_table() -> str:
    rows = []
    for texture in FINENESS_ORDER:
        entry = SOIL_PARAMETERS[texture]
        params = ", ".join(
            (
                _number(entry["theta_r"]),
                _number(entry["theta_s"]),
                _number(entry["alpha"]),
                _number(entry["n"]),
                _number(entry["Ks"] / 24.0),
            )
        )
        key = f'"{texture}",'
        rows.append(f"    {{{key.ljust(20)}{{{params}}}}},")
    return _HEADER + "\n" + "\n".join(rows) + "\n};"


def current_table() -> str | None:
    """The generated block as it stands in soil.cpp, or None if absent."""
    if not SOIL_CPP.exists():
        return None
    text = SOIL_CPP.read_text(encoding="utf-8")
    match = re.search(r"// GENERATED FILE.*?^\};", text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None


def write_table() -> bool:
    """Rewrite soil.cpp. Returns True when the file changed."""
    text = SOIL_CPP.read_text(encoding="utf-8")
    desired = render_table()
    existing = current_table()
    if existing == desired:
        return False
    if existing is None:
        raise SystemExit(
            f"{SOIL_CPP} has no generated block. Add one with a "
            f"'{_HEADER.splitlines()[0]}' header so --check can find it."
        )
    text = text.replace(existing, desired, 1)
    if _LEGACY_COMMENT in text:
        text = text.replace(_LEGACY_COMMENT, _COMMENT_ABOVE_TABLE, 1)
    SOIL_CPP.write_text(text, encoding="utf-8", newline="\n")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.data.generate_cpp_table")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if soil.cpp is not in step with the CSV",
    )
    args = parser.parse_args(argv)

    if args.check:
        if current_table() is None:
            print(f"FAIL: {SOIL_CPP} carries no generated table block")
            return 1
        if current_table() != render_table():
            print(
                f"FAIL: {SOIL_CPP} is out of step with "
                f"engine/data/soil_vg_table.csv.\n"
                f"  regenerate with: python -m engine.data.generate_cpp_table"
            )
            return 1
        print(f"soil.cpp is in step with the CSV ({len(FINENESS_ORDER)} textures)")
        return 0

    if write_table():
        print(f"soil.cpp regenerated from the CSV: {len(FINENESS_ORDER)} textures")
    else:
        print("soil.cpp already in step")
    return 0


if __name__ == "__main__":
    sys.exit(main())
