"""Ports: the engine's declared dependencies on the outside world.

Each protocol here is derived from a real call site in the engine, not from a
guess at what the engine might need. A port with no consumer is dead code and
is not created. See each module's docstring for the call sites that justify it.

=================================  ============================================
Port                               Justified by
=================================  ============================================
:class:`SessionPort`               13 persistence call sites
:class:`QueryPort`                 the ``query().filter().first()`` chain in them
:class:`SessionFactory`            how those 13 sites obtain a session
:class:`UnitOfWork`                 ``mrv/iot_ingest.get_latest_readings``
:class:`Clock`                     16 ``date.today()`` / ``datetime.now()``
                                    calls in calibration, biofertilizer
:class:`ReadingSink`               ``MqttIotConsumer(store=...)``
=================================  ============================================

Deliberately **not** here, because nothing consumes them:

* An event publisher. ``mrv/iot_ingest.py`` has no publish/emit/dispatch call
  anywhere. See ``sinks.py`` for the measurement.
* An HTTP client port. The engine makes no outbound HTTP call that is not
  already behind a lazily-imported connector in ``hydroma/data_pipeline``.
* A filesystem port. The engine reads DEMs and reference tables directly; only
  ``database`` is in scope for this change.

Importing this package is free of ``database``, ``services``, ``sqlalchemy``,
``fastapi``, ``httpx`` and ``pydantic_settings``. The one function that must
reach for ``database`` does so inside its body
(:func:`~engine.ports.session.default_session_factory`).
"""

from engine.ports.clock import Clock, FixedClock, SystemClock
from engine.ports.evidence_adapter import (
    ComputationRecord,
    EvidenceAdapter,
    default_evidence_adapter,
)
from engine.ports.persistence import (
    FileBackedPersistence,
    InMemoryPersistence,
    PersistencePort,
    default_persistence_port,
)
from engine.ports.session import (
    QueryPort,
    SessionFactory,
    SessionPort,
    UnitOfWork,
    default_session_factory,
    default_unit_of_work,
    resolve_database_attr,
)
from engine.ports.sinks import NullReadingSink, ReadingSink

__all__ = [
    "Clock",
    "ComputationRecord",
    "EvidenceAdapter",
    "FileBackedPersistence",
    "FixedClock",
    "InMemoryPersistence",
    "NullReadingSink",
    "PersistencePort",
    "QueryPort",
    "ReadingSink",
    "SessionFactory",
    "SessionPort",
    "SystemClock",
    "UnitOfWork",
    "default_evidence_adapter",
    "default_persistence_port",
    "default_session_factory",
    "default_unit_of_work",
    "resolve_database_attr",
]
