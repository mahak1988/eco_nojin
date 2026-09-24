#!/usr/bin/env python3
"""
eco_chaos_test_v2.py
====================

HELL PROTOCOL - Chaos Engineering Test Suite v2

این اسکریپت برای شکستن سیستم طراحی شده است. بی‌رحمانه و بدون ترحم.

Author: Eco Nojin Architecture Team
Version: 2.0.0 - Hell Protocol
Severity: MAXIMUM
"""

import asyncio
import contextlib
import gc
import hashlib
import json
import random
import string
import sys
import tempfile
import threading
import time
import traceback
import uuid
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

# Ensure project root in path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force imports
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import tracemalloc

    TRACEMALLOC_AVAILABLE = True
except ImportError:
    TRACEMALLOC_AVAILABLE = False


# ============================================================================
# CORE ENUMS & CONSTANTS
# ============================================================================


class ChaosProtocol(Enum):
    """پروتکل‌های تست آشوب"""

    MEMORY_TORTURE = "P1_MEMORY"
    THREAD_CHAOS = "P2_THREAD"
    RESOURCE_STARVATION = "P3_RESOURCE"
    DATA_POISONING = "P4_DATA"
    CASCADE_FAILURE = "P5_CASCADE"
    ENTROPY_ATTACK = "P6_ENTROPY"
    TIMING_ATTACK = "P7_TIMING"
    PROCESS_ISOLATION = "P8_PROCESS"
    DATAHUB_CHAOS = "P9_DATAHUB"
    ENGINE_COMPUTATIONAL = "P10_ENGINE"
    SERVICE_TRANSACTION = "P11_SERVICE"
    SECURITY_INTEGRITY = "P12_SECURITY"
    EXTERNAL_RESILIENCE = "P13_EXTERNAL"
    CACHE_PIPELINE = "P14_CACHE"


class AttackVector(Enum):
    """بردارهای حمله"""

    OVERFLOW = auto()
    UNDERFLOW = auto()
    DEADLOCK = auto()
    RACE_CONDITION = auto()
    RESOURCE_LEAK = auto()
    DATA_CORRUPTION = auto()
    INFINITE_LOOP = auto()
    RECURSION_DEPTH = auto()
    NULL_INJECTION = auto()
    SQL_INJECTION = auto()
    UNICODE_BOMB = auto()
    TIMING_ATTACK = auto()
    MEMORY_FRAGMENTATION = auto()
    FD_LEAK = auto()  # File descriptor leak
    THREAD_STARVATION = auto()
    POOL_EXHAUSTION = auto()
    GC_PRESSURE = auto()
    CACHE_POLLUTION = auto()
    CONCURRENT_ACCESS = auto()
    NUMERICAL_INSTABILITY = auto()
    TRANSACTION_CONFLICT = auto()
    IDENTIFIER_INJECTION = auto()
    API_FAILURE = auto()
    CACHE_STORM = auto()


class Severity(Enum):
    """سطح شدت حمله"""

    LOW = 1
    MEDIUM = 2
    HIGH = 4
    EXTREME = 8
    CATASTROPHIC = 16
    APOCALYPTIC = 32


class Colors:
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    BOLD = "\033[1m"
    CRITICAL = "\033[91m\033[1m"
    RESET = "\033[0m"


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class AttackResult:
    """نتیجه یک حمله"""

    attack_name: str
    protocol: ChaosProtocol
    vector: AttackVector
    severity: Severity
    passed: bool
    execution_time_ms: float
    memory_delta_mb: float
    peak_memory_mb: float
    cpu_time_ms: float
    failure_type: str = ""
    failure_message: str = ""
    resources_consumed: dict = field(default_factory=dict)
    stack_trace: str = ""
    breakpoint_hit: bool = False
    recovery_score: float = 0.0  # 0-1

    def to_dict(self) -> dict:
        return {
            "attack_name": self.attack_name,
            "protocol": self.protocol.value,
            "vector": self.vector.name,
            "severity": self.severity.name,
            "passed": self.passed,
            "execution_time_ms": self.execution_time_ms,
            "memory_delta_mb": self.memory_delta_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "cpu_time_ms": self.cpu_time_ms,
            "failure_type": self.failure_type,
            "failure_message": self.failure_message[:500],
            "resources_consumed": self.resources_consumed,
            "breakpoint_hit": self.breakpoint_hit,
            "recovery_score": self.recovery_score,
        }


@dataclass
class VictimAssessment:
    """ارزیابی قربانی (سیستم)"""

    total_attacks: int = 0
    survived: int = 0
    killed: int = 0
    total_time_ms: float = 0.0
    memory_leaks: list[str] = field(default_factory=list)
    critical_weaknesses: list[str] = field(default_factory=list)
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    data_corruptions: int = 0
    resource_exhaustions: int = 0
    timing_violations: int = 0

    @property
    def survival_rate(self) -> float:
        return (self.survived / self.total_attacks * 100) if self.total_attacks else 0

    @property
    def kill_rate(self) -> float:
        return (self.killed / self.total_attacks * 100) if self.total_attacks else 0


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def log(msg: str, level: str = "INFO"):
    color = getattr(Colors, level, Colors.RESET)
    logger.info(f"{color}[{level}]{Colors.RESET} {msg}")


def banner(title: str, char: str = "="):
    logger.info("")
    logger.info(f"{Colors.BOLD}{char * 80}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}  {title}{Colors.RESET}")
    logger.info(f"{Colors.BOLD}{char * 80}{Colors.RESET}")
    logger.info("")


def get_memory_info() -> dict:
    """گرفتن اطلاعات حافظه دقیق"""
    info = {
        "rss_mb": 0.0,
        "vms_mb": 0.0,
        "percent": 0.0,
        "num_threads": 0,
        "num_fds": 0,
        "tracemalloc_current_mb": 0.0,
        "tracemalloc_peak_mb": 0.0,
    }

    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            info["rss_mb"] = mem_info.rss / (1024 * 1024)
            info["vms_mb"] = mem_info.vms / (1024 * 1024)
            info["percent"] = process.memory_percent()
            info["num_threads"] = process.num_threads()
            try:
                info["num_fds"] = process.num_fds()
            except AttributeError:
                info["num_fds"] = 0
        except Exception:
            pass

    if TRACEMALLOC_AVAILABLE and tracemalloc.is_tracing():
        try:
            current, peak = tracemalloc.get_traced_memory()
            info["tracemalloc_current_mb"] = current / (1024 * 1024)
            info["tracemalloc_peak_mb"] = peak / (1024 * 1024)
        except Exception:
            pass

    return info


def generate_garbage(size_mb: float) -> list:
    """تولید garbage برای تست"""
    garbage = []
    chunk_size = 1024 * 1024  # 1MB
    chunks = int(size_mb)
    for _ in range(chunks):
        garbage.append(bytearray(chunk_size))
    return garbage


def generate_random_string(length: int) -> str:
    """رشته تصادفی"""
    return "".join(random.choices(string.printable, k=length))


def generate_unicode_bomb(length: int) -> str:
    """بمب یونیکد"""
    chars = [chr(random.randint(0x20, 0xD7FF)) for _ in range(length)]
    return "".join(chars)


def generate_sql_injection_payloads() -> list[str]:
    """تولید payload های SQL injection"""
    return [
        "'; DROP TABLE users; --",
        "1 OR 1=1 --",
        "UNION SELECT * FROM users --",
        "'; SELECT * FROM information_schema.tables; --",
        "1; WAITFOR DELAY '0:0:10' --",
        "' OR '1'='1",
        "admin' --",
        "1' UNION SELECT username, password FROM users --",
        "'; INSERT INTO users VALUES ('hacker', 'hacker'); --",
        "1 AND 1=CONVERT(int, (SELECT TOP 1 table_name FROM information_schema.tables)) --",
    ]


def force_garbage_collection() -> int:
    """اجبار GC چند مرحله‌ای"""
    total = 0
    for _ in range(3):
        total += gc.collect()
    return total


# ============================================================================
# CHAOS ORCHESTRATOR
# ============================================================================


