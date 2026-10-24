"""Tests for the science knowledge helpers (AGROVOC, datasets, citations)."""

import os

import pytest

from services.science import agrovoc, citations, datasets


class TestAgrovoc:
    """Tests for the offline AGROVOC map."""

    def test_map_is_not_empty(self):
        assert len(agrovoc.AGROVOC_MAP) > 0

    def test_every_entry_has_the_required_keys(self):
        for entry in agrovoc.AGROVOC_MAP:
            assert entry["term"]
            assert entry["term_en"]
            assert entry["uri"]
            assert entry["group"]
            assert entry["aliases"]

    def test_every_uri_points_at_agrovoc(self):
        for entry in agrovoc.AGROVOC_MAP:
            assert entry["uri"].startswith(agrovoc.AGROVOC_BASE)

    def test_uris_carry_a_concept_code(self):
        """A URI without a ``c_<id>`` concept code is not an AGROVOC concept."""
        for entry in agrovoc.AGROVOC_MAP:
            assert "/c_" in entry["uri"]

    def test_concept_codes_are_unique(self):
        codes = [e["uri"].rsplit("c_", 1)[-1] for e in agrovoc.AGROVOC_MAP]
        assert len(codes) == len(set(codes))

    def test_english_terms_are_unique(self):
        terms = [e["term_en"] for e in agrovoc.AGROVOC_MAP]
        assert len(terms) == len(set(terms))

    def test_every_concept_is_reachable_by_its_own_name(self):
        """The exact lookup must resolve every concept by its own names."""
        for entry in agrovoc.AGROVOC_MAP:
            assert agrovoc.agrovoc_uri_for_term(entry["term_en"]) == entry["uri"]
            assert agrovoc.agrovoc_uri_for_term(entry["term"]) == entry["uri"]

    def test_every_alias_resolves_to_a_uri(self):
        for entry in agrovoc.AGROVOC_MAP:
            for alias in entry["aliases"]:
                assert agrovoc.agrovoc_uri_for_term(alias) == entry["uri"]

    def test_unknown_term_returns_none(self):
        assert agrovoc.agrovoc_uri_for_term("not-a-real-agrovoc-term") is None

    def test_search_finds_a_concept_by_its_english_name(self):
        hits = agrovoc.agrovoc_search("maize")
        assert any(h["term_en"] == "maize" for h in hits)

    def test_search_on_an_empty_query_returns_nothing(self):
        assert agrovoc.agrovoc_search("   ") == []

    def test_stats_count_every_concept(self):
        stats = agrovoc.agrovoc_stats()
        assert sum(stats.values()) == len(agrovoc.AGROVOC_MAP)


class TestDatasetCatalog:
    """Tests for the dataset availability report."""

    def test_catalog_lists_datasets(self):
        catalog = datasets.dataset_catalog()
        assert catalog["count"] > 0
        assert len(catalog["datasets"]) == catalog["count"]

    def test_every_dataset_declares_its_status(self):
        catalog = datasets.dataset_catalog()
        for ds in catalog["datasets"]:
            assert ds["status"] in ("live", "offline")

    def test_no_dataset_claims_live_without_credentials(self):
        """A dataset may only be 'live' when its credentials are present."""
        cds = bool(os.environ.get("CDS_API_KEY"))
        cdse = bool(os.environ.get("CDSE_CLIENT_ID") or os.environ.get("CDSE_USERNAME"))
        catalog = datasets.dataset_catalog()
        by_id = {ds["id"]: ds for ds in catalog["datasets"]}
        if by_id.get("era5-cds"):
            assert by_id["era5-cds"]["status"] == ("live" if cds else "offline")
        if by_id.get("sentinel2-cdse"):
            assert by_id["sentinel2-cdse"]["status"] == ("live" if cdse else "offline")

    def test_every_dataset_states_its_requirements(self):
        catalog = datasets.dataset_catalog()
        for ds in catalog["datasets"]:
            assert ds["requires"]
            assert ds["license"]


class TestCitations:
    """Tests for the model citation helper."""

    def test_unknown_slug_is_refused(self):
        """The citation helper must never fabricate a reference."""
        with pytest.raises(ValueError, match="unknown model slug"):
            citations.citation_for_model("definitely-not-a-real-model")

    def test_citation_index_is_wellformed(self):
        index = citations.citation_index()
        assert index["count"] == len(index["items"])

    def test_index_entries_carry_a_citation_string(self):
        index = citations.citation_index()
        for item in index["items"]:
            assert item["citation"]
            assert item["reference"]
            assert item["slug"]
