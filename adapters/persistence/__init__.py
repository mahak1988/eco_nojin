"""Persistence adapters for the ECO-04 §4.5 persistence contract.

Exports the SQLite-backed adapter implementing the abstract
``PersistencePort`` contract from section ۴.۵ of
``docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md``.
"""

from engine.ports.persistence_port import PersistencePort

from .sqlite_persistence import SQLitePersistence

__all__ = ["PersistencePort", "SQLitePersistence"]
