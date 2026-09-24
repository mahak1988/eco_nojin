from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import uuid
import logging
from dataclasses import dataclass

from orchestrator.src.state.models import (
    TaskSpec, TaskStatus, AgentGroup, AgentSpec, AgentRegistry,
    DependencyGraph, OrchestratorState, ApprovalGate, ApprovalGateStatus
)

logger = logging.getLogger(__name__)


class TaskPlanner:
    """Decomposes high-level goals into executable tasks with dependencies"""

    def __init__(self, state: 'OrchestratorState'):
        self.state = state

    def create_task(
        self,
        name: str,
        description: str,
        agent_id: str,
        group: AgentGroup,
        dependencies: List[str] = None,
        priority: int = 0,
        estimated_duration: Optional[int] = None,
        tags: List[str] = None,
        approval_gate: Optional[str] = None
    ) -> str:
        """Create a new task and add to state"""
        task = TaskSpec(
            name=name,
            description=description,
            agent_id=agent_id,
            group=group,
            dependencies=dependencies or [],
            priority=priority,
            estimated_duration=estimated_duration,
            tags=tags or [],
            approval_gate=approval_gate
        )
        self.state.add_task(task)
        logger.info(f"Created task: {task.id} - {name} (agent: {agent_id})")
        return task.id

    def create_task_batch(self, tasks: List[Dict]) -> List[str]:
        """Create multiple tasks at once"""
        task_ids = []
        for task_data in tasks:
            task_id = self.create_task(**task_data)
            task_ids.append(task_id)
        return task_ids

    def get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (dependencies met)"""
        return self.state.dag.get_ready_tasks(self.state.completed_tasks)

    def validate_dag(self) -> bool:
        """Check for cycles in dependency graph"""
        if self.state.dag.has_cycles():
            logger.error("Cycle detected in task dependency graph!")
            return False
        return True

    def get_execution_order(self) -> List[str]:
        """Get topological sort of all tasks"""
        return self.state.dag.topological_sort()


class Scheduler:
    """Schedules ready tasks to available agents"""

    def __init__(self, state: 'OrchestratorState', message_bus: 'MessageBus'):
        self.state = state
        self.message_bus = message_bus
        self.running = False

    async def schedule_next(self) -> List[str]:
        """Schedule ready tasks to available agents"""
        scheduled = []

        ready_tasks = self.state.planner.get_ready_tasks()
        if not ready_tasks:
            return scheduled

        # Get available agents
        available_agents = self.state.agents.get_ready_agents()

        for task_id in ready_tasks:
            task_state = self.state.tasks.get(task_id)
            if not task_state:
                continue

            task = task_state.task
            if task.status != TaskStatus.PENDING:
                continue

            # Find suitable agent
            assigned = False
            for agent_id in available_agents:
                spec = self.state.agents.agents.get(task.agent_id)
                if spec and spec.id == task.agent_id:
                    # Check agent capacity
                    health = self.state.agents.health.get(agent_id)
                    if health and health.status == 'healthy':
                        await self._assign_task(task.id, agent_id)
                        scheduled.append(task_id)
                        assigned = True
                        break

            if not assigned:
                logger.warning(f"No available agent for task {task_id} (agent: {task.agent_id})")

        return scheduled

    async def _assign_task(self, task_id: str, agent_id: str):
        task_state = self.state.tasks[task_id]
        task_state.task.status = TaskStatus.RUNNING
        task_state.task.started_at = datetime.utcnow()

        # Update agent health
        if agent_id in self.state.agents.health:
            health = self.state.agents.health[agent_id]
            health.current_task = task_id

        # Publish task started event
        if self.message_bus:
            from orchestrator.src.messaging.bus import EventPublisher
            publisher = EventPublisher(self.message_bus)
            await publisher.task_started(task_id, agent_id)

        logger.info(f"Assigned task {task_id} to agent {agent_id}")

    async def check_timeouts(self):
        """Check for stuck tasks and handle timeouts"""
        for task_id, task_state in self.state.tasks.items():
            task = task_state.task
            if task.status == TaskStatus.RUNNING and task.started_at:
                elapsed = (datetime.utcnow() - task.started_at).total_seconds()
                if elapsed > task.timeout:
                    logger.warning(f"Task {task.id} timed out after {elapsed}s")
                    await self._handle_timeout(task_id)

    async def _handle_timeout(self, task_id: str):
        task_state = self.state.tasks[task_id]
        task = task_state.task

        if task.retry_count < task.max_retries:
            task.status = TaskStatus.PENDING
            task.error = f"Timeout after {task.timeout}s, retrying"
            logger.info(f"Retrying task {task_id} (attempt {task.retry_count + 1})")
        else:
            task.status = TaskStatus.FAILED
            task.error = f"Max retries ({task.max_retries}) exceeded"
            logger.error(f"Task {task_id} failed after {task.max_retries} retries")

    async def check_stuck_tasks(self, threshold_seconds: int = 3600):
        """Check for tasks stuck in RUNNING state"""
        for task_id, task_state in self.state.tasks.items():
            task = task_state.task
            if task.status == TaskStatus.RUNNING and task.started_at:
                elapsed = (datetime.utcnow() - task.started_at).total_seconds()
                if elapsed > threshold_seconds:
                    logger.warning(f"Task {task.id} stuck for {elapsed}s")
                    if self.message_bus:
                        from orchestrator.src.messaging.bus import EventPublisher
                        publisher = EventPublisher(self.message_bus)
                        await publisher.task_stuck(task.id, task.agent_id, int(elapsed))


class ApprovalManager:
    """Manages approval gates for critical tasks"""

    def __init__(self, state: 'OrchestratorState', message_bus: 'MessageBus'):
        self.state = state
        self.message_bus = message_bus

    async def request_approval(
        self,
        gate_id: str,
        name: str,
        description: str,
        required_roles: List[str],
        timeout: str,
        escalation: str
    ) -> str:
        """Create and request approval gate"""
        gate = ApprovalGate(
            id=gate_id,
            name=name,
            description=description,
            required_roles=required_roles,
            timeout=timeout,
            escalation=escalation,
            status=ApprovalGateStatus.PENDING,
            requested_at=datetime.utcnow()
        )
        self.state.approval_gates[gate_id] = gate

        # Save to state store
        if hasattr(self.state, 'store') and self.state.store:
            await self.state.store.save_approval_gate(gate)

        # Notify via message bus
        if self.message_bus:
            from orchestrator.src.messaging.bus import EventPublisher
            publisher = EventPublisher(self.message_bus)
            await publisher.human_approval_required(gate_id, description, required_roles)

        logger.info(f"Approval requested: {gate_id} ({name})")
        return gate_id

    async def approve(self, gate_id: str, decided_by: str, decision: str) -> bool:
        gate = self.state.approval_gates.get(gate_id)
        if not gate:
            return False

        gate.status = ApprovalGateStatus.APPROVED
        gate.decided_at = datetime.utcnow()
        gate.decided_by = decided_by
        gate.decision = decision

        # Unblock dependent tasks
        await self._unblock_dependent_tasks(gate_id)

        logger.info(f"Approval granted: {gate_id} by {decided_by}")
        return True

    async def reject(self, gate_id: str, decided_by: str, reason: str) -> bool:
        gate = self.state.approval_gates.get(gate_id)
        if not gate:
            return False

        gate.status = ApprovalGateStatus.REJECTED
        gate.decided_at = datetime.utcnow()
        gate.decided_by = decided_by
        gate.decision = reason

        # Fail dependent tasks
        await self._fail_dependent_tasks(gate_id, reason)

        logger.info(f"Approval rejected: {gate_id} by {decided_by}: {reason}")
        return True

    async def check_timeouts(self):
        """Check for expired approval gates"""
        for gate_id, gate in self.state.approval_gates.items():
            if gate.status != ApprovalGateStatus.PENDING:
                continue

            # Parse timeout (e.g., "72h", "24h", "4h")
            timeout_hours = self._parse_timeout(gate.timeout)
            if gate.requested_at:
                elapsed = (datetime.utcnow() - gate.requested_at).total_seconds() / 3600
                if elapsed >= timeout_hours:
                    gate.status = ApprovalGateStatus.EXPIRED
                    await self._escalate(gate_id)

    def _parse_timeout(self, timeout: str) -> float:
        """Parse timeout string like '72h', '24h', '4h' to hours"""
        timeout = timeout.lower().strip()
        if timeout.endswith('h'):
            return float(timeout[:-1])
        elif timeout.endswith('m'):
            return float(timeout[:-1]) / 60
        elif timeout.endswith('d'):
            return float(timeout[:-1]) * 24
        return 24.0  # default 24 hours

    async def _escalate(self, gate_id: str):
        gate = self.state.approval_gates.get(gate_id)
        if not gate:
            return

        gate.status = ApprovalGateStatus.ESCALATED
        # Notify escalation contact
        logger.warning(f"Approval gate escalated: {gate_id} -> {gate.escalation}")

    async def _unblock_dependent_tasks(self, gate_id: str):
        """Unblock tasks waiting on this approval gate"""
        for task_state in self.state.tasks.values():
            task = task_state.task
            if task.approval_gate == gate_id and task.status == TaskStatus.BLOCKED:
                task.status = TaskStatus.PENDING
                logger.info(f"Unblocked task {task.id} after approval {gate_id}")

    async def _fail_dependent_tasks(self, gate_id: str, reason: str):
        """Fail tasks waiting on this approval gate"""
        for task_state in self.state.tasks.values():
            task = task_state.task
            if task.approval_gate == gate_id and task.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]:
                task.status = TaskStatus.FAILED
                task.error = f"Approval rejected: {reason}"
                logger.error(f"Task {task.id} failed due to rejected approval: {reason}")