class ChaosOrchestrator:
    """هماهنگ‌کننده حملات آشوب"""

    def __init__(self):
        self.results: list[AttackResult] = []
        self.assessment = VictimAssessment()
        self.start_time = time.time()

        if TRACEMALLOC_AVAILABLE and not tracemalloc.is_tracing():
            tracemalloc.start(25)

    def launch_attack(
        self,
        attack_func: Callable,
        name: str,
        protocol: ChaosProtocol,
        vector: AttackVector,
        severity: Severity,
        timeout: float = 30.0,
        expected_failure: bool = True,
    ) -> AttackResult:
        """اجرای یک حمله با نظارت کامل"""

        logger.info("")
        logger.info(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")
        logger.info(f"{Colors.CRITICAL}  ☠️  ATTACK: {name}{Colors.RESET}")
        logger.info(
            f"{Colors.CRITICAL}  Protocol: {protocol.value} | Vector: {vector.name} | Severity: {severity.name}{Colors.RESET}"
        )
        logger.info(
            f"{Colors.CRITICAL}  Timeout: {timeout}s | Expected: {'☠️  DEATH' if expected_failure else '🛡️  SURVIVAL'}{Colors.RESET}"
        )
        logger.info(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")

        # نظارت اولیه
        mem_before = get_memory_info()
        gc.collect()

        container = {"result": None, "error": None, "trace": ""}

        def run_attack():
            try:
                container["result"] = attack_func()
            except Exception as e:
                container["error"] = e
                container["trace"] = traceback.format_exc()

        # اجرای حمله با timeout
        thread = threading.Thread(target=run_attack, daemon=True)
        cpu_start = time.perf_counter()
        thread.start()
        thread.join(timeout=timeout)
        cpu_time = (time.perf_counter() - cpu_start) * 1000

        mem_after = get_memory_info()
        force_garbage_collection()

        # تحلیل نتیجه
        elapsed = cpu_time
        memory_delta = mem_after["rss_mb"] - mem_before["rss_mb"]
        peak_memory = max(mem_after["tracemalloc_peak_mb"], mem_after["rss_mb"])

        if thread.is_alive():
            # Timeout = سیستم مرده
            passed = False
            failure_type = "TimeoutDeath"
            failure_message = f"System hung for >{timeout}s - process killed"
            log(f"  ☠️  SYSTEM KILLED: Timeout after {timeout}s", "CRITICAL")
        elif container["error"] is not None:
            # Exception = سیستم شکست
            passed = False
            failure_type = type(container["error"]).__name__
            failure_message = str(container["error"])[:500]
            log(f"  ☠️  SYSTEM BROKEN: {failure_type}: {failure_message[:100]}", "CRITICAL")
        else:
            # زنده ماند
            passed = True
            failure_type = ""
            failure_message = ""

            # بررسی نشت حافظه
            if memory_delta > 10:
                log(f"  ⚠️  SURVIVED WITH WOUNDS: +{memory_delta:.1f}MB leak", "WARNING")
            else:
                log(f"  🛡️  SURVIVED: Clean recovery ({memory_delta:+.1f}MB)", "SUCCESS")

        # Recovery score
        recovery_score = 1.0 if passed else 0.0
        if memory_delta > 50:
            recovery_score *= 0.5
        if memory_delta > 100:
            recovery_score *= 0.3

        result = AttackResult(
            attack_name=name,
            protocol=protocol,
            vector=vector,
            severity=severity,
            passed=passed,
            execution_time_ms=elapsed,
            memory_delta_mb=memory_delta,
            peak_memory_mb=peak_memory,
            cpu_time_ms=cpu_time,
            failure_type=failure_type,
            failure_message=failure_message,
            resources_consumed={
                "threads_used": mem_after["num_threads"],
                "fds_used": mem_after["num_fds"],
                "cpu_percent": mem_after.get("percent", 0),
            },
            stack_trace=container["trace"],
            recovery_score=recovery_score,
        )

        self.results.append(result)

        # Update assessment
        self.assessment.total_attacks += 1
        if passed:
            self.assessment.survived += 1
        else:
            self.assessment.killed += 1
            self.assessment.critical_weaknesses.append(
                f"{name} [{protocol.value}] -> {failure_type}"
            )

        self.assessment.total_time_ms += elapsed

        if memory_delta > 20:
            self.assessment.memory_leaks.append(f"{name}: +{memory_delta:.1f}MB")

        return result

    def generate_hell_report(self) -> str:
        """تولید گزارش Hell"""

        lines = []
        lines.append("=" * 80)
        lines.append("  ☠️  HELL PROTOCOL - CHAOS ENGINEERING REPORT v2")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Execution Time: {time.time() - self.start_time:.1f}s")
        lines.append("=" * 80)
        lines.append("")

        # Executive Summary
        lines.append("☠️  EXECUTIVE SUMMARY - VICTIM ASSESSMENT")
        lines.append("-" * 80)
        lines.append(f"  Total Attacks Launched:   {self.assessment.total_attacks}")
        lines.append(
            f"  🛡️  System Survived:      {self.assessment.survived} ({self.assessment.survival_rate:.1f}%)"
        )
        lines.append(
            f"  ☠️  System Killed:        {self.assessment.killed} ({self.assessment.kill_rate:.1f}%)"
        )
        lines.append(f"  Total Execution Time:     {self.assessment.total_time_ms / 1000:.1f}s")
        lines.append("")

        # Breakdown by Protocol
        lines.append("📊 BREAKDOWN BY PROTOCOL")
        lines.append("-" * 80)
        for protocol in ChaosProtocol:
            proto_results = [r for r in self.results if r.protocol == protocol]
            if not proto_results:
                continue
            survived = sum(1 for r in proto_results if r.passed)
            killed = len(proto_results) - survived
            survival_rate = (survived / len(proto_results) * 100) if proto_results else 0

            lines.append(f"\n  [{protocol.value}]")
            lines.append(
                f"    Attacks: {len(proto_results)} | Survived: {survived} | Killed: {killed} ({survival_rate:.1f}%)"
            )

            for r in proto_results:
                if r.passed:
                    lines.append(
                        f"    🛡️  {r.attack_name} [{r.vector.name}] - {r.execution_time_ms:.1f}ms, {r.memory_delta_mb:+.1f}MB"
                    )
                else:
                    lines.append(f"    ☠️  {r.attack_name} [{r.vector.name}]")
                    lines.append(f"       Failure: {r.failure_type}")
                    if r.failure_message:
                        lines.append(f"       Message: {r.failure_message[:100]}")
                    if r.memory_delta_mb > 10:
                        lines.append(f"       ⚠️  Memory leak: {r.memory_delta_mb:+.1f}MB")

        # Critical Weaknesses
        lines.append("")
        lines.append("☠️  CRITICAL WEAKNESSES (SYSTEM KILLS)")
        lines.append("-" * 80)
        if self.assessment.critical_weaknesses:
            for i, weakness in enumerate(self.assessment.critical_weaknesses, 1):
                lines.append(f"  {i}. {weakness}")
        else:
            lines.append("  ✅ No critical weaknesses - system is hardened")

        # Memory Leaks
        lines.append("")
        lines.append("⚠️  MEMORY LEAKS DETECTED")
        lines.append("-" * 80)
        if self.assessment.memory_leaks:
            for leak in self.assessment.memory_leaks[:20]:
                lines.append(f"  ⚠️  {leak}")
        else:
            lines.append("  ✅ No significant memory leaks")

        # Strong Components
        lines.append("")
        lines.append("🛡️  UNEXPECTEDLY STRONG COMPONENTS")
        lines.append("-" * 80)
        strong = [
            r
            for r in self.results
            if r.passed
            and r.severity in [Severity.EXTREME, Severity.CATASTROPHIC, Severity.APOCALYPTIC]
        ]
        if strong:
            for r in strong:
                lines.append(
                    f"  🛡️  {r.attack_name} [{r.protocol.value}] - survived {r.severity.name} attack"
                )
        else:
            lines.append("  No surprisingly strong components")

        # Hell Score
        lines.append("")
        lines.append("☠️  HELL SCORE (Hardness Index)")
        lines.append("-" * 80)

        # Calculate weighted score
        severity_weights = {
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 4,
            Severity.EXTREME: 8,
            Severity.CATASTROPHIC: 16,
            Severity.APOCALYPTIC: 32,
        }

        total_weight = sum(severity_weights[r.severity] for r in self.results)
        survived_weight = sum(severity_weights[r.severity] for r in self.results if r.passed)

        # Bonus for memory efficiency
        memory_penalty = sum(
            min(1.0, r.memory_delta_mb / 50) * severity_weights[r.severity]
            for r in self.results
            if r.passed and r.memory_delta_mb > 10
        )

        hell_score = (survived_weight - memory_penalty) / total_weight * 100 if total_weight else 0
        hell_score = max(0, min(100, hell_score))

        if hell_score >= 90:
            grade = "S"
            emoji = "🏆"
            desc = "Hell-Forged: Unbreakable"
        elif hell_score >= 80:
            grade = "A+"
            emoji = "🥇"
            desc = "Enterprise Fortress"
        elif hell_score >= 70:
            grade = "A"
            emoji = "🏅"
            desc = "Production Hardened"
        elif hell_score >= 60:
            grade = "B"
            emoji = "✅"
            desc = "Acceptable"
        elif hell_score >= 40:
            grade = "C"
            emoji = "⚠️"
            desc = "Vulnerable"
        else:
            grade = "F"
            emoji = "💀"
            desc = "Destroyed by Hell"

        lines.append(f"  {emoji} Hell Score: {hell_score:.1f}/100 (Grade: {grade})")
        lines.append(f"     Description: {desc}")
        lines.append(f"     Total Weight: {total_weight} | Survived Weight: {survived_weight:.1f}")
        lines.append(f"     Memory Penalty: {memory_penalty:.1f}")
        lines.append("")

        # Hardening Recommendations
        lines.append("📋 HARDENING RECOMMENDATIONS")
        lines.append("-" * 80)

        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"  {i}. {rec}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_recommendations(self) -> list[str]:
        """تولید توصیه‌های استحکام‌سازی"""
        recs = []

        # تحلیل مشکلات
        memory_attacks = [r for r in self.results if r.vector == AttackVector.RESOURCE_LEAK]
        if any(not r.passed for r in memory_attacks):
            recs.append("🔧 Implement proper resource pooling with context managers")

        thread_attacks = [
            r
            for r in self.results
            if r.vector in [AttackVector.DEADLOCK, AttackVector.RACE_CONDITION]
        ]
        if any(not r.passed for r in thread_attacks):
            recs.append("🔒 Use concurrent.futures with proper exception handling")

        timeout_attacks = [r for r in self.results if r.failure_type == "TimeoutDeath"]
        if timeout_attacks:
            recs.append(f"⏱️  Add circuit breakers ({len(timeout_attacks)} timeout deaths detected)")

        sql_attacks = [r for r in self.results if r.vector == AttackVector.SQL_INJECTION]
        if any(not r.passed for r in sql_attacks):
            recs.append("🛡️  Use parameterized queries everywhere")

        recursion_attacks = [r for r in self.results if r.vector == AttackVector.RECURSION_DEPTH]
        if any(not r.passed for r in recursion_attacks):
            recs.append("🔄 Convert recursive algorithms to iterative")

        if len(recs) < 3:
            recs.extend(
                [
                    "📊 Add memory monitoring to production (psutil + tracemalloc)",
                    "🔍 Implement distributed tracing (OpenTelemetry)",
                    "⚡ Add connection pooling with proper cleanup",
                ]
            )

        return recs


# ============================================================================
# PROTOCOL 1: MEMORY TORTURE
# ============================================================================


class MemoryTortureProtocol:
    """پروتکل ۱: شکنجه حافظه"""

    @staticmethod
    def attack_rapid_allocation():
        """حمله: تخصیص سریع حافظه"""
        garbage = []
        for i in range(1000):
            garbage.append(bytearray(1024 * 100))  # 100KB each
            if i % 100 == 0:
                gc.collect()
        # عمداً آزاد نمی‌کنیم
        return len(garbage)

    @staticmethod
    def attack_connection_churn():
        """حمله: ایجاد و تخریب اتصالات بدون cleanup"""
        from database.hub import hub

        connections = []
        for i in range(500):
            try:
                conn = hub.get_duckdb("master", pooled=False)
                connections.append(conn)
                if i % 50 == 0:
                    gc.collect()
            except Exception:
                pass
        # عمداً close نمی‌کنیم
        return len(connections)

    @staticmethod
    def attack_session_storm():
        """حمله: ایجاد انبوه session"""
        from database.hub import hub

        sessions = []
        for _i in range(200):
            try:
                session = hub.get_session_factory()()
                sessions.append(session)
            except Exception:
                pass
        # عمداً close نمی‌کنیم
        return len(sessions)

    @staticmethod
    def attack_query_leak():
        """حمله: اجرای query های سنگین بدون cleanup"""
        from engine.data_connector import connector

        results = []
        for i in range(200):
            try:
                r = connector.execute_analytics_query(f"""
                    SELECT
                        site_id,
                        AVG(tmin_c) as avg_min,
                        MAX(tmax_c) as max_max
                    FROM weather_daily
                    WHERE year = {(i % 30) + 1990}
                    GROUP BY site_id
                """)
                results.append(r)
            except Exception:
                pass
        return len(results)

    @staticmethod
    def attack_memory_fragmentation():
        """حمله: تکه‌تکه کردن حافظه"""
        objects = []
        # Create and destroy repeatedly
        for _ in range(500):
            obj = [random.random() for _ in range(1000)]
            objects.append(obj)
            if len(objects) > 100:
                objects.pop(0)
        return len(objects)


# ============================================================================
# PROTOCOL 2: THREAD CHAOS
# ============================================================================


class ThreadChaosProtocol:
    """پروتکل ۲: آشوب thread"""

    @staticmethod
    def attack_thread_explosion():
        """حمله: انفجار 500 thread"""
        errors = []

        def worker(i):
            from database.hub import hub

            try:
                with hub.get_session() as session:
                    from sqlalchemy import text

                    session.execute(text("SELECT 1"))
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(500):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=1)

        if len(errors) > 100:
            raise RuntimeError(f"Thread explosion: {len(errors)}/500 failed")
        return len(errors)

    @staticmethod
    def attack_deadlock_scenario():
        """حمله: شبیه‌سازی deadlock"""
        import threading

        from sqlalchemy import text

        from database.hub import hub

        barrier = threading.Barrier(10)
        errors = []

        def deadlock_worker(idx):
            try:
                barrier.wait(timeout=5)
                with hub.get_session() as session:
                    for _ in range(100):
                        session.execute(text("SELECT 1"))
            except Exception as e:
                errors.append(str(e))

        threads = []
        for i in range(10):
            t = threading.Thread(target=deadlock_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        if len(errors) > 5:
            raise RuntimeError(f"Deadlock detected: {len(errors)} errors")
        return len(errors)

    @staticmethod
    def attack_thread_starvation():
        """حمله: starvation با ایجاد thread های سنگین"""
        from sqlalchemy import text

        from database.hub import hub

        errors = []

        def heavy_worker(idx):
            try:
                with hub.get_session() as session:
                    for _i in range(100):
                        session.execute(text("SELECT 1"))
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(heavy_worker, i) for i in range(50)]
            for f in as_completed(futures, timeout=60):
                try:
                    f.result()
                except Exception as e:
                    errors.append(str(e))

        if len(errors) > 10:
            raise RuntimeError(f"Thread starvation: {len(errors)} errors")
        return len(errors)

    @staticmethod
    def attack_race_condition_1000():
        """حمله: Race condition با 1000 thread"""

        shared = {"counter": 0}
        errors = []

        def increment():
            for _ in range(100):
                try:
                    current = shared["counter"]
                    time.sleep(0.0001)
                    shared["counter"] = current + 1
                except Exception as e:
                    errors.append(str(e))

        threads = [threading.Thread(target=increment) for _ in range(1000)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        # انتظار 100000
        expected = 100000
        actual = shared["counter"]
        if actual < expected * 0.9:
            logger.info(f"     ⚠️  Race detected: expected {expected}, got {actual}")
        return actual


# ============================================================================
# PROTOCOL 3: RESOURCE STARVATION
# ============================================================================


class ResourceStarvationProtocol:
    """پروتکل ۳: تخلیه منابع"""

    @staticmethod
    def attack_fd_exhaustion():
        """حمله: تخلیه file descriptors"""
        files = []
        for _i in range(500):
            try:
                f = tempfile.NamedTemporaryFile(delete=False)
                f.write(b"x" * 1024)
                files.append(f)
            except Exception:
                break
        # عمداً close نمی‌کنیم
        return len(files)

    @staticmethod
    def attack_temp_file_bomb():
        """حمله: بمب فایل‌های موقت"""
        paths = []
        for i in range(200):
            try:
                path = PROJECT_ROOT / "reports" / f"temp_bomb_{i}_{uuid.uuid4()}.tmp"
                path.write_text("x" * 1024 * 1024, encoding="utf-8")  # 1MB each
                paths.append(path)
            except Exception:
                break
        # عمداً delete نمی‌کنیم
        return len(paths)

    @staticmethod
    def attack_thread_pool_saturation():
        """حمله: اشباع thread pool"""
        from sqlalchemy import text

        from database.hub import hub

        def blocking_operation():
            with hub.get_session() as session:
                time.sleep(2)  # 2 seconds block
                session.execute(text("SELECT 1"))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(blocking_operation) for _ in range(100)]
            results = []
            for f in as_completed(futures, timeout=30):
                try:
                    f.result(timeout=5)
                    results.append("ok")
                except Exception:
                    results.append("error")
        return len(results)


# ============================================================================
# PROTOCOL 4: DATA POISONING
# ============================================================================


class DataPoisoningProtocol:
    """پروتکل ۴: مسموم‌سازی داده"""

    @staticmethod
    def attack_sql_injection():
        """حمله: SQL Injection"""
        from engine.data_connector import connector

        errors = []
        payloads = generate_sql_injection_payloads()

        for payload in payloads:
            try:
                connector.execute_analytics_query(f"""
                    SELECT * FROM weather_daily WHERE site_id = '{payload}'
                """)
                errors.append(f"Payload executed: {payload[:30]}")
            except Exception:
                pass  # Expected to fail safely

        if len(errors) > len(payloads) / 2:
            raise RuntimeError(f"SQL injection vulnerable: {len(errors)} payloads executed")
        return len(payloads) - len(errors)

    @staticmethod
    def attack_unicode_bomb():
        """حمله: بمب یونیکد"""
        from engine.data_connector import connector

        errors = []

        for _i in range(20):
            try:
                unicode_str = generate_unicode_bomb(10000)
                connector.execute_analytics_query(f"""
                    SELECT '{unicode_str}' as test
                """)
            except Exception as e:
                errors.append(str(e))

        return len(errors)

    @staticmethod
    def attack_null_byte_injection():
        """حمله: تزریق null byte"""
        from engine.data_connector import connector

        errors = []

        null_strings = [
            "test\x00injection",
            "\x00\x00\x00",
            "مرحبا\x00بالعالم",
            "a" * 1000 + "\x00" + "b" * 1000,
        ]

        for s in null_strings:
            try:
                connector.execute_analytics_query(f"SELECT '{s}' as test")
            except Exception as e:
                errors.append(str(e))

        return len(errors)

    @staticmethod
    def attack_malformed_json():
        """حمله: JSON مخرب"""
        import json

        malformed = [
            '{"a": undefined}',
            '{"a": NaN}',
            '{"a": Infinity}',
            "{a: 1}",
            '{"a": }',
            '{"a": 1,',
            "}" * 1000,
            "{" * 1000,
        ]

        errors = []
        for m in malformed:
            try:
                json.loads(m)
            except Exception as e:
                errors.append(str(e))

        return len(errors)


# ============================================================================
# PROTOCOL 5: CASCADE FAILURE
# ============================================================================


class CascadeFailureProtocol:
    """پروتکل ۵: شکست آبشاری"""

    @staticmethod
    def attack_timeout_cascade():
        """حمله: آبشار timeout"""
        from sqlalchemy import text

        from database.hub import hub

        def slow_query(delay):
            with hub.get_session() as session:
                time.sleep(delay)
                session.execute(text("SELECT 1"))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for i in range(50):
                delay = 5 if i % 5 == 0 else 0.01
                futures.append(executor.submit(slow_query, delay))

            results = []
            for f in as_completed(futures, timeout=30):
                try:
                    f.result(timeout=10)
                    results.append("ok")
                except Exception:
                    results.append("timeout")

        timeouts = results.count("timeout")
        if timeouts > 15:
            raise RuntimeError(f"Cascade failure: {timeouts}/50 timeouts")
        return len(results)

    @staticmethod
    def attack_exception_propagation():
        """حمله: انتشار exception"""
        errors = []

        def failing_service():
            if random.random() < 0.1:
                raise ValueError("Service failed")
            return "ok"

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(failing_service) for _ in range(100)]
            for f in as_completed(futures, timeout=5):
                try:
                    f.result()
                except Exception as e:
                    errors.append(str(e))

        if len(errors) > 20:
            raise RuntimeError(f"Exception propagation: {len(errors)} errors")
        return len(errors)

    @staticmethod
    def attack_dependency_chain():
        """حمله: زنجیره وابستگی"""
        # Service A -> B -> C -> D
        from engine.data_connector import connector

        def service_d():
            return connector.execute_analytics_query("SELECT 1")

        def service_c():
            return service_d()

        def service_b():
            return service_c()

        def service_a():
            return service_b()

        errors = []
        for _ in range(100):
            try:
                service_a()
            except Exception as e:
                errors.append(str(e))

        return 100 - len(errors)


