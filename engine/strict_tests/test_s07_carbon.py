"""S07 — Carbon accounting: identities, provenance and honest bounds.

Domain under test
-----------------
``engine/hydroma/carbon/calculator.py`` is an IPCC Tier-1 *screening* tool. It
states in its own docstring that it is not process-based and must not be used
for credit issuance. The tests below therefore hold it to what a screening tool
can be held to:

1. **Accounting identities.** For an annually sequestering project,
       total = annual_rate x area x years x discount
   and the reported minimum and maximum must bracket the point estimate.
2. **One-time versus annual accumulation.** Biochar is applied once, so its
   total is independent of the project duration beyond amortisation, and its
   annual rate is total / years.
3. **Area and duration are linear.** Doubling either doubles the tonnes.
4. **Units are tonnes CO2**, not tonnes C, and revenue is tonnes x USD/t.
5. **Provenance.** The module documents that a repository is preferred over the
   in-memory registry, so a repository failure must not masquerade as success.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from engine.hydroma.carbon.calculator import (
    CARBON_PRICES,
    SEQUESTRATION_RATES,
    CarbonProject,
    CarbonProjectType,
    calculate_carbon_sequestration,
    compare_project_types,
    get_project,
    list_projects,
    register_project,
    set_repository,
)

ANNUALLY_SEQUESTERING = [t for t in CarbonProjectType if t is not CarbonProjectType.BIOCHAR]

# The engine's own documented discount for uncertainty.
UNCERTAINTY_DISCOUNT = 0.85


class TestRateTable:
    def test_every_project_type_has_a_rate_entry(self) -> None:
        assert set(SEQUESTRATION_RATES) == set(CarbonProjectType)

    @pytest.mark.parametrize("project_type", list(CarbonProjectType))
    def test_rate_brackets_are_ordered_and_positive(self, project_type: CarbonProjectType) -> None:
        rates = SEQUESTRATION_RATES[project_type]
        assert 0.0 < rates["min"] <= rates["rate"] <= rates["max"]
        assert rates["permanence_years"] > 0

    def test_permanence_ranks_biochar_highest(self) -> None:
        """Biochar carbon is the most stable fraction in the table; the module's
        own comment says so."""
        permanences = {t: r["permanence_years"] for t, r in SEQUESTRATION_RATES.items()}
        assert max(permanences, key=permanences.get) is CarbonProjectType.BIOCHAR

    def test_afforestation_outranks_soil_practices(self) -> None:
        assert (
            SEQUESTRATION_RATES[CarbonProjectType.AFFORESTATION]["rate"]
            > SEQUESTRATION_RATES[CarbonProjectType.SOIL_CARBON_NO_TILL]["rate"]
        )

    def test_price_table_is_annotated_as_illustrative(self) -> None:
        import inspect

        from engine.hydroma.carbon import calculator

        source = inspect.getsource(calculator)
        assert "illustrative" in source
        assert "EU" in source, "the directive citation that constrains use was removed"


class TestAccountingIdentities:
    @pytest.mark.parametrize("project_type", ANNUALLY_SEQUESTERING)
    @pytest.mark.parametrize("region", ["tropical", "temperate", "arid"])
    def test_total_equals_rate_times_area_times_years(
        self, project_type: CarbonProjectType, region: str
    ) -> None:
        out = calculate_carbon_sequestration(project_type, 50.0, duration_years=20, region=region)
        rates = SEQUESTRATION_RATES[project_type]
        factor = {"tropical": 1.3, "temperate": 1.0, "arid": 0.6}[region]
        expected = rates["rate"] * factor * 50.0 * 20 * UNCERTAINTY_DISCOUNT
        assert out["total_carbon_tonnes"] == pytest.approx(expected, rel=1e-3)

    @pytest.mark.parametrize("project_type", ANNUALLY_SEQUESTERING)
    @pytest.mark.parametrize("region", ["tropical", "temperate", "arid"])
    def test_range_brackets_the_point_estimate(
        self, project_type: CarbonProjectType, region: str
    ) -> None:
        out = calculate_carbon_sequestration(project_type, 50.0, duration_years=20, region=region)
        assert out["total_carbon_min"] <= out["total_carbon_tonnes"] <= out["total_carbon_max"], (
            f"{project_type.value}/{region}: min {out['total_carbon_min']} "
            f"point {out['total_carbon_tonnes']} max {out['total_carbon_max']}"
        )

    def test_biochar_range_brackets_the_point_estimate(self) -> None:
        """Biochar is a one-time application, so the range must be computed from
        the same one-time basis as the point estimate."""
        out = calculate_carbon_sequestration(CarbonProjectType.BIOCHAR, 100.0, duration_years=10)
        assert out["total_carbon_min"] <= out["total_carbon_tonnes"] <= out["total_carbon_max"], (
            f"min {out['total_carbon_min']} > point {out['total_carbon_tonnes']} "
            f"(max {out['total_carbon_max']})"
        )

    def test_biochar_annual_rate_is_not_double_scaled_by_area(self) -> None:
        out = calculate_carbon_sequestration(CarbonProjectType.BIOCHAR, 100.0, duration_years=10)
        assert out["annual_rate_tonnes"] == pytest.approx(
            out["total_carbon_tonnes"] / 10.0, rel=1e-6
        )

    def test_biochar_range_uses_the_one_time_basis(self) -> None:
        out = calculate_carbon_sequestration(CarbonProjectType.BIOCHAR, 100.0, duration_years=10)
        rates = SEQUESTRATION_RATES[CarbonProjectType.BIOCHAR]
        assert out["total_carbon_min"] == pytest.approx(
            rates["min"] * 100.0 * UNCERTAINTY_DISCOUNT, rel=1e-3
        )
        assert out["total_carbon_max"] == pytest.approx(
            rates["max"] * 100.0 * UNCERTAINTY_DISCOUNT, rel=1e-3
        )

    @pytest.mark.parametrize("project_type", list(CarbonProjectType))
    def test_revenue_is_tonnes_times_price(self, project_type: CarbonProjectType) -> None:
        out = calculate_carbon_sequestration(project_type, 50.0, duration_years=10)
        price = CARBON_PRICES["voluntary_market"]
        assert out["price_per_tonne_usd"] == price
        assert out["estimated_revenue_usd"] == pytest.approx(
            out["total_carbon_tonnes"] * price, rel=0.02
        )

    @pytest.mark.parametrize("project_type", ANNUALLY_SEQUESTERING)
    def test_annual_revenue_never_exceeds_total_revenue(
        self, project_type: CarbonProjectType
    ) -> None:
        """A ten-year project cannot earn more in one year than in all ten."""
        out = calculate_carbon_sequestration(project_type, 50.0, duration_years=10)
        assert out["annual_revenue_usd"] <= out["estimated_revenue_usd"] + 1.0, (
            f"{project_type.value}: annual {out['annual_revenue_usd']} > "
            f"total {out['estimated_revenue_usd']}"
        )

    def test_permanence_and_methodology_are_reported(self) -> None:
        out = calculate_carbon_sequestration(CarbonProjectType.AFFORESTATION, 10.0)
        assert (
            out["permanence_years"]
            == SEQUESTRATION_RATES[CarbonProjectType.AFFORESTATION]["permanence_years"]
        )
        assert "IPCC" in out["methodology"]
        assert out["confidence"] in {"low", "medium", "high"}


class TestScaling:
    @pytest.mark.parametrize("project_type", list(CarbonProjectType))
    def test_total_is_linear_in_area(self, project_type: CarbonProjectType) -> None:
        one = calculate_carbon_sequestration(project_type, 1.0)["total_carbon_tonnes"]
        hundred = calculate_carbon_sequestration(project_type, 100.0)["total_carbon_tonnes"]
        assert hundred == pytest.approx(100.0 * one, rel=0.02)

    @pytest.mark.parametrize("project_type", ANNUALLY_SEQUESTERING)
    def test_total_is_linear_in_duration(self, project_type: CarbonProjectType) -> None:
        five = calculate_carbon_sequestration(project_type, 10.0, duration_years=5)
        twenty = calculate_carbon_sequestration(project_type, 10.0, duration_years=20)
        assert twenty["total_carbon_tonnes"] == pytest.approx(
            4.0 * five["total_carbon_tonnes"], rel=0.01
        )

    def test_tropical_beats_temperate_beats_arid(self) -> None:
        for project_type in CarbonProjectType:
            values = [
                calculate_carbon_sequestration(project_type, 10.0, region=r)["total_carbon_tonnes"]
                for r in ("tropical", "temperate", "arid")
            ]
            assert values[0] > values[1] > values[2], project_type.value

    def test_region_factors_match_the_documented_values(self) -> None:
        base = calculate_carbon_sequestration(
            CarbonProjectType.AFFORESTATION, 10.0, region="temperate"
        )["total_carbon_tonnes"]
        tropical = calculate_carbon_sequestration(
            CarbonProjectType.AFFORESTATION, 10.0, region="tropical"
        )["total_carbon_tonnes"]
        arid = calculate_carbon_sequestration(CarbonProjectType.AFFORESTATION, 10.0, region="arid")[
            "total_carbon_tonnes"
        ]
        assert tropical == pytest.approx(1.3 * base, rel=0.01)
        assert arid == pytest.approx(0.6 * base, rel=0.01)

    @given(
        area=st.floats(min_value=0.01, max_value=1e5, allow_nan=False),
        years=st.integers(min_value=1, max_value=100),
        project_type=st.sampled_from(list(CarbonProjectType)),
    )
    def test_never_negative_for_admissible_input(
        self, area: float, years: int, project_type: CarbonProjectType
    ) -> None:
        out = calculate_carbon_sequestration(project_type, area, duration_years=years)
        assert out["total_carbon_tonnes"] >= 0.0
        assert out["total_carbon_min"] >= 0.0
        assert out["total_carbon_max"] >= out["total_carbon_min"]


class TestInputValidation:
    def test_unknown_project_type_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown project type"):
            calculate_carbon_sequestration("afforestation", 10.0)  # type: ignore[arg-type]

    def test_biochar_with_zero_duration_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            calculate_carbon_sequestration(CarbonProjectType.BIOCHAR, 10.0, duration_years=0)

    @pytest.mark.parametrize("area", [-1.0, -50.0])
    def test_negative_area_is_rejected(self, area: float) -> None:
        with pytest.raises(ValueError):
            calculate_carbon_sequestration(CarbonProjectType.AFFORESTATION, area)

    def test_unknown_region_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            calculate_carbon_sequestration(
                CarbonProjectType.AFFORESTATION, 10.0, region="troppical"
            )

    @pytest.mark.parametrize("years", [0, -5])
    def test_non_positive_duration_is_rejected_for_annual_types(self, years: int) -> None:
        with pytest.raises(ValueError):
            calculate_carbon_sequestration(
                CarbonProjectType.AFFORESTATION, 10.0, duration_years=years
            )


class TestComparison:
    def test_every_project_type_is_ranked(self) -> None:
        result = compare_project_types(area_ha=100, duration_years=10)
        assert set(result["ranking"]) == {t.value for t in CarbonProjectType}

    def test_ranking_is_sorted_by_total_carbon(self) -> None:
        result = compare_project_types(area_ha=100, duration_years=10)
        by_name = {d["project_type"]: d["total_carbon_tonnes"] for d in result["details"]}
        values = [by_name[name] for name in result["ranking"]]
        assert values == sorted(values, reverse=True)

    def test_best_carbon_matches_the_ranking(self) -> None:
        result = compare_project_types(area_ha=100, duration_years=10)
        assert result["best_carbon"] == result["ranking"][0]

    def test_best_revenue_is_consistent_with_the_details(self) -> None:
        result = compare_project_types(area_ha=100, duration_years=10)
        revenues = {d["project_type"]: d["estimated_revenue_usd"] for d in result["details"]}
        assert result["best_revenue"] == max(revenues, key=revenues.get)

    def test_a_failing_project_type_is_reported_not_dropped(self, monkeypatch) -> None:
        import engine.hydroma.carbon.calculator as calc

        real = calc.calculate_carbon_sequestration

        def flaky(project_type, *args, **kwargs):
            if project_type is CarbonProjectType.AGROFORESTRY:
                raise RuntimeError("simulated failure")
            return real(project_type, *args, **kwargs)

        monkeypatch.setattr(calc, "calculate_carbon_sequestration", flaky)
        result = calc.compare_project_types(area_ha=100, duration_years=10)
        assert len(result["ranking"]) == len(CarbonProjectType), (
            "a raising project type was silently dropped from the comparison"
        )


class TestRegistryProvenance:
    @pytest.fixture(autouse=True)
    def _reset_registry(self):
        from engine.hydroma.carbon import calculator as calc

        original_projects = dict(calc._projects)
        calc._projects.clear()
        yield
        calc._projects.clear()
        calc._projects.update(original_projects)
        set_repository(None)

    def test_round_trip_through_the_in_memory_registry(self) -> None:
        project = CarbonProject(name="test", area_ha=10.0)
        project_id = register_project(project)
        assert get_project(project_id) is project
        assert [p.id for p in list_projects()] == [project_id]

    def test_status_filter(self) -> None:
        draft = CarbonProject(name="a", status="draft")
        verified = CarbonProject(name="b", status="verified")
        register_project(draft)
        register_project(verified)
        assert [p.name for p in list_projects(status="verified")] == ["b"]

    def test_unknown_project_returns_none(self) -> None:
        assert get_project("does-not-exist") is None

    def test_default_ids_are_unique(self) -> None:
        ids = {CarbonProject().id for _ in range(50)}
        assert len(ids) == 50

    def test_default_status_is_draft(self) -> None:
        assert CarbonProject().status == "draft"

    def test_declared_limitations_are_present(self) -> None:
        import inspect

        from engine.hydroma.carbon import calculator

        source = inspect.getsource(calculator)
        assert "LIMITATIONS" in source
        assert "Do NOT use" in source or "Do not use" in source

    def test_repository_failure_is_surfaced(self) -> None:
        class BrokenRepository:
            def create_project(self, **kwargs):
                raise RuntimeError("database unavailable")

        set_repository(BrokenRepository())
        with pytest.raises(RuntimeError, match="database unavailable"):
            register_project(CarbonProject(name="x", area_ha=1.0))

    def test_registry_is_not_shared_process_wide(self) -> None:
        import threading

        register_project(CarbonProject(name="baseline"))
        results: list[int] = []
        barrier = threading.Barrier(4)

        def worker() -> None:
            barrier.wait()
            register_project(CarbonProject(name="tenant"))
            results.append(len(list_projects()))

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(set(results)) == 1, (
            f"concurrent registration observed {sorted(set(results))} states"
        )
