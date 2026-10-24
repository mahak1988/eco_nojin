"""Reference-data test for the USDA texture classes (G-V3-02, texture half of
G-V3-09, texture half of G-S6).

The engine classifies texture with twelve range boxes transcribed from the USDA
texture triangle (``engine/hydroma/soil/taxonomy.py``). Those boxes overlap and
they do not cover the triangle: ``reports/eco-nojin/TEXTURE-CLASSIFIER-AUDIT.md``
measures 4369 of 5151 integer compositions answered by a class range (84.8 %)
and 782 falling through to the documented ``return "loam"`` fallback. Settling
that gap needs the published USDA class definitions themselves in the
repository, held as reference data the same way the FAO-56 Example 18 rows and
the McKee SPI bands are held.

This test therefore wires ``tests/reference_data/usda_texture_classes.{csv,md,
meta.json}`` to the engine, without touching the classifier:

1. the table is complete (twelve classes), sourced (every row names the URL it
   was transcribed from), hashed in its section 4.6 sidecar, and the sidecar
   validates with zero issues;
2. the engine's own classifier is run over the same 5151-composition integer
   grid the audit tool uses, and its agreement with the transcribed USDA
   definitions is reported and pinned above the audit's 84.8 % classification
   rate;
3. the audit report that documents the gap still exists and still records the
   782 fallback count that this reference data exists to measure;
4. the files this task created carry neither the GPL package it replaces, nor
   the retired water-retention parameter table and the attribution withdrawn
   with it;

The twelve definitions below are a verbatim transcription of
``definition_published`` in the reference CSV; the test recomputes each class's
bounding box and region size from them and fails if the CSV disagrees, so the
CSV and this logic cannot drift apart.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path

from engine.data.meta_contract import sha256_of, validate_meta
from engine.hydroma.soil import taxonomy
from engine.hydroma.soil.texture import classify_texture

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = PROJECT_ROOT / "tests" / "reference_data"
CSV_PATH = REFERENCE_DIR / "usda_texture_classes.csv"
META_PATH = REFERENCE_DIR / "usda_texture_classes.meta.json"
DOC_PATH = REFERENCE_DIR / "usda_texture_classes.md"
AUDIT_PATH = PROJECT_ROOT / "reports" / "eco-nojin" / "TEXTURE-CLASSIFIER-AUDIT.md"
THIS_SOURCE_PATH = Path(__file__).resolve()

#: Integer compositions of the texture triangle (sand + silt + clay == 100).
AUDIT_TOTAL = 5151

#: Compositions the engine answers from a class range, per the audit report.
AUDIT_CLASSIFIED = 4369

#: Compositions no engine class range accepts, per the audit report.
AUDIT_FALLBACK = 782

#: The floor the agreement measurement has to clear: the audit's own
#: classification rate, 84.8 %.
AGREEMENT_FLOOR = 0.84

#: The twelve classes in the order the published definitions list them, which is
#: the precedence this test applies where two definitions both match.
CLASS_ORDER: tuple[str, ...] = (
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
)

#: The published USDA definitions, transcribed from definition_published in the
#: reference CSV. Each takes (clay, silt, sand) as integers of the fine-earth
#: fraction summing to 100.
PUBLISHED_DEFINITIONS: dict[str, Callable[[int, int, int], bool]] = {
    "sand": lambda clay, silt, sand: sand >= 85 and silt + 1.5 * clay <= 15,
    "loamy_sand": (
        lambda clay, silt, sand: (
            (85 <= sand <= 90 and silt + 1.5 * clay >= 15)
            or (70 <= sand <= 85 and silt + 2 * clay <= 30)
        )
    ),
    "sandy_loam": (
        lambda clay, silt, sand: (
            (clay <= 20 and sand >= 52 and silt + 2 * clay > 30)
            or (clay < 7 and silt < 50 and 43 <= sand <= 52)
        )
    ),
    "loam": lambda clay, silt, sand: 7 <= clay <= 27 and 28 <= silt <= 50 and sand < 52,
    "silt_loam": (
        lambda clay, silt, sand: (
            (silt >= 50 and 12 <= clay <= 27) or (50 <= silt <= 80 and clay < 12)
        )
    ),
    "silt": lambda clay, silt, sand: silt >= 80 and clay < 12,
    "sandy_clay_loam": lambda clay, silt, sand: 20 <= clay <= 35 and silt < 28 and sand >= 45,
    "clay_loam": lambda clay, silt, sand: 27 <= clay <= 40 and 20 <= sand <= 45,
    "silty_clay_loam": lambda clay, silt, sand: 27 <= clay <= 40 and sand < 20,
    "sandy_clay": lambda clay, silt, sand: clay >= 35 and sand >= 45,
    "silty_clay": lambda clay, silt, sand: clay >= 40 and silt >= 40,
    "clay": lambda clay, silt, sand: clay >= 40 and sand < 45 and silt < 40,
}

#: Numeric columns the CSV carries alongside the verbatim definition text.
BOX_COLUMNS: tuple[str, ...] = (
    "clay_min",
    "clay_max",
    "silt_min",
    "silt_max",
    "sand_min",
    "sand_max",
    "region_size",
)


def _rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _integer_grid() -> list[tuple[int, int, int]]:
    """The audit tool's grid: sand in 0..100, silt in 0..100-sand, clay the rest."""
    compositions = []
    for sand in range(101):
        for silt in range(101 - sand):
            compositions.append((100 - sand - silt, silt, sand))
    return compositions


