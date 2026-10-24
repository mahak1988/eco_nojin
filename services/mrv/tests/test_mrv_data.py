"""Tests for the MRV field/lab data helpers."""

import json

import pytest

from services.mrv import kobo, lab_data


class TestAverageMeasuredSoc:
    """Tests for the mean soil-organic-carbon helper."""

    def test_no_submissions_gives_none(self):
        assert kobo.average_measured_soc({"submissions": []}) is None

    def test_a_missing_submissions_key_gives_none(self):
        assert kobo.average_measured_soc({}) is None

    def test_the_mean_is_computed(self):
        payload = {"submissions": [{"soc_t_ha": 2.0}, {"soc_t_ha": 4.0}]}
        assert kobo.average_measured_soc(payload) == 3.0

    def test_samples_without_a_value_are_skipped(self):
        payload = {"submissions": [{"soc_t_ha": 2.0}, {"soc_t_ha": None}, {}]}
        assert kobo.average_measured_soc(payload) == 2.0

    def test_every_sample_unusable_gives_none(self):
        payload = {"submissions": [{"soc_t_ha": None}, {}]}
        assert kobo.average_measured_soc(payload) is None

    def test_the_result_is_rounded_to_three_decimals(self):
        payload = {"submissions": [{"soc_t_ha": 1.0}, {"soc_t_ha": 2.0}, {"soc_t_ha": 2.0}]}
        assert kobo.average_measured_soc(payload) == 1.667


class TestLabData:
    """Tests for the local lab-sample store.

    The store is a JSON file on disk, so the tests point it at a throwaway
    directory.
    """

    @pytest.fixture(autouse=True)
    def _isolated_store(self, tmp_path, monkeypatch):
        data_dir = tmp_path / "lab"
        data_dir.mkdir()
        monkeypatch.setattr(lab_data, "DATA_DIR", str(data_dir))
        monkeypatch.setattr(lab_data, "STORE", str(data_dir / "lab_samples.json"))

    def _row(self, **overrides):
        row = {
            "lat": 35.0,
            "lon": 51.0,
            "soc_t_ha": 1.5,
            "depth_cm": 30,
            "lab": "lab-a",
        }
        row.update(overrides)
        return row

    def test_an_empty_store_lists_nothing(self):
        result = lab_data.list_lab_samples()
        assert result["count"] == 0
        assert result["status"] == "no_lab_data"

    def test_added_samples_are_listed(self):
        lab_data.add_lab_samples([self._row()])
        result = lab_data.list_lab_samples()
        assert result["count"] == 1
        assert result["status"] == "ok"

    def test_the_store_survives_a_reload(self):
        lab_data.add_lab_samples([self._row()])
        raw = json.loads(lab_data.STORE and open(lab_data.STORE, encoding="utf-8").read())
        assert len(raw) == 1
        assert raw[0]["lat"] == 35.0

    def test_a_row_out_of_range_is_rejected(self):
        result = lab_data.add_lab_samples([self._row(lat=200.0)])
        assert result["added"] == 0
        assert result["status"] == "no_valid_rows"
        assert result["errors"]

    def test_a_non_positive_soc_is_rejected(self):
        result = lab_data.add_lab_samples([self._row(soc_t_ha=0)])
        assert result["added"] == 0
        assert result["errors"]

    def test_a_missing_coordinate_is_rejected(self):
        result = lab_data.add_lab_samples([{"soc_t_ha": 1.5}])
        assert result["added"] == 0
        assert result["errors"]

    def test_a_valid_row_gets_a_generated_id(self):
        lab_data.add_lab_samples([self._row()])
        raw = json.loads(open(lab_data.STORE, encoding="utf-8").read())
        assert raw[0]["lab_id"].startswith("LAB-")

    def test_an_explicit_lab_id_is_kept(self):
        lab_data.add_lab_samples([self._row(lab_id="LAB-XYZ")])
        raw = json.loads(open(lab_data.STORE, encoding="utf-8").read())
        assert raw[0]["lab_id"] == "LAB-XYZ"

    def test_the_total_counts_the_previous_rows(self):
        lab_data.add_lab_samples([self._row()])
        result = lab_data.add_lab_samples([self._row()])
        assert result["added"] == 1
        assert result["total"] == 2
