"""Event Bus Package
===================
The single NATS JetStream stack for Eco Nojin.

Consolidated in phase 4 (S-EVENT). Two stacks previously existed:
``services/api_gateway/eventbus`` and ``services/event_bus``, with two
different implementations of subject naming, so one logical event could land on
two different subjects. The gateway stack is the survivor; the other was
deleted, and the working backoff/dead-letter behaviour was ported here from
``event_bus/retry.py`` because the gateway stack lacked it.

``dlq.py`` was removed with them. It implemented a full dead-letter store that
nothing ever called: the failure path used a bare ``nak()`` with no delay and
no attempt cap. Dead-lettering now happens inline in
``retry.retry_or_term``, which back off, publishes to the dead-letter subject
once the attempts are exhausted, and then terminates the message.
"""

from services.api_gateway.eventbus.nats_client import (
    NATSConfig,
    NATSManager,
    get_nats_manager,
    get_or_create_nats_manager,
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
from services.api_gateway.eventbus.retry import (
    DEAD_LETTER_SUFFIX,
    RetryPolicy,
    delivery_attempt,
    execute_with_retry,
    retry_or_term,
)
from services.api_gateway.eventbus.worker import EventWorker, run_worker

__all__ = [
    "DEAD_LETTER_SUFFIX",
    "EventWorker",
    "NATSConfig",
    "NATSManager",
    "RetryPolicy",
    "delivery_attempt",
    "execute_with_retry",
    "get_nats_manager",
    "get_or_create_nats_manager",
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
    "retry_or_term",
    "run_worker",
    "shutdown_nats",
]
