"""Observation sink port.

Correction to the original design note
---------------------------------------
This port was specified as an *event publisher* for ``mrv/iot_ingest.py``.
That was wrong: ``iot_ingest.py`` publishes nothing. A search of the module for
``publish``/``emit``/``dispatch``/``EventBus`` returns no hits, and a search of
all of ``engine/`` for ``def publish``/``EventBus``/``EventPublisher`` returns
no files. The only "broker" in the module is the MQTT *subscriber* in
:class:`~engine.hydroma.mrv.iot_ingest.MqttIotConsumer`, which is inbound.

So this is a **sink**, not a publisher: the direction of travel is a validated
reading arriving from the network and needing somewhere to go. That is the
collateral ``MqttIotConsumer`` actually accepts, and it is where the real
injection point is.

The existing default is unchanged. ``MqttIotConsumer.__init__`` already
defaults ``store`` to a no-op lambda (``self._store = store or (lambda
_reading: None)``), so a constructed consumer has never required a broker or a
database. Naming that lambda as :class:`ReadingSink` and keeping
:class:`NullReadingSink` as the default preserves that behaviour exactly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["NullReadingSink", "ReadingSink"]


@runtime_checkable
class ReadingSink(Protocol):
    """Accepts one QA/QC-screened reading."""

    def __call__(self, reading: object) -> None:
        """Persist, forward, or discard one reading.

        ``object`` rather than a concrete schema so that this module keeps no
        import edge into ``mrv.schemas``; the consumer passes an ``IoTReading``
        and the implementation narrows it.
        """


class NullReadingSink:
    """Discards every reading. The historical default for an unconfigured
    consumer."""

    __slots__ = ()

    def __call__(self, reading: object) -> None:
        return None

    def __repr__(self) -> str:
        return "NullReadingSink()"
