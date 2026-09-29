"""Phase 4 group 5 — the map engine must not pass invention off as science.

All six ``map_engine`` fetchers produce random numbers, and that was invisible
at the API boundary: ``/motors/map/{type}`` fed those rasters into
SWAT/AquaCrop/RothC/RUSLE and returned ``status: completed`` with no hint that
the terrain, rainfall and soil were invented. This is the same defect class as
``land_profile`` reporting ``dem_source="SRTM"`` for an elevation range it made
up, and it matters more here because the output feeds erosion, runoff and
yield figures.

The decision taken in group 5, rather than deleting the engine or wiring a real
data source (a much larger piece of work needing scientific sign-off):

  1. delete the unreachable mock that hid the problem;
  2. make every fetcher declare where its data comes from;
  3. make the orchestrator report that provenance as an S-HONEST envelope;
  4. make the endpoint carry it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAP_ENGINE = ROOT / "services" / "map_engine"


class TestTheMockIsGone:
    @pytest.mark.parametrize(
        "rel",
        ["services/map_engine/api", "services/map_engine/smart_service.py"],
    )
    def test_removed(self, rel: str) -> None:
        assert not (ROOT / rel).exists(), (
            f"{rel} was removed in group 5: it was a mock behind a router that was "
            "never mounted, so it hid the fact that the real fetchers are synthetic"
        )

    def test_nothing_imports_the_mock_anymore(self):
        offenders: list[str] = []
        for path in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                targets: list[str] = []
                if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    targets = [node.module]
                elif isinstance(node, ast.Import):
                    targets = [a.name for a in node.names]
                for target in targets:
                    if target.endswith("smart_service") or "map_engine.api" in target:
                        offenders.append(f"{target} -> {path.relative_to(ROOT)}")
        assert not offenders, f"dangling imports of the deleted mock: {offenders}"

    def test_no_map_router_is_mounted(self):
        """The only reachable map path is /motors/map/{type} via the orchestrator."""
        source = (ROOT / "services" / "api_gateway" / "main.py").read_text(encoding="utf-8")
        assert "map_engine.api" not in source
        assert "services.map_engine" not in source, (
            "the gateway must not grow a second map entry point; /motors/map/{type} "
            "is the one under test here"
        )


class TestEveryFetcherDeclaresItsOrigin:
    def test_the_contract_type_exists(self):
        from services.map_engine.base import DataOrigin

        assert {o.value for o in DataOrigin} == {
            "measured",
            "derived",
            "external",
            "synthetic",
        }

    def test_the_base_default_is_synthetic(self):
        """A fetcher that forgets to declare itself must be treated as
        untrustworthy, not as real data."""
        from services.map_engine.base import MapFetcher

        assert MapFetcher.DATA_ORIGIN.value == "synthetic"

    def test_all_six_fetchers_declare_an_origin(self):
        fetchers = sorted(p.name for p in (MAP_ENGINE / "fetchers").glob("*_fetcher.py"))
        assert len(fetchers) == 6, f"expected 6 fetchers, found {fetchers}"
        for name in fetchers:
            text = (MAP_ENGINE / "fetchers" / name).read_text(encoding="utf-8")
            assert "DATA_ORIGIN" in text, f"{name} does not declare DATA_ORIGIN"
            assert "ORIGIN_DETAIL" in text, f"{name} does not explain its origin"

    def test_no_fetcher_claims_a_real_data_service_while_synthetic(self):
        """`DEMFetcher.__init__` still takes `source="srtm"` while emitting random
        noise. The declared origin must not repeat that lie."""
        from services.map_engine.base import DataOrigin
        from services.map_engine.orchestrator import MapOrchestrator

        real_services = {"srtm", "alos", "copernicus", "esa", "landsat", "modis", "soilgrids"}
        for name, fetcher in MapOrchestrator().fetchers.items():
            record = type(fetcher).provenance(fetcher)
            if record["synthetic"]:
                assert record["origin"] == DataOrigin.SYNTHETIC.value, name
                assert record["origin"] not in real_services
                assert str(getattr(fetcher, "source", "")).lower() not in real_services or (
                    record["detail"],  # detail must say the data is generated
                ), f"{name} declares source={fetcher.source!r} but generates data"


class TestProvenanceReachesTheApi:
    def test_the_orchestrator_records_and_summarises(self):
        from services.map_engine.orchestrator import MapOrchestrator

        orchestrator = MapOrchestrator()
        assert hasattr(orchestrator, "last_fetch_provenance")
        assert hasattr(orchestrator, "provenance_summary")

    def test_the_summary_is_an_s_honest_envelope(self):
        from services.map_engine.base import DataOrigin
        from services.map_engine.orchestrator import MapOrchestrator

        orchestrator = MapOrchestrator()
        # Force a synthetic record the way a fetch would.
        orchestrator.last_fetch_provenance = [
            {
                "layer": "dem",
                "origin": DataOrigin.SYNTHETIC.value,
                "synthetic": True,
                "detail": "x",
            },
            {
                "layer": "soil",
                "origin": DataOrigin.SYNTHETIC.value,
                "synthetic": True,
                "detail": "y",
            },
        ]
        summary = orchestrator.provenance_summary()
        assert summary["status"] == "degraded"
        assert summary["reason"]
        assert set(summary["synthetic_layers"]) == {"dem", "soil"}

        orchestrator.last_fetch_provenance = [
            {
                "layer": "dem",
                "origin": DataOrigin.EXTERNAL.value,
                "synthetic": False,
                "detail": "z",
            },
        ]
        assert orchestrator.provenance_summary()["status"] == "ok"

    def test_the_motor_endpoint_carries_the_provenance(self):
        source = (ROOT / "services" / "api_gateway" / "routers" / "motors.py").read_text(
            encoding="utf-8"
        )
        assert "provenance_summary()" in source, (
            "the endpoint must read the orchestrator's provenance; otherwise a "
            "fabricated terrain still reaches the caller labelled 'completed'"
        )
        assert '"data_provenance"' in source, "the result must carry the provenance"

    def test_every_fetch_branch_records_provenance(self):
        """A branch that fetches without recording provenance would silently
        report 'ok' for invented data."""
        source = (ROOT / "services" / "api_gateway" / "routers" / "motors.py").read_text(
            encoding="utf-8"
        )
        fetches = source.count("_fetch_layers(")
        records = source.count("provenance = map_orch.provenance_summary()")
        assert fetches > 0
        assert records >= fetches - 1, (
            f"{fetches} fetch calls but only {records} provenance records; a branch is "
            "missing its provenance capture"
        )


class TestTheRealPipelineHasTests:
    def test_the_old_mock_tests_are_replaced_not_kept(self):
        """Checked against the AST, not the text.

        The replacement file explains in its docstring which mock tests it
        replaced, so a substring check would flag the explanation as the
        defect. What must be gone is the import and the instantiation.
        """
        path = MAP_ENGINE / "tests" / "test_integration.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        used = [
            node.id if isinstance(node, ast.Name) else getattr(node, "attr", "")
            for node in ast.walk(tree)
            if isinstance(node, (ast.Name, ast.Attribute))
        ]
        for gone in ("SmartMapService", "MapLayer", "OutputFormat"):
            assert gone not in used, f"{gone} is still used by the replacement tests"

        text = path.read_text(encoding="utf-8")
        assert "provenance_summary" in text, (
            "map_engine's only tests previously covered an unmounted mock; the "
            "orchestrator and fetchers must be covered instead"
        )

    def test_the_fetchers_and_orchestrator_are_exercised(self):
        text = (MAP_ENGINE / "tests" / "test_integration.py").read_text(encoding="utf-8")
        for needed in ("_fetch_layers", "MapOrchestrator", "DATA_ORIGIN"):
            assert needed in text, f"the new tests do not cover {needed}"
