from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AgentStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class AgentGroup(str, Enum):
    MARKETPLACE = "marketplace"
    BAZAAR = "bazaar"
    INFRA = "infra"


class ApprovalGateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class AgentSpec(BaseModel):
    id: str
    group: AgentGroup
    specialization: str
    owned_paths: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    provides: List[Dict[str, Any]] = Field(default_factory=list)
    state_keys: List[str] = Field(default_factory=list)
    max_concurrent_tasks: int = 3
    heartbeat_interval: int = 30  # seconds
    restart_policy: str = "on-failure"


class AgentHealth(BaseModel):
    agent_id: str
    status: AgentStatus = AgentStatus.STARTING
    last_heartbeat: Optional[datetime] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    restart_count: int = 0
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskSpec(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent_id: str
    group: AgentGroup
    dependencies: List[str] = Field(default_factory=list)
    priority: int = 0
    estimated_duration: Optional[int] = None  # minutes
    timeout: int = 3600  # seconds
    retry_count: int = 0
    max_retries: int = 2
    tags: List[str] = Field(default_factory=list)
    approval_gate: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0


class TaskState(BaseModel):
    task: TaskSpec
    agent_health: Optional[AgentHealth] = None
    logs: List[str] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)


class ApprovalGate(BaseModel):
    id: str
    name: str
    description: str
    required_roles: List[str]
    timeout: str  # e.g., "72h", "24h", "4h"
    escalation: str
    status: ApprovalGateStatus = ApprovalGateStatus.PENDING
    requested_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision: Optional[str] = None


class DependencyGraph(BaseModel):
    nodes: Dict[str, TaskSpec] = Field(default_factory=dict)
    edges: Dict[str, List[str]] = Field(default_factory=dict)  # task_id -> [dependent_task_ids]

    def add_task(self, task: TaskSpec):
        self.nodes[task.id] = task
        if task.id not in self.edges:
            self.edges[task.id] = []
        for dep_id in task.dependencies:
            if dep_id not in self.edges:
                self.edges[dep_id] = []
            if task.id not in self.edges[dep_id]:
                self.edges[dep_id].append(task.id)

    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        ready = []
        for task_id, task in self.nodes.items():
            if task.status == TaskStatus.PENDING:
                deps_met = all(dep in completed for dep in task.dependencies)
                if deps_met:
                    ready.append(task_id)
        return ready

    def has_cycles(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.edges.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        for node in self.nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> List[str]:
        visited = set()
        temp = set()
        order = []

        def dfs(node: str):
            if node in temp:
                raise ValueError("Cycle detected")
            if node in visited:
                return
            temp.add(node)
            for neighbor in self.edges.get(node, []):
                dfs(neighbor)
            temp.remove(node)
            visited.add(node)
            order.append(node)

        for node in self.nodes:
            if node not in visited:
                dfs(node)
        return order[::-1]


class AgentRegistry(BaseModel):
    agents: Dict[str, AgentSpec] = Field(default_factory=dict)
    health: Dict[str, AgentHealth] = Field(default_factory=dict)

    def register(self, spec: AgentSpec):
        self.agents[spec.id] = spec
        self.health[spec.id] = AgentHealth(agent_id=spec.id)

    def get_ready_agents(self, max_concurrent: int = 3) -> List[str]:
        ready = []
        for agent_id, health in self.health.items():
            spec = self.agents.get(agent_id)
            if not spec:
                continue
            current_tasks = sum(1 for t in spec.owned_paths if t)  # rough estimate
            if health.status == AgentStatus.HEALTHY and current_tasks < spec.max_concurrent_tasks:
                ready.append(agent_id)
        return ready[:max_concurrent]


class OrchestratorState(BaseModel):
    tasks: Dict[str, TaskState] = Field(default_factory=dict)
    dag: DependencyGraph = Field(default_factory=DependencyGraph)
    agents: AgentRegistry = Field(default_factory=AgentRegistry)
    approval_gates: Dict[str, ApprovalGate] = Field(default_factory=dict)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)
    completed_tasks: Set[str] = Field(default_factory=set)
    failed_tasks: Set[str] = Field(default_factory=set)
    blocked_tasks: Set[str] = Field(default_factory=set)

    def add_task(self, task: TaskSpec):
        self.tasks[task.id] = TaskState(task=task)
        self.dag.add_task(task)

    def complete_task(self, task_id: str, result: Dict[str, Any]):
        if task_id in self.tasks:
            self.tasks[task_id].task.status = TaskStatus.COMPLETED
            self.tasks[task_id].task.completed_at = datetime.utcnow()
            self.tasks[task_id].task.result = result
            self.completed_tasks.add(task_id)
            self.audit_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "task_completed",
                "task_id": task_id,
                "result": result
            })

    def fail_task(self, task_id: str, error: str):
        if task_id in self.tasks:
            task = self.tasks[task_id].task
            task.retry_count += 1
            if task.retry_count >= task.max_retries:
                task.status = TaskStatus.FAILED
                task.error = error
                self.failed_tasks.add(task_id)
                self.audit_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "task_failed",
                    "task_id": task_id,
                    "error": error,
                    "retries": task.retry_count
                })
            else:
                task.status = TaskStatus.PENDING
                task.error = error

    def block_task(self, task_id: str, reason: str):
        if task_id in self.tasks:
            self.tasks[task_id].task.status = TaskStatus.BLOCKED
            self.blocked_tasks.add(task_id)
            self.audit_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "task_blocked",
                "task_id": task_id,
                "reason": reason
            })