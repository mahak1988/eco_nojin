"""Decision — a navigable mirror of the spec §3.1 chain (re-export layer).

What this package is
--------------------
``engine/decision`` is the spec §3.1 *decision* node: the tier that turns
evidence and knowledge into a traceable decision. Today it is a re-export
layer. Every name below is imported from the module that owns it today —
``engine.tasmimyar``, the Decision Engine — so the chain stays navigable
without moving anything.

Module migration happens later, behind a mandate: A-4 step 2 migrates families
into this package one at a time, each behind a parity test. Nothing here has
started that migration — this file holds no scoring logic, no weights and no
branch of its own.

The TODAY-correct modules mirrored here
---------------------------------------
* ``engine.tasmimyar`` — the Decision Engine (``DecisionEngine`` and the
  ``Decision`` / ``DecisionCriterion`` / ``DecisionTrace`` vocabulary it
  produces).
* ``decision.weights_loader`` — the governance weights reader. It is
  *not* importable today: the root ``decision`` package holds
  ``weights.yaml`` (the governance record) and ``__init__.py`` only, so the
  shim exposes a documented placeholder instead of pretending the loader
  exists. The loader that actually reads ``decision/weights.yaml`` lives at
  ``engine.tasmimyar.weights_loader``; pointing at it here is navigation,
  not a move.
"""

from __future__ import annotations

from typing import Any

from engine.tasmimyar import (
    Decision,
    DecisionCriterion,
    DecisionEngine,
    DecisionOutcome,
    DecisionStatus,
    DecisionTrace,
    create_decision_engine,
    economic_criteria_weights,
)

try:  # ``decision`` is a real package; ``weights_loader`` has never existed in it.
    from decision.weights_loader import load_weights
except ImportError as _exc:  # pragma: no cover - the module is absent today
    _WEIGHTS_LOADER_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"

    def load_weights(*args: Any, **kwargs: Any) -> Any:
        """Placeholder for the absent ``decision.weights_loader`` module.

        Raised rather than returned so that a caller who reaches for the
        governance weights through this shim gets an actionable diagnostic
        instead of an ``ImportError`` at import time or a silent wrong answer.

        Raises:
            NotImplementedError: always. The governance weights are read from
                ``decision/weights.yaml`` by ``engine.tasmimyar.weights_loader``
                today; ``decision.weights_loader`` does not exist.
        """
        raise NotImplementedError(
            "decision.weights_loader does not exist: the root decision package "
            "holds weights.yaml (the governance record) and no loader module. "
            f"(import failed with {_WEIGHTS_LOADER_IMPORT_ERROR}). Read "
            "decision/weights.yaml through engine.tasmimyar.weights_loader."
        )

else:
    _WEIGHTS_LOADER_IMPORT_ERROR = ""

__all__ = [
    "Decision",
    "DecisionCriterion",
    "DecisionEngine",
    "DecisionOutcome",
    "DecisionStatus",
    "DecisionTrace",
    "create_decision_engine",
    "economic_criteria_weights",
    "load_weights",
]
