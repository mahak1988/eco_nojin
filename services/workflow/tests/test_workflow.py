"""Tests for the workflow orchestration service."""

import pytest

from services.workflow.service import (
    WorkflowRequest,
    WorkflowService,
)


@pytest.fixture
def service(db_session):
    return WorkflowService(db=db_session)


def _request(**overrides):
    payload = {
        "farmer_id": "farmer-1",
        "field_id": "field-1",
        "crop_type": "wheat",
    }
    payload.update(overrides)
    return WorkflowRequest(**payload)


class TestStageRouting:
    """Tests for the stage dispatch."""

    def test_an_unknown_stage_is_refused(self, service):
        with pytest.raises(ValueError, match="Unknown stage"):
            import asyncio

            asyncio.run(service._run_stage("not-a-stage", _request()))

    async def test_the_ingest_stage_reports_the_inputs(self, service):
        output = await service._run_stage("ingest", _request())
        assert output["farmer_id"] == "farmer-1"
        assert output["field_id"] == "field-1"
        assert output["crop_type"] == "wheat"

    async def test_the_ingest_stage_stamps_the_time(self, service):
        output = await service._run_stage("ingest", _request())
        assert "ingested_at" in output


class TestRun:
    """Tests for a whole workflow run."""

    #: The simulation chain needs the erosion factors; the caller supplies
    #: them. The workflow must not invent them.
    SIM_METADATA = {
        "area_ha": 2.0,
        "r_factor": 100.0,
        "k_factor": 0.3,
        "ls_factor": 0.5,
        "c_factor_base": 0.2,
        "initial_soc_t_ha": 30.0,
        "clay_pct": 25.0,
    }

    async def test_a_run_executes_every_requested_stage(self, service):
        response = await service.run(_request(stages=["ingest"], metadata=self.SIM_METADATA))
        assert [s.stage for s in response.stages] == ["ingest"]
        assert response.status == "success"

    async def test_the_simulate_stage_runs_with_a_complete_configuration(self, service):
        response = await service.run(
            _request(stages=["simulate"], metadata=self.SIM_METADATA)
        )
        assert response.status == "success", response.stages[0].error
        assert response.stages[0].output

    async def test_the_simulate_stage_names_the_missing_parameters(self, service):
        """Without the erosion factors the stage must say which are missing.

        It must not substitute defaults: a simulation with invented factors
        is a fabricated result.
        """
        response = await service.run(_request(stages=["simulate"]))
        assert response.status == "partial"
        error = response.stages[0].error
        assert error
        assert "r_factor" in error

    async def test_the_run_carries_an_id(self, service):
        response = await service.run(_request(stages=["ingest"]))
        assert response.run_id.startswith("wf_")

    async def test_the_run_records_the_timestamps(self, service):
        response = await service.run(_request(stages=["ingest"]))
        assert response.started_at
        assert response.completed_at

    async def test_a_failing_stage_makes_the_run_partial(self, service):
        """A failed stage must not be reported as a success."""
        response = await service.run(_request(stages=["ingest", "not-a-stage"]))
        assert response.status == "partial"
        failed = [s for s in response.stages if s.status == "failed"]
        assert len(failed) == 1
        assert failed[0].stage == "not-a-stage"
        assert failed[0].error

    async def test_a_failing_stage_does_not_abort_the_run(self, service):
        """The remaining stages still run, and the outcome is honest."""
        response = await service.run(_request(stages=["not-a-stage", "ingest"]))
        assert len(response.stages) == 2
        assert response.stages[0].status == "failed"
        assert response.stages[1].status == "success"

    async def test_the_stage_durations_are_measured(self, service):
        response = await service.run(_request(stages=["ingest"]))
        assert response.stages[0].duration_ms >= 0
