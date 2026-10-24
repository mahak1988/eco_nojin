"""Integration tests for the Map Engine — on the code that actually runs.

Replaces a previous version of this file that tested ``SmartMapService``,
the mock behind ``services/map_engine/api/__init__.py``. That router was never
mounted in the API gateway, so those two tests exercised a path no request
could reach, while the orchestrator, the five pipelines and the six fetchers
that ``/motors/map/{type}`` *does* use had no tests at all.

What is covered now:
  * every fetcher declares where its data comes from;
  * the orchestrator reports that provenance and marks a fetch ``degraded``
    when any layer was fabricated;
  * a map result carries the provenance of its inputs.
"""

import pytest
from shapely.geometry import Polygon

from services.map_engine.base import DataOrigin, MapFetcher, MapType
from services.map_engine.orchestrator import MapOrchestrator

REGION = Polygon([(51.4, 35.4), (51.5, 35.4), (51.5, 35.5), (51.4, 35.5), (51.4, 35.4)])


class TestEveryFetcherDeclaresItsOrigin:
    def test_all_fetchers_are_registered(self):
        orchestrator = MapOrchestrator()
        assert set(orchestrator.fetchers) >= {"dem", "soil", "landcover", "rainfall"}

    def test_no_fetcher_silently_expects_trust(self):
        """The base default is SYNTHETIC, so a fetcher that forgets to declare
        itself is treated as untrustworthy rather than as real."""
        assert MapFetcher.DATA_ORIGIN is DataOrigin.SYNTHETIC

    def test_each_registered_fetcher_reports_provenance(self):
        orchestrator = MapOrchestrator()
        for fetcher in orchestrator.fetchers.values():
            record = type(fetcher).provenance(fetcher)
            assert record["layer"] in orchestrator.fetchers, (
                f"provenance reports layer {record['layer']!r}, which is not registered"
            )
            assert record["origin"], f"{record['layer']} has no origin"
            assert record["detail"], f"{record['layer']} has no detail"
            assert isinstance(record["synthetic"], bool)

    def test_synthetic_fetchers_say_so_rather_than_claiming_a_source(self):
        """Regression guard for the exact defect group 5 addresses.

        ``DEMFetcher.__init__`` still takes ``source="srtm"`` while generating
        random noise. A caller that read ``fetcher.source`` would conclude the
        terrain came from SRTM. The declared origin must not be one of the
        real data services.
        """
        orchestrator = MapOrchestrator()
        for fetcher in orchestrator.fetchers.values():
            record = type(fetcher).provenance(fetcher)
            if record["synthetic"]:
                assert record["origin"] == DataOrigin.SYNTHETIC.value
                assert record["origin"] not in {"srtm", "alos", "copernicus", "esa"}


class TestOrchestratorProvenance:
    def test_empty_summary_is_ok(self):
        assert MapOrchestrator().provenance_summary()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_a_fetch_records_the_provenance_of_every_layer(self, tmp_path):
        orchestrator = MapOrchestrator(cache_dir=tmp_path)
        await orchestrator._fetch_layers(["dem", "soil"], REGION)
        summary = orchestrator.provenance_summary()
        assert {r["layer"] for r in summary["layers"]} == {"dem", "soil"}

    @pytest.mark.asyncio
    async def test_a_synthetic_fetch_is_reported_as_degraded_with_a_reason(self, tmp_path):
        """The core of the group 5 fix: an invented terrain may not be reported
        as a clean result."""
        orchestrator = MapOrchestrator(cache_dir=tmp_path)
        await orchestrator._fetch_layers(["dem", "rainfall"], REGION)
        summary = orchestrator.provenance_summary()

        assert summary["status"] == "degraded"
        assert summary["synthetic_layers"], "synthetic layers must be named"
        assert "synthetic" in summary["reason"]
        assert "demonstration of the method" in summary["reason"], (
            "the reason must say what the number is not"
        )

    @pytest.mark.asyncio
    async def test_an_unknown_layer_still_raises(self, tmp_path):
        orchestrator = MapOrchestrator(cache_dir=tmp_path)
        with pytest.raises(ValueError, match="No fetcher for layer"):
            await orchestrator._fetch_layers(["not_a_layer"], REGION)


class TestPipelinesAreRegistered:
    def test_the_four_live_pipelines_are_present(self):
        orchestrator = MapOrchestrator()
        for map_type in (MapType.M_TOP, MapType.M_ERS, MapType.M_VEG, MapType.M_RUN):
            assert map_type in orchestrator.pipelines, f"{map_type} is not registered"

    def test_slope_aspect_is_actually_registered(self):
        """``orchestrator.py`` carried a comment claiming SlopeAspectPipeline
        was "not yet implemented" while importing it successfully. Assert the
        real state so the comment cannot lie again."""
        orchestrator = MapOrchestrator()
        assert MapType.M_SLP in orchestrator.pipelines
