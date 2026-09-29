"""Provenance for anything the engine returns.

Why this module exists
----------------------

`engine/hydroma/simulation/contracts.py` already stated the rule in 2026:

    Every model output carries an explicit provenance: ``data_source`` is
    "simulated" for model runs (never mislabeled as measured data) and the
    ``model`` field records the engine (name + version) so dashboards can show
    where a number came from.

`engine/hydroma/models/base.py:73-80` stated it again, and explained the
failure it was written to prevent: "Several models in this codebase can return
a plausible number without running: a solver falls back to a mock, a surrogate
returns noise, and nothing about the returned value distinguishes that from a
real result."

The rule was correct. It was applied in three places and not in twenty-one.
Of the twenty-four result types under ``engine/`` at the time this module was
written, three carried provenance and twenty-one did not. The two that caused
the most damage were the two that had no field to carry it at all:

* ``mrv/nojin_mrv.py`` built satellite observations from hard-coded constants
  and fed them into carbon-credit pricing. ``SatelliteObservation`` had no
  provenance field, so a fabricated reading and a real one were the same object.
* ``simulation/hecras.py`` returned ``{"status": "safe", "factor_of_safety":
  1.8}``. ``HECRASOutput`` had no provenance field, so nothing downstream could
  tell a structural verdict from a constant.

Why an enum, and why no default
-------------------------------

``Literal`` rather than ``str`` so a typo is a validation error rather than a
label nobody queries.

No default, deliberately. A default is the thing that makes a field
optional in practice: ``data_source: str = "simulated"`` on ``ModelOutput``
let twenty call sites omit it, and any of them could have omitted it while
returning a measured number. Requiring the argument moves the decision to the
one place that knows the answer -- the function that produced the value.

Why provenance is not the same as the data's origin
---------------------------------------------------

A number can be computed from live satellite data and still be fabricated, and
a number can be entirely internal and still be honest. The two questions are
independent, and both are captured:

* ``data_source`` -- where the inputs came from
* ``computed`` -- whether the engine actually ran to produce this

A caller checking only one of them can still be misled, which is why
:class:`Provenance` carries both.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

#: Where the inputs to a result came from.
#:
#: ``measured``     a sensor, gauge or observation supplied the inputs
#: ``modelled``     the inputs were computed or estimated, not observed
#: ``simulated``    the inputs were synthesised, typically by the engine itself
#: ``unavailable``  nothing ran; the result says only that
DataSource = Literal["measured", "modelled", "simulated", "unavailable"]


class Provenance(BaseModel):
    """The mandatory companion to a number.

    Both fields are required. A caller can then ask "was this computed?" and
    "where did the inputs come from?" without knowing which model produced it,
    which is the property the original docstrings asked for and could not get
    while ``data_source`` had a default.

    Attributes:
        data_source: Where the inputs came from.
        model: The engine that produced the value, with its version, so a
            dashboard can attribute the number later. A bare name is enough
            here; the registry in ``models/expansion`` carries versions.
        computed: Whether the engine actually ran. ``False`` means the result
            exists only to explain why a value is missing, and any numeric
            field beside it is not a result.
    """

    data_source: DataSource = Field(
        description="Where the inputs came from. Required: no default, so a "
        "call site cannot forget it and be wrong."
    )
    model: str = Field(
        description="Engine that produced this value, name and version where known."
    )
    computed: bool = Field(
        default=True,
        description="False when nothing ran and the result only explains why.",
    )


class ProvenanceCarrier:
    """Provenance for the duck-typed results in ``simulation/contracts.py``.

    Twelve of those classes accept ``*args, **kwargs`` and store whatever they
    are given, so they validate nothing. That is a separate defect and it is
    what let the orchestrator build a ``SWATInput`` missing two required
    fields. This base does not fix that, but it does stop the classes from
    being *unable* to say where a number came from.

    ``data_source`` and ``model`` are keyword-only and required. ``setattr``
    from the leftover ``kwargs`` cannot supply them, so a caller that omits one
    gets a ``TypeError`` at construction rather than a result nobody can
    attribute.
    """

    __slots__ = ("data_source", "model", "computed")

    def __init__(self, *, data_source: DataSource, model: str, computed: bool = True):
        self.data_source = data_source
        self.model = model
        self.computed = computed

    def provenance(self) -> dict:
        """The three fields as a plain dict, for embedding in a payload."""
        return {
            "data_source": self.data_source,
            "model": self.model,
            "computed": self.computed,
        }
