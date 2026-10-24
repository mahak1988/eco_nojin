"""IoT ingest adapters for MRV level 2: MQTT consumer + TTN v3 webhook parsing.

Persistence is shared with the REST API through :func:`persist_iot_reading`
so every path (MQTT, LoRaWAN webhook, direct REST) applies identical QA/QC
screening and the same audit-trail semantics: rejected rows are still
persisted with ``qa_status="rejected"`` and never feed dashboard metrics.
"""

from __future__ import annotations

import contextlib
import hmac
import json
import logging
from collections.abc import Callable
from typing import Any, cast

from engine.hydroma.mrv.qa import validate_reading
from engine.hydroma.mrv.schemas import IoTReading, SensorType
from engine.ports import (
    NullReadingSink,
    ReadingSink,
    SessionPort,
    UnitOfWork,
    default_unit_of_work,
    resolve_database_attr,
)

logger = logging.getLogger(__name__)

# Unit map for TTN v3 / LoRaWAN decoded payloads (field-name -> unit).
TTN_UNIT_MAP: dict[str, str] = {
    "soil_moisture": "%",
    "temp": "°C",
    "ec": "dS/m",
    "flow": "L/s",
}


def persist_iot_reading(db: SessionPort, reading: IoTReading):
    """QA/QC screen and persist one IoT reading; returns the stored row.

    The session is supplied by the caller rather than opened here, which is
    what lets the same function serve the REST route (which already has a
    session), the MQTT consumer, and a test with an in-memory double.
    """
    report = validate_reading(reading.sensor_type, reading.value, reading.unit)
    observation = resolve_database_attr("models", "MRVObservation")
    obs = observation(
        site_id=reading.site_id,
        level=2,
        source="iot",
        sensor_type=reading.sensor_type,
        value=reading.value,
        unit=reading.unit,
        payload=reading.model_dump(mode="json"),
        data_source="real",
        qa_status=report.qa_status,
        qa_message=report.message,
        observed_at=reading.ts,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


def parse_ttn_v3(payload: dict[str, Any], site_id: str | None = None) -> list[IoTReading]:
    """Parse a TTN v3 uplink into IoTReading objects.

    Supports two payload shapes:

    1. Direct: ``{"site_id": ..., "sensor_type": ..., "value": ..., "unit": ...}``
    2. Decoded: ``{"site_id": ..., "soil_moisture": 34.5, "temp": 21.3}`` with
       units inferred from :data:`TTN_UNIT_MAP`.

    Unreadable fields are skipped; an empty list means nothing usable.
    """
    readings: list[IoTReading] = []
    decoded = payload.get("uplink_message", {}).get("decoded_payload", payload)
    if not isinstance(decoded, dict):
        return readings

    sid = site_id or decoded.get("site_id") or payload.get("site_id")
    if sid is None:
        return readings

    if "sensor_type" in decoded and "value" in decoded:
        with contextlib.suppress(ValueError, TypeError):
            readings.append(
                IoTReading(
                    site_id=str(sid),
                    # The literal check inside IoTReading is the runtime
                    # filter: an unknown sensor type raises and is suppressed
                    # above, so the payload string is accepted as-is here.
                    sensor_type=cast("SensorType", str(decoded["sensor_type"])),
                    value=float(decoded["value"]),
                    unit=str(decoded.get("unit") or "-"),
                )
            )
        return readings

    for field_name, unit in TTN_UNIT_MAP.items():
        raw = decoded.get(field_name)
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            try:
                readings.append(
                    IoTReading(
                        site_id=str(sid),
                        # Same literal check as above; the except below is the
                        # filter for keys that are not a known sensor type.
                        sensor_type=cast("SensorType", field_name),
                        value=float(raw),
                        unit=unit,
                    )
                )
            except ValueError:
                continue
    return readings


def get_latest_readings(
    site_id: str,
    sensor_types: list[str] | None = None,
    limit: int = 10,
    # A context-manager *factory* (what default_unit_of_work() returns), not
    # the scope itself: ``with scope() as session`` calls it first.
    unit_of_work: Callable[[], UnitOfWork] | None = None,
) -> list[IoTReading]:
    """Fetch the most recent IoT readings for a site.

    Queries the MRVObservation table for level=2 (IoT) readings,
    filtered by site_id and optionally by sensor_types.

    Args:
        site_id: Site/parcel identifier
        sensor_types: Optional list of sensor types to filter (e.g., ["soil_moisture", "temp"])
        limit: Maximum number of readings to return (default 10)
        unit_of_work: Context-managed session source. Defaults to
            ``database.hub.hub.get_session()``, resolved on first call rather
            than at import.

    Returns:
        List of IoTReading objects, most recent first
    """
    observation = resolve_database_attr("models", "MRVObservation")
    scope = unit_of_work or default_unit_of_work()

    with scope() as session:
        query = session.query(observation).filter(
            observation.site_id == site_id,
            observation.level == 2,
            observation.source == "iot",
        )
        if sensor_types:
            query = query.filter(observation.sensor_type.in_(sensor_types))

        query = query.order_by(observation.observed_at.desc()).limit(limit)
        rows = query.all()

    readings: list[IoTReading] = []
    for row in rows:
        try:
            readings.append(
                IoTReading(
                    site_id=row.site_id,
                    sensor_type=row.sensor_type,
                    value=row.value,
                    unit=row.unit,
                    ts=row.observed_at,
                )
            )
        except (ValueError, TypeError):
            continue
    return readings


def webhook_key_ok(provided: str | None, expected: str) -> bool:
    """Constant-time comparison; an empty expected key means 'not configured'."""
    if not expected:
        return False
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)


class MqttIotConsumer:
    """MQTT subscriber that persists IoT readings through a store callback.

    The broker is only contacted when :meth:`start` is called, so importing
    or constructing the consumer never blocks or fails on missing brokers.
    """

    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        topics: tuple[str, ...] = ("hydroma/+/reading",),
        store: ReadingSink | None = None,
    ) -> None:
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._username = username
        self._password = password
        self._topics = topics
        self._store: ReadingSink = store or NullReadingSink()
        self._client: Any = None

    def start(self) -> MqttIotConsumer:
        """Connect and subscribe; raises RuntimeError when paho-mqtt is absent."""
        try:
            import paho.mqtt.client as mqtt  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on env
            raise RuntimeError("paho-mqtt is not installed; run: pip install paho-mqtt") from exc

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self._username:
            client.username_pw_set(self._username, self._password)
        client.on_message = self._on_message
        client.connect(self._broker_host, self._broker_port, keepalive=30)
        for topic in self._topics:
            client.subscribe(topic)
        client.loop_start()
        self._client = client
        logger.info(
            "MQTT consumer connected to %s:%s (topics=%s)",
            self._broker_host,
            self._broker_port,
            self._topics,
        )
        return self

    def stop(self) -> None:
        """Disconnect from the broker and stop the network loop."""
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None

    def _on_message(self, _client: Any, _userdata: Any, message: Any) -> None:
        """Parse one MQTT message and persist it; malformed messages are logged."""
        try:
            data = json.loads(message.payload.decode("utf-8"))
            reading = IoTReading(**data)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("dropping malformed MQTT message: %s", exc)
            return
        try:
            self._store(reading)
        except Exception:
            logger.exception("failed to persist MQTT reading")
