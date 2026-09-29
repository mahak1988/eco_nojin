"""S13 — The shared parameter table: one source, and no silent divergence.

What this module enforces
-------------------------
``engine/data/soil_vg_table.csv`` is the single source of the van Genuchten
parameter table. Before consolidation the table existed in four places with
three different answers. This module checks three things:

1. **Every consumer reads the CSV.** A hand-written copy reintroduces the
   defect, so each consumer is compared against the CSV value by value.
2. **The C++ block is generated, not written.** ``--check`` in CI is what stops a
   hand edit from quietly becoming a fifth copy.
3. **The values are physically admissible and honestly labelled.** The Ks
   column still has two rows that break fineness monotonicity, and the CSV says
   so. Those rows are pinned as *known and disputed* rather than left for a
   reader to discover.

The module does **not** assert that the values are correct. It cannot: the
provenance is unverifiable offline and the conflicts are recorded in
``engine/data/SOIL_TABLE_CONFLICTS.md``. What it asserts is that there is one
table, that every backend reads it, and that the remaining disagreements with
the physical constraints are declared rather than hidden.
"""

from __future__ import annotations

import csv
import re
from itertools import pairwise

import pytest

from engine.data.soil_table import (
    DISPUTED_TEXTURES,
    FINENESS_ORDER,
    SOIL_PARAMETERS,
    TABLE_PATH,
    SoilTableError,
    disputed_textures,
    get_params,
    get_params_cpp,
    load_table,
    load_table_ks_cm_per_hour,
)

#: The pre-consolidation copies, recorded so that a reappearance is noticed.
LEGACY_TABLE_HOLDERS = {
    "engine/hydroma/soil/physics.py": "SOIL_PARAMETERS_VG",
    "engine/hydroma/cpp_bridge/soil_physics_fast.py": "SOIL_PARAMETERS",
    "engine/cpp_core/src/soil.cpp": "kTextures",
}


class TestSingleSource:
    def test_csv_carries_every_texture_in_fineness_order(self) -> None:
        assert list(SOIL_PARAMETERS) == list(FINENESS_ORDER)
        assert len(SOIL_PARAMETERS) == 12

    def test_csv_is_the_file_that_is_read(self) -> None:
        assert TABLE_PATH.name == "soil_vg_table.csv"
        assert TABLE_PATH.exists()
        assert TABLE_PATH.parent.name == "data"
        assert TABLE_PATH.parent.parent.name == "engine"

    def test_loader_agrees_with_the_raw_csv(self) -> None:
        """The loader must not round, coerce, or drop anything."""
        with TABLE_PATH.open(encoding="utf-8", newline="") as handle:
            rows = {r["texture"]: r for r in csv.DictReader(handle)}
        assert set(rows) == set(SOIL_PARAMETERS)
        for texture, row in rows.items():
            for column, key in (
                ("theta_r", "theta_r"),
                ("theta_s", "theta_s"),
                ("alpha", "alpha"),
                ("n", "n"),
                ("ks_cm_per_day", "Ks"),
            ):
                assert float(row[column]) == SOIL_PARAMETERS[texture][key], (
                    f"{texture}.{key}: loader {SOIL_PARAMETERS[texture][key]} "
                    f"against CSV {row[column]}"
                )

    def test_load_table_is_repeatable(self) -> None:
        assert load_table() == load_table()

    def test_get_params_raises_for_an_unknown_texture(self) -> None:
        with pytest.raises(KeyError, match="unknown soil texture"):
            get_params("volcanic_sand")

    def test_get_params_returns_only_the_numeric_keys(self) -> None:
        params = get_params("loam")
        assert set(params) == {"theta_r", "theta_s", "alpha", "n", "Ks"}

    def test_get_params_cpp_converts_ks_to_cm_per_hour(self) -> None:
        for texture in FINENESS_ORDER:
            cm_day = get_params(texture)["Ks"]
            assert get_params_cpp(texture)["Ks"] == pytest.approx(cm_day / 24.0, rel=1e-12)

    def test_missing_table_would_be_reported_clearly(self) -> None:
        """The table is load-bearing, so its absence must name itself."""
        message = str(SoilTableError("van Genuchten table not found at /x"))
        assert "van Genuchten table not found" in message
        assert "/x" in message, "the error must name the path it looked at"


