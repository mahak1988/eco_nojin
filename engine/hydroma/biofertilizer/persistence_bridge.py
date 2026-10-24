"""Persistence-port bridge for the biofertilizer calibration entry points.

Remediation item B-2 (``reports/eco-nojin/ARCHITECTURE-REMEDIATION-PLAN.md``)
asks for one thing: ``engine/hydroma/biofertilizer/calibration.py`` must stop
importing ``SessionLocal`` from ``database.config`` and take the existing
``PersistencePort`` abstraction by injection instead. This module is that
injection point.

What the port is
----------------
``calibration.py`` consumes exactly two things from persistence: the two ORM
row classes it names (``NojinFieldTrialDB`` for trial reads,
``NojinCalibrationRecordDB`` for the record it writes and reads back) and
something that produces a session over them. Those are the two methods of
:class:`CalibrationPersistencePort`, and their names are deliberately the ones
``engine.ports.session`` already expects of a production port –
``get_model_attr`` (see :func:`engine.ports.session.resolve_database_attr`) and
``get_session_factory`` (see :func:`engine.ports.session.default_session_factory`)
- so a production adapter that satisfies those helpers satisfies this protocol
unchanged.

The default (no port injected)
------------------------------
:class:`InProcessCalibrationPort`: a lazily built, in-process SQLite database
behind engine-local row classes. It imports nothing from ``database``, so
calibration runs - and is testable - with the services tier unwired. It is not
the production store: its rows are process-local and transient, and it exists
so the engine's default is "no database" rather than "a hidden one".

Why not ``SQLitePersistence`` / ``InMemoryPersistence``?
--------------------------------------------------------
Both implement the spec 4.5 *domain* contract (``save_dataset`` /
``save_model_run`` / ``save_evidence`` ...), which is a different surface from
the one calibration needs: a session over ORM rows, not a domain-object store.
They remain the right contract for the evidence / knowledge / decision
engines; neither can serve as calibration's session source, so the in-process
adapter below speaks the session surface directly.

Production wiring (services / adapters layer)
---------------------------------------------
The DB-backed adapter belongs to the application layer, which already owns the
``database`` imports. An adapter satisfying this protocol is two methods::

    class HubCalibrationPort:
        def get_session_factory(self):
            return hub.get_session_factory()   # database.config.SessionLocal

        def get_model_attr(self, module, name):
            ...  # resolve the ORM row class from database.models

and is handed to ``calibrate_formulation_model(..., port=...)`` /
``load_calibrated_model(..., port=...)``. The engine never imports it.
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol, runtime_checkable

from sqlalchemy import JSON, Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

__all__ = [
    "CalibrationPersistencePort",
    "InProcessCalibrationPort",
    "default_calibration_port",
]


@runtime_checkable
class CalibrationPersistencePort(Protocol):
    """The persistence surface the calibration entry points consume.

    ``database.hub.Hub`` already satisfies half of it (it has
    ``get_session_factory`` and only lacks ``get_model_attr``), so a production
    adapter over it is two small methods - see the module docstring.
    """

    def get_session_factory(self) -> Any:
        """Return a callable producing a ``SessionPort``-shaped session."""

    def get_model_attr(self, module: str, name: str) -> Any:
        """Return the ORM row class registered as ``<module>.<name>``.

        ``calibration.py`` resolves ``("models", "NojinFieldTrialDB")`` and
        ``("models", "NojinCalibrationRecordDB")`` through here.
        """


# --------------------------------------------------------------------------- #
# In-process rows
#
# A private declarative registry: these rows must never land on the shared
# ``database.base`` registry - that shared-registry coupling is exactly what
# B-2 removes - and a dedicated ``declarative_base()`` here is what buys the
# isolation.
# --------------------------------------------------------------------------- #

# mypy binds the constructor result as a single class object and rejects it as
# a base class; SQLAlchemy's ``declarative_base()`` is the documented,
# runtime-validated pattern (the same suppression
# ``engine/hydroma/biofertilizer/models.py`` uses for its either-or base
# fallback).
_InProcessBase = declarative_base()  # type: ignore[misc]


class _FieldTrialRow(_InProcessBase):  # type: ignore[misc, valid-type]
    """The trial columns ``calibration.py`` reads, on an in-process store."""

    __tablename__ = "nojin_field_trials_in_process"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    application_plan_id = Column(String(36))
    trial_location = Column(String(200))
    trial_date = Column(Date)
    crop_type = Column(String(100))
    plot_area_ha = Column(Float)
    treatment_design = Column(JSON)
    dosage_kg_ha = Column(Float)
    baseline_data = Column(JSON)
    post_application_data = Column(JSON)
    yield_response = Column(Float)
    soil_improvement = Column(JSON)
    observations = Column(String(500))
    statistical_analysis = Column(JSON)


class _CalibrationRecordRow(_InProcessBase):  # type: ignore[misc, valid-type]
    """The calibration-record columns ``calibration.py`` writes and reads."""

    __tablename__ = "nojin_calibration_records_in_process"

    id = Column(Integer, primary_key=True, autoincrement=True)
    formulation_id = Column(String(100), nullable=False)
    calibration_date = Column(Date, nullable=False)
    calibration_data = Column(JSON, nullable=False)
    model_version = Column(String(50), nullable=False)
    parameters_updated = Column(JSON)
    validation_results = Column(JSON)
    calibration_quality_score = Column(Float)
    calibrated_by = Column(String(100))


#: The row classes the port hands out, keyed by the ``name`` half of the
#: ``("models", name)`` pair ``calibration.py`` asks for.
_IN_PROCESS_MODELS = {
    "NojinFieldTrialDB": _FieldTrialRow,
    "NojinCalibrationRecordDB": _CalibrationRecordRow,
}

#: One shared in-memory database per port. ``StaticPool`` keeps a single
#: connection alive for the port's lifetime, so every session it produces sees
#: the same rows; a plain ``sqlite://`` pool would hand out a fresh, empty
#: in-memory database per connection.
_IN_PROCESS_URL = "sqlite://"


class InProcessCalibrationPort:
    """Database-free default port: in-memory SQLite over engine-local rows.

    Built on first use (lazily, by :func:`default_calibration_port`) rather
    than at import, so importing the engine still costs no database setup.
    """

    def __init__(self, url: str = _IN_PROCESS_URL) -> None:
        self._engine = create_engine(
            url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        _InProcessBase.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def get_session_factory(self) -> Any:
        """Return the in-process session factory (one engine per port)."""
        return self._session_factory

    def get_model_attr(self, module: str, name: str) -> Any:
        """Return the in-process row class for ``("models", name)``.

        Raises:
            AttributeError: for any other module/name pair, mirroring the
                production port's contract.
        """
        if module != "models":
            raise AttributeError(
                f"InProcessCalibrationPort has no module {module!r}"
            )
        try:
            return _IN_PROCESS_MODELS[name]
        except KeyError:
            raise AttributeError(
                f"InProcessCalibrationPort has no model {name!r} in {module!r}"
            ) from None


#: The process-wide default. Built on first use, never at import time.
_DEFAULT_PORT: InProcessCalibrationPort | None = None


def default_calibration_port() -> CalibrationPersistencePort:
    """Return the default calibration port, building it on first call.

    The default is the in-process adapter, so a caller that injects nothing
    gets a working (transient) store instead of a database import.
    """
    global _DEFAULT_PORT
    if _DEFAULT_PORT is None:
        _DEFAULT_PORT = InProcessCalibrationPort()
    return _DEFAULT_PORT
