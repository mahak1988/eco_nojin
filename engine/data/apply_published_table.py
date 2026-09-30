"""One command to close the four disputed rows once the publication is in hand.

    python -m engine.data.apply_published_table --from published.csv

``published.csv`` needs the columns ``texture`` and ``ks_cm_per_day``, and
optionally ``theta_r``, ``theta_s``, ``alpha``, ``n`` and ``reference``. The
script will not accept a table that violates the fineness ordering of saturated
conductivity, because accepting one would replace a recorded defect with a
different one and leave the record claiming to be verified.

It validates, writes, re-derives the admissible intervals, flips the status of
the rows it changed to ``verified`` with the citation supplied, and prints what
still remains disputed.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import sys
from pathlib import Path

TABLE = Path(__file__).resolve().parent / "soil_vg_table.csv"

REQUIRED = ("texture", "ks_cm_per_day")
OPTIONAL = ("theta_r", "theta_s", "alpha", "n", "reference")

FINENESS = [
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_clay_loam",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
]


def read_published(path: Path) -> dict[str, dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SystemExit(f"{path} is empty")
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        raise SystemExit(f"{path} is missing the column(s) {missing}")
    return {r["texture"]: r for r in rows}


def merged_column(published: dict[str, dict]) -> dict[str, float]:
    """The supplied values laid over the current table.

    The ordering has to be checked on the merged column, not on the supplied
    rows alone. A partial transcription naming only sand and clay contains no
    adjacent pair at all, so an adjacency check over the supplied rows would
    find nothing to complain about and the disputed values would be written.
    """
    merged: dict[str, float] = {}
    with TABLE.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            merged[row["texture"]] = float(row["ks_cm_per_day"])
    for texture, row in published.items():
        try:
            merged[texture] = float(row["ks_cm_per_day"])
        except (TypeError, ValueError):
            raise SystemExit(f"{texture}: ks_cm_per_day is not a number") from None
    return merged


def check_against_physics(
    published: dict[str, dict], base: dict[str, float] | None = None
) -> list[str]:
    """Reject a table that itself breaks the fineness ordering.

    This is the check that would have caught the table already in the
    repository. Running it on the current values reports the four disputed rows,
    which is the point: the tool is also a validator.
    """
    if base is None:
        base = {}
        with TABLE.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                base[row["texture"]] = float(row["ks_cm_per_day"])
    ks = dict(base)
    for texture, row in published.items():
        try:
            ks[texture] = float(row["ks_cm_per_day"])
        except (TypeError, ValueError):
            raise SystemExit(f"{texture}: ks_cm_per_day is not a number") from None
    problems: list[str] = []
    for coarse, fine in itertools.pairwise(FINENESS):
        if coarse in ks and fine in ks and ks[fine] > ks[coarse]:
            problems.append(
                f"{fine} ({ks[fine]:g}) conducts more than {coarse} "
                f"({ks[coarse]:g}), which fineness forbids"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.data.apply_published_table")
    parser.add_argument(
        "--from",
        dest="source",
        type=Path,
        required=True,
        help="CSV transcribed from the source publication",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and report without writing",
    )
    args = parser.parse_args(argv)

    published = read_published(args.source)
    problems = check_against_physics(published)
    if problems:
        print("REFUSED: the supplied table breaks the fineness ordering of")
        print("saturated conductivity, so it cannot be recorded as verified:\n")
        for line in problems:
            print(f"  {line}")
        print("\nNothing was written. Transcribe the source again; if the source")
        print("itself is ordered this way, the ordering claim is wrong and this")
        print("check should be revisited rather than the table.")
        return 1

    with TABLE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fieldnames = list(rows[0].keys())
    index = {r["texture"]: r for r in rows}

    reference = next(
        (r.get("reference", "").strip() for r in published.values() if r.get("reference")),
        "",
    )
    if not reference:
        print("REFUSED: no row carries a 'reference'. A value with no citation")
        print("is exactly what this table already had; do not repeat it.")
        return 1

    changed: list[str] = []
    for texture, source in published.items():
        if texture not in index:
            print(f"  {texture}: not in the table, ignored")
            continue
        row = index[texture]
        for column in ("ks_cm_per_day", *OPTIONAL[:4]):
            if (
                column in source
                and str(source[column]).strip()
                and str(row[column]) != str(source[column]).strip()
            ):
                row[column] = str(source[column]).strip()
                if column == "ks_cm_per_day":
                    changed.append(texture)
        row["provenance"] = f"transcribed from {reference}"
        row["status"] = "verified"

    if not changed:
        print("no conductivity value changed; the table may already be current")

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    # Re-derive the intervals, which depend on the whole column.
    ks = {r["texture"]: float(r["ks_cm_per_day"]) for r in rows}
    still: list[str] = []
    for position, texture in enumerate(FINENESS):
        row = index[texture]
        lower = ks[FINENESS[position + 1]] if position + 1 < len(FINENESS) else 0.0
        upper = ks[FINENESS[position - 1]] if position else float("inf")
        row["ks_admissible_min"] = f"{lower:.4f}"
        row["ks_admissible_max"] = "" if upper == float("inf") else f"{upper:.4f}"
        if lower > upper or not (lower <= ks[texture] <= upper):
            still.append(texture)

    with TABLE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {TABLE.name}: {len(changed)} conductivity value(s) changed, {len(rows)} rows")
    if still:
        print(f"still disputed: {still}")
    else:
        print("no row violates the fineness ordering any more")
    print()
    print("next: python -m engine.data.generate_cpp_table")
    print("      then rebuild the extension and regenerate the baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
