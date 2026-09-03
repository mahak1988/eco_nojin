#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.memory_monitor
=====================

Memory monitoring and leak detection for Eco Nojin services.

Usage:
    from engine.memory_monitor import memory_monitor, track_memory

    with track_memory("operation_name") as tracker:
        # ... your code ...
        pass
    print(tracker.summary())

Author: Eco Nojin Architecture Team
Version: 3.0.0
"""

import gc
import sys
import tracemalloc
from typing import Optional, List, Dict
from contextlib import contextmanager
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class MemoryTracker:
    """Track memory usage during an operation."""

    def __init__(self, name: str, warn_threshold_mb: float = 10.0):
        self.name = name
        self.warn_threshold_mb = warn_threshold_mb
        self.start_mb = 0.0
        self.end_mb = 0.0
        self.delta_mb = 0.0
        self.gc_before = 0
        self.gc_after = 0

    def start(self):
        """Start memory tracking."""
        gc.collect()
        self.gc_before = gc.get_stats()[0]["collected"]
        if not tracemalloc.is_tracing():
            tracemalloc.start(10)  # Track 10 frames
        self.start_mb = tracemalloc.get_traced_memory()[0] / (1024 * 1024)
        return self

    def stop(self):
        """Stop memory tracking."""
        gc.collect()
        self.gc_after = gc.get_stats()[0]["collected"]
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            self.end_mb = current / (1024 * 1024)
            self.delta_mb = self.end_mb - self.start_mb
        return self

    def get_snapshot(self, limit: int = 10) -> List[str]:
        """Get top memory-consuming locations."""
        if not tracemalloc.is_tracing():
            return ["Memory tracing not started"]
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        return [
            f"{stat.traceback}: {stat.size / 1024:.1f} KB"
            for stat in top_stats[:limit]
        ]

    def summary(self) -> str:
        """Get human-readable summary."""
        status = "⚠️  LEAK" if self.delta_mb > self.warn_threshold_mb else "✅ OK"
        return (
            f"[{self.name}] Memory: {self.start_mb:.1f}MB -> {self.end_mb:.1f}MB "
            f"(delta: {self.delta_mb:+.1f}MB) {status} "
            f"(GC: {self.gc_before} -> {self.gc_after})"
        )

    def is_leaking(self) -> bool:
        """Check if operation leaked memory."""
        return self.delta_mb > self.warn_threshold_mb


@contextmanager
def track_memory(name: str, warn_threshold_mb: float = 10.0):
    """Context manager to track memory usage."""
    tracker = MemoryTracker(name, warn_threshold_mb)
    tracker.start()
    try:
        yield tracker
    finally:
        tracker.stop()


def monitor_memory(warn_threshold_mb: float = 10.0):
    """Decorator to monitor memory usage of a function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with track_memory(func.__name__, warn_threshold_mb) as tracker:
                result = func(*args, **kwargs)
            if tracker.is_leaking():
                logger.warning(tracker.summary())
            return result
        return wrapper
    return decorator


class MemoryManager:
    """Centralized memory management for services."""

    def __init__(self):
        self._history = []
        self._total_operations = 0
        self._leak_count = 0

    def track(self, name: str, delta_mb: float, warn_threshold_mb: float = 10.0):
        """Record a memory measurement."""
        self._total_operations += 1
        is_leak = delta_mb > warn_threshold_mb
        if is_leak:
            self._leak_count += 1
        self._history.append({
            "name": name,
            "delta_mb": delta_mb,
            "is_leak": is_leak,
        })
        # Keep only last 100 operations
        if len(self._history) > 100:
            self._history = self._history[-100:]

    def get_stats(self) -> Dict:
        """Get overall memory statistics."""
        if not self._history:
            return {"operations": 0, "leaks": 0, "leak_rate": 0.0}
        total_delta = sum(h["delta_mb"] for h in self._history)
        return {
            "operations": self._total_operations,
            "leaks": self._leak_count,
            "leak_rate": self._leak_count / max(1, self._total_operations),
            "total_delta_mb": total_delta,
            "avg_delta_mb": total_delta / len(self._history),
        }

    def force_cleanup(self) -> int:
        """Force garbage collection."""
        gc.collect()
        gc.collect()
        gc.collect()
        return gc.get_stats()[0]["collected"]


# Global memory manager
memory_monitor = MemoryManager()


__all__ = [
    "MemoryTracker",
    "track_memory",
    "monitor_memory",
    "MemoryManager",
    "memory_monitor",
]