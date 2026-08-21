"""Tests: Phase 4 alert runner (real-data gating)."""
from services.bots.core.alert_runner import evaluate_farm_alerts, latest_real_satellite_row


class FakeSatRow:
    def __init__(self, ndvi, data_source):
        self.ndvi = ndvi
        self.evi = 0.3
        self.savi = 0.2
        self.data_source = data_source
        self.analyzed_at = "2026-08-16"


class FakeFarm:
    def __init__(self, name):
        self.name = name


class FakeDB:
    """Minimal stand-in for a SQLAlchemy Session."""

    def __init__(self, rows, farm):
        self._rows = rows
        self._farm = farm

    def query(self, model):
        return self

    def filter(self, *conds):
        return self

    def order_by(self, *cols):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def get(self, model, farm_id):
        return self._farm


def test_latest_real_satellite_row_prefers_copernicus():
    db = FakeDB(
        [FakeSatRow(0.2, "copernicus")],
        FakeFarm("مزرعه نمونه"),
    )
    row = latest_real_satellite_row(db, 1)
    assert row is not None
    assert row.data_source == "copernicus"


def test_evaluate_farm_alerts_empty_without_real_data():
    db = FakeDB([], FakeFarm("مزرعه نمونه"))
    assert evaluate_farm_alerts(db, 1) == []


def test_evaluate_farm_alerts_never_fires_on_simulated():
    db = FakeDB(
        [FakeSatRow(0.2, "simulated")],
        FakeFarm("مزرعه نمونه"),
    )
    assert evaluate_farm_alerts(db, 1) == []


def test_evaluate_farm_alerts_fires_on_real_low_ndvi():
    db = FakeDB(
        [FakeSatRow(0.20, "copernicus")],
        FakeFarm("مزرعه نمونه"),
    )
    messages = evaluate_farm_alerts(db, 1)
    assert len(messages) >= 1
    assert "مزرعه نمونه" in messages[0]
    assert "NDVI" in messages[0]
