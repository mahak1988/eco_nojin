"""NATS JetStream configuration for Eco Nojin events."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EventBusConfig:
    """Runtime settings used by the NATS JetStream client modules."""

    servers: tuple[str, ...]
    user: str | None = None
    password: str | None = None
    token: str | None = None
    stream: str = "ECONOJIN"
    subject_prefix: str = "econojin.events"
    durable_consumer: str = "econojin-workers"
    consumer_queue: str = ""
    max_retries: int = 5
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    connect_timeout: float = 2.0
    enabled: bool = True

    @classmethod
    def from_settings(cls, settings: Any = None) -> EventBusConfig:
        """Build configuration from the shared application settings."""
        if settings is None:
            from engine.hydroma.config.settings import get_settings

            settings = get_settings()

        def value(name: str, default: Any = None) -> Any:
            if isinstance(settings, Mapping):
                return settings.get(name, default)
            return getattr(settings, name, default)

        def bool_value(name: str, default: bool) -> bool:
            raw = value(name, default)
            if isinstance(raw, bool):
                return raw
            return str(raw).strip().lower() in {"1", "true", "yes", "on"}

        servers_value = value("nats_servers", "") or value("nats_url", "nats://localhost:4222")
        if isinstance(servers_value, str):
            servers = tuple(server.strip() for server in servers_value.split(",") if server.strip())
        else:
            servers = tuple(str(server).strip() for server in servers_value if str(server).strip())

        max_retries = int(value("nats_max_retries", 5))
        retry_base_delay = float(value("nats_retry_base_delay", 1.0))
        retry_max_delay = float(value("nats_retry_max_delay", 60.0))

        return cls(
            servers=servers or ("nats://localhost:4222",),
            user=value("nats_user", "") or None,
            password=value("nats_password", "") or None,
            token=value("nats_token", "") or None,
            stream=value("nats_stream", "ECONOJIN"),
            subject_prefix=value("nats_subject_prefix", "econojin.events"),
            durable_consumer=value(
                "nats_durable_consumer", value("nats_durable", "econojin-workers")
            ),
            consumer_queue=value("nats_consumer_queue", value("nats_queue", "")),
            max_retries=max_retries,
            retry_base_delay=retry_base_delay,
            retry_max_delay=retry_max_delay,
            connect_timeout=float(value("nats_connect_timeout", 2.0)),
            enabled=bool_value("enable_event_bus", True),
        )

    @classmethod
    def from_env(cls) -> EventBusConfig:
        """Build configuration from the current process environment."""
        return cls.from_settings()

    def subject_for(self, event_type: str) -> str:
        """Return the JetStream subject for an event type."""
        if not event_type or any(character in event_type for character in (" ", ">", "*")):
            raise ValueError("event_type must be a non-empty NATS subject segment")
        return f"{self.subject_prefix.rstrip('.')}.{event_type.lstrip('.')}"


__all__ = ["EventBusConfig"]
