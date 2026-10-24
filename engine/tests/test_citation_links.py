"""Citation-extraction tests (X-10, offline).

The *resolution* of DOIs is network-only and therefore lives in the CI job
(``tools/check_citations.py``), never in the model runtime. What is testable
offline is the extraction itself: a citation the extractor cannot see is a
citation nobody will ever check, so the extraction is the part that needs
tests.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CHECKER_PATH = Path(__file__).resolve().parents[2] / "tools" / "check_citations.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_citations", _CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extracts_dois_from_realistic_prose() -> None:
    checker = _load_checker()
    text = (
        "van Genuchten (1980), https://doi.org/10.2136/sssaj1980-8439\n"
        "See also 10.1016/S0022-1694(01)00466-8, and Schaap et al. (2001) "
        "doi:10.1029/2000WR900130. A zenodo record 10.5281/zenodo.4725384 "
        "rounds it off."
    )
    found = checker.extract_dois(text)
    assert "10.2136/sssaj1980-8439" in found  # trailing newline stripped
    assert "10.1016/S0022-1694(01)00466-8" in found
    assert "10.1029/2000WR900130" in found
    assert "10.5281/zenodo.4725384" in found


def test_doi_cleaning_does_not_eat_payload() -> None:
    checker = _load_checker()
    # publisher-parenthesised DOIs keep their inner parentheses
    assert checker._clean_doi("10.1016/S0022-1694(01)00466-8") == "10.1016/S0022-1694(01)00466-8"
    assert checker._clean_doi("10.5281/zenodo.12345.") == "10.5281/zenodo.12345"
    assert checker._clean_doi("10.5281/zenodo.12345)") == "10.5281/zenodo.12345"
    # prose that opens its own parenthesis before the DOI is truncated at it
    assert checker._clean_doi("10.5281/zenodo.1(234") == "10.5281/zenodo.1"


def test_extracts_parenthesised_publisher_dois() -> None:
    checker = _load_checker()
    text = "Elsevier DOI 10.1016/S0022-1694(01)00466-8 appears inside prose (see 10.1016/j.hydro.2004.01.002)."
    found = checker.extract_dois(text)
    assert found == ["10.1016/S0022-1694(01)00466-8", "10.1016/j.hydro.2004.01.002"]


def test_scan_targets_cover_the_claims() -> None:
    checker = _load_checker()
    targets = checker.SCAN_TARGETS
    assert "engine/models/cards/*.md" in targets
    assert "indicators/*.yaml" in targets


def test_collect_files_finds_the_cards() -> None:
    checker = _load_checker()
    files = checker.collect_files(Path(__file__).resolve().parents[2])
    cards = [f for f in files if "cards" in str(f)]
    assert cards, "no model cards found — the checker would scan nothing"
