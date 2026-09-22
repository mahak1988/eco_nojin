"""
Event Bus Package
=================
NATS JetStream event bus for Eco Nojin.
"""

from services.api_gateway.eventbus.nats_client import (
    NATSConfig,
    NATSManager,
    get_nats_manager,
    init_nats,
    shutdown_nats,
    nats_lifespan,
)
from services.api_gateway.eventbus.publisher import (
    publish_user_event,
    publish_sync_event,
    publish_realtime_event,
    publish_carbon_event,
    publish_mrv_event,
    publish_marketplace_event,
    publish_farm_event,
    publish_simulation_event,
    publish_event,
)
from services.api_gateway.eventbus.dlq import DLQHandler, get_dlq_handler

__all__ = [
    "NATSConfig",
    "NATSManager",
    "get_nats_manager",
    "init_nats",
    "shutdown_nats",
    "nats_lifespan",
    "publish_user_event",
    "publish_sync_event",
    "publish_realtime_event",
    "publish_carbon_event",
    "publish_mrv_event",
    "publish_marketplace_event",
    "publish_farm_event",
    "publish_simulation_event",
    "publish_event",
    "DLQHandler",
    "get_dlq_handler",
]