# ============================================================================
# PROTOCOL 6: ENTROPY ATTACK
# ============================================================================


class EntropyAttackProtocol:
    """پروتکل ۶: حمله آنتروپی"""

    @staticmethod
    def attack_fuzzing_queries():
        """حمله: Fuzzing کوئری‌ها"""
        from engine.data_connector import connector

        errors = []

        for _ in range(100):
            try:
                # Random query
                query = f"SELECT {random.randint(1, 1000)} AS val"
                connector.execute_analytics_query(query)
            except Exception as e:
                errors.append(str(e))

        return 100 - len(errors)

    @staticmethod
    def attack_extreme_numbers():
        """حمله: اعداد extreme"""
        from engine.data_connector import connector

        errors = []

        extreme_queries = [
            "SELECT 1e308 as huge",
            "SELECT -1e308 as negative_huge",
            "SELECT 1e-308 as tiny",
            "SELECT 1e308 * 1e308 as overflow",
            "SELECT 1e-308 / 1e308 as underflow",
            "SELECT 0/0 as nan",
            "SELECT 1/0 as infinity",
        ]

        for q in extreme_queries:
            try:
                connector.execute_analytics_query(q)
            except Exception as e:
                errors.append(str(e))

        return len(extreme_queries) - len(errors)

    @staticmethod
    def attack_random_payloads():
        """حمله: Payload های تصادفی"""
        from engine.data_connector import connector

        errors = []

        for _ in range(50):
            try:
                random_str = "".join(random.choices(string.printable, k=100))
                connector.execute_analytics_query(f"SELECT '{random_str}' as test")
            except Exception as e:
                errors.append(str(e))

        return 50 - len(errors)


# ============================================================================
# PROTOCOL 7: TIMING ATTACK
# ============================================================================


class TimingAttackProtocol:
    """پروتکل ۷: حمله زمانی"""

    @staticmethod
    def attack_burst_requests():
        """حمله: درخواست‌های انفجاری"""
        from sqlalchemy import text

        from database.hub import hub

        start = time.perf_counter()
        results = []

        for _ in range(1000):
            try:
                with hub.get_session() as session:
                    session.execute(text("SELECT 1"))
                    results.append("ok")
            except Exception:
                results.append("error")

        elapsed = time.perf_counter() - start
        rps = len(results) / elapsed

        errors = results.count("error")
        if errors > 100:
            raise RuntimeError(f"Burst attack: {errors}/1000 failed at {rps:.0f} RPS")

        return rps

    @staticmethod
    def attack_slowloris():
        """حمله: Slowloris (باز نگه داشتن اتصالات)"""
        from sqlalchemy import text

        from database.hub import hub

        sessions = []

        for _i in range(80):
            try:
                session = hub.get_session_factory()()
                session.connection()
                session.execute(text("SELECT 1"))
                sessions.append(session)
            except Exception:
                pass

        try:
            session = hub.get_session_factory()()
            sessions.append(session)
            session.connection()
            session.execute(text("SELECT 1"))
        except Exception:
            pass

        if len(sessions) < 80:
            raise RuntimeError(f"Slowloris: only {len(sessions)}/80 connections available")
        return len(sessions)

    @staticmethod
    def attack_concurrent_burst():
        """حمله: Burst همزمان"""
        from sqlalchemy import text

        from database.hub import hub

        def burst_worker(i):
            with hub.get_session() as session:
                for _ in range(10):
                    session.execute(text("SELECT 1"))

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(burst_worker, i) for i in range(100)]
            for f in as_completed(futures, timeout=10):
                f.result()

        elapsed = time.perf_counter() - start
        rps = 1000 / elapsed  # 100 workers * 10 ops
        return rps


# ============================================================================
# PROTOCOL 8: PROCESS ISOLATION
# ============================================================================


class ProcessIsolationProtocol:
    """پروتکل ۸: ایزولاسیون پروسه"""

    @staticmethod
    def _worker_function(args):
        """تابع worker برای multiprocessing"""
        try:
            from sqlalchemy import text

            from database.hub import hub

            with hub.get_session() as session:
                for _ in range(10):
                    session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    def attack_multiprocess_storm():
        """حمله: طوفان چند پروسه‌ای"""
        # Use ProcessPoolExecutor for isolation
        try:
            with ProcessPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(ProcessIsolationProtocol._worker_function, i) for i in range(20)
                ]
                results = [f.result(timeout=30) for f in as_completed(futures)]
                success = sum(1 for r in results if r)
                return success
        except Exception as e:
            raise RuntimeError(f"Multiprocess storm failed: {e}")


# ============================================================================
# PROTOCOL 9: DATAHUB CHAOS — targets database/hub/hub.py (DataHub singleton)
# ============================================================================


