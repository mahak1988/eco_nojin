"""IoT ingest adapters for MRV level 2: MQTT consumer + TTN v3 webhook parsing.

Persistence is shared with the REST API through :func:`persist_iot_reading`
so every path (MQTT, LoRaWAN webhook, direct REST) applies identical QA/QC
screening and the same audit-trail semantics: rejected rows are still
persisted with ``qa_status="rejected"`` and never feed dashboard metrics.
"""

from __future__ import annotations

import hmac
import json
import logging
from typing import Any, Callable

from database.models import MRVObservation
from engine.hydroma.mrv.qa import validate_reading
from engine.hydroma.mrv.schemas import IoTReading

logger = logging.getLogger(__name__)

# Unit map for TTN v3 / LoRaWAN decoded payloads (field-name -> unit).
TTN_UNIT_MAP: dict[str, str] = {
    "soil_moisture": "%",
    "temp": "°C",
    "ec": "dS/m",
    "flow": "L/s",
}


def persist_iot_reading(db, reading: IoTReading) -> MRVObservation:
    """QA/QC screen and persist one IoT reading; returns the stored row."""
    report = validate_reading(reading.sensor_type, reading.value, reading.unit)
    obs = MRVObservation(
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
        try:
            readings.append(
                IoTReading(
                    site_id=str(sid),
                    sensor_type=str(decoded["sensor_type"]),
                    value=float(decoded["value"]),
                    unit=str(decoded.get("unit") or "-"),
                )
            )
        except (ValueError, TypeError):
            pass
        return readings

    for field_name, unit in TTN_UNIT_MAP.items():
        raw = decoded.get(field_name)
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            try:
                readings.append(
                    IoTReading(site_id=str(sid), sensor_type=field_name, value=float(raw), unit=unit)
                )
            except ValueError:
                continue
    return readings


def webhook_key_ok(provided: str | None, expected: str) -> bool:
    """Constant-time comparison; an empty expected key means 'not configured'."""
    if not expected:
        return False
    return bool(provided) and hmac.compare_digest(provided, expected)


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
        store: Callable[[IoTReading], None] | None = None,
    ) -> None:
        self._broker_host = broker_host
        self._broker_port = broker_port
        self._username = username
        self._password = password
        self._topics = topics
        self._store = store or (lambda _reading: None)
        self._client: Any = None

    def start(self) -> "MqttIotConsumer":
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
        logger.info("MQTT consumer connected to %s:%s (topics=%s)", self._broker_host, self._broker_port, self._topics)
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
        except Exception:  # noqa: BLE001 - ingestion must not kill the loop
            logger.exception("failed to persist MQTT reading")
