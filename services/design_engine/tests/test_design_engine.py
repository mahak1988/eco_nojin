"""Tests for the design-engine services (irrigation and water structures)."""

from datetime import date, timedelta

import pytest

from services.design_engine.irrigation_design_service import (
    IrrigationDesigner,
    IrrigationDesignInput,
    IrrigationScheduleItem,
)


def _input(**overrides):
    payload = {
        "site_location_lat": 35.0,
        "site_location_lon": 51.0,
        "crop_type": "wheat",
        "area_ha": 1.0,
        "irrigation_type": "drip",
        "water_source_flow_m3hr": 10.0,
        "plant_spacing_m": 0.5,
        "row_spacing_m": 1.0,
    }
    payload.update(overrides)
    return IrrigationDesignInput(**payload)


class TestIrrigationDesignInput:
    """Tests for the input contract."""

    def test_a_valid_input_is_accepted(self):
        assert _input().area_ha == 1.0

    def test_a_latitude_out_of_range_is_refused(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _input(site_location_lat=200.0)

    def test_a_longitude_out_of_range_is_refused(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _input(site_location_lon=200.0)

    def test_a_zero_area_is_refused(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _input(area_ha=0.0)

    def test_a_negative_area_is_refused(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _input(area_ha=-1.0)

    def test_an_unknown_irrigation_type_is_refused(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _input(irrigation_type="not-a-type")


class TestDripDesign:
    """Tests for the drip-irrigation design."""

    @pytest.fixture
    def designer(self):
        return IrrigationDesigner()

    def test_the_design_produces_a_layout(self, designer):
        output = designer.execute(_input())
        assert output.design_id.startswith("DIP-")
        assert output.layout_geojson["type"] == "GeometryCollection"

    def test_the_equipment_list_counts_drippers(self, designer):
        output = designer.execute(_input())
        assert output.equipment_list["drippers"] > 0
        assert output.equipment_list["valves"] >= 1

    def test_the_plant_count_scales_with_the_area(self, designer):
        small = designer.execute(_input(area_ha=1.0))
        large = designer.execute(_input(area_ha=2.0))
        assert (
            large.design_summary["total_plants"] > small.design_summary["total_plants"]
        )

    def test_the_schedule_covers_the_season(self, designer):
        output = designer.execute(_input())
        assert len(output.irrigation_schedule) == 30

    def test_the_schedule_dates_do_not_overflow_the_month(self, designer):
        """The schedule must roll into the next month, not raise.

        The dates were built with ``date.today().replace(day=day + offset)``,
        which raises ``ValueError: day is out of range for month`` as soon as
        the offset crosses the end of the month -- so the drip design failed
        for most of the calendar month.
        """
        output = designer.execute(_input())
        for item in output.irrigation_schedule:
            assert isinstance(item, IrrigationScheduleItem)
            assert item.date >= date.today()

    def test_the_schedule_is_chronological(self, designer):
        output = designer.execute(_input())
        dates = [item.date for item in output.irrigation_schedule]
        assert dates == sorted(dates)

    def test_the_schedule_is_within_the_season(self, designer):
        output = designer.execute(_input())
        first = output.irrigation_schedule[0].date
        last = output.irrigation_schedule[-1].date
        assert last - first <= timedelta(days=95)


class TestSprinklerDesign:
    """Tests for the sprinkler design."""

    @pytest.fixture
    def designer(self):
        return IrrigationDesigner()

    def test_the_sprinkler_design_produces_equipment(self, designer):
        output = designer.execute(_input(irrigation_type="sprinkler"))
        assert output.design_id.startswith("SPR-")
        assert output.equipment_list


class TestFurrowDesign:
    """Tests for the furrow design."""

    @pytest.fixture
    def designer(self):
        return IrrigationDesigner()

    def test_the_furrow_design_produces_equipment(self, designer):
        output = designer.execute(_input(irrigation_type="furrow"))
        assert output.design_id.startswith("FUR-")
        assert output.equipment_list