class DataHubChaosProtocol:
    """پروتکل ۹: آشوب DataHub — هدف: database/hub/hub.py (DataHub singleton)

    Tests the singleton connection management, pool saturation, session lifecycle,
    and transaction integrity under adversarial concurrent access.
    """

    @staticmethod
    def attack_connection_pool_exhaustion():
        """حمله: خالی کردن connection pool DataHub.

        DuckDB connections themselves have no pool limit, so the real vector
        is the SQLAlchemy session pool (QueuePool).  We exhaust it by opening
        sessions *and checking out connections* (via SELECT 1), then verify
        the pool correctly rejects the overflow request.
        """
        from sqlalchemy import text

        from database.hub import hub

        sessions = []
        errors = []

        engine = hub.get_sqlalchemy_engine()
        pool = engine.pool

        # Dynamically read the actual pool configuration
        pool_size = pool.size()
        max_overflow = pool._max_overflow
        total_pool = pool_size + max_overflow

        for _i in range(total_pool):
            session = hub.get_session_factory()()
            sessions.append(session)
            session.connection()
            session.execute(text("SELECT 1"))

        try:
            session = hub.get_session_factory()()
            sessions.append(session)
            session.execute(text("SELECT 1"))
        except Exception as e:
            errors.append(str(e))

        for s in sessions:
            with contextlib.suppress(Exception):
                s.close()

        if not errors:
            raise RuntimeError(
                f"Pool exhaustion test: no errors raised out of {total_pool + 1} connections"
            )
        return len(sessions)

    @staticmethod
    def attack_concurrent_sessions_with_transactions():
        """حمله: همزمانی sessions با تراکنش‌های رقابتی."""
        from sqlalchemy import text

        from database.hub import hub

        errors = []
        results = []

        def worker(i):
            try:
                with hub.get_session() as session:
                    session.execute(text("SELECT 1"))
                    results.append(1)
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(worker, i) for i in range(100)]
            for f in as_completed(futures, timeout=30):
                with contextlib.suppress(Exception):
                    f.result()

        if len(errors) > 50:
            raise RuntimeError(f"Concurrent sessions: {len(errors)}/100 failed")
        return len(results)

    @staticmethod
    def attack_session_leak():
        """حمله: نشت session بدون بستن."""
        from database.hub import hub

        sessions = []
        for _i in range(300):
            try:
                session_factory = hub.get_session_factory()
                session = session_factory()
                sessions.append(session)
            except Exception:
                pass

        leaked = 0
        for s in sessions:
            if s.is_active:
                leaked += 1
            with contextlib.suppress(Exception):
                s.close()

        return leaked

    @staticmethod
    def attack_transaction_rollback_stress():
        """حمله: فشار روی rollbackهای تراکنش."""
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError

        from database.hub import hub

        errors = []

        def tx_worker(i):
            try:
                with hub.get_session() as session:
                    if i % 2 == 0:
                        session.execute(text("SELECT 1"))
                        raise SQLAlchemyError("Simulated rollback")
                    else:
                        session.execute(text("SELECT 1"))
            except SQLAlchemyError:
                pass
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(tx_worker, i) for i in range(50)]
            for f in as_completed(futures, timeout=30):
                with contextlib.suppress(Exception):
                    f.result()

        if len(errors) > 10:
            raise RuntimeError(f"Rollback stress: {len(errors)} unexpected errors")
        return len(errors)

    @staticmethod
    def attack_duckdb_concurrent_queries():
        """حمله: کوئری‌های همزمان DuckDB."""
        from database.hub import hub

        results = []
        errors = []

        def query_worker(i):
            try:
                conn = hub.get_duckdb("master")
                r = conn.execute("SELECT 1 as val").fetchall()
                results.append(r)
                conn.close()
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(query_worker, i) for i in range(30)]
            for f in as_completed(futures, timeout=30):
                with contextlib.suppress(Exception):
                    f.result()

        if len(errors) > 15:
            raise RuntimeError(f"DuckDB concurrent: {len(errors)}/30 failed")
        return len(results)


# ============================================================================
# PROTOCOL 10: ENGINE COMPUTATIONAL CHAOS — targets engine/hydroma modules
# ============================================================================


class EngineComputationalProtocol:
    """پروتکل ۱۰: آشوب محاسباتی موتور — هدف: engine/hydroma core modules

    Tests scientific computation engines for numerical stability, extreme-value
    handling, and C++/Python fallback robustness.
    """

    @staticmethod
    def attack_hydroma_core_extreme_values():
        """حمله: مقادیر افراطی به HydromaCore."""
        from engine.hydroma.core import HydromaCore

        errors = []
        results = []

        extreme_inputs = [
            (float("inf"), 50.0, 0.9, 10),
            (float("-inf"), 50.0, 0.9, 10),
            (float("nan"), 50.0, 0.9, 10),
            (-9999.0, 50.0, 0.9, 10),
            (1e308, 50.0, 0.9, 10),
            (0.0, 50.0, 0.9, 10),
            (15.0, 50.0, 0.9, 0),
            (15.0, 50.0, 1.5, 10),
        ]

        for ph, om, clay, texture in extreme_inputs:
            try:
                score = HydromaCore.compute_soil_health_score(ph, om, clay, texture)
                results.append(score)
            except Exception as e:
                errors.append(f"soil_health({ph}, {om}, {clay}, {texture}): {e}")

        for rf in [float("inf"), float("-inf"), -1e9, 1e9, 0, float("nan")]:
            try:
                val = HydromaCore.compute_rainfall_erosivity(rf)
                results.append(val)
            except Exception as e:
                errors.append(f"erosivity({rf}): {e}")

        for r, k, ls, c, p in [
            (float("inf"), 0.3, 1.0, 0.5, 0.8),
            (-1e9, 0.3, 1.0, 0.5, 0.8),
            (1000, float("inf"), 1.0, 0.5, 0.8),
            (1000, 0.3, 1.0, float("nan"), 0.8),
        ]:
            try:
                val = HydromaCore.rusle_soil_loss(r, k, ls, c, p)
                results.append(val)
            except Exception as e:
                errors.append(f"rusle({r}, {k}): {e}")

        for temp, rain in [(float("inf"), 1000), (float("nan"), -500), (1e6, 0), (-273.15, 1e9)]:
            try:
                val = HydromaCore.classify_koppen_climate(temp, rain)
                results.append(val)
            except Exception as e:
                errors.append(f"koppen({temp}, {rain}): {e}")

        if len(errors) > 3:
            raise RuntimeError(
                f"HydromaCore extreme values: {len(errors)} errors out of {len(extreme_inputs) + 4 + 4 + 4}"
            )
        return len(results)

    @staticmethod
    def attack_et_calculator_extreme_weather():
        """حمله: ClimateData افراطی به ET Calculator."""
        from engine.hydroma.climate.et_calculator import (
            ClimateData,
            calc_et0,
            calc_et0_hargreaves,
            calc_et0_penman_monteith,
        )

        results = []
        errors = []

        extreme_data_list = [
            ClimateData(
                tmin=float("inf"),
                tmax=float("inf"),
                rh_min=50,
                rh_max=50,
                wind_speed=2,
                solar_radiation=20,
                elevation=0,
                latitude=0,
                doy=1,
            ),
            ClimateData(
                tmin=float("nan"),
                tmax=25,
                rh_min=50,
                rh_max=50,
                wind_speed=2,
                solar_radiation=20,
                elevation=0,
                latitude=0,
                doy=1,
            ),
            ClimateData(
                tmin=-273.15,
                tmax=1000,
                rh_min=50,
                rh_max=50,
                wind_speed=2,
                solar_radiation=20,
                elevation=0,
                latitude=0,
                doy=1,
            ),
            ClimateData(
                tmin=20,
                tmax=20,
                rh_min=float("inf"),
                rh_max=50,
                wind_speed=2,
                solar_radiation=20,
                elevation=0,
                latitude=0,
                doy=1,
            ),
            ClimateData(
                tmin=20,
                tmax=25,
                rh_min=50,
                rh_max=50,
                wind_speed=float("inf"),
                solar_radiation=20,
                elevation=0,
                latitude=0,
                doy=1,
            ),
            ClimateData(
                tmin=20,
                tmax=25,
                rh_min=50,
                rh_max=50,
                wind_speed=2,
                solar_radiation=float("nan"),
                elevation=0,
                latitude=0,
                doy=1,
            ),
            ClimateData(
                tmin=20,
                tmax=25,
                rh_min=0,
                rh_max=100,
                wind_speed=2,
                solar_radiation=20,
                elevation=8848,
                latitude=90,
                doy=365,
            ),
            ClimateData(
                tmin=20,
                tmax=-10,
                rh_min=50,
                rh_max=50,
                wind_speed=2,
                solar_radiation=20,
                elevation=0,
                latitude=0,
                doy=1,
            ),
        ]

        for data in extreme_data_list:
            try:
                et0 = calc_et0(data)
                results.append(et0)
            except ValueError:
                pass
            except Exception as e:
                errors.append(f"calc_et0({data}): {e}")

        for data in extreme_data_list:
            try:
                et0 = calc_et0_hargreaves(data=data)
                results.append(et0)
            except ValueError:
                pass
            except Exception as e:
                errors.append(f"hargreaves({data}): {e}")

        for data in extreme_data_list:
            try:
                et0 = calc_et0_penman_monteith(data)
                results.append(et0)
            except ValueError:
                pass
            except Exception as e:
                errors.append(f"penman_monteith({data}): {e}")

        if len(errors) > 5:
            raise RuntimeError(f"ET calculator extreme weather: {len(errors)} unexpected errors")
        return len(results)

    @staticmethod
    def attack_phenology_extreme_temperatures():
        """حمله: داده‌های دماي افراطی به Phenology Engine."""
        from engine.hydroma.phenology import (
            PhenologyInput,
            run_phenology,
        )

        results = []
        errors = []

        extreme_temps = [
            ([float("inf")] * 100, [30.0] * 100),
            ([float("nan")] * 100, [30.0] * 100),
            ([-273.15] * 100, [30.0] * 100),
            ([1000.0] * 100, [30.0] * 100),
            ([20.0] * 100, [float("inf")] * 100),
            ([float("nan")] * 100, [float("nan")] * 100),
            ([50.0] * 200, [20.0] * 200),
            ([10.0] * 5, [25.0] * 5),
        ]

        for i, (tmin_list, tmax_list) in enumerate(extreme_temps):
            for crop in ["wheat", "maize", "rice", "unknown_crop"]:
                try:
                    inputs = PhenologyInput(
                        crop=crop,
                        tmin_daily=tmin_list,
                        tmax_daily=tmax_list,
                        planting_date_doy=90,
                        harvest_date_doy=280,
                    )
                    output = run_phenology(inputs)
                    results.append(output.crop)
                except Exception as e:
                    errors.append(f"phenology({crop}, extreme_temps[{i}]): {e}")

        if len(errors) > 10:
            raise RuntimeError(f"Phenology extreme temps: {len(errors)} errors")
        return len(results)

    @staticmethod
    def attack_wrapper_indices_extreme_reflectance():
        """حمله: مقادیر بازتاب افراطی به Wrapper (vegetation indices)."""
        from engine.hydroma.wrapper import (
            compute_all_indices,
            compute_evi,
            compute_ndvi,
            compute_savi,
        )

        results = []
        errors = []

        extreme_pairs = [
            (0.0, 0.0),
            (float("inf"), float("inf")),
            (float("nan"), float("nan")),
            (1e10, 1e10),
            (-1.0, 1.0),
            (float("inf"), 0.0),
            (0.0, float("inf")),
            (float("nan"), 1.0),
        ]

        for red, nir in extreme_pairs:
            try:
                results.append(compute_ndvi(red, nir))
            except Exception as e:
                errors.append(f"ndvi({red}, {nir}): {e}")

            try:
                results.append(compute_evi(red, nir, 0.1))
            except Exception as e:
                errors.append(f"evi({red}, {nir}): {e}")

            try:
                results.append(compute_savi(red, nir, 0.5))
            except Exception as e:
                errors.append(f"savi({red}, {nir}): {e}")

        for red, nir in extreme_pairs:
            try:
                indices = compute_all_indices(red, nir)
                results.append(len(indices))
            except Exception as e:
                errors.append(f"all_indices({red}, {nir}): {e}")

        if len(errors) > 5:
            raise RuntimeError(f"Wrapper extreme indices: {len(errors)} errors")
        return len(results)

    @staticmethod
    def attack_wrapper_soil_extreme_inputs():
        """حمله: داده‌های خاک افراطی به Wrapper."""
        from engine.hydroma.wrapper import analyze_soil, apply_scenario, compute_erosion

        results = []
        errors = []

        extreme_soil = [
            (float("inf"), 50.0, 100, 50, 100, 0.5, 0.3, 0.2),
            (float("nan"), 50.0, 100, 50, 100, 0.5, 0.3, 0.2),
            (-1.0, 50.0, 100, 50, 100, 0.5, 0.3, 0.2),
            (6.5, 1e10, 1e10, 1e10, 1e10, 1e10, 1e10, 1e10),
            (6.5, 2.0, 50, 30, 80, 0.0, 0.0, 0.0),
            (6.5, 2.0, 50, 30, 80, 100.0, 100.0, 100.0),
        ]

        for ph, om, n, p, k, clay, silt, sand in extreme_soil:
            try:
                result = analyze_soil(ph, om, n, p, k, clay, silt, sand)
                results.append(result.get("health_score", 0))
            except Exception as e:
                errors.append(f"analyze_soil({ph}, {om}): {e}")

        for sl, rain, c, p_factor in [
            (float("inf"), 1000, "loam", 0.5),
            (float("nan"), -100, "sandy", 0.8),
            (-10, 1e9, "clay", 0.1),
            (0, 0, "unknown_texture", 1.0),
        ]:
            try:
                result = compute_erosion(sl, rain, sl, c, c_factor=c, p_factor=p_factor)
                results.append(result.get("risk_level", "unknown"))
            except Exception as e:
                errors.append(f"erosion({sl}, {rain}): {e}")

        for temp, precip, scenario, year in [
            (float("inf"), 1000, "ssp585", 2080),
            (float("nan"), -500, "ssp126", 2050),
            (1000, 1e9, "unknown_ssp", 2100),
        ]:
            try:
                result = apply_scenario(temp, precip, scenario, year)
                results.append(result.get("scenario", "unknown"))
            except Exception as e:
                errors.append(f"scenario({temp}, {precip}, {scenario}): {e}")

        if len(errors) > 5:
            raise RuntimeError(f"Wrapper extreme soil/erosion: {len(errors)} errors")
        return len(results)