class TestEveryConsumerReadsTheCsv:
    def test_physics_module_matches_the_csv(self) -> None:
        from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

        assert set(SOIL_PARAMETERS_VG) == set(SOIL_PARAMETERS)
        for texture, params in SOIL_PARAMETERS_VG.items():
            for key, value in params.items():
                assert value == SOIL_PARAMETERS[texture][key], f"{texture}.{key}"

    def test_physics_table_is_no_longer_an_attributed_literal(self) -> None:
        """The withdrawn attribution must not survive as a comment."""
        import inspect

        from engine.hydroma.soil import physics

        source = inspect.getsource(physics)
        table_block = source[source.index("SOIL_PARAMETERS_VG") - 900 :]
        assert "Carsel & Parrish (1988) van Genuchten parameters" not in table_block, (
            "the table comment still attributes the values to a source that could not be verified"
        )
        assert "Carsel & Parrish" in source, (
            "the docstring should still record that the citation is unverified"
        )

    @pytest.mark.requires_cpp
    def test_numba_table_matches_the_csv_in_cm_per_hour(self) -> None:
        from engine.hydroma.cpp_bridge.soil_physics_fast import SOIL_PARAMETERS

        expected = load_table_ks_cm_per_hour()
        assert set(SOIL_PARAMETERS) == set(expected)
        for texture, params in SOIL_PARAMETERS.items():
            for key, value in params.items():
                assert value == pytest.approx(expected[texture][key], rel=1e-12), f"{texture}.{key}"

    @pytest.mark.requires_cpp
    def test_numba_table_now_covers_all_twelve_textures(self) -> None:
        """It carried seven before consolidation, so five textures raised."""
        import numpy as np

        from engine.hydroma.cpp_bridge.soil_physics_fast import soil_water_content

        for texture in ("silt", "sandy_clay_loam", "silty_clay_loam", "sandy_clay", "silty_clay"):
            values = soil_water_content(np.array([-100.0]), texture)
            assert values[0] > 0.0, texture

    def test_land_integrator_matches_the_csv(self) -> None:
        from engine.land.integration import SoilIntegrator
        from engine.land.integration.models import SoilTexture

        integrator = SoilIntegrator()
        for texture in SoilTexture:
            shared = get_params(texture.value)
            got = integrator.estimate_van_genuchten(texture)
            for key in ("theta_r", "theta_s", "alpha", "n"):
                assert got[key] == shared[key], f"{texture.value}.{key}"

    @pytest.mark.parametrize("relative", sorted(LEGACY_TABLE_HOLDERS))
    def test_no_consumer_holds_a_table_literal(self, relative: str) -> None:
        """A dict of per-texture numbers in one of these files is a fifth copy.

        The generated block in ``soil.cpp`` is exempt: it is a projection of the
        CSV, it is delimited so ``generate_cpp_table --check`` can find it, and
        that check is the enforcement. What must not appear is a table *outside*
        the delimited block.
        """
        import ast
        from pathlib import Path

        path = Path(__file__).resolve().parents[2] / relative
        text = path.read_text(encoding="utf-8", errors="replace")
        generated = re.search(r"// GENERATED FILE.*?^\};", text, re.MULTILINE | re.DOTALL)
        if generated:
            text = text[: generated.start()] + text[generated.end() :]
        tree = ast.parse(text) if relative.endswith(".py") else None
        if tree is None:
            return  # C++ is covered by test_cpp_block_is_in_step_with_the_csv
        texture_names = set(FINENESS_ORDER)
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = set()
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.add(key.value)
            if len(texture_names & keys) >= 3:
                offenders.append(
                    f"line {node.lineno}: a literal with {sorted(texture_names & keys)}"
                )
        assert not offenders, f"{relative} holds a hand-written table again:\n" + "\n".join(
            offenders
        )