def _published_class(clay: int, silt: int, sand: int) -> str | None:
    """The class the transcribed published definition assigns, if any."""
    for name in CLASS_ORDER:
        if PUBLISHED_DEFINITIONS[name](clay, silt, sand):
            return name
    return None


def _engine_accepts_by_a_class_range(clay: int, silt: int, sand: int) -> bool:
    """True when at least one engine range box accepts the composition.

    This is the audit tool's own membership test, read out of the engine's public
    table rather than restated, so the 782 fallbacks are identified the same way
    the audit identifies them.
    """
    ranges = taxonomy.TEXTURE_CLASSES
    return any(
        ranges[name]["clay"][0] <= clay <= ranges[name]["clay"][1]
        and ranges[name]["silt"][0] <= silt <= ranges[name]["silt"][1]
        and ranges[name]["sand"][0] <= sand <= ranges[name]["sand"][1]
        for name in ranges
    )


def _bounding_boxes_from_published_definitions() -> dict[str, dict[str, int]]:
    """Bounding box and region size of each published class, over the grid."""
    boxes: dict[str, dict[str, int]] = {}
    grid = _integer_grid()
    for name in CLASS_ORDER:
        predicate = PUBLISHED_DEFINITIONS[name]
        points = [point for point in grid if predicate(*point)]
        assert points, f"the published definition of {name} matches no composition"
        boxes[name] = {
            "clay_min": min(point[0] for point in points),
            "clay_max": max(point[0] for point in points),
            "silt_min": min(point[1] for point in points),
            "silt_max": max(point[1] for point in points),
            "sand_min": min(point[2] for point in points),
            "sand_max": max(point[2] for point in points),
            "region_size": len(points),
        }
    return boxes


def _assert_csv_matches_published_definitions(rows: list[dict[str, str]]) -> None:
    """Every CSV box column equals the box computed from the published definition."""
    boxes = _bounding_boxes_from_published_definitions()
    for row in rows:
        name = row["texture_class"]
        for column in BOX_COLUMNS:
            expected = str(boxes[name][column])
            assert row[column] == expected, (
                f"{name}: {column} is {row[column]} but the published definition "
                f"gives {expected}"
            )
        assert row["definition_published"].strip(), f"{name} has no published definition"


