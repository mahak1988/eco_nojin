"""Validation reference data and cases for the HyDroMa models.

Before this work, everything here was inert: the package ``__init__`` was a single
docstring line, no module imported ``reference_data``, nothing read a YAML case
file, and nothing loaded a ``.npy``. The corpus was written with citations and
never connected to the implementations it was meant to check.

``loader`` reads the cases and the stored reference values. ``runner`` compares
an implementation against a case and reports, separately, a genuine mismatch and
a case that cannot be satisfied by any correct implementation.
"""

from __future__ import annotations

from .loader import (
    CASE_DIR,
    REFERENCE_DIR,
    ValidationCase,
    available_references,
    case_names,
    corpus_summary,
    expand_case,
    expand_repeats,
    load_all_cases,
    load_cases,
    load_reference,
    reference_metadata,
)
from .runner import CaseOutcome, report, run_all, run_case, summary

__all__ = [
    "CASE_DIR",
    "CaseOutcome",
    "REFERENCE_DIR",
    "ValidationCase",
    "available_references",
    "case_names",
    "corpus_summary",
    "load_all_cases",
    "load_cases",
    "load_reference",
    "reference_metadata",
    "report",
    "run_all",
    "run_case",
    "summary",
]
