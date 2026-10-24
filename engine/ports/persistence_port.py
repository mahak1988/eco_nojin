"""Spec §4.5 persistence port: the abstract ``PersistencePort`` contract.

This module hosts the abstract persistence contract of section ۴.۵
("Persistence Port / قرارداد انتزاعی") of ``ECO-NOJIN MASTER EXECUTION
SPECIFICATION.md`` at the exact file location the spec mandates:
``engine/ports/persistence_port.py``. The ABC below reproduces that
section's eleven ``@abstractmethod`` declarations — ``save_dataset``,
``get_dataset``, ``save_model_run``, ``get_model_run``, ``save_evidence``,
``get_evidence``, ``save_claim``, ``link_evidence_to_claim``,
``get_claim_evidence``, ``save_scenario`` and ``save_decision`` — with
their names, order, signatures, defaults and semantics unchanged. Only the
annotation syntax is modernised (``dict`` / ``list`` / ``X | None``, the
house style of ``engine/ports`` — see :mod:`engine.ports.persistence_impl`)
because Python 3.11+ is the floor.

This is *not* the engine's production persistence port. That interface is
the pre-existing ``PersistencePort`` ``typing.Protocol`` in
:mod:`engine.ports.persistence` — a different contract with a different
surface: ``get_duckdb`` / ``get_sqlite`` / ``get_duckdb_pooled`` /
``return_duckdb_pooled`` for database access, plus the domain methods
``save_evidence(Evidence)`` / ``load_evidence`` / ``save_fact`` /
``load_fact`` / ``save_decision`` / ``load_decision`` / ``list_evidence``,
which the engine consumes through dependency injection.

The two contracts share a class name but not a method surface, and each
keeps its own module and definition. They are designed to COEXIST: this
module neither imports, edits nor re-exports the production ``Protocol``,
and :mod:`engine.ports.persistence` (and the rest of the existing
``engine/ports`` package) is untouched by it.

Migrating production callers from the ``Protocol`` to this ABC is a
Wave-3+ decision: it is a public API change (brake 2) and requires an
explicit mandate. Until then, nothing in the engine depends on this
module; its consumer is the spec-conformant SQLite adapter at
``adapters/persistence/sqlite_persistence.py``.
"""

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["PersistencePort"]


class PersistencePort(ABC):
    """Abstract persistence contract (spec §4.5), reproduced verbatim."""

    @abstractmethod
    def save_dataset(self, dataset: dict[str, Any]) -> str:
        """returns dataset_id"""
        pass

    @abstractmethod
    def get_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def save_model_run(self, model_run: dict[str, Any]) -> str:
        """returns run_id"""
        pass

    @abstractmethod
    def get_model_run(self, run_id: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def save_evidence(self, evidence: dict[str, Any]) -> str:
        """returns evidence_id"""
        pass

    @abstractmethod
    def get_evidence(self, evidence_id: str) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def save_claim(self, claim: dict[str, Any]) -> str:
        """returns claim_id"""
        pass

    @abstractmethod
    def link_evidence_to_claim(
        self,
        claim_id: str,
        evidence_id: str,
        relationship: str,
        weight: float = 1.0,
    ) -> None:
        pass

    @abstractmethod
    def get_claim_evidence(self, claim_id: str) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def save_scenario(self, scenario: dict[str, Any]) -> str:
        pass

    @abstractmethod
    def save_decision(self, decision: dict[str, Any]) -> str:
        pass