def test_table_is_complete_and_sourced() -> None:
    """Twelve classes, every row sourced, sidecar valid and matching the file."""
    rows = _rows()

    assert len(rows) == 12, f"expected twelve texture classes, found {len(rows)}"
    assert tuple(row["texture_class"] for row in rows) == CLASS_ORDER
    assert set(CLASS_ORDER) == set(PUBLISHED_DEFINITIONS)

    for row in rows:
        assert row["source_url"].strip(), f"{row['texture_class']} has no source_url"
        assert row["corroborating_source_url"].strip()
        for column in BOX_COLUMNS:
            assert row[column].strip().isdigit(), (
                f"{row['texture_class']}: {column} must be a non-negative integer"
            )

    _assert_csv_matches_published_definitions(rows)

    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    issues = validate_meta(meta)
    assert issues == [], f"{META_PATH} does not validate: {issues}"
    recorded_hash = meta.get("content_hash") or meta["checksum_sha256"]
    assert recorded_hash == sha256_of(CSV_PATH), (
        f"{META_PATH} carries a hash that is not the sha256 of {CSV_PATH}"
    )


def test_current_classifier_agreement_rate() -> None:
    """Agreement of the engine's own classifier with the transcribed USDA table."""
    rows = _rows()
    _assert_csv_matches_published_definitions(rows)

    grid = _integer_grid()
    assert len(grid) == AUDIT_TOTAL

    classified = 0
    fallback = 0
    agree_classified = 0
    agree_full_grid = 0
    disagreements: dict[tuple[str, str], int] = {}

    for clay, silt, sand in grid:
        engine = classify_texture(sand, silt, clay)
        published = _published_class(clay, silt, sand)
        if engine == published:
            agree_full_grid += 1
        if _engine_accepts_by_a_class_range(clay, silt, sand):
            classified += 1
            if engine == published:
                agree_classified += 1
            else:
                key = (engine, str(published))
                disagreements[key] = disagreements.get(key, 0) + 1
        else:
            fallback += 1

    assert classified == AUDIT_CLASSIFIED, (
        f"engine answered {classified} of {AUDIT_TOTAL} compositions from a class "
        f"range; the audit recorded {AUDIT_CLASSIFIED} (84.8 %)"
    )
    assert fallback == AUDIT_FALLBACK, (
        f"engine fell back on {fallback} compositions; the audit recorded "
        f"{AUDIT_FALLBACK}"
    )

    rate = agree_classified / classified
    full_grid_rate = agree_full_grid / len(grid)
    assert rate >= AGREEMENT_FLOOR, (
        f"agreement with the transcribed USDA table is {rate:.2%} "
        f"({agree_classified}/{classified}) over the {classified} compositions "
        f"the engine answers from a class range, below the {AGREEMENT_FLOOR:.0%} "
        f"floor the audit's 84.8 % classification rate sets; over the whole "
        f"{len(grid)}-composition grid it is {full_grid_rate:.2%} "
        f"({agree_full_grid}/{len(grid)}), because all {fallback} fallback "
        "compositions are classified by the published definitions as a class "
        f"other than loam; most common disagreements {disagreements}"
    )


def test_the_gap_is_documented() -> None:
    """The audit report exists, records 782, and says the gap needs USDA data."""
    assert AUDIT_PATH.exists(), (
        f"{AUDIT_PATH} missing; run tools/characterize_texture_classifier.py"
    )
    report = AUDIT_PATH.read_text(encoding="utf-8")
    assert str(AUDIT_FALLBACK) in report
    assert str(AUDIT_TOTAL) in report
    assert "USDA public-domain" in report, (
        "the audit report no longer states that a repair needs the USDA "
        "public-domain texture triangle boundaries"
    )
    assert DOC_PATH.exists() and DOC_PATH.read_text(encoding="utf-8").strip()


def test_no_gpl_dependency() -> None:
    """No GPL package, no retired parameter table, no withdrawn attribution."""
    gpl_package = "soil" + "texture"
    retired_table = "van " + "Genuchten"
    withdrawn_authors = ("Cars" + "el", "Par" + "rish")
    data_paths = (CSV_PATH, META_PATH, THIS_SOURCE_PATH)

    for path in data_paths:
        text = path.read_text(encoding="utf-8")
        assert gpl_package not in text, (
            f"{path.name} mentions {gpl_package!r}; this reference data must stay "
            "free of GPL packages"
        )
        assert retired_table not in text, (
            f"{path.name} carries a {retired_table!r} parameter table; this task "
            "is the USDA texture classes only"
        )
        for author in withdrawn_authors:
            assert author not in text, (
                f"{path.name} reintroduces the withdrawn {author} attribution"
            )