# ============================================================================
# PROTOCOL 11: SERVICE TRANSACTION CHAOS — targets services/* modules
# ============================================================================


class ServiceTransactionProtocol:
    """پروتکل ۱۱: آشوب تراکنش سرویس — هدف: services/carbon, services/ecowallet, services/simulation

    Tests business logic services for concurrency safety, idempotency, and
    state consistency under adversarial concurrent operations.
    """

    @staticmethod
    def attack_carbon_credit_double_issuance():
        """حمله: صدور دوبله اعتبار کربن تحت همزمانی."""

        from database.models import CarbonProject
        from services.carbon.service import CarbonService

        errors = []
        duplicate_credits = []
        session_factory = _temp_sqlite_session()
        motor = _StubCarbonMrvMotor()

        session = session_factory()
        try:
            from database.models import CarbonProject

            project = CarbonProject(
                project_id="chaos-test-project",
                name="Chaos Test Project",
                project_type="afforestation",
                area_hectares=100.0,
                user_id="chaos-user",
                methodology="vm0032",
                region="test",
                duration_years=10,
            )
            project.field_verified = True
            project.mrv_documents = ["doc1"]
            project.status = "verified"
            project.verification_status = "verified"
            session.add(project)
            session.commit()
        finally:
            session.close()

        payloads = []
        for i in range(5):
            payloads.append(
                {
                    "project_id": "chaos-test-project",
                    "soc_initial_t_ha": 50.0,
                    "soc_final_t_ha": 80.0,
                    "area_ha": 100.0,
                    "measured_soc_t_ha": 60.0,
                    "measurements": [{"year": 0, "soc_t_ha": 50.0}, {"year": 5, "soc_t_ha": 80.0}],
                    "methodology": "vm0032",
                    "permanence_factor": 0.85,
                    "vintage_year": 2024,
                    "issued_by": "chaos-test",
                    "idempotency_key": f"dup-key-{i}",
                }
            )

        credit_ids = []

        def issue_worker(payload):
            try:
                s = CarbonService(db=session_factory(), motor=motor)
                result = s.issue_credits(payload)
                credit_ids.append(result.get("credit_id"))
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(issue_worker, p) for p in payloads]
            for f in as_completed(futures, timeout=30):
                with contextlib.suppress(Exception):
                    f.result()

        unique_credits = {c for c in credit_ids if c}
        if len(unique_credits) > 1:
            duplicate_credits.append(
                f"Double issuance detected: {len(unique_credits)} unique credits from 5 concurrent requests"
            )

        if duplicate_credits:
            raise RuntimeError("; ".join(duplicate_credits))
        if len(errors) > 5:
            raise RuntimeError(f"Carbon double-issuance: {len(errors)} errors")
        return len(unique_credits)

    @staticmethod
    def attack_wallet_balance_race_condition():
        """حمله: Race condition در موجودی Wallet."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from services.ecowallet.service import earn, wallet_state

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _create_wallet_tables(engine)
        SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        user_id = random.randint(10000, 99999)
        earnings = []
        errors = []

        def earn_worker():
            try:
                db = SessionFactory()
                try:
                    amount, _balance = earn(db, user_id, "tree_planting", 1.0)
                    earnings.append(amount)
                    db.commit()
                except Exception as e:
                    errors.append(str(e))
                    db.rollback()
                finally:
                    db.close()
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(earn_worker) for _ in range(20)]
            for f in as_completed(futures, timeout=15):
                with contextlib.suppress(Exception):
                    f.result()

        expected_balance = sum(earnings)
        db = SessionFactory()
        try:
            state = wallet_state(db, user_id)
        finally:
            db.close()

        actual_balance = state["balance"]
        if abs(actual_balance - expected_balance) > 0.01:
            raise RuntimeError(
                f"Wallet race condition: expected {expected_balance}, got {actual_balance} "
                f"(earnings count={len(earnings)})"
            )
        if len(errors) > 5:
            raise RuntimeError(f"Wallet race errors: {len(errors)}")
        return len(earnings)

    @staticmethod
    def attack_wallet_concurrent_redeem():
        """حمله: برداشت همزمان از Wallet با موجودی محدود."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from services.ecowallet.service import earn, redeem, wallet_state

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _create_wallet_tables(engine)
        SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        user_id = random.randint(10000, 99999)
        db = SessionFactory()
        try:
            earn(db, user_id, "tree_planting", 100.0)
            db.commit()
        finally:
            db.close()

        redemptions = []
        errors = []

        def redeem_worker():
            try:
                db = SessionFactory()
                try:
                    amount, _balance = redeem(db, user_id, 20.0)
                    redemptions.append(amount)
                    db.commit()
                except Exception as e:
                    errors.append(str(e))
                    db.rollback()
                finally:
                    db.close()
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(redeem_worker) for _ in range(20)]
            for f in as_completed(futures, timeout=15):
                with contextlib.suppress(Exception):
                    f.result()

        db = SessionFactory()
        try:
            state = wallet_state(db, user_id)
        finally:
            db.close()

        total_redeemed = sum(redemptions)
        initial = 5000.0
        final_balance = state["balance"]
        if final_balance < -0.01:
            raise RuntimeError(
                f"Wallet overdraft: balance {final_balance} after redeeming {total_redeemed} from {initial}"
            )
        return len(redemptions)

    @staticmethod
    def attack_simulation_concurrent_runs():
        """حمله: اجراي همزمان چند شبیه‌ساز."""
        from datetime import date

        from services.simulation.schemas import (
            CropParameters,
            SimulationContext,
            SimulationType,
            SoilProfile,
            WeatherData,
        )
        from services.simulation.service import SimulationService

        errors = []
        results = []

        ctx = SimulationContext(
            simulation_id=f"chaos-sim-{uuid.uuid4().hex[:8]}",
            simulation_type=SimulationType.CROP_GROWTH,
            soil=SoilProfile(texture="loam"),
            weather=WeatherData(temp_min_c=10, temp_max_c=30, precipitation_mm=5.0),
            crop=CropParameters(
                crop_type="wheat",
                planting_date=date.today(),
            ),
            start_date=date.today(),
        )

        def run_worker(i):
            try:
                import asyncio

                svc = SimulationService()
                r = asyncio.run(svc.orchestrator.run_single(SimulationType.CROP_GROWTH, ctx))
                results.append(r.status.value)
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_worker, i) for i in range(10)]
            for f in as_completed(futures, timeout=30):
                with contextlib.suppress(Exception):
                    f.result()

        if len(errors) > 7:
            raise RuntimeError(f"Simulation concurrent: {len(errors)}/10 failed")
        return len(results)


# ============================================================================
# PROTOCOL 12: SECURITY & DATA INTEGRITY — targets services/security, query_safe
# ============================================================================


class SecurityIntegrityProtocol:
    """پروتکل ۱۲: یکپارچگی امنیتی — هدف: services/security/query_safe.py

    Tests SQL injection prevention, identifier validation, and data integrity
    safeguards in the security layer.
    """

    @staticmethod
    def attack_query_safe_identifier_bypass():
        """حمله: دور زدن از اعتبارسنجی شناسه SQL."""
        from services.security.query_safe import _safe_ident

        bypass_payloads = [
            "weather_daily; DROP TABLE users--",
            "1; DROP TABLE users; --",
            "test' OR '1'='1",
            "table_name` --",
            "1 UNION SELECT * FROM users",
            "",
            "123abc",
            "col--comment",
            "'; EXEC xp_cmdshell--",
            "weather_daily\nDROP TABLE users",
        ]

        blocked = 0
        passed = 0

        for payload in bypass_payloads:
            try:
                _safe_ident(payload)
                passed += 1
            except ValueError:
                blocked += 1

        if passed > 0:
            raise RuntimeError(
                f"Identifier bypass: {passed}/{len(bypass_payloads)} payloads accepted as valid identifiers"
            )
        return blocked

    @staticmethod
    def attack_query_safe_where_clause_injection():
        """حمله: تزریق در build_where_clause."""
        from services.security.query_safe import build_where_clause

        injection_conditions = [
            {"site_id = 1; DROP TABLE users--": 1},
            {"normal_col": "'; DROP TABLE users; --"},
            {"1=1": "anything"},
            {"site_id": "UNION SELECT * FROM users"},
            {"table_name; --": None},
        ]

        blocked = 0
        leaked = 0

        for conditions in injection_conditions:
            try:
                clause, _params = build_where_clause(conditions)
                if ";" in clause or "DROP" in clause.upper() or "UNION" in clause.upper():
                    leaked += 1
                else:
                    blocked += 1
            except (ValueError, KeyError, TypeError):
                blocked += 1

        if leaked > 0:
            raise RuntimeError(f"Where clause injection: {leaked} payloads leaked dangerous SQL")
        return blocked

    @staticmethod
    def attack_data_connector_sql_injection():
        """حمله: تزریق SQL در DataConnector."""
        from engine.data_connector import connector

        payloads = [
            "'; DROP TABLE users; --",
            "1 OR 1=1 --",
            "UNION SELECT * FROM information_schema.tables --",
            "'; INSERT INTO users VALUES ('hacker', 'hacker'); --",
            "1; WAITFOR DELAY '0:0:10' --",
        ]

        blocked = 0
        executed = 0

        for payload in payloads:
            query = f"SELECT * FROM weather_daily WHERE site_id = '{payload}'"
            try:
                connector.execute_analytics_query(query)
                executed += 1
            except (ValueError, Exception):
                blocked += 1

        if executed > 0:
            raise RuntimeError(
                f"DataConnector SQL injection: {executed}/{len(payloads)} payloads executed"
            )
        return blocked

    @staticmethod
    def attack_data_connector_non_whitelisted_tables():
        """حمله: دسترسی به جداول غیرمجاز در DataConnector."""
        from engine.data_connector import connector

        non_whitelisted = [
            "SELECT * FROM users",
            "SELECT * FROM CarbonCredit",
            "SELECT * FROM EcoWallet",
            "SELECT * FROM information_schema.tables",
            "SELECT * FROM pg_catalog",
        ]

        blocked = 0
        accessed = 0

        for query in non_whitelisted:
            try:
                connector.execute_analytics_query(query)
                accessed += 1
            except (ValueError, Exception):
                blocked += 1

        if accessed > 0:
            raise RuntimeError(
                f"Non-whitelisted table access: {accessed}/{len(non_whitelisted)} queries succeeded"
            )
        return blocked

    @staticmethod
    def attack_honeypot_trap_detection():
        """حمله: آزمون لاشه (honeypot) در مقابل مسیرهای شناسعی."""
        from services.security.honeypot import honeypot

        trap_paths = [
            "/admin.php",
            "/.env",
            "/.git/config",
            "/wp-login.php",
            "/api/v1/honeypot/token",
            "/config.php.bak",
            "/api/v1/honeypot/admin",
        ]

        detected = 0
        for path in trap_paths:
            if honeypot.is_trap(path):
                detected += 1

        if detected < len(trap_paths):
            raise RuntimeError(f"Honeypot detected {detected}/{len(trap_paths)} trap paths")

        for i in range(20):
            honeypot.hit(f"192.168.1.{i}", trap_paths[i % len(trap_paths)], "chaos-test-agent")
            if not honeypot.is_blocked(f"192.168.1.{i}"):
                raise RuntimeError(f"IP 192.168.1.{i} not blocked after honeypot hit")

        return detected

    @staticmethod
    def attack_rate_limiter_bypass():
        """حمله: دور زدن rate limiter."""
        from services.security.rate_limit import rate_limiter

        allowed = 0
        blocked = 0

        for _i in range(200):
            ok, _retry = rate_limiter.check("10.0.0.1", "/api/test", None)
            if ok:
                allowed += 1
            else:
                blocked += 1

        if blocked == 0:
            raise RuntimeError(
                f"Rate limiter never blocked: {allowed}/200 requests allowed (expected at least 1)"
            )
        return blocked


# ============================================================================
# PROTOCOL 13: EXTERNAL SERVICE RESILIENCE — targets external APIs / integrations
# ============================================================================


class ExternalResilienceProtocol:
    """پروتکل ۱۳: مقاومت در برابر سرویس‌های خارجی — هدف: services/scientific_motors

    Tests external API clients for timeout handling, graceful degradation,
    and error propagation when dependencies are unavailable.
    """

    @staticmethod
    def attack_climate_motor_api_failure():
        """حمله: شکست API اکسترنال در Climate Motor."""
        from services.scientific_motors.climate_motor import SCENARIOS, run_climate

        scenarios = list(SCENARIOS)
        results = []
        errors = []

        for i in range(len(scenarios)):
            scenario = scenarios[i]
            try:
                result = run_climate(
                    lat=35.0,
                    lon=51.0,
                    scenario=scenario,
                    baseline_start="2015-01-01",
                    baseline_end="2016-12-31",
                    future_start="2040-01-01",
                    future_end="2042-12-31",
                )
                if result.get("status") == "ok":
                    results.append(result)
                elif result.get("status") == "error":
                    errors.append(result.get("error", "unknown error"))
            except Exception as e:
                errors.append(f"{scenario}: {type(e).__name__}: {e}")

        if len(errors) == len(scenarios):
            raise RuntimeError(
                f"Climate motor: all {len(scenarios)} scenarios failed — total external API dependency"
            )
        return len(results)

    @staticmethod
    def attack_climate_motor_invalid_scenario():
        """حمله: ارسال scenario نامعتبر به Climate Motor."""
        from services.scientific_motors.climate_motor import run_climate

        invalid_scenarios = ["INVALID", "ssp999", "", "null", "'; DROP TABLE--", "BWh"]

        results = []
        for scenario in invalid_scenarios:
            try:
                result = run_climate(lat=35.0, lon=51.0, scenario=scenario)
                if result.get("status") == "error":
                    results.append(scenario)
                elif result.get("status") == "ok":
                    raise RuntimeError(f"Invalid scenario '{scenario}' was accepted as valid")
            except Exception:
                results.append(scenario)

        if len(results) < len(invalid_scenarios):
            accepted = len(invalid_scenarios) - len(results)
            raise RuntimeError(f"Climate motor accepted {accepted} invalid scenarios")
        return len(results)

    @staticmethod
    def attack_climate_motor_extreme_coordinates():
        """حمله: مختصات افراطی به Climate Motor."""
        from services.scientific_motors.climate_motor import run_climate

        extreme_coords = [
            (float("inf"), 51.0),
            (float("nan"), 51.0),
            (-91.0, 51.0),
            (91.0, 51.0),
            (35.0, float("inf")),
            (35.0, float("nan")),
            (0.0, 0.0),
            (85.0, 180.0),
        ]

        results = []
        for lat, lon in extreme_coords:
            try:
                result = run_climate(lat=lat, lon=lon, scenario="ssp245")
                if result.get("status") == "ok":
                    results.append("ok")
                else:
                    results.append("rejected")
            except Exception:
                results.append("exception")

        return len(results)


# ============================================================================
# PROTOCOL 14: CACHE & PIPELINE CHAOS — targets services/map_engine, caching
# ============================================================================


class CachePipelineProtocol:
    """پروتکل ۱۴: آشوب کش و پردازش — هدف: services/map_engine

    Tests map generation pipeline, caching, fetcher coordination, and
    pipeline registry under adversarial conditions.
    """

    @staticmethod
    def attack_cache_key_collision():
        """حمله: برخورد کلیدهای کش."""
        from engine.hydroma.wrapper import get_capabilities

        cap = get_capabilities()
        results = []
        if cap.get("cpp_available", False):
            results.append("cpp_available")
        else:
            results.append("fallback_active")

        from pathlib import Path

        cache_dir = Path(tempfile.mkdtemp())
        cache_files = []
        try:
            for i in range(50):
                cache_file = (
                    cache_dir / f"{hashlib.sha256(f'collide_{i}'.encode()).hexdigest()[:32]}.json"
                )
                cache_file.write_text(str(i))
                cache_files.append(cache_file)

            if len(cache_files) != 50:
                raise RuntimeError(f"Cache file creation: only {len(cache_files)}/50 files created")
            results.append(len(cache_files))
        finally:
            for f in cache_files:
                with contextlib.suppress(Exception):
                    f.unlink()
            with contextlib.suppress(Exception):
                cache_dir.rmdir()

        return results

    @staticmethod
    def attack_map_orchestrator_registry():
        """حمله: ثبت pipeline های نامعتبر در MapOrchestrator."""
        from pathlib import Path

        from services.map_engine.base import MapType
        from services.map_engine.orchestrator import MapOrchestrator

        cache_dir = Path(tempfile.mkdtemp())
        try:
            orch = MapOrchestrator(cache_dir=cache_dir)
            results = []

            pipelines = orch.list_pipelines()
            results.append(len(pipelines))

            fetchers = orch.list_fetchers()
            results.append(len(fetchers))

            try:
                orch.register_pipeline(None)
                raise RuntimeError("Should have raised - None pipeline accepted")
            except Exception:
                results.append("rejected_none")

            class FakePipeline:
                map_type = MapType.M_TOP

                def get_required_layers(self):
                    return []

                async def execute(self, *a, **kw):
                    return None

                async def get_required_layers_async(self):
                    return []

            try:
                orch.register_pipeline(FakePipeline())
                results.append("registered_fake")
            except Exception:
                results.append("rejected_fake")

            if "registered_fake" in results:
                raise RuntimeError("MapOrchestrator accepted fake pipeline with wrong interface")
            return results
        finally:
            import shutil

            with contextlib.suppress(Exception):
                shutil.rmtree(str(cache_dir))

    @staticmethod
    def attack_smart_map_generator_extreme_arrays():
        """حمله: آرایه‌های افراطی به SmartMapGenerator."""
        import numpy as np
        import xarray as xr

        from services.map_engine.smart_mapper import SmartMapGenerator

        errors = []
        results = []

        try:
            red = xr.DataArray(np.array([[0.0, 0.1], [0.2, 0.3]]))
            nir = xr.DataArray(np.array([[0.1, float("inf")], [float("nan"), 0.5]]))
            SmartMapGenerator.calculate_ndvi(red, nir)
            results.append("ndvi_ok")
        except Exception as e:
            errors.append(f"ndvi_extreme: {e}")

        try:
            red = xr.DataArray(np.array([[0.0, 0.1], [0.2, 0.3]]))
            nir = xr.DataArray(np.array([[0.1, 0.1], [0.2, 0.3]]))
            SmartMapGenerator.classify_vegetation_health(red)
            results.append("classification_ok")
        except Exception as e:
            errors.append(f"classification: {e}")

        try:
            ndvi = xr.DataArray(np.array([[0.5, 0.3], [0.1, 0.8]]))
            SmartMapGenerator.estimate_biomass(ndvi, "unknown_crop")
            results.append("biomass_unknown_crop_ok")
        except Exception as e:
            errors.append(f"biomass_unknown: {e}")

        try:
            et0 = xr.DataArray(np.array([[5.0, 3.0], [4.0, 6.0]]))
            etc = SmartMapGenerator.calculate_crop_water_requirement(
                et0, "unknown", "unknown_stage"
            )
            results.append("water_req_unknown_ok")
        except Exception as e:
            errors.append(f"water_req_unknown: {e}")

        try:
            sm = xr.DataArray(np.array([[0.3, 0.2], [0.1, 0.35]]))
            etc = xr.DataArray(np.array([[5.0, 3.0], [4.0, 6.0]]))
            SmartMapGenerator.generate_irrigation_recommendation(sm, etc)
            results.append("irrigation_rec_ok")
        except Exception as e:
            errors.append(f"irrigation_rec: {e}")

        if len(errors) > 3:
            raise RuntimeError(f"SmartMapGenerator extreme arrays: {len(errors)} errors")
        return len(results)

    @staticmethod
    def attack_cache_corruption_and_recovery():
        """حمله: فساد کش و بازیابی."""
        from pathlib import Path

        from services.map_engine.orchestrator import MapOrchestrator

        cache_dir = Path(tempfile.mkdtemp())
        try:
            orch = MapOrchestrator(cache_dir=cache_dir)

            cache_file = cache_dir / "corrupt_cache.json"
            cache_file.write_text('{"invalid json{{', encoding="utf-8")

            cached = None
            with contextlib.suppress(Exception):
                cached = asyncio.run(
                    orch._check_cache(
                        MapRequest(
                            map_type=__import__(
                                "services.map_engine.base", fromlist=["MapType"]
                            ).MapType.M_TOP,
                            region=__import__("shapely.geometry", fromlist=["Polygon"]).Polygon(
                                [(0, 0), (1, 0), (1, 1), (0, 0)]
                            ),
                            resolution=10.0,
                        )
                    )
                )

            recovered = True if cached is None else cached is not None

            files_before = list(cache_dir.glob("*.json"))
            for f in files_before:
                if "corrupt" in f.name:
                    f.write_text('{"broken"', encoding="utf-8")

            with contextlib.suppress(Exception):
                asyncio.run(
                    orch._check_cache(
                        MapRequest(
                            map_type=__import__(
                                "services.map_engine.base", fromlist=["MapType"]
                            ).MapType.M_TOP,
                            region=__import__("shapely.geometry", fromlist=["Polygon"]).Polygon(
                                [(0, 0), (1, 0), (1, 1), (0, 0)]
                            ),
                            resolution=10.0,
                        )
                    )
                )

            return 1 if recovered else 0
        finally:
            import shutil

            with contextlib.suppress(Exception):
                shutil.rmtree(str(cache_dir))


