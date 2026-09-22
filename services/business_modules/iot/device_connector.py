"""IoT device manager - connects DeviceManager service to MQTT backend.

This module wires the DeviceManager (services/business_modules/iot/device_manager.py)
with the MQTT broker for real-time device provisioning and status updates.

Usage:
    from services.business_modules.iot.device_connector import DeviceConnector
    connector = DeviceConnector(broker_host="localhost", broker_port=1883)
    connector.start()
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MQTTConfig:
    broker_host: str = "localhost"
    broker_port: int = 1883
    username: str | None = None
    password: str | None = None
    topics: tuple[str, ...] = ("hydroma/+/reading",)

    @property
    def is_configured(self) -> bool:
        return bool(self.broker_host)


class DeviceConnector:
    """Wires DeviceManager with MQTT broker for real-time updates.

    Subscribes to MQTT topics, persists readings via DeviceManager,
    and publishes device status updates.
    """

    def __init__(self, config: MQTTConfig | None = None):
        self.config = config or MQTTConfig()
        self._client = None
        self._device_manager = None

        try:
            from services.business_modules.iot.device_manager import DeviceManager

            self._device_manager = DeviceManager()
        except Exception as exc:
            logger.warning("DeviceManager import failed: %s", exc)

    def start(self):
        """Connect to MQTT broker and start listening."""
        if not self.config.is_configured:
            logger.warning("MQTT broker not configured - skipping connection")
            return

        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if self.config.username:
                self._client.username_pw_set(self.config.username, self.config.password)

            self._client.on_message = self._on_message
            self._client.connect(self.config.broker_host, self.config.broker_port, keepalive=30)

            for topic in self.config.topics:
                self._client.subscribe(topic)

            self._client.loop_start()
            logger.info(
                "MQTT device connector started on %s:%s",
                self.config.broker_host,
                self.config.broker_port,
            )
        except ImportError:
            logger.warning("paho-mqtt not installed - MQTT integration disabled")
        except Exception as exc:
            logger.warning("MQTT connection failed: %s", exc)

    def stop(self):
        """Disconnect from MQTT broker."""
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            logger.info("MQTT device connector stopped")

    def _on_message(self, _client, _userdata, message):
        """Handle incoming MQTT messages - persist readings."""
        import json

        try:
            data = json.loads(message.payload.decode("utf-8"))
            if self._device_manager:
                from engine.hydroma.mrv.iot_ingest import parse_ttn_v3

                readings = parse_ttn_v3({"uplink_message": {"decoded_payload": data}})
                for reading in readings:
                    # Persist via iot_ingest
                    try:
                        from database.hub import hub
                        from engine.hydroma.mrv.iot_ingest import persist_iot_reading

                        with hub.get_session() as session:
                            persist_iot_reading(session, reading)
                    except Exception as exc:
                        logger.warning("Failed to persist IoT reading: %s", exc)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("Malformed MQTT message: %s", exc)

    def publish_device_status(self, device_id: str, status: str):
        """Publish device status update to MQTT."""
        if self._client is None:
            return
        try:
            self._client.publish(
                f"hydroma/{device_id}/status",
                json.dumps({"device_id": device_id, "status": status}),
            )
        except Exception as exc:
            logger.warning("Failed to publish device status: %s", exc)
