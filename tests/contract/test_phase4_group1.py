"""Phase 4 group 1 — horizontal infrastructure consolidation.

The plan's rule for consolidation is that nothing may grow and existing debt
may only shrink. Group 1 removed three parallel implementations and wired one
that was being announced but not used. These tests pin that state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class TestDeadImplementationsAreGone:
    @pytest.mark.parametrize(
        "path",
        [
            "services/event_bus",
            "services/api_gateway/resilience",
            "services/api_gateway/cache",
        ],
    )
    def test_removed(self, path: str) -> None:
        assert not (ROOT / path).exists(), (
            f"{path} was removed in the phase 4 consolidation; it duplicated a surviving "
            "implementation and nothing imported it"
        )

    def test_nothing_still_imports_them(self) -> None:
        """Match real import statements, not prose.

        The surviving modules *mention* the deleted paths in comments explaining
        where code moved from, so a naive substring search flags them.
        """
        import ast

        deleted = {
            "services.event_bus",
            "services.api_gateway.resilience",
            "services.api_gateway.cache",
        }
        offenders: list[str] = []
        for path in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except (SyntaxError, ValueError, OSError):
                continue
            for node in ast.walk(tree):
                targets: list[str] = []
                if isinstance(node, ast.Import):
                    targets = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    targets = [node.module]
                for target in targets:
                    if target in deleted or any(target.startswith(f"{name}.") for name in deleted):
                        offenders.append(f"{target} -> {path.relative_to(ROOT)}")
        assert not offenders, f"dangling imports: {offenders}"


class TestResilienceHasOneHome:
    def test_engine_resilience_is_the_survivor(self) -> None:
        source = _read("engine/resilience.py")
        for symbol in ("with_timeout", "with_retry", "circuit_breaker", "get_circuit_breaker"):
            assert symbol in source, f"engine/resilience.py should still export {symbol}"

    def test_engine_resilience_reexports_from_the_package(self) -> None:
        import engine

        assert hasattr(engine, "circuit_breaker")
        assert hasattr(engine, "with_timeout")

    def test_the_survivor_keeps_the_registry_lock(self) -> None:
        """The deleted copy had an unsynchronised registry, so two callers could
        each get their own breaker and half the traffic would bypass it."""
        source = _read("engine/resilience.py")
        assert "_registry_lock" in source

    def test_the_survivor_keeps_a_working_timeout(self) -> None:
        source = _read("engine/resilience.py")
        assert "future.result(timeout=" in source, (
            "the deleted copy's call_with_timeout never actually applied a timeout"
        )


class TestCustomMetricsAreReallyRegistered:
    def test_main_imports_the_custom_metrics(self) -> None:
        source = _read("services/api_gateway/main.py")
        assert "from services.api_gateway import metrics" in source, (
            "metrics.py was never imported by anything, so /metrics exposed only the "
            "HTTP series while the log claimed custom metrics were enabled"
        )

    def test_the_log_does_not_overclaim(self) -> None:
        source = _read("services/api_gateway/main.py")
        assert "with custom metrics" not in source, (
            "the old log line asserted custom metrics regardless of whether the import "
            "succeeded; S-HONEST forbids that"
        )

    @pytest.mark.asyncio
    async def test_custom_series_appear_on_the_metrics_endpoint(self) -> None:
        import warnings

        warnings.filterwarnings("ignore")
        from fastapi.testclient import TestClient

        from services.api_gateway.main import app

        with TestClient(app) as client:
            body = client.get("/metrics").text
        custom = [
            line
            for line in body.splitlines()
            if line.startswith(("econojin_redis", "econojin_postgres", "econojin_business"))
        ]
        assert custom, "no custom metric families on /metrics; the import is not taking effect"


class TestNothingShrankTheWrongWay:
    def test_the_event_bus_package_still_exports_its_surface(self) -> None:
        import services.api_gateway.eventbus as eventbus

        for name in ("init_nats", "shutdown_nats", "nats_lifespan", "publish_event"):
            assert hasattr(eventbus, name), f"consolidation dropped {name}"

    def test_the_worker_entrypoint_still_runs(self) -> None:
        import services.workers.event_worker as worker

        assert hasattr(worker, "run_event_worker")
        assert hasattr(worker, "main")