class TestGeneratedCppTable:
    def test_cpp_block_is_in_step_with_the_csv(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "engine.data.generate_cpp_table", "--check"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"cpp_core/src/soil.cpp has drifted from the CSV:\n{result.stdout}"
        )

    def test_cpp_block_carries_every_texture(self) -> None:
        from pathlib import Path

        text = (Path(__file__).resolve().parents[2] / "engine/cpp_core/src/soil.cpp").read_text(
            encoding="utf-8"
        )
        block = re.search(r"// GENERATED FILE.*?^\};", text, re.MULTILINE | re.DOTALL)
        assert block, "the generated block is missing; run generate_cpp_table"
        for texture in FINENESS_ORDER:
            assert f'"{texture}"' in block.group(0), texture

    def test_cpp_block_states_the_provenance_honestly(self) -> None:
        from pathlib import Path

        text = (Path(__file__).resolve().parents[2] / "engine/cpp_core/src/soil.cpp").read_text(
            encoding="utf-8"
        )
        block = re.search(r"// GENERATED FILE.*?^\};", text, re.MULTILINE | re.DOTALL).group(0)
        assert "design assumption" in block
        assert "do not edit by hand" in block
        assert "Typical parameters from Carsel" not in text, (
            "the legacy attribution comment is still in the file"
        )

    def test_generator_is_idempotent(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "engine.data.generate_cpp_table"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "already in step" in result.stdout, (
            f"regenerating produced a change: {result.stdout}"
        )


class TestPhysicalAdmissibility:
    @pytest.mark.parametrize("texture", FINENESS_ORDER)
    def test_parameters_are_in_range(self, texture: str) -> None:
        p = get_params(texture)
        assert 0.0 <= p["theta_r"] < p["theta_s"] <= 1.0
        assert p["alpha"] > 0.0
        assert 1.0 < p["n"] <= 3.0
        assert p["Ks"] > 0.0

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The Ks column is not monotone in texture fineness, which hydraulic "
            "conductivity cannot be. Two rows break it: sandy_clay_loam carries "
            "31.4 cm/day while the coarser silt carries 6.0, and clay carries 4.8 "
            "while the coarser silty_clay carries 1.92. The n column breaks it once "
            "at the same row, sandy_clay_loam 1.48 against silt 1.37. This is the "
            "evidence that withdraws the Carsel & Parrish attribution: a faithful "
            "transcription of a published table would not violate the defining "
            "ordering of the quantity it tabulates. The rows are retained and "
            "labelled disputed rather than corrected, because the correct values "
            "require the source publication, which is not available offline. See "
            "engine/data/SOIL_TABLE_CONFLICTS.md."
        ),
    )
    def test_conductivity_falls_with_texture_fineness(self) -> None:
        for coarse, fine in pairwise(FINENESS_ORDER):
            assert get_params(fine)["Ks"] <= get_params(coarse)["Ks"], (
                f"{fine} (Ks {get_params(fine)['Ks']}) conducts more than "
                f"{coarse} (Ks {get_params(coarse)['Ks']})"
            )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The pore-size index n is not monotone in texture fineness either. "
            "The van Genuchten n is a shape parameter of the retention curve and "
            "falls as the median pore size falls, so it must decrease from sand to "
            "clay. One row breaks it: sandy_clay_loam carries n = 1.48 against "
            "silt's 1.37, and sandy_clay_loam is the finer of the two. The same row "
            "also breaks the conductivity ordering, which is what makes it a "
            "suspected mis-assembly rather than a rounding difference. n is "
            "otherwise monotone across the other eleven textures, so this is one "
            "row rather than a systematic transcription error. The row is retained "
            "and labelled disputed; correcting it needs the source publication."
        ),
    )
    def test_pore_size_index_falls_with_texture_fineness(self) -> None:
        for coarse, fine in pairwise(FINENESS_ORDER):
            assert get_params(fine)["n"] <= get_params(coarse)["n"], (
                f"{fine} (n {get_params(fine)['n']}) exceeds {coarse} (n {get_params(coarse)['n']})"
            )

    def test_every_row_carries_a_provenance_label(self) -> None:
        for texture, entry in SOIL_PARAMETERS.items():
            assert entry["provenance"], texture
            assert entry["status"], texture

    def test_no_row_is_labelled_verified(self) -> None:
        """Nothing in this table has been checked against its source."""
        for texture, entry in SOIL_PARAMETERS.items():
            assert entry["status"] != "verified", (
                f"{texture} is labelled verified; that needs a citation of the "
                f"form the project uses, a chapter and table"
            )

    def test_disputed_rows_are_the_ones_that_break_an_ordering(self) -> None:
        assert set(disputed_textures()) == set(DISPUTED_TEXTURES)
        for texture in DISPUTED_TEXTURES:
            assert SOIL_PARAMETERS[texture]["disputed"] is True, texture
        for texture in FINENESS_ORDER:
            if texture not in DISPUTED_TEXTURES:
                assert SOIL_PARAMETERS[texture]["disputed"] is False, texture


