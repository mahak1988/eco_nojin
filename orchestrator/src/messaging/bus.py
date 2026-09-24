import json
import nats
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy, ConsumerConfig
from typing import Any, Dict, Callable, Optional, List
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Message:
    subject: str
    data: Dict[str, Any]
    timestamp: datetime
    headers: Dict[str, str]


class MessageBus:
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc: Optional[nats.NATS] = None
        self.js: Optional[JetStreamContext] = None
        self.subscriptions: Dict[str, Any] = {}

    async def connect(self):
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        await self._setup_streams()
        logger.info(f"Connected to NATS at {self.nats_url}")

    async def _setup_streams(self):
        """Create JetStream streams for different event categories"""
        streams = [
            StreamConfig(
                name="TASK_EVENTS",
                subjects=["task.*"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=100000,
                max_age=86400,  # 24 hours
                storage="file",
            ),
            StreamConfig(
                name="AGENT_EVENTS",
                subjects=["agent.*"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=50000,
                max_age=86400,
                storage="file",
            ),
            StreamConfig(
                name="STATE_EVENTS",
                subjects=["state.*"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=10000,
                max_age=86400,
                storage="file",
            ),
            StreamConfig(
                name="APPROVAL_EVENTS",
                subjects=["approval.*"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=10000,
                max_age=86400,
                storage="file",
            ),
            StreamConfig(
                name="SYSTEM_EVENTS",
                subjects=["system.*"],
                retention=RetentionPolicy.LIMITS,
                max_msgs=10000,
                max_age=86400,
                storage="file",
            ),
        ]

        for stream in streams:
            try:
                await self.js.add_stream(stream)
            except Exception as e:
                if "stream name already in use" not in str(e):
                    logger.warning(f"Stream setup warning: {e}")

    async def publish(self, subject: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None):
        """Publish message to subject"""
        if not self.nc or not self.nc.is_connected:
            raise RuntimeError("NATS not connected")

        payload = json.dumps({
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }).encode()

        headers_dict = headers or {}
        headers_dict["Nats-Msg-Id"] = f"{datetime.utcnow().timestamp()}"

        await self.nc.publish(
            subject,
            payload,
            headers=headers_dict
        )

    async def request(self, subject: str, data: Dict[str, Any], timeout: float = 5.0) -> Optional[Dict]:
        """Request-reply pattern"""
        payload = json.dumps({
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }).encode()

        try:
            response = await self.nc.request(subject, payload, timeout=timeout)
            return json.loads(response.data.decode())
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    async def subscribe(self, subject: str, callback: callable, queue: Optional[str] = None) -> str:
        """Subscribe to subject with callback"""
        async def handler(msg):
            try:
                data = json.loads(msg.data.decode())
                await callback(Message(
                    subject=msg.subject,
                    data=data.get("data", {}),
                    timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
                    headers=dict(msg.headers) if msg.headers else {}
                ))
            except Exception as e:
                logger.error(f"Message handler error: {e}")

        if queue:
            sub = await self.nc.subscribe(subject, queue=queue, cb=handler)
        else:
            sub = await self.nc.subscribe(subject, cb=handler)
        
        sub_id = f"{subject}_{id(sub)}"
        self.subscriptions[sub_id] = sub
        return sub_id

    async def unsubscribe(self, sub_id: str):
        if sub_id in self.subscriptions:
            await self.subscriptions[sub_id].unsubscribe()
            del self.subscriptions[sub_id]

    async def close(self):
        for sub in self.subscriptions.values():
            await sub.unsubscribe()
        self.subscriptions.clear()
        if self.nc:
            await self.nc.drain()


# Subject constants
class Subjects:
    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_BLOCKED = "task.blocked"
    TASK_CANCELLED = "task.cancelled"
    TASK_PROGRESS = "task.progress"

    # Agent lifecycle
    AGENT_STARTED = "agent.started"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_STOPPED = "agent.stopped"
    AGENT_CRASHED = "agent.crashed"
    AGENT_HEALTH_CHANGED = "agent.health_changed"

    # State changes
    STATE_UPDATED = "state.updated"
    STATE_SYNC = "state.sync"

    # Approval gates
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXPIRED = "approval.expired"
    APPROVAL_ESCALATED = "approval.escalated"

    # Cross-agent events
    CHECKOUT_COMPLETED = "checkout.completed"
    ORDER_CREATED = "order.created"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_DISPUTED = "order.disputed"
    ESCROW_LOCKED = "escrow.locked"
    ESCROW_RELEASED = "escrow.released"
    ESCROW_DISPUTED = "escrow.disputed"
    BAZAAR_ESTABLISHED = "bazaar.established"
    STORE_CREATED = "store.created"

    # System
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_CRASHED = "agent.crashed"
    HUMAN_APPROVAL_REQUIRED = "human.approval.required"
    DEADLOCK_DETECTED = "deadlock.detected"
    TASK_STUCK = "task.stuck"
    APPROVAL_GATE_TIMEOUT = "approval.gate.timeout"


class EventPublisher:
    def __init__(self, bus: 'MessageBus'):
        self.bus = bus

    async def task_created(self, task_id: str, agent_id: str, data: Dict):
        await self.bus.publish(Subjects.TASK_CREATED, {
            "task_id": task_id,
            "agent_id": agent_id,
            "data": data
        })

    async def task_started(self, task_id: str, agent_id: str):
        await self.bus.publish(Subjects.TASK_STARTED, {
            "task_id": task_id,
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def task_completed(self, task_id: str, agent_id: str, result: Dict):
        await self.bus.publish(Subjects.TASK_COMPLETED, {
            "task_id": task_id,
            "agent_id": agent_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def task_failed(self, task_id: str, agent_id: str, error: str, retry_count: int):
        await self.bus.publish(Subjects.TASK_FAILED, {
            "task_id": task_id,
            "agent_id": agent_id,
            "error": error,
            "retry_count": retry_count,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def task_progress(self, task_id: str, agent_id: str, progress: float):
        await self.bus.publish(Subjects.TASK_PROGRESS, {
            "task_id": task_id,
            "agent_id": agent_id,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def agent_started(self, agent_id: str, group: str):
        await self.bus.publish(Subjects.AGENT_STARTED, {
            "agent_id": agent_id,
            "group": group,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def agent_heartbeat(self, agent_id: str, status: str, current_task: Optional[str] = None):
        await self.bus.publish(Subjects.AGENT_HEARTBEAT, {
            "agent_id": agent_id,
            "status": status,
            "current_task": current_task,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def agent_health_changed(self, agent_id: str, old_status: str, new_status: str):
        await self.bus.publish(Subjects.AGENT_HEALTH_CHANGED, {
            "agent_id": agent_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def checkout_completed(self, order_id: str, transaction_key: str):
        await self.bus.publish(Subjects.CHECKOUT_COMPLETED, {
            "order_id": order_id,
            "transaction_key": transaction_key,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def order_created(self, order_id: str, buyer_id: str, seller_id: str, escrow_id: str):
        await self.bus.publish(Subjects.ORDER_CREATED, {
            "order_id": order_id,
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "escrow_id": escrow_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def order_shipped(self, order_id: str, tracking_number: str):
        await self.bus.publish(Subjects.ORDER_SHIPPED, {
            "order_id": order_id,
            "tracking_number": tracking_number,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def order_delivered(self, order_id: str):
        await self.bus.publish(Subjects.ORDER_DELIVERED, {
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def order_disputed(self, order_id: str, dispute_id: str, reason: str):
        await self.bus.publish(Subjects.ORDER_DISPUTED, {
            "order_id": order_id,
            "dispute_id": dispute_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def escrow_locked(self, escrow_id: str, amount: int, parties: List[str]):
        await self.bus.publish(Subjects.ESCROW_LOCKED, {
            "escrow_id": escrow_id,
            "amount": amount,
            "parties": parties,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def escrow_released(self, escrow_id: str, seller_id: str):
        await self.bus.publish(Subjects.ESCROW_RELEASED, {
            "escrow_id": escrow_id,
            "seller_id": seller_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def bazaar_established(self, bazaar_id: str, founders: List[str]):
        await self.bus.publish(Subjects.BAZAAR_ESTABLISHED, {
            "bazaar_id": bazaar_id,
            "founders": founders,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def store_created(self, store_id: str, bazaar_id: str, owner_id: str):
        await self.bus.publish(Subjects.STORE_CREATED, {
            "store_id": store_id,
            "bazaar_id": bazaar_id,
            "owner_id": owner_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def human_approval_required(self, gate_id: str, reason: str, roles: List[str]):
        await self.bus.publish(Subjects.HUMAN_APPROVAL_REQUIRED, {
            "gate_id": gate_id,
            "reason": reason,
            "required_roles": roles,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def deadlock_detected(self, cycle: List[str]):
        await self.bus.publish(Subjects.DEADLOCK_DETECTED, {
            "cycle": cycle,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def task_stuck(self, task_id: str, agent_id: str, duration: int):
        await self.bus.publish(Subjects.TASK_STUCK, {
            "task_id": task_id,
            "agent_id": agent_id,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def approval_gate_timeout(self, gate_id: str):
        await self.bus.publish(Subjects.APPROVAL_GATE_TIMEOUT, {
            "gate_id": gate_id,
            "timestamp": datetime.utcnow().isoformat()
        })