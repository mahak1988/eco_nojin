"""
Custom Prometheus Metrics for Eco Nojin
=======================================
Provides custom metrics for alerting: Redis, PostgreSQL, Sync, C++, Business KPIs.
"""

import time
from collections.abc import Callable
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram

# ============================================================================
# REDIS METRICS
# ============================================================================

redis_operations_total = Counter(
    "econojin_redis_operations_total",
    "Total number of Redis operations",
    ["operation", "status"],  # GET, SET, DEL, etc. / success, error
)

redis_operation_duration_seconds = Histogram(
    "econojin_redis_operation_duration_seconds",
    "Redis operation latency in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

redis_memory_used_bytes = Gauge(
    "econojin_redis_memory_used_bytes",
    "Redis memory usage in bytes",
)

redis_connected = Gauge(
    "econojin_redis_connected",
    "Redis connection status (1=connected, 0=disconnected)",
)

redis_cache_hits_total = Counter(
    "econojin_redis_cache_hits_total",
    "Total cache hits",
)

redis_cache_misses_total = Counter(
    "econojin_redis_cache_misses_total",
    "Total cache misses",
)

# ============================================================================
# POSTGRESQL METRICS
# ============================================================================

pg_queries_total = Counter(
    "econojin_postgres_queries_total",
    "Total number of PostgreSQL queries",
    ["query_type", "status"],  # SELECT, INSERT, etc. / success, error
)

pg_query_duration_seconds = Histogram(
    "econojin_postgres_query_duration_seconds",
    "PostgreSQL query latency in seconds",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

pg_connections_active = Gauge(
    "econojin_postgres_connections_active",
    "Number of active PostgreSQL connections",
)

pg_connections_idle = Gauge(
    "econojin_postgres_connections_idle",
    "Number of idle PostgreSQL connections",
)

pg_connections_max = Gauge(
    "econojin_postgres_connections_max",
    "Maximum PostgreSQL connections",
)

pg_replication_lag_bytes = Gauge(
    "econojin_postgres_replication_lag_bytes",
    "PostgreSQL replication lag in bytes",
)

# ============================================================================
# SYNC SERVICE METRICS
# ============================================================================

sync_pending_events = Gauge(
    "econojin_sync_pending_events",
    "Number of pending sync events in outbox",
)

sync_events_processed_total = Counter(
    "econojin_sync_events_processed_total",
    "Total sync events processed",
    ["status"],  # success, failed
)

sync_events_failed_total = Counter(
    "econojin_sync_events_failed_total",
    "Total sync events failed",
    ["error_type"],
)

sync_duration_seconds = Histogram(
    "econojin_sync_duration_seconds",
    "Sync operation duration in seconds",
    ["operation"],  # push, pull, full
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

sync_supabase_connected = Gauge(
    "econojin_sync_supabase_connected",
    "Supabase connection status (1=connected, 0=disconnected)",
)

sync_supabase_latency_seconds = Histogram(
    "econojin_sync_supabase_latency_seconds",
    "Supabase API latency in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ============================================================================
# C++ CORE METRICS
# ============================================================================

cpp_core_available = Gauge(
    "econojin_cpp_core_available",
    "C++ core availability (1=available, 0=fallback)",
)

cpp_calls_total = Counter(
    "econojin_cpp_calls_total",
    "Total C++ core calls",
    ["function", "status"],  # success, fallback, error
)

cpp_fallback_calls_total = Counter(
    "econojin_cpp_fallback_calls_total",
    "Total C++ fallback calls (Python used instead)",
    ["function"],
)

cpp_call_duration_seconds = Histogram(
    "econojin_cpp_call_duration_seconds",
    "C++ core call duration in seconds",
    ["function"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

cpp_fallback_rate = Gauge(
    "econojin_cpp_fallback_rate",
    "C++ fallback rate (fallback_calls / total_calls)",
)

# ============================================================================
# REALTIME / SSE METRICS
# ============================================================================

realtime_active_connections = Gauge(
    "econojin_realtime_active_connections",
    "Number of active SSE/WebSocket connections",
)

realtime_connections_total = Counter(
    "econojin_realtime_connections_total",
    "Total realtime connections",
    ["status"],  # connected, disconnected
)

realtime_stream_errors_total = Counter(
    "econojin_realtime_stream_errors_total",
    "Total SSE stream errors",
    ["error_type"],
)

realtime_message_latency_seconds = Histogram(
    "econojin_realtime_message_latency_seconds",
    "Realtime message delivery latency in seconds",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

realtime_messages_sent_total = Counter(
    "econojin_realtime_messages_sent_total",
    "Total realtime messages sent",
    ["event_type"],
)

# ============================================================================
# BUSINESS KPI METRICS
# ============================================================================

user_registrations_total = Counter(
    "econojin_user_registrations_total",
    "Total user registrations",
    ["source"],  # web, mobile, ussd, telegram
)

active_users_daily = Gauge(
    "econojin_active_users_daily",
    "Daily active users",
)

active_users_monthly = Gauge(
    "econojin_active_users_monthly",
    "Monthly active users",
)

farm_creations_total = Counter(
    "econojin_farm_creations_total",
    "Total farms created",
)

carbon_credits_issued_total = Counter(
    "econojin_carbon_credits_issued_total",
    "Total carbon credits issued",
    ["project_type"],
)

carbon_credits_retired_total = Counter(
    "econojin_carbon_credits_retired_total",
    "Total carbon credits retired",
    ["project_type"],
)

marketplace_orders_total = Counter(
    "econojin_marketplace_orders_total",
    "Total marketplace orders",
    ["status"],  # pending, completed, cancelled
)

marketplace_gmv_total = Counter(
    "econojin_marketplace_gmv_total",
    "Total marketplace GMV (Gross Merchandise Value)",
    ["currency"],
)

simulation_runs_total = Counter(
    "econojin_simulation_runs_total",
    "Total simulation runs",
    ["model", "status"],  # success, failed
)

mrv_reports_submitted_total = Counter(
    "econojin_mrv_reports_submitted_total",
    "Total MRV reports submitted",
    ["status"],
)

# ============================================================================
# HTTP REQUEST METRICS (Enhanced)
# ============================================================================

http_request_duration_highr_seconds = Histogram(
    "http_request_duration_highr_seconds",
    "Latency with many buckets but no API specific labels. Made for more accurate percentile calculations.",
    buckets=[
        0.001,
        0.0025,
        0.005,
        0.0075,
        0.01,
        0.015,
        0.02,
        0.025,
        0.03,
        0.035,
        0.04,
        0.05,
        0.06,
        0.07,
        0.08,
        0.09,
        0.1,
        0.125,
        0.15,
        0.175,
        0.2,
        0.25,
        0.3,
        0.35,
        0.4,
        0.5,
        0.75,
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
        4.0,
        5.0,
        7.5,
        10.0,
        20.0,
        30.0,
        60.0,
    ],
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def record_redis_operation(operation: str, duration: float, success: bool):
    """Record Redis operation metrics."""
    status = "success" if success else "error"
    redis_operations_total.labels(operation=operation, status=status).inc()
    redis_operation_duration_seconds.labels(operation=operation).observe(duration)


def record_pg_query(query_type: str, duration: float, success: bool):
    """Record PostgreSQL query metrics."""
    status = "success" if success else "error"
    pg_queries_total.labels(query_type=query_type, status=status).inc()
    pg_query_duration_seconds.labels(query_type=query_type).observe(duration)


def record_sync_event(status: str, error_type: str | None = None):
    """Record sync event metrics."""
    if status == "success":
        sync_events_processed_total.labels(status="success").inc()
    else:
        sync_events_processed_total.labels(status="failed").inc()
        if error_type:
            sync_events_failed_total.labels(error_type=error_type).inc()


def record_cpp_call(function: str, duration: float, success: bool, fallback: bool = False):
    """Record C++ core call metrics."""
    status = "success" if success else "error"
    cpp_calls_total.labels(function=function, status=status).inc()
    cpp_call_duration_seconds.labels(function=function).observe(duration)

    if fallback:
        cpp_fallback_calls_total.labels(function=function).inc()

    # Update fallback rate
    try:
        total = sum(
            cpp_calls_total.labels(function=function, status=s)._value.get()
            for s in ["success", "error", "fallback"]
        )
        fallback_count = cpp_fallback_calls_total.labels(function=function)._value.get()
        if total > 0:
            cpp_fallback_rate.labels(function=function).set(fallback_count / total)
    except Exception:
        pass


def record_realtime_connection(connected: bool):
    """Record realtime connection metrics."""
    if connected:
        realtime_active_connections.inc()
        realtime_connections_total.labels(status="connected").inc()
    else:
        realtime_active_connections.dec()
        realtime_connections_total.labels(status="disconnected").inc()


def record_realtime_message(event_type: str, latency: float):
    """Record realtime message metrics."""
    realtime_messages_sent_total.labels(event_type=event_type).inc()
    realtime_message_latency_seconds.observe(latency)


def record_business_kpi(metric: str, value: float = 1, labels: dict | None = None):
    """Record business KPI metrics."""
    label_dict = labels or {}

    if metric == "user_registration":
        user_registrations_total.labels(**label_dict).inc(value)
    elif metric == "farm_creation":
        farm_creations_total.inc(value)
    elif metric == "carbon_credit_issued":
        carbon_credits_issued_total.labels(**label_dict).inc(value)
    elif metric == "carbon_credit_retired":
        carbon_credits_retired_total.labels(**label_dict).inc(value)
    elif metric == "marketplace_order":
        marketplace_orders_total.labels(**label_dict).inc(value)
    elif metric == "marketplace_gmv":
        marketplace_gmv_total.labels(**label_dict).inc(value)
    elif metric == "simulation_run":
        simulation_runs_total.labels(**label_dict).inc(value)
    elif metric == "mrv_report":
        mrv_reports_submitted_total.labels(**label_dict).inc(value)


# ============================================================================
# DECORATORS FOR EASY INSTRUMENTATION
# ============================================================================


def instrument_redis(operation: str):
    """Decorator to instrument Redis operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                record_redis_operation(operation, time.perf_counter() - start, True)
                return result
            except Exception:
                record_redis_operation(operation, time.perf_counter() - start, False)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                record_redis_operation(operation, time.perf_counter() - start, True)
                return result
            except Exception:
                record_redis_operation(operation, time.perf_counter() - start, False)
                raise

        import asyncio

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def instrument_pg(query_type: str):
    """Decorator to instrument PostgreSQL queries."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                record_pg_query(query_type, time.perf_counter() - start, True)
                return result
            except Exception:
                record_pg_query(query_type, time.perf_counter() - start, False)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                record_pg_query(query_type, time.perf_counter() - start, True)
                return result
            except Exception:
                record_pg_query(query_type, time.perf_counter() - start, False)
                raise

        import asyncio

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def instrument_cpp(function: str):
    """Decorator to instrument C++ core calls."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                record_cpp_call(function, time.perf_counter() - start, True)
                return result
            except Exception:
                record_cpp_call(function, time.perf_counter() - start, False)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                record_cpp_call(function, time.perf_counter() - start, True)
                return result
            except Exception:
                record_cpp_call(function, time.perf_counter() - start, False)
                raise

        import asyncio

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def instrument_realtime(event_type: str):
    """Decorator to instrument realtime events."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                record_realtime_message(event_type, time.perf_counter() - start)
                return result
            except Exception as e:
                realtime_stream_errors_total.labels(error_type=type(e).__name__).inc()
                raise

        return async_wrapper

    return decorator


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================


class track_realtime_connection:
    """Context manager to track realtime connection lifecycle."""

    def __enter__(self):
        record_realtime_connection(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        record_realtime_connection(False)
        return False


class track_cpp_call:
    """Context manager to track C++ core call."""

    def __init__(self, function: str, fallback: bool = False):
        self.function = function
        self.fallback = fallback
        self.start = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start
        success = exc_type is None
        record_cpp_call(self.function, duration, success, self.fallback)
        return False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "active_users_daily",
    "active_users_monthly",
    "carbon_credits_issued_total",
    "carbon_credits_retired_total",
    "cpp_call_duration_seconds",
    "cpp_calls_total",
    # C++
    "cpp_core_available",
    "cpp_fallback_calls_total",
    "cpp_fallback_rate",
    "farm_creations_total",
    # HTTP
    "http_request_duration_highr_seconds",
    "instrument_cpp",
    "instrument_pg",
    "instrument_realtime",
    "instrument_redis",
    "marketplace_gmv_total",
    "marketplace_orders_total",
    "mrv_reports_submitted_total",
    "pg_connections_active",
    "pg_connections_idle",
    "pg_connections_max",
    # PostgreSQL
    "pg_queries_total",
    "pg_query_duration_seconds",
    "pg_replication_lag_bytes",
    # Realtime
    "realtime_active_connections",
    "realtime_connections_total",
    "realtime_message_latency_seconds",
    "realtime_messages_sent_total",
    "realtime_stream_errors_total",
    "record_business_kpi",
    "record_cpp_call",
    "record_pg_query",
    "record_realtime_connection",
    "record_realtime_message",
    "record_redis_operation",
    "record_sync_event",
    "redis_cache_hits_total",
    "redis_cache_misses_total",
    "redis_connected",
    "redis_memory_used_bytes",
    "redis_operation_duration_seconds",
    # Redis
    "redis_operations_total",
    "simulation_runs_total",
    "sync_duration_seconds",
    "sync_events_failed_total",
    "sync_events_processed_total",
    # Sync
    "sync_pending_events",
    "sync_supabase_connected",
    "sync_supabase_latency_seconds",
    "track_cpp_call",
    "track_realtime_connection",
    # Business
    "user_registrations_total",
]
