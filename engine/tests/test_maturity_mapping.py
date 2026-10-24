"""Maturity mapping (S0..S6) over the registry's status triple.

Covers ``engine/models/maturity.py``, the reporting view that translates the
registry's (implementation, verification, validation) statuses into the
maturity vocabulary of spec §4.4 (``models.maturity_level`` CHECK constraint)
and answers spec §6.6 ECO-06's "at least one model at maturity S3+" bar:

* every registered model maps to a level in the vocabulary;
* the summary is a reconcilable partition of the registry -- the counts sum to
  the number of registered models and ``s3_plus`` is exactly the models the
  mapping lifts to ``S3`` or above;
* an unknown id is an error, not a default level;
* and the honest gap: nothing maps above ``S3`` today, because the repository
  holds no independent reference-data validation, no documented calibration and
  no quantified uncertainty (spec gap G-S2/S6b). If that last test ever fails,
  the repository gained that evidence and the mapping -- not just this test --
  must be extended deliberately.
"""

from __future__ import annotations

import pytest

from engine.models.maturity import S_LEVELS, maturity_of, maturity_summary
from engine.models.registry import get_registry

#: The ECO-06 bar of spec §6.6: "S3 or above".
S3_PLUS = S_LEVELS[S_LEVELS.index("S3") :]


def test_every_registered_model_maps_to_valid_level() -> None:
    for model_id in get_registry().list_ids():
        assert maturity_of(model_id) in S_LEVELS


def test_summary_covers_all_models() -> None:
    summary = maturity_summary()
    counts = summary["counts"]
    assert sum(counts.values()) == len(get_registry().list_ids())

    expected = sorted(i for i in get_registry().list_ids() if maturity_of(i) in S3_PLUS)
    assert sorted(summary["s3_plus"]) == expected


def test_unknown_model_raises() -> None:
    with pytest.raises(KeyError):
        maturity_of("NO-SUCH-ID")


def test_no_model_above_s3_today() -> None:
    """Spec gap G-S2/S6b: no model reaches S4..S6 yet.

    ``S4`` needs an independent reference-data validation, ``S5`` a documented
    calibration with quantified uncertainty and ``S6`` independent validation +
    calibration + reproducibility. The registry's three status dimensions carry
    none of that, so the honest report is that the ladder stops at ``S3``.
    """
    counts = maturity_summary()["counts"]
    assert counts.get("S4", 0) + counts.get("S5", 0) + counts.get("S6", 0) == 0


def test_eco06_bar_is_met() -> None:
    """Spec §6.6 ECO-06 Definition of Done: at least one model at S3+."""
    summary = maturity_summary()
    assert summary["s3_plus"], "no model reaches S3+: the ECO-06 bar is not met"


def test_by_level_partitions_the_registry() -> None:
    """Every model is in exactly one bucket, and no bucket invents a model."""
    summary = maturity_summary()
    bucketed = [model_id for ids in summary["by_level"].values() for model_id in ids]
    assert sorted(bucketed) == sorted(get_registry().list_ids())
    assert len(bucketed) == len(set(bucketed))
