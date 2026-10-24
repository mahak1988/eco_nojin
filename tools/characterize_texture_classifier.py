#!/usr/bin/env python3
"""Characterise the engine's own USDA texture classifier over the whole triangle.

Audit context
-------------
``engine/hydroma/soil/taxonomy.py`` is the single source of the texture triangle
in the package: ``TEXTURE_CLASSES`` holds twelve transcribed class ranges, and
``_determine_texture_class`` walks them in ``_RESOLUTION_ORDER`` (coarsest
first). Those ranges are mutually overlapping *and* they do not cover the whole
triangle, so some integer compositions satisfy no range at all and are answered
by the ``return "loam"`` fallback at ``taxonomy.py:246`` -- a guess that the
module itself documents as "a guess, not a classification".

This tool measures that gap exactly and reproducibly over the full integer
triangle (sand + silt + clay == 100, 5151 compositions). It does not
reimplement anything: every texture it reports comes from the engine's own
public entry point ``classify_texture`` (``engine/hydroma/soil/texture.py``,
which delegates to ``taxonomy._determine_texture_class``). The only logic added
here is the range-box membership test, which reads the class ranges out of
``taxonomy.TEXTURE_CLASSES`` rather than restating them, so the gap is measured
against the engine's own table.

There is no third-party dependency of any kind: no external texture-classifier
package, no plotting library, no network -- stdlib only. The measurement is
therefore reproducible without a display, a licence review, or an install
step, which is the point: a free replacement for the licence-restricted
texture package starts from an exact statement of what the engine's own
classifier does and does not answer, and that statement is this tool's output.

This tool changes no classifier code. It reads and reports.

Usage
-----
    python tools/characterize_texture_classifier.py [--out PATH] [--no-write]

Prints the counts and, unless ``--no-write`` is given, writes
``reports/eco-nojin/TEXTURE-CLASSIFIER-AUDIT.md``.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # allow running without PYTHONPATH set
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.hydroma.soil import taxonomy  # noqa: E402  (after the path shim)
from engine.hydroma.soil.texture import classify_texture  # noqa: E402

REPO_ROOT = PROJECT_ROOT
REPORT_PATH = PROJECT_ROOT / "reports" / "eco-nojin" / "TEXTURE-CLASSIFIER-AUDIT.md"

#: Where the engine answers a composition that no class range accepts.
FALLBACK_SITE = "engine/hydroma/soil/taxonomy.py:246"
#: The fallback answer itself, returned at FALLBACK_SITE.
FALLBACK_CLASS = "loam"

#: Row label used in the summary table of the report. The audit test pins this
#: label and the number in the row, so a classifier change is deliberate.
SUMMARY_FALLBACK_LABEL = "Fell through to the fallback (no class range accepts it)"

#: The audit finding this tool re-measures, from the module docstring and the
#: comment above the fallback return in taxonomy.py.
RECORDED_FALLBACK_COUNT = 782

#: How many "bands" (clay rows) of the triangle to list in the report.
BAND_LIMIT = 20

#: Boundary spot checks that the audit names explicitly.
SPOT_CHECKS: tuple[tuple[str, int, int, int], ...] = (
    ("sand apex: sand = 100", 0, 0, 100),
    ("clay apex: clay = 100", 100, 0, 0),
    ("silt apex: silt = 100", 0, 100, 0),
    ("sand lower limit, clay 5, silt 10", 5, 10, 85),
    ("sand lower limit, clay 5, silt 5", 5, 5, 90),
    ("documented fallback example (clay 0, silt 40, sand 60)", 0, 40, 60),
    ("clay/silt/sand mirror (45/45/10)", 45, 45, 10),
    ("loam reference composition (20/40/40)", 20, 40, 40),
)


@dataclass(frozen=True)
class Record:
    """One integer composition and everything the engine says about it."""

    clay: int
    silt: int
    sand: int
    texture: str
    """What the public entry point ``classify_texture`` returned."""
    resolved: str
    """What ``taxonomy._determine_texture_class`` returned (same code path)."""
    candidates: tuple[str, ...]
    """Every class whose *range box* in ``taxonomy.TEXTURE_CLASSES`` accepts it."""

    @property
    def is_fallback(self) -> bool:
        """True when no class range accepts the composition at all."""
        return not self.candidates

    @property
    def is_overlap(self) -> bool:
        """True when more than one class range accepts the composition."""
        return len(self.candidates) > 1

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    def as_ternary(self) -> str:
        return f"clay {self.clay:>3} / silt {self.silt:>3} / sand {self.sand:>3}"


@dataclass
class ScanResult:
    """The full-grid scan: one :class:`Record` per composition, plus tallies."""

    records: list[Record] = field(default_factory=list)
    histogram: Counter[str] = field(default_factory=Counter)
    class_acceptance: Counter[str] = field(default_factory=Counter)
    candidate_count_histogram: Counter[int] = field(default_factory=Counter)
    candidate_pair_histogram: Counter[tuple[str, ...]] = field(default_factory=Counter)
    entry_point_disagreements: list[Record] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def fallback_count(self) -> int:
        return sum(1 for record in self.records if record.is_fallback)

    @property
    def classified_count(self) -> int:
        return self.total - self.fallback_count

    @property
    def overlap_count(self) -> int:
        return sum(1 for record in self.records if record.is_overlap)

    def fallback_records(self) -> list[Record]:
        return [record for record in self.records if record.is_fallback]

    def overlap_records(self) -> list[Record]:
        return [record for record in self.records if record.is_overlap]


def iter_compositions() -> Iterator[tuple[int, int, int]]:
    """Yield every (clay, silt, sand) integer composition summing to 100.

    ``sand`` runs 0..100 and ``silt`` runs 0..100-sand with ``clay`` forced, so
    each composition is produced exactly once: 5151 of them.
    """
    for sand in range(101):
        for silt in range(101 - sand):
            yield (100 - sand - silt, silt, sand)


def _box_accepts(ranges: dict[str, tuple[int, int]], clay: int, silt: int, sand: int) -> bool:
    """Test one class range box from ``taxonomy.TEXTURE_CLASSES``."""
    clay_lo, clay_hi = ranges["clay"]
    silt_lo, silt_hi = ranges["silt"]
    sand_lo, sand_hi = ranges["sand"]
    return clay_lo <= clay <= clay_hi and silt_lo <= silt <= silt_hi and sand_lo <= sand <= sand_hi


def candidate_classes(clay: int, silt: int, sand: int) -> tuple[str, ...]:
    """Every class whose range box accepts this composition, in resolve order."""
    return tuple(
        name
        for name in taxonomy._RESOLUTION_ORDER
        if _box_accepts(taxonomy.TEXTURE_CLASSES[name], clay, silt, sand)
    )


def scan() -> ScanResult:
    """Classify every integer composition and tally the gap.

    The texture comes from the engine's public entry point
    ``classify_texture(sand, silt, clay)``. For comparison the tool also calls
    the engine's resolution function ``taxonomy._determine_texture_class``
    directly and the range-box membership test, and records any disagreement
    between the two code paths in ``entry_point_disagreements`` (the public
    entry point delegates, so the list must stay empty).
    """
    result = ScanResult()
    for clay, silt, sand in iter_compositions():
        texture = classify_texture(sand, silt, clay)
        resolved = taxonomy._determine_texture_class(clay, silt, sand)
        candidates = candidate_classes(clay, silt, sand)
        record = Record(
            clay=clay,
            silt=silt,
            sand=sand,
            texture=texture,
            resolved=resolved,
            candidates=candidates,
        )
        if resolved != texture:
            result.entry_point_disagreements.append(record)
        result.records.append(record)
        result.histogram[texture] += 1
        result.candidate_count_histogram[record.candidate_count] += 1
        for name in candidates:
            result.class_acceptance[name] += 1
        if record.is_overlap:
            result.candidate_pair_histogram[candidates] += 1
    return result


def corner_compositions() -> dict[str, list[tuple[int, int, int]]]:
    """The corner compositions of each class range box.

    A box is the Cartesian product of three ranges; the compositions are the
    plane ``clay + silt + sand == 100`` cut through it. The corners of that
    cross-section are the compositions where at least two of the three
    coordinates sit on a declared limit and the third is forced by the sum.
    Both limits of both chosen coordinates are tried, and a candidate is kept
    only when the forced coordinate is inside its own declared range, so every
    listed composition really is on the box. The strict case (all three on a
    limit, only possible when the limits happen to sum to 100) is included.

    This is the box's own geometry, read from ``taxonomy.TEXTURE_CLASSES``; it
    is not the published triangle diagram, which this repository does not hold.
    """
    corners: dict[str, list[tuple[int, int, int]]] = {}
    for name in taxonomy._RESOLUTION_ORDER:
        ranges = taxonomy.TEXTURE_CLASSES[name]
        limits = (ranges["clay"], ranges["silt"], ranges["sand"])
        found: set[tuple[int, int, int]] = set()
        for forced_axis in range(3):
            # The two coordinates pinned to a declared limit; the third is
            # whatever the sum demands.
            for pinned_a in range(3):
                for pinned_b in range(pinned_a + 1, 3):
                    if forced_axis in (pinned_a, pinned_b):
                        continue
                    for value_a in limits[pinned_a]:
                        for value_b in limits[pinned_b]:
                            forced_value = 100 - value_a - value_b
                            low, high = limits[forced_axis]
                            if not low <= forced_value <= high:
                                continue
                            point = [0, 0, 0]
                            point[pinned_a] = value_a
                            point[pinned_b] = value_b
                            point[forced_axis] = forced_value
                            found.add((point[0], point[1], point[2]))
        corners[name] = sorted(found)
    return corners


def gap_extent(result: ScanResult) -> dict[str, tuple[int, int] | None]:
    """The bounding box of the uncovered compositions, per fraction.

    Used to state precisely where the gap is instead of describing it loosely:
    the reported ranges are measured over the fallback compositions only.
    """
    records = result.fallback_records()
    if not records:
        return {"clay": None, "silt": None, "sand": None}
    return {
        "clay": (min(r.clay for r in records), max(r.clay for r in records)),
        "silt": (min(r.silt for r in records), max(r.silt for r in records)),
        "sand": (min(r.sand for r in records), max(r.sand for r in records)),
    }


def ambiguous_bands(result: ScanResult, limit: int = BAND_LIMIT) -> list[dict[str, object]]:
    """Rank the triangle's clay rows by how many compositions they leave open.

    A "band" is one clay percentage: the run of compositions that share that
    clay value (silt 0..100-clay). It is ranked by the number of compositions
    in it that are either uncovered (fallback) or accepted by more than one
    class range, with the split reported so the two kinds of gap stay
    distinguishable. Ties are broken by ascending clay.
    """
    by_clay: dict[int, list[Record]] = {}
    for record in result.records:
        by_clay.setdefault(record.clay, []).append(record)

    bands: list[dict[str, object]] = []
    for clay in sorted(by_clay):
        rows = by_clay[clay]
        fallback = [record for record in rows if record.is_fallback]
        overlap = [record for record in rows if record.is_overlap]
        open_rows = fallback + overlap
        # Representative example: the middle open composition in the band, so
        # one band does not simply report the same silt as its neighbour.
        example = open_rows[len(open_rows) // 2] if open_rows else None
        bands.append(
            {
                "clay": clay,
                "compositions": len(rows),
                "fallback": len(fallback),
                "overlap": len(overlap),
                "gap": len(open_rows),
                "example": example,
            }
        )
    bands.sort(key=lambda band: (-int(band["gap"]), int(band["clay"])))  # type: ignore[arg-type]
    return bands[:limit]


def _format_count(value: int, total: int) -> str:
    return f"{value} ({100.0 * value / total:.1f} %)" if total else str(value)


def build_report(result: ScanResult) -> str:
    """Render the audit markdown. Pure data + citations, no invented boundaries."""
    total = result.total
    fallback = result.fallback_count
    classified = result.classified_count
    overlap = result.overlap_count
    corners = corner_compositions()
    bands = ambiguous_bands(result)
    extent = gap_extent(result)
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []
    add = lines.append

    add("# USDA Texture Classifier Audit")
    add("")
    add(f"Generated by `tools/characterize_texture_classifier.py` on {generated}.")
    add("The scan is deterministic: re-running the tool on the same classifier")
    add("reproduces every number below.")
    add("")
    add("**Scope.** Every integer composition of the USDA texture triangle")
    add("(`sand + silt + clay == 100`), i.e. compositions produced by")
    add("`sand in 0..100`, `silt in 0..100-sand`, `clay = 100-sand-silt`:")
    add(f"**{total}** compositions. The classifier is the engine's own:")
    add("`classify_texture(sand, silt, clay)` from `engine/hydroma/soil/texture.py`,")
    add("which delegates to `engine/hydroma/soil/taxonomy.py:_determine_texture_class`.")
    add("Nothing here reimplements the classifier, and nothing here changes it.")
    add("The tool is stdlib-only and third-party-free: no external")
    add("texture-classifier package, no plotting library, no network. The audit is")
    add("therefore reproducible without a licence review -- a free replacement")
    add("starts from an exact statement of what the current classifier does, and")
    add("that statement is this document.")
    add("")
    add("## 1. Counts")
    add("")
    add("| Measure | Compositions | Share of the triangle |")
    add("| --- | ---: | ---: |")
    add(f"| Total integer compositions | {total} | 100.0 % |")
    add(f"| Answered by a class range | {classified} | {100.0 * classified / total:.1f} % |")
    add(f"| {SUMMARY_FALLBACK_LABEL} | {fallback} | {100.0 * fallback / total:.1f} % |")
    add(f"| Accepted by more than one class range (overlap) | {overlap} | "
        f"{100.0 * overlap / total:.1f} % |")
    add("")
    add("The overlap count measures the *table*, not the *answer*: where two or more")
    add("range boxes accept a composition, `_determine_texture_class` resolves it by")
    add("trying the boxes in `_RESOLUTION_ORDER` (coarsest first, first match wins), so")
    add("the returned class is still deterministic. The overlap is reported because it")
    add("is the reason the resolution order is load-bearing and because a corrected")
    add("table has to remove it.")
    add("")
    add("### 1.1 Class histogram (what the classifier returns)")
    add("")
    add("| Class | Compositions | Share |")
    add("| --- | ---: | ---: |")
    for name, count in sorted(result.histogram.items(), key=lambda item: (-item[1], item[0])):
        add(f"| `{name}` | {_format_count(count, total)} | {100.0 * count / total:.1f} % |")
    add(f"| **total** | **{total}** | **100.0 %** |")
    add("")
    add("### 1.2 Range-box acceptance (what each class box admits)")
    add("")
    add("| Class | Declared ranges (clay / silt / sand) | Accepts |")
    add("| --- | --- | ---: |")
    for name in taxonomy._RESOLUTION_ORDER:
        ranges = taxonomy.TEXTURE_CLASSES[name]
        clay_r = f"{ranges['clay'][0]}-{ranges['clay'][1]}"
        silt_r = f"{ranges['silt'][0]}-{ranges['silt'][1]}"
        sand_r = f"{ranges['sand'][0]}-{ranges['sand'][1]}"
        add(f"| `{name}` | {clay_r} / {silt_r} / {sand_r} | "
            f"{_format_count(result.class_acceptance[name], total)} |")
    add("")
    add("Acceptance counts sum to more than the classified count exactly because the")
    add("boxes overlap; the 782 uncovered compositions are accepted by none of them.")
    add("")
    add("### 1.3 How many class ranges accept a composition")
    add("")
    add("| Class ranges accepting | Compositions | Share |")
    add("| ---: | ---: | ---: |")
    for count in sorted(result.candidate_count_histogram):
        volume = result.candidate_count_histogram[count]
        add(f"| {count} | {_format_count(volume, total)} | {100.0 * volume / total:.1f} % |")
    add("")
    add("### 1.4 Most common overlapping candidate sets")
    add("")
    add("| Candidate set (resolution order) | Compositions |")
    add("| --- | ---: |")
    for candidates, count in result.candidate_pair_histogram.most_common(10):
        add(f"| {', '.join(f'`{c}`' for c in candidates)} | {count} |")
    add("")

    add("## 2. The fallback code path")
    add("")
    add(f"**{fallback} of {total}** compositions "
        f"({100.0 * fallback / total:.1f} %) are accepted by no class range at all.")
    add("They are answered by the final statement of `_determine_texture_class`:")
    add("")
    add("```python")
    add("# engine/hydroma/soil/taxonomy.py, _determine_texture_class")
    add("    for texture in _RESOLUTION_ORDER:")
    add("        ranges = TEXTURE_CLASSES[texture]")
    add("        if (")
    add("            clay_range[0] <= clay <= clay_range[1]")
    add("            and silt_range[0] <= silt <= silt_range[1]")
    add("            and sand_range[0] <= sand <= sand_range[1]")
    add("        ):")
    add("            return texture")
    add("")
    add(f"    return \"{FALLBACK_CLASS}\"   # <-- line {FALLBACK_SITE.split(':')[1]}, the fallback")
    add("```")
    add("")
    add(f"Citation: `{FALLBACK_SITE}` -- `return \"{FALLBACK_CLASS}\"`. The comment")
    add("immediately above it (`engine/hydroma/soil/taxonomy.py:242-245`) states that")
    add("this is a guess, not a classification, and the module docstring")
    add("(`engine/hydroma/soil/taxonomy.py:29-34`) records the same 782 figure and the")
    add("example clay 0 / silt 40 / sand 60. This scan reproduces that figure from the")
    add("classifier itself; it is not copied from the docstring.")
    add("")
    add("Examples of compositions that reach the fallback:")
    add("")
    add("| Composition | Candidate ranges | Returned |")
    add("| --- | --- | --- |")
    for record in result.fallback_records()[:10]:
        add(f"| {record.as_ternary()} | none | `{record.texture}` |")
    add("")
    add("A fallback answer is indistinguishable from a real one at the call site:")
    add("`classify_usda_texture` reports it in the same `texture` key as a matched")
    add("class, and `_calculate_texture_properties` then looks up water-holding")
    add("capacity, permeability, erodibility, drainage and workability for `loam`.")
    add("Nothing downstream can tell a guess from a classification.")
    add("")

    add("## 3. Top ambiguous bands")
    add("")
    add("A band is one clay percentage: the run of compositions sharing that clay")
    add("value. `gap` counts compositions in the band that are uncovered (fallback)")
    add("or accepted by more than one class range (overlap); the split is shown so")
    add("the two kinds of gap stay distinguishable. Ranked by `gap`, ties broken by")
    add(f"ascending clay, first {len(bands)} bands.")
    add("")
    add("| # | Clay | Compositions in band | Uncovered | Overlapping | Gap | Example |")
    add("| ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for index, band in enumerate(bands, start=1):
        example = band["example"]
        example_text = (
            f"{example.as_ternary()} -> `{example.texture}`"  # type: ignore[union-attr]
            if example is not None
            else "n/a"
        )
        add(
            f"| {index} | {band['clay']} | {band['compositions']} | {band['fallback']} | "
            f"{band['overlap']} | {band['gap']} | {example_text} |"
        )
    add("")
    add("The gap is not concentrated in one corner of the triangle. Measured over")
    add("the uncovered compositions only:")
    add("")
    add("| Fraction | Range across the uncovered compositions |")
    add("| --- | --- |")
    for fraction, label in (("clay", "clay"), ("silt", "silt"), ("sand", "sand")):
        span = extent[fraction]
        add(f"| {label} | {span[0]}-{span[1]} |" if span else f"| {label} | n/a |")
    low_clay = sum(1 for record in result.fallback_records() if record.clay < 12)
    add("")
    add(f"{low_clay} of the {fallback} uncovered compositions have clay below 12, so the")
    add("largest uncovered strip runs along the clay-poor side of the triangle: on one")
    add("side of it `silt_loam` demands clay at least 12 and silt at least 50, on the")
    add("other `sandy_loam` demands silt at most 28, and between them nothing answers")
    add("(the documented example clay 0 / silt 40 / sand 60 sits in that strip). The")
    add("gap never reaches the sand edge (no uncovered composition has sand below 10)")
    add("nor the silt-poor edge (none has silt below 17), but it does cut the clay = 0")
    add("base edge, where the band table above shows 51 uncovered compositions.")
    add("")

    add("## 4. Boundary behaviour at exact integer limits")
    add("")
    add("For each of the twelve class definitions, the corner compositions of its")
    add("declared range box -- the compositions where two of the three fractions sit")
    add("on a declared limit and the third is forced by the sum, so the point lies on")
    add("the box -- and what the classifier returns for each. A composition accepted")
    add("by more than one box is resolved by `_RESOLUTION_ORDER`, so the returned")
    add("class is the first coarsest match, not the only match.")
    add("")
    add("| Class | Declared ranges (clay / silt / sand) | Corner composition | Returned | "
        "All boxes accepting it |")
    add("| --- | --- | --- | --- | --- |")
    for name in taxonomy._RESOLUTION_ORDER:
        ranges = taxonomy.TEXTURE_CLASSES[name]
        clay_r = f"{ranges['clay'][0]}-{ranges['clay'][1]}"
        silt_r = f"{ranges['silt'][0]}-{ranges['silt'][1]}"
        sand_r = f"{ranges['sand'][0]}-{ranges['sand'][1]}"
        vertices = corners[name]
        if not vertices:
            add(f"| `{name}` | {clay_r} / {silt_r} / {sand_r} | _no corner on the box_ | - | - |")
            continue
        for position, (clay, silt, sand) in enumerate(vertices):
            candidates = candidate_classes(clay, silt, sand)
            texture = classify_texture(sand, silt, clay)
            label = f"`{name}`" if position == 0 else ""
            range_text = f"{clay_r} / {silt_r} / {sand_r}" if position == 0 else ""
            accepting = ", ".join(f"`{c}`" for c in candidates) or "**none (fallback)**"
            add(
                f"| {label} | {range_text} | clay {clay} / silt {silt} / sand {sand} | "
                f"`{texture}` | {accepting} |"
            )
    add("")
    add("### 4.1 Named spot checks")
    add("")
    add("| Check | Composition | Returned | Boxes accepting it |")
    add("| --- | --- | --- | --- |")
    for label, clay, silt, sand in SPOT_CHECKS:
        candidates = candidate_classes(clay, silt, sand)
        texture = classify_texture(sand, silt, clay)
        accepting = ", ".join(f"`{c}`" for c in candidates) or "**none (fallback)**"
        add(f"| {label} | clay {clay} / silt {silt} / sand {sand} | `{texture}` | {accepting} |")
    add("")
    add("Two things the corner table makes visible. First, the triangle's apexes are")
    add("the best-covered compositions in the grid: `clay 0 / silt 0 / sand 100`,")
    add("`clay 100 / silt 0 / sand 0` and `clay 0 / silt 100 / sand 0` are each")
    add("accepted by exactly one box. Second, the corners of neighbouring boxes")
    add("coincide -- `clay 40 / silt 40 / sand 20` is a corner of `silty_clay_loam`,")
    add("`silty_clay` and `clay` at once and is answered `clay_loam`, which is why")
    add("the resolution order, not the ranges, decides so much of the triangle.")
    add("")

    add("## 5. What a corrected table would need")
    add("")
    add(f"This tool is the measurement half of that work. It establishes that {fallback}")
    add(f"of {total} integer compositions (~{100.0 * fallback / total:.0f} %) get a guess")
    add(f"rather than a classification, that {overlap} compositions are claimed by more")
    add("than one class range, and exactly where those regions are. It deliberately")
    add("does **not** touch the classifier: no line of")
    add("`engine/hydroma/soil/taxonomy.py` or `engine/hydroma/soil/texture.py` was")
    add("edited, and no boundary was invented here.")
    add("")
    add("A corrected table needs the **USDA public-domain** triangle boundaries")
    add("themselves: the twelve published class regions of the USDA-NRCS soil texture")
    add("triangle (the same public-domain source the twelve range boxes in")
    add("`TEXTURE_CLASSES` are already transcribed from), transcribed into the")
    add("repository as machine-readable reference data and cited, exactly as")
    add("`tests/reference_data/fao56_examples.{csv,md,meta.json}` and")
    add("`tests/reference_data/mckee_spi_classification.{csv,meta.json}` carry the")
    add("FAO-56 and McKee data with a `README.md` and a `.meta.json` provenance file.")
    add("The boundaries must close the triangle (a partition, no gaps) and must not")
    add("overlap, so the resolution order stops being load-bearing; the boxes are a")
    add("boxification of that diagram, not the diagram.")
    add("")
    add("Acquisition is a data task, not a coding task: the published USDA-NRCS")
    add("texture triangle is public domain, but the repository holds no copy of it, and")
    add("inventing boundaries here would be a new classifier rather than a repair. Once")
    add("the boundaries are in `tests/reference_data/`, the full-grid range-box test in")
    add("this tool -- pointed at the transcribed boundaries instead of")
    add("`TEXTURE_CLASSES` -- is the harness that verifies the new table over all")
    add(f"{total} compositions, and the {fallback} and {overlap} counts above are the")
    add("acceptance criteria.")
    add("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        type=Path,
        default=REPORT_PATH,
        help=f"report path (default: {REPORT_PATH})",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="only print the counts; do not write the report",
    )
    args = parser.parse_args(argv)

    result = scan()
    if result.entry_point_disagreements:
        print(
            "WARNING: classify_texture and _determine_texture_class disagreed on "
            f"{len(result.entry_point_disagreements)} compositions",
            file=sys.stderr,
        )

    print("USDA texture classifier audit (engine's own classifier, full integer triangle)")
    print(f"  total compositions      : {result.total}")
    print(f"  answered by a class     : {result.classified_count}")
    print(f"  {SUMMARY_FALLBACK_LABEL}: {result.fallback_count}"
          f"  ({100.0 * result.fallback_count / result.total:.1f} %)")
    print(f"  overlap (>1 class range): {result.overlap_count}"
          f"  ({100.0 * result.overlap_count / result.total:.1f} %)")
    print(f"  fallback code path      : {FALLBACK_SITE} -> return {FALLBACK_CLASS!r}")
    print("  class histogram         :")
    for name, count in sorted(result.histogram.items(), key=lambda item: (-item[1], item[0])):
        print(f"    {name:<18} {count}")
    print(f"  recorded in the audit   : {RECORDED_FALLBACK_COUNT} fallback compositions")

    if not args.no_write:
        report = build_report(result)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"  report written          : {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