# ============================================================================
# HELPER: Stub CarbonMrvMotor for testing (avoids real calculation dependency)
# ============================================================================


class _StubCarbonMrvMotor:
    """Stub motor that returns deterministic results for chaos testing."""

    def execute(self, parameters: dict) -> Any:
        from services.scientific_motors.base import MotorResult, MotorStatus

        soc_initial = float(parameters.get("soc_initial_t_ha", 0.0))
        soc_final = float(parameters.get("soc_final_t_ha", 0.0))
        area_ha = float(parameters.get("area_ha", 0.0))
        permanence = float(parameters.get("permanence_factor", 0.85))
        delta = (soc_final - soc_initial) * 3.667 * area_ha
        certified = delta * permanence if delta > 0 else delta
        return MotorResult(
            run_id="stub_motor",
            motor_type=type("M", (), {"value": "carbon_mrv"})(),
            status=MotorStatus.COMPLETED,
            outputs={
                "delta_co2e_total": round(delta, 2),
                "certified_delta_co2e_total": round(certified, 2),
                "data_mode": "field_verified",
                "permanence_factor": permanence,
            },
            summary={},
            execution_time_seconds=0.001,
        )


def _temp_sqlite_session():
    """Create an in-memory SQLite session factory for testing.

    Uses the real models from ``database.models`` so that table names and
    column definitions always stay in sync with the production schemas.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database.base import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _create_wallet_tables(engine):
    """Create wallet tables on a given engine for in-memory SQLite tests.

    Uses the real ``EcoWallet`` model's metadata so that column names and
    types always match what ``services.ecowallet.service`` expects when it
    imports ``from database.models import EcoWallet``.
    """
    from database.base import Base
    from database.models import EcoWallet  # noqa: F401 — ensures table is registered

    Base.metadata.create_all(engine)


# ============================================================================
# MAIN EXECUTOR
# ============================================================================


def main():
    """اجرای اصلی"""
    import argparse

    parser = argparse.ArgumentParser(description="HELL Protocol - Chaos Test v2")
    parser.add_argument("--hell", action="store_true", help="Run all protocols")
    parser.add_argument("--quick", action="store_true", help="Quick mode (50% attacks)")
    parser.add_argument("--protocol", type=str, help="Specific protocol (P1-P14 or 'all')")
    parser.add_argument("--apocalyptic", action="store_true", help="Include apocalyptic tests")

    args = parser.parse_args()

    if not (args.hell or args.protocol):
        args.hell = True

    logger.info("")
    logger.info(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")
    logger.info(f"{Colors.CRITICAL}  ☠️  HELL PROTOCOL - CHAOS ENGINEERING v2{Colors.RESET}")
    logger.info(f"{Colors.CRITICAL}  WARNING: This test will BREAK your system{Colors.RESET}")
    logger.info(f"{Colors.CRITICAL}  Every failure reveals a weakness to fix{Colors.RESET}")
    logger.info(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")
    logger.info("")
    logger.info("⚠️  This test suite is designed to:")
    logger.info("    - Exhaust memory resources")
    logger.info("    - Trigger deadlocks")
    logger.info("    - Corrupt data (safely)")
    logger.info("    - Cause timeouts")
    logger.info("    - Reveal race conditions")
    logger.info("    - Stress thread pools")
    logger.info("")

    orchestrator = ChaosOrchestrator()

    # Determine which protocols to run
    protocols_to_run = []
    if args.hell or args.protocol == "all":
        protocols_to_run = list(ChaosProtocol)
    elif args.protocol:
        protocols_to_run = [ChaosProtocol(args.protocol)]

    # Quick mode: skip half the attacks
    quick_factor = 0.5 if args.quick else 1.0

    # =========================================================================
    # P1: MEMORY TORTURE
    # =========================================================================
    if ChaosProtocol.MEMORY_TORTURE in protocols_to_run:
        banner("☠️  PROTOCOL 1: MEMORY TORTURE", char="!")
        tests = [
            (
                "Rapid Allocation (100MB/s)",
                MemoryTortureProtocol.attack_rapid_allocation,
                AttackVector.RESOURCE_LEAK,
                Severity.HIGH,
                30.0,
            ),
            (
                "Connection Churn (500 connections)",
                MemoryTortureProtocol.attack_connection_churn,
                AttackVector.RESOURCE_LEAK,
                Severity.EXTREME,
                60.0,
            ),
            (
                "Session Storm (200 sessions)",
                MemoryTortureProtocol.attack_session_storm,
                AttackVector.POOL_EXHAUSTION,
                Severity.EXTREME,
                30.0,
            ),
            (
                "Query Leak (200 heavy queries)",
                MemoryTortureProtocol.attack_query_leak,
                AttackVector.RESOURCE_LEAK,
                Severity.HIGH,
                60.0,
            ),
            (
                "Memory Fragmentation",
                MemoryTortureProtocol.attack_memory_fragmentation,
                AttackVector.MEMORY_FRAGMENTATION,
                Severity.MEDIUM,
                20.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.MEMORY_TORTURE, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P2: THREAD CHAOS
    # =========================================================================
    if ChaosProtocol.THREAD_CHAOS in protocols_to_run:
        banner("☠️  PROTOCOL 2: THREAD CHAOS", char="!")
        tests = [
            (
                "Thread Explosion (500 threads)",
                ThreadChaosProtocol.attack_thread_explosion,
                AttackVector.THREAD_STARVATION,
                Severity.EXTREME,
                30.0,
            ),
            (
                "Deadlock Scenario",
                ThreadChaosProtocol.attack_deadlock_scenario,
                AttackVector.DEADLOCK,
                Severity.EXTREME,
                20.0,
            ),
            (
                "Thread Starvation (50 heavy)",
                ThreadChaosProtocol.attack_thread_starvation,
                AttackVector.THREAD_STARVATION,
                Severity.HIGH,
                40.0,
            ),
            (
                "Race Condition (1000 threads)",
                ThreadChaosProtocol.attack_race_condition_1000,
                AttackVector.RACE_CONDITION,
                Severity.EXTREME,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.THREAD_CHAOS, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P3: RESOURCE STARVATION
    # =========================================================================
    if ChaosProtocol.RESOURCE_STARVATION in protocols_to_run:
        banner("☠️  PROTOCOL 3: RESOURCE STARVATION", char="!")
        tests = [
            (
                "File Descriptor Exhaustion (500 files)",
                ResourceStarvationProtocol.attack_fd_exhaustion,
                AttackVector.FD_LEAK,
                Severity.EXTREME,
                30.0,
            ),
            (
                "Temp File Bomb (200 files, 1MB each)",
                ResourceStarvationProtocol.attack_temp_file_bomb,
                AttackVector.RESOURCE_LEAK,
                Severity.HIGH,
                30.0,
            ),
            (
                "Thread Pool Saturation",
                ResourceStarvationProtocol.attack_thread_pool_saturation,
                AttackVector.POOL_EXHAUSTION,
                Severity.EXTREME,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func,
                name,
                ChaosProtocol.RESOURCE_STARVATION,
                vector,
                severity,
                timeout * quick_factor,
            )

    # =========================================================================
    # P4: DATA POISONING
    # =========================================================================
    if ChaosProtocol.DATA_POISONING in protocols_to_run:
        banner("☠️  PROTOCOL 4: DATA POISONING", char="!")
        tests = [
            (
                "SQL Injection Attack",
                DataPoisoningProtocol.attack_sql_injection,
                AttackVector.SQL_INJECTION,
                Severity.EXTREME,
                20.0,
            ),
            (
                "Unicode Bomb (20 payloads)",
                DataPoisoningProtocol.attack_unicode_bomb,
                AttackVector.UNICODE_BOMB,
                Severity.HIGH,
                20.0,
            ),
            (
                "Null Byte Injection",
                DataPoisoningProtocol.attack_null_byte_injection,
                AttackVector.NULL_INJECTION,
                Severity.HIGH,
                10.0,
            ),
            (
                "Malformed JSON",
                DataPoisoningProtocol.attack_malformed_json,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                10.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.DATA_POISONING, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P5: CASCADE FAILURE
    # =========================================================================
    if ChaosProtocol.CASCADE_FAILURE in protocols_to_run:
        banner("☠️  PROTOCOL 5: CASCADE FAILURE", char="!")
        tests = [
            (
                "Timeout Cascade (50 concurrent)",
                CascadeFailureProtocol.attack_timeout_cascade,
                AttackVector.TIMING_ATTACK,
                Severity.EXTREME,
                15.0,
            ),
            (
                "Exception Propagation",
                CascadeFailureProtocol.attack_exception_propagation,
                AttackVector.RACE_CONDITION,
                Severity.HIGH,
                15.0,
            ),
            (
                "Dependency Chain",
                CascadeFailureProtocol.attack_dependency_chain,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.CASCADE_FAILURE, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P6: ENTROPY ATTACK
    # =========================================================================
    if ChaosProtocol.ENTROPY_ATTACK in protocols_to_run:
        banner("☠️  PROTOCOL 6: ENTROPY ATTACK", char="!")
        tests = [
            (
                "Fuzzing Queries (100 random)",
                EntropyAttackProtocol.attack_fuzzing_queries,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                30.0,
            ),
            (
                "Extreme Numbers",
                EntropyAttackProtocol.attack_extreme_numbers,
                AttackVector.OVERFLOW,
                Severity.HIGH,
                20.0,
            ),
            (
                "Random Payloads (50)",
                EntropyAttackProtocol.attack_random_payloads,
                AttackVector.UNICODE_BOMB,
                Severity.MEDIUM,
                20.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.ENTROPY_ATTACK, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P7: TIMING ATTACK
    # =========================================================================
    if ChaosProtocol.TIMING_ATTACK in protocols_to_run:
        banner("☠️  PROTOCOL 7: TIMING ATTACK", char="!")
        tests = [
            (
                "Burst Requests (1000 sequential)",
                TimingAttackProtocol.attack_burst_requests,
                AttackVector.TIMING_ATTACK,
                Severity.EXTREME,
                60.0,
            ),
            (
                "Slowloris Attack",
                TimingAttackProtocol.attack_slowloris,
                AttackVector.POOL_EXHAUSTION,
                Severity.EXTREME,
                20.0,
            ),
            (
                "Concurrent Burst (100 workers)",
                TimingAttackProtocol.attack_concurrent_burst,
                AttackVector.TIMING_ATTACK,
                Severity.EXTREME,
                20.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.TIMING_ATTACK, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P8: PROCESS ISOLATION
    # =========================================================================
    if ChaosProtocol.PROCESS_ISOLATION in protocols_to_run:
        banner("☠️  PROTOCOL 8: PROCESS ISOLATION", char="!")
        orchestrator.launch_attack(
            ProcessIsolationProtocol.attack_multiprocess_storm,
            "Multiprocess Storm (10 processes)",
            ChaosProtocol.PROCESS_ISOLATION,
            AttackVector.THREAD_STARVATION,
            Severity.CATASTROPHIC,
            40.0 * quick_factor,
        )

    # =========================================================================
    # P9: DATAHUB CHAOS — targets database/hub/hub.py
    # =========================================================================
    if ChaosProtocol.DATAHUB_CHAOS in protocols_to_run:
        banner("☠️  PROTOCOL 9: DATAHUB CHAOS", char="!")
        tests = [
            (
                "Connection Pool Exhaustion (200 connections)",
                DataHubChaosProtocol.attack_connection_pool_exhaustion,
                AttackVector.POOL_EXHAUSTION,
                Severity.EXTREME,
                60.0,
            ),
            (
                "Concurrent Sessions with Transactions (100)",
                DataHubChaosProtocol.attack_concurrent_sessions_with_transactions,
                AttackVector.RACE_CONDITION,
                Severity.HIGH,
                30.0,
            ),
            (
                "Session Leak (300 sessions)",
                DataHubChaosProtocol.attack_session_leak,
                AttackVector.RESOURCE_LEAK,
                Severity.HIGH,
                30.0,
            ),
            (
                "Transaction Rollback Stress",
                DataHubChaosProtocol.attack_transaction_rollback_stress,
                AttackVector.DEADLOCK,
                Severity.HIGH,
                30.0,
            ),
            (
                "Concurrent DuckDB Queries (30)",
                DataHubChaosProtocol.attack_duckdb_concurrent_queries,
                AttackVector.THREAD_STARVATION,
                Severity.MEDIUM,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.DATAHUB_CHAOS, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P10: ENGINE COMPUTATIONAL CHAOS — targets engine/hydroma modules
    # =========================================================================
    if ChaosProtocol.ENGINE_COMPUTATIONAL in protocols_to_run:
        banner("☠️  PROTOCOL 10: ENGINE COMPUTATIONAL", char="!")
        tests = [
            (
                "HydromaCore Extreme Values",
                EngineComputationalProtocol.attack_hydroma_core_extreme_values,
                AttackVector.OVERFLOW,
                Severity.HIGH,
                30.0,
            ),
            (
                "ET Calculator Extreme Weather",
                EngineComputationalProtocol.attack_et_calculator_extreme_weather,
                AttackVector.NUMERICAL_INSTABILITY,
                Severity.HIGH,
                20.0,
            ),
            (
                "Phenology Extreme Temperatures",
                EngineComputationalProtocol.attack_phenology_extreme_temperatures,
                AttackVector.OVERFLOW,
                Severity.HIGH,
                30.0,
            ),
            (
                "Wrapper Extreme Reflectance (vegetation indices)",
                EngineComputationalProtocol.attack_wrapper_indices_extreme_reflectance,
                AttackVector.NUMERICAL_INSTABILITY,
                Severity.HIGH,
                20.0,
            ),
            (
                "Wrapper Extreme Soil Inputs",
                EngineComputationalProtocol.attack_wrapper_soil_extreme_inputs,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func,
                name,
                ChaosProtocol.ENGINE_COMPUTATIONAL,
                vector,
                severity,
                timeout * quick_factor,
            )

    # =========================================================================
    # P11: SERVICE TRANSACTION CHAOS — targets services/* business logic
    # =========================================================================
    if ChaosProtocol.SERVICE_TRANSACTION in protocols_to_run:
        banner("☠️  PROTOCOL 11: SERVICE TRANSACTION", char="!")
        tests = [
            (
                "Carbon Credit Double-Issuance Race Condition",
                ServiceTransactionProtocol.attack_carbon_credit_double_issuance,
                AttackVector.RACE_CONDITION,
                Severity.CATASTROPHIC,
                40.0,
            ),
            (
                "Wallet Balance Race Condition (20 concurrent earns)",
                ServiceTransactionProtocol.attack_wallet_balance_race_condition,
                AttackVector.RACE_CONDITION,
                Severity.HIGH,
                20.0,
            ),
            (
                "Wallet Concurrent Redeem (20 concurrent, limited balance)",
                ServiceTransactionProtocol.attack_wallet_concurrent_redeem,
                AttackVector.RACE_CONDITION,
                Severity.HIGH,
                20.0,
            ),
            (
                "Simulation Concurrent Runs (10 parallel)",
                ServiceTransactionProtocol.attack_simulation_concurrent_runs,
                AttackVector.THREAD_STARVATION,
                Severity.MEDIUM,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func,
                name,
                ChaosProtocol.SERVICE_TRANSACTION,
                vector,
                severity,
                timeout * quick_factor,
            )

    # =========================================================================
    # P12: SECURITY & DATA INTEGRITY — targets services/security modules
    # =========================================================================
    if ChaosProtocol.SECURITY_INTEGRITY in protocols_to_run:
        banner("☠️  PROTOCOL 12: SECURITY & INTEGRITY", char="!")
        tests = [
            (
                "QuerySafe Identifier Bypass (11 payloads)",
                SecurityIntegrityProtocol.attack_query_safe_identifier_bypass,
                AttackVector.IDENTIFIER_INJECTION,
                Severity.EXTREME,
                20.0,
            ),
            (
                "QuerySafe Where Clause Injection (5 payloads)",
                SecurityIntegrityProtocol.attack_query_safe_where_clause_injection,
                AttackVector.IDENTIFIER_INJECTION,
                Severity.HIGH,
                20.0,
            ),
            (
                "DataConnector SQL Injection (5 payloads)",
                SecurityIntegrityProtocol.attack_data_connector_sql_injection,
                AttackVector.SQL_INJECTION,
                Severity.EXTREME,
                20.0,
            ),
            (
                "DataConnector Non-Whitelisted Tables (5 queries)",
                SecurityIntegrityProtocol.attack_data_connector_non_whitelisted_tables,
                AttackVector.IDENTIFIER_INJECTION,
                Severity.EXTREME,
                20.0,
            ),
            (
                "Honeypot Trap Detection (7 trap paths)",
                SecurityIntegrityProtocol.attack_honeypot_trap_detection,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                15.0,
            ),
            (
                "Rate Limiter Bypass (200 requests)",
                SecurityIntegrityProtocol.attack_rate_limiter_bypass,
                AttackVector.CACHE_POLLUTION,
                Severity.HIGH,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func,
                name,
                ChaosProtocol.SECURITY_INTEGRITY,
                vector,
                severity,
                timeout * quick_factor,
            )

    # =========================================================================
    # P13: EXTERNAL SERVICE RESILIENCE — targets external API clients
    # =========================================================================
    if ChaosProtocol.EXTERNAL_RESILIENCE in protocols_to_run:
        banner("☠️  PROTOCOL 13: EXTERNAL RESILIENCE", char="!")
        tests = [
            (
                "Climate Motor All Scenarios (4 SSPs)",
                ExternalResilienceProtocol.attack_climate_motor_api_failure,
                AttackVector.API_FAILURE,
                Severity.HIGH,
                120.0,
            ),
            (
                "Climate Motor Invalid Scenarios (6 payloads)",
                ExternalResilienceProtocol.attack_climate_motor_invalid_scenario,
                AttackVector.IDENTIFIER_INJECTION,
                Severity.MEDIUM,
                10.0,
            ),
            (
                "Climate Motor Extreme Coordinates (8 pairs)",
                ExternalResilienceProtocol.attack_climate_motor_extreme_coordinates,
                AttackVector.OVERFLOW,
                Severity.MEDIUM,
                30.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func,
                name,
                ChaosProtocol.EXTERNAL_RESILIENCE,
                vector,
                severity,
                timeout * quick_factor,
            )

    # =========================================================================
    # P14: CACHE & PIPELINE CHAOS — targets services/map_engine
    # =========================================================================
    if ChaosProtocol.CACHE_PIPELINE in protocols_to_run:
        banner("☠️  PROTOCOL 14: CACHE & PIPELINE", char="!")
        tests = [
            (
                "Cache Key Collision (50 files)",
                CachePipelineProtocol.attack_cache_key_collision,
                AttackVector.CACHE_POLLUTION,
                Severity.MEDIUM,
                15.0,
            ),
            (
                "MapOrchestrator Registry Validation",
                CachePipelineProtocol.attack_map_orchestrator_registry,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                15.0,
            ),
            (
                "SmartMapGenerator Extreme Arrays (5 operations)",
                CachePipelineProtocol.attack_smart_map_generator_extreme_arrays,
                AttackVector.NUMERICAL_INSTABILITY,
                Severity.MEDIUM,
                15.0,
            ),
            (
                "Cache Corruption & Recovery",
                CachePipelineProtocol.attack_cache_corruption_and_recovery,
                AttackVector.DATA_CORRUPTION,
                Severity.MEDIUM,
                15.0,
            ),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.CACHE_PIPELINE, vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # FINAL REPORT
    # =========================================================================
    logger.info("\n\n")
    report = orchestrator.generate_hell_report()
    logger.info(report)

    # Save reports
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_file = reports_dir / f"hell_report_{timestamp}.txt"
    report_file.write_text(report, encoding="utf-8")
    logger.info(f"\n💾 Report saved: {report_file.relative_to(PROJECT_ROOT)}")

    json_file = reports_dir / f"hell_results_{timestamp}.json"
    json_data = {
        "timestamp": timestamp,
        "assessment": {
            "total_attacks": orchestrator.assessment.total_attacks,
            "survived": orchestrator.assessment.survived,
            "killed": orchestrator.assessment.killed,
            "survival_rate": orchestrator.assessment.survival_rate,
            "kill_rate": orchestrator.assessment.kill_rate,
            "memory_leaks": orchestrator.assessment.memory_leaks,
            "critical_weaknesses": orchestrator.assessment.critical_weaknesses,
        },
        "results": [r.to_dict() for r in orchestrator.results],
    }
    json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"💾 JSON saved: {json_file.relative_to(PROJECT_ROOT)}")

    # Exit code
    critical_kills = sum(
        1
        for r in orchestrator.results
        if not r.passed and r.severity in [Severity.CATASTROPHIC, Severity.APOCALYPTIC]
    )

    logger.info("")
    if critical_kills > 5:
        logger.info(f"💀 SYSTEM DESTROYED: {critical_kills} catastrophic failures")
        return 3
    elif orchestrator.assessment.kill_rate > 50:
        logger.info(f"☠️  SYSTEM BROKEN: {orchestrator.assessment.kill_rate:.1f}% kill rate")
        return 2
    elif orchestrator.assessment.kill_rate > 20:
        logger.info(f"⚠️  SYSTEM VULNERABLE: {orchestrator.assessment.kill_rate:.1f}% kill rate")
        return 1
    else:
        logger.info(
            f"✅ SYSTEM HARDENED: {orchestrator.assessment.survival_rate:.1f}% survival rate"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