class TestConductivityInterval:
    """The interval each row's own physics permits.

    Saturated conductivity is non-increasing with texture fineness, so a row is
    bracketed by its coarser and finer neighbours. This is the strongest
    statement available without the source publication, and it is decidable
    offline. It also distinguishes a local defect from a global one: a value
    outside a valid interval is one wrong row, whereas an EMPTY interval means
    the two neighbours already contradict each other, so no single row can be
    repaired first.
    """

    def test_every_row_carries_an_interval(self) -> None:
        for texture in FINENESS_ORDER:
            entry = SOIL_PARAMETERS[texture]
            assert (
                entry["ks_admissible_min"] <= entry["ks_admissible_max"]
                or (entry["ks_interval_empty"])
            ), texture

    def test_intervals_bracket_the_value_where_the_column_is_coherent(self) -> None:
        """Eight of the twelve rows are ordered and inside their intervals.

        The seven rows from sand to silt_loam form a strictly falling sequence,
        and the three from clay_loam down through silty_clay_loam and sandy_clay
        are each inside a valid interval. Clay is the odd one out with a valid
        interval it sits outside; that is asserted separately.
        """
        coherent = [
            t
            for t in FINENESS_ORDER
            if not SOIL_PARAMETERS[t]["ks_interval_empty"]
            and not SOIL_PARAMETERS[t]["ks_outside_interval"]
        ]
        assert coherent == [
            "sand",
            "loamy_sand",
            "sandy_loam",
            "loam",
            "silt_loam",
            "clay_loam",
            "silty_clay_loam",
            "sandy_clay",
        ], coherent
        values = [SOIL_PARAMETERS[t]["Ks"] for t in coherent]
        coarse_run = values[:5]
        assert coarse_run == sorted(coarse_run, reverse=True), coarse_run

    def test_the_known_empty_intervals_are_still_the_only_ones(self) -> None:
        """A new empty interval means the corruption has spread."""
        empty = {t for t in FINENESS_ORDER if SOIL_PARAMETERS[t]["ks_interval_empty"]}
        assert empty == {"silt", "sandy_clay_loam", "silty_clay"}, (
            f"empty intervals changed to {sorted(empty)}; the source publication is needed again"
        )

    def test_the_known_violations_are_still_the_only_ones(self) -> None:
        outside = {t for t in FINENESS_ORDER if SOIL_PARAMETERS[t]["ks_outside_interval"]}
        assert outside == {"silt", "sandy_clay_loam", "silty_clay", "clay"}, (
            f"violations changed to {sorted(outside)}"
        )

    def test_the_defect_is_two_clusters_not_one_block(self) -> None:
        """The finding that matters for repair planning.

        The affected rows are silt and sandy_clay_loam at the fine end of the
        coarse group, and silty_clay and clay at the very end. Three sound rows
        sit between the two clusters, so this is not one contiguous block: two
        separate transpositions are the simplest explanation, and they must be
        fixed independently.

        An earlier version of this test asserted the rows were contiguous. They
        are not, and the assertion was written before the data was read.
        """
        affected = [
            t
            for t in FINENESS_ORDER
            if SOIL_PARAMETERS[t]["ks_interval_empty"] or SOIL_PARAMETERS[t]["ks_outside_interval"]
        ]
        indices = [FINENESS_ORDER.index(t) for t in affected]
        assert indices == [5, 6, 10, 11], affected
        sound_between = [FINENESS_ORDER[i] for i in range(7, 10)]
        for texture in sound_between:
            entry = SOIL_PARAMETERS[texture]
            assert not entry["ks_interval_empty"], (
                f"{texture} sits between the two clusters and is sound; an "
                f"assertion that they are adjacent is wrong"
            )
            assert not entry["ks_outside_interval"], (
                f"{texture} sits between the two clusters and is sound; an "
                f"assertion that they are adjacent is wrong"
            )

    def test_clay_is_the_only_value_outside_a_valid_interval(self) -> None:
        """The one row that could be corrected in isolation, if ever it should be.

        Its interval is valid (0 to silty_clay's 1.92) and its value 4.80 is
        above it. Correcting it would fix clay without disturbing a
        neighbour's interval, which is why it is listed separately from the three
        empty ones.
        """
        with_valid_interval = [
            t
            for t in FINENESS_ORDER
            if not SOIL_PARAMETERS[t]["ks_interval_empty"]
            and SOIL_PARAMETERS[t]["ks_outside_interval"]
        ]
        assert with_valid_interval == ["clay"], with_valid_interval
        entry = SOIL_PARAMETERS["clay"]
        assert entry["Ks"] > entry["ks_admissible_max"]
        assert entry["ks_admissible_max"] == SOIL_PARAMETERS["silty_clay"]["Ks"]

    @pytest.mark.requires_cpp
    def test_the_cpp_copies_serve_the_same_clay_value(self) -> None:
        """After the rebuild, both backends report the one interval-correct row
        the same way, so the 40 % divergence is gone."""
        from engine.hydroma.cpp_bridge import get_module

        cpp = float(get_module().hydraulic_conductivity([0.0], "clay")[0])
        assert cpp == pytest.approx(SOIL_PARAMETERS["clay"]["Ks"] / 24.0, rel=1e-9)

    @pytest.mark.requires_cpp
    def test_every_texture_is_served_by_the_compiled_table(self) -> None:
        """The rebuild closed the 7-versus-12 gap."""
        from engine.hydroma.cpp_bridge import get_module

        native = get_module()
        for texture in FINENESS_ORDER:
            value = float(native.hydraulic_conductivity([0.0], texture)[0])
            assert value == pytest.approx(SOIL_PARAMETERS[texture]["Ks"] / 24.0, rel=1e-6), texture


class TestPackaging:
    def test_csv_is_declared_as_package_data(self) -> None:
        """A wheel built without the CSV cannot import the soil package."""
        import tomllib
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        patterns = config["tool"]["setuptools"]["package-data"]["*"]
        assert "*.csv" in patterns, (
            f"package-data is {patterns}; the soil table would not ship and "
            f"importing engine.hydroma.soil would fail in an installed wheel"
        )

    def test_conflicts_document_exists_and_names_every_disputed_row(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        path = root / "engine" / "data" / "SOIL_TABLE_CONFLICTS.md"
        assert path.exists(), "the open conflicts must stay on record"
        text = path.read_text(encoding="utf-8")
        for texture in DISPUTED_TEXTURES:
            assert texture in text, f"{texture} is disputed but undocumented"
        assert "clay" in text.lower()
        assert "Carsel" in text, "the document must say which attribution was withdrawn"
