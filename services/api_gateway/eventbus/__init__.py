"""
Event Bus Package
=================
NATS JetStream event bus for Eco Nojin.
"""

from services.api_gateway.eventbus.dlq import DLQHandler, get_dlq_handler
from services.api_gateway.eventbus.nats_client import (
    NATSConfig,
    NATSManager,
    get_nats_manager,
    init_nats,
    nats_lifespan,
    shutdown_nats,
)
from services.api_gateway.eventbus.publisher import (
    publish_carbon_event,
    publish_event,
    publish_farm_event,
    publish_marketplace_event,
    publish_mrv_event,
    publish_realtime_event,
    publish_simulation_event,
    publish_sync_event,
    publish_user_event,
)

__all__ = [
    "DLQHandler",
    "NATSConfig",
    "NATSManager",
    "get_dlq_handler",
    "get_nats_manager",
    "init_nats",
    "nats_lifespan",
    "publish_carbon_event",
    "publish_event",
    "publish_farm_event",
    "publish_marketplace_event",
    "publish_mrv_event",
    "publish_realtime_event",
    "publish_simulation_event",
    "publish_sync_event",
    "publish_user_event",
    "shutdown_nats",
]
