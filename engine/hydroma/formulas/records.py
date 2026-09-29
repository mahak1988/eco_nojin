"""Formula records: the shape every registered formula must take.

The point of the registry is that a formula cannot be added to this codebase
without declaring what it is, where it is implemented, what it is cited from, and
which test proves it. A record missing ``parity_tests`` is treated as invalid by
``registry.register`` -- see that module for the hard rules.

Provenance
----------
A formula does not have to have a published standard to belong here. Most
deployed science is novel work: a new index, a new composite, a reassembly of
published factors for a purpose they were not written for. Requiring a published
reference before such a formula could be recorded would keep exactly the
contributions most worth recording out of the registry.

``provenance`` therefore says where a formula comes from, and ``status`` says what
has been *checked* -- two independent questions:

``standard``
    The expression is a published result and the record cites it. Checked against
    the published value.
``novel``
    An original contribution of this project. There is no external standard and
    none is expected yet. It is checked against its own research definition
    (``research_definition``), plus the same internal guarantees every other
    formula gets: one canonical implementation, stated expression, bounded
    output, and tests. A novel formula is marked ``verified`` when that holds --
    not held back waiting for a standard that may never arrive.
``composite``
    Assembled here from published factors, but the composition is ours. Cites
    each factor; the product is a contribution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Status = Literal["verified", "divergent", "stub"]
Domain = Literal["scalar", "array", "both"]
Provenance = Literal["standard", "novel", "composite"]


@dataclass(frozen=True)
class FormulaRecord:
    """One physical quantity, its single canonical implementation, and its proof.

    Attributes
    ----------
    quantity:
        Unique name. Synonyms are not allowed to have their own records; that is
        how NDVI ended up with five implementations in the first place.
    canonical:
        Path to the module that owns the expression. Exactly one per quantity.
    literature_ref:
        Where the equation comes from. "A paper" is not enough; a number and
        edition is the point.
    units:
        Dimensional unit. Two implementations of "the same" number in different
        units are not a parity problem to be tolerated, they are two quantities.
    domain:
        Whether the implementation accepts scalars, arrays, or both.
    backend_priority:
        Ordered backend preference, decided by measurement rather than by which
        language the code was written in.
    parity_tests:
        Tests that prove the implementations agree. An empty tuple is rejected.
    reference_values:
        The anchor the implementation is checked against. For ``standard`` and
        ``composite`` these are published values. Checking against another
        implementation is a closed loop and proves nothing. For ``novel`` the
        anchor is the project's own research definition, named in
        ``research_definition``.
    provenance:
        ``standard``, ``novel`` or ``composite``. See the module docstring. A
        novel formula does not need a published standard and is not penalised
        for lacking one.
    research_definition:
        Path to the written definition of a novel contribution: the expression as
        a closed form, the rationale for each factor, the domain of validity,
        and the intended range. Required when ``provenance`` is ``novel``.
    status:
        ``verified`` when the anchors above hold and the tests pass -- for a
        novel formula, against its own research definition rather than against a
        standard. ``divergent`` is allowed while a formula is being reconciled
        and is refused for anything on a request path.
    notes:
        Measured facts. No plans.
    """

    quantity: str
    canonical: str
    literature_ref: str
    units: str
    domain: Domain
    backend_priority: tuple[str, ...]
    parity_tests: tuple[str, ...]
    reference_values: str | None = None
    status: Status = "stub"
    provenance: Provenance = "standard"
    research_definition: str | None = None
    stub_reason: str = ""
    backends_impl: dict[str, bool] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.parity_tests:
            raise ValueError(
                f"{self.quantity}: a formula without parity_tests is not registrable. "
                "An unproven implementation is exactly what the registry exists to prevent."
            )
        if self.provenance == "novel" and not self.research_definition:
            raise ValueError(
                f"{self.quantity}: a novel formula must name its research_definition. "
                "A contribution with no written definition cannot be reviewed, "
                "reproduced, or improved."
            )
        if self.status == "verified" and not self.reference_values:
            raise ValueError(
                f"{self.quantity}: status 'verified' requires an anchor in "
                "reference_values -- published values for a standard or composite, "
                "or the research definition's own anchor cases for a novel formula. "
                "Parity with another implementation is a closed loop and proves "
                "nothing."
            )
        if self.status == "stub" and not self.stub_reason.strip():
            raise ValueError(
                f"{self.quantity}: a stub must state why in `stub_reason`. A record "
                "that is unusable without saying what is missing is an unexamined gap "
                "dressed as an honest one."
            )

    @property
    def is_verified(self) -> bool:
        return self.status == "verified"
