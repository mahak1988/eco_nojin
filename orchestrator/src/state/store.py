import json
import redis.asyncio as redis
from typing import Any, Optional, List, Dict, Set
from datetime import datetime
import logging
from orchestrator.src.state.models import (
    OrchestratorState, TaskState, TaskSpec, TaskStatus,
    AgentHealth, AgentStatus, ApprovalGate, ApprovalGateStatus
)

logger = logging.getLogger(__name__)


class StateStore:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None

    async def connect(self):
        self.client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20
        )
        await self.client.ping()
        logger.info(f"Connected to Redis at {self.redis_url}")

    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.close()
        if self.client:
            await self.client.close()

    # --- Task Operations ---
    async def save_task(self, task_state: "TaskState") -> bool:
        key = f"task:{task_state.task.id}"
        data = task_state.model_dump_json()
        await self.client.set(key, data)
        await self.client.sadd("tasks:all", task_state.task.id)
        if task_state.task.status == TaskStatus.COMPLETED:
            await self.client.sadd("tasks:completed", task_state.task.id)
        elif task_state.task.status == TaskStatus.FAILED:
            await self.client.sadd("tasks:failed", task_state.task.id)
        elif task_state.task.status == TaskStatus.BLOCKED:
            await self.client.sadd("tasks:blocked", task_state.task.id)
        return True

    async def get_task(self, task_id: str) -> Optional["TaskState"]:
        from orchestrator.src.state.models import TaskState
        key = f"task:{task_id}"
        data = await self.client.get(key)
        if data:
            return TaskState.model_validate_json(data)
        return None

    async def update_task_status(self, task_id: str, status: TaskStatus, **kwargs) -> bool:
        task_state = await self.get_task(task_id)
        if not task_state:
            return False
        task_state.task.status = status
        for k, v in kwargs.items():
            if hasattr(task_state.task, k):
                setattr(task_state.task, k, v)
        return await self.save_task(task_state)

    async def get_tasks_by_status(self, status: TaskStatus) -> List[str]:
        key = f"tasks:{status.value}"
        return await self.client.smembers(key)

    async def add_task_log(self, task_id: str, log: str):
        key = f"task:{task_id}:logs"
        await self.client.rpush(key, f"[{datetime.utcnow().isoformat()}] {log}")

    async def get_task_logs(self, task_id: str, limit: int = 100) -> List[str]:
        key = f"task:{task_id}:logs"
        return await self.client.lrange(key, -limit, -1)

    # --- Agent Health ---
    async def update_agent_health(self, health: "AgentHealth") -> bool:
        key = f"agent:health:{health.agent_id}"
        data = health.model_dump_json()
        await self.client.set(key, data)
        await self.client.sadd("agents:all", health.agent_id)
        return True

    async def get_agent_health(self, agent_id: str) -> Optional["AgentHealth"]:
        from orchestrator.src.state.models import AgentHealth
        key = f"agent:health:{agent_id}"
        data = await self.client.get(key)
        if data:
            return AgentHealth.model_validate_json(data)
        return None

    async def get_all_agent_health(self) -> List["AgentHealth"]:
        from orchestrator.src.state.models import AgentHealth
        agent_ids = await self.client.smembers("agents:all")
        health_list = []
        for agent_id in agent_ids:
            health = await self.get_agent_health(agent_id)
            if health:
                health_list.append(health)
        return health_list

    async def update_agent_heartbeat(self, agent_id: str):
        key = f"agent:heartbeat:{agent_id}"
        await self.client.set(key, datetime.utcnow().isoformat(), ex=120)

    async def check_agent_alive(self, agent_id: str, timeout: int = 90) -> bool:
        key = f"agent:heartbeat:{agent_id}"
        last = await self.client.get(key)
        if not last:
            return False
        last_time = datetime.fromisoformat(last)
        return (datetime.utcnow() - last_time).total_seconds() < timeout

    # --- Approval Gates ---
    async def save_approval_gate(self, gate: "ApprovalGate") -> bool:
        from orchestrator.src.state.models import ApprovalGate
        key = f"approval:{gate.id}"
        data = gate.model_dump_json()
        await self.client.set(key, data)
        await self.client.sadd("approvals:all", gate.id)
        if gate.status == ApprovalGateStatus.PENDING:
            await self.client.sadd("approvals:pending", gate.id)
        return True

    async def get_approval_gate(self, gate_id: str) -> Optional["ApprovalGate"]:
        from orchestrator.src.state.models import ApprovalGate
        key = f"approval:{gate_id}"
        data = await self.client.get(key)
        if data:
            return ApprovalGate.model_validate_json(data)
        return None

    async def get_pending_approvals(self) -> List["ApprovalGate"]:
        from orchestrator.src.state.models import ApprovalGate
        gate_ids = await self.client.smembers("approvals:pending")
        gates = []
        for gid in gate_ids:
            gate = await self.get_approval_gate(gid)
            if gate:
                gates.append(gate)
        return gates

    # --- Feature Flags ---
    async def set_feature_flag(self, flag: str, value: bool):
        await self.client.set(f"feature:{flag}", str(value).lower())

    async def get_feature_flag(self, flag: str) -> bool:
        val = await self.client.get(f"feature:{flag}")
        return val == "true" if val else False

    # --- Audit Log ---
    async def append_audit(self, event: Dict[str, Any]):
        event["timestamp"] = datetime.utcnow().isoformat()
        await self.client.lpush("audit:log", json.dumps(event))
        await self.client.ltrim("audit:log", 0, 9999)

    async def get_audit_log(self, limit: int = 100) -> List[Dict]:
        logs = await self.client.lrange("audit:log", 0, limit - 1)
        return [json.loads(l) for l in logs]

    # --- Pub/Sub for real-time events ---
    async def publish(self, channel: str, message: Dict[str, Any]):
        await self.client.publish(channel, json.dumps(message))

    async def subscribe(self, channels: List[str]):
        self._pubsub = self.client.pubsub()
        await self._pubsub.subscribe(*channels)
        return self._pubsub

    async def listen(self):
        if not self._pubsub:
            return
        async for message in self._pubsub.listen():
            yield message

    # --- Full State Backup/Restore ---
    async def backup_state(self) -> str:
        """Export full state as JSON"""
        keys = await self.client.keys("*")
        data = {}
        for key in keys:
            if await self.client.type(key) == "string":
                data[key] = await self.client.get(key)
        return json.dumps(data, indent=2)

    async def restore_state(self, json_data: str):
        data = json.loads(json_data)
        pipe = self.client.pipeline()
        for key, value in data.items():
            pipe.set(key, value)
        await pipe.execute()