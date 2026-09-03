#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_chaos_test_v2.py
====================

HELL PROTOCOL - Chaos Engineering Test Suite v2

این اسکریپت برای شکستن سیستم طراحی شده است. بی‌رحمانه و بدون ترحم.

Author: Eco Nojin Architecture Team
Version: 2.0.0 - Hell Protocol
Severity: MAXIMUM
"""

import sys
import os
import gc
import time
import random
import string
import threading
import multiprocessing
import traceback
import statistics
import hashlib
import math
import uuid
import tempfile
import struct
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from contextlib import contextmanager
import json

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
    resources_consumed: Dict = field(default_factory=dict)
    stack_trace: str = ""
    breakpoint_hit: bool = False
    recovery_score: float = 0.0  # 0-1

    def to_dict(self) -> Dict:
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
    memory_leaks: List[str] = field(default_factory=list)
    critical_weaknesses: List[str] = field(default_factory=list)
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
    print(f"{color}[{level}]{Colors.RESET} {msg}")


def banner(title: str, char: str = "="):
    print()
    print(f"{Colors.BOLD}{char * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{char * 80}{Colors.RESET}")
    print()


def get_memory_info() -> Dict:
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


def generate_garbage(size_mb: float) -> List:
    """تولید garbage برای تست"""
    garbage = []
    chunk_size = 1024 * 1024  # 1MB
    chunks = int(size_mb)
    for _ in range(chunks):
        garbage.append(bytearray(chunk_size))
    return garbage


def generate_random_string(length: int) -> str:
    """رشته تصادفی"""
    return ''.join(random.choices(string.printable, k=length))


def generate_unicode_bomb(length: int) -> str:
    """بمب یونیکد"""
    chars = [chr(random.randint(0x20, 0xD7FF)) for _ in range(length)]
    return ''.join(chars)


def generate_sql_injection_payloads() -> List[str]:
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
        self.results: List[AttackResult] = []
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

        print()
        print(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")
        print(f"{Colors.CRITICAL}  ☠️  ATTACK: {name}{Colors.RESET}")
        print(f"{Colors.CRITICAL}  Protocol: {protocol.value} | Vector: {vector.name} | Severity: {severity.name}{Colors.RESET}")
        print(f"{Colors.CRITICAL}  Timeout: {timeout}s | Expected: {'☠️  DEATH' if expected_failure else '🛡️  SURVIVAL'}{Colors.RESET}")
        print(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")

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
            self.assessment.memory_leaks.append(
                f"{name}: +{memory_delta:.1f}MB"
            )

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
        lines.append(f"  🛡️  System Survived:      {self.assessment.survived} ({self.assessment.survival_rate:.1f}%)")
        lines.append(f"  ☠️  System Killed:        {self.assessment.killed} ({self.assessment.kill_rate:.1f}%)")
        lines.append(f"  Total Execution Time:     {self.assessment.total_time_ms/1000:.1f}s")
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
            lines.append(f"    Attacks: {len(proto_results)} | Survived: {survived} | Killed: {killed} ({survival_rate:.1f}%)")

            for r in proto_results:
                if r.passed:
                    lines.append(f"    🛡️  {r.attack_name} [{r.vector.name}] - {r.execution_time_ms:.1f}ms, {r.memory_delta_mb:+.1f}MB")
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
        strong = [r for r in self.results if r.passed and r.severity in [Severity.EXTREME, Severity.CATASTROPHIC, Severity.APOCALYPTIC]]
        if strong:
            for r in strong:
                lines.append(f"  🛡️  {r.attack_name} [{r.protocol.value}] - survived {r.severity.name} attack")
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
            for r in self.results if r.passed and r.memory_delta_mb > 10
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

    def _generate_recommendations(self) -> List[str]:
        """تولید توصیه‌های استحکام‌سازی"""
        recs = []

        # تحلیل مشکلات
        memory_attacks = [r for r in self.results if r.vector == AttackVector.RESOURCE_LEAK]
        if any(not r.passed for r in memory_attacks):
            recs.append("🔧 Implement proper resource pooling with context managers")

        thread_attacks = [r for r in self.results if r.vector in [AttackVector.DEADLOCK, AttackVector.RACE_CONDITION]]
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
            recs.extend([
                "📊 Add memory monitoring to production (psutil + tracemalloc)",
                "🔍 Implement distributed tracing (OpenTelemetry)",
                "⚡ Add connection pooling with proper cleanup",
            ])

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
        for i in range(200):
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
        from database.hub import hub
        from sqlalchemy import text
        import threading

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
        from database.hub import hub
        from sqlalchemy import text
        errors = []

        def heavy_worker(idx):
            try:
                with hub.get_session() as session:
                    for i in range(1000):
                        session.execute(text("SELECT 1"))
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(heavy_worker, i) for i in range(50)]
            for f in as_completed(futures, timeout=30):
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
        from database.hub import hub
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
            print(f"     ⚠️  Race detected: expected {expected}, got {actual}")
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
        for i in range(500):
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
        from database.hub import hub
        from sqlalchemy import text

        def blocking_operation():
            with hub.get_session() as session:
                time.sleep(5)  # 5 seconds block
                session.execute(text("SELECT 1"))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(blocking_operation) for _ in range(100)]
            results = []
            for f in as_completed(futures, timeout=10):
                try:
                    f.result(timeout=1)
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
                result = connector.execute_analytics_query(f"""
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

        for i in range(20):
            try:
                unicode_str = generate_unicode_bomb(10000)
                result = connector.execute_analytics_query(f"""
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
            '{a: 1}',
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
        from database.hub import hub
        from sqlalchemy import text

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
            for f in as_completed(futures, timeout=5):
                try:
                    f.result(timeout=1)
                    results.append("ok")
                except Exception:
                    results.append("timeout")

        timeouts = results.count("timeout")
        if timeouts > 10:
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
                random_str = ''.join(random.choices(string.printable, k=100))
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
        from database.hub import hub
        from sqlalchemy import text

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
        from database.hub import hub
        connections = []

        for i in range(50):
            try:
                conn = hub.get_duckdb("master", pooled=False)
                connections.append(conn)
                # Keep open without using
                time.sleep(0.1)
            except Exception:
                pass

        # Hold for 5 seconds
        time.sleep(5)

        # Try to create more connections
        errors = 0
        for _ in range(20):
            try:
                conn = hub.get_duckdb("master", pooled=False)
                connections.append(conn)
            except Exception:
                errors += 1

        # Cleanup
        for conn in connections:
            try:
                conn.close()
            except Exception:
                pass

        if errors > 10:
            raise RuntimeError(f"Slowloris: {errors}/20 new connections failed")
        return len(connections)

    @staticmethod
    def attack_concurrent_burst():
        """حمله: Burst همزمان"""
        from database.hub import hub
        from sqlalchemy import text

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
            from database.hub import hub
            from sqlalchemy import text

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
                futures = [executor.submit(ProcessIsolationProtocol._worker_function, i)
                           for i in range(20)]
                results = [f.result(timeout=30) for f in as_completed(futures)]
                success = sum(1 for r in results if r)
                return success
        except Exception as e:
            raise RuntimeError(f"Multiprocess storm failed: {e}")


# ============================================================================
# MAIN EXECUTOR
# ============================================================================

def main():
    """اجرای اصلی"""
    import argparse

    parser = argparse.ArgumentParser(description="HELL Protocol - Chaos Test v2")
    parser.add_argument("--hell", action="store_true", help="Run all protocols")
    parser.add_argument("--quick", action="store_true", help="Quick mode (50% attacks)")
    parser.add_argument("--protocol", type=str, help="Specific protocol (P1-P8)")
    parser.add_argument("--apocalyptic", action="store_true", help="Include apocalyptic tests")

    args = parser.parse_args()

    if not (args.hell or args.protocol):
        args.hell = True

    print()
    print(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.CRITICAL}  ☠️  HELL PROTOCOL - CHAOS ENGINEERING v2{Colors.RESET}")
    print(f"{Colors.CRITICAL}  WARNING: This test will BREAK your system{Colors.RESET}")
    print(f"{Colors.CRITICAL}  Every failure reveals a weakness to fix{Colors.RESET}")
    print(f"{Colors.CRITICAL}{'=' * 80}{Colors.RESET}")
    print()
    print("⚠️  This test suite is designed to:")
    print("    - Exhaust memory resources")
    print("    - Trigger deadlocks")
    print("    - Corrupt data (safely)")
    print("    - Cause timeouts")
    print("    - Reveal race conditions")
    print("    - Stress thread pools")
    print()

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
            ("Rapid Allocation (100MB/s)",
             MemoryTortureProtocol.attack_rapid_allocation,
             AttackVector.RESOURCE_LEAK,
             Severity.HIGH, 30.0),
            ("Connection Churn (500 connections)",
             MemoryTortureProtocol.attack_connection_churn,
             AttackVector.RESOURCE_LEAK,
             Severity.EXTREME, 60.0),
            ("Session Storm (200 sessions)",
             MemoryTortureProtocol.attack_session_storm,
             AttackVector.POOL_EXHAUSTION,
             Severity.EXTREME, 30.0),
            ("Query Leak (200 heavy queries)",
             MemoryTortureProtocol.attack_query_leak,
             AttackVector.RESOURCE_LEAK,
             Severity.HIGH, 60.0),
            ("Memory Fragmentation",
             MemoryTortureProtocol.attack_memory_fragmentation,
             AttackVector.MEMORY_FRAGMENTATION,
             Severity.MEDIUM, 20.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.MEMORY_TORTURE,
                vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P2: THREAD CHAOS
    # =========================================================================
    if ChaosProtocol.THREAD_CHAOS in protocols_to_run:
        banner("☠️  PROTOCOL 2: THREAD CHAOS", char="!")
        tests = [
            ("Thread Explosion (500 threads)",
             ThreadChaosProtocol.attack_thread_explosion,
             AttackVector.THREAD_STARVATION,
             Severity.EXTREME, 30.0),
            ("Deadlock Scenario",
             ThreadChaosProtocol.attack_deadlock_scenario,
             AttackVector.DEADLOCK,
             Severity.EXTREME, 20.0),
            ("Thread Starvation (50 heavy)",
             ThreadChaosProtocol.attack_thread_starvation,
             AttackVector.THREAD_STARVATION,
             Severity.HIGH, 40.0),
            ("Race Condition (1000 threads)",
             ThreadChaosProtocol.attack_race_condition_1000,
             AttackVector.RACE_CONDITION,
             Severity.EXTREME, 30.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.THREAD_CHAOS,
                vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P3: RESOURCE STARVATION
    # =========================================================================
    if ChaosProtocol.RESOURCE_STARVATION in protocols_to_run:
        banner("☠️  PROTOCOL 3: RESOURCE STARVATION", char="!")
        tests = [
            ("File Descriptor Exhaustion (500 files)",
             ResourceStarvationProtocol.attack_fd_exhaustion,
             AttackVector.FD_LEAK,
             Severity.EXTREME, 30.0),
            ("Temp File Bomb (200 files, 1MB each)",
             ResourceStarvationProtocol.attack_temp_file_bomb,
             AttackVector.RESOURCE_LEAK,
             Severity.HIGH, 30.0),
            ("Thread Pool Saturation",
             ResourceStarvationProtocol.attack_thread_pool_saturation,
             AttackVector.POOL_EXHAUSTION,
             Severity.EXTREME, 30.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.RESOURCE_STARVATION,
                vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P4: DATA POISONING
    # =========================================================================
    if ChaosProtocol.DATA_POISONING in protocols_to_run:
        banner("☠️  PROTOCOL 4: DATA POISONING", char="!")
        tests = [
            ("SQL Injection Attack",
             DataPoisoningProtocol.attack_sql_injection,
             AttackVector.SQL_INJECTION,
             Severity.EXTREME, 20.0),
            ("Unicode Bomb (20 payloads)",
             DataPoisoningProtocol.attack_unicode_bomb,
             AttackVector.UNICODE_BOMB,
             Severity.HIGH, 20.0),
            ("Null Byte Injection",
             DataPoisoningProtocol.attack_null_byte_injection,
             AttackVector.NULL_INJECTION,
             Severity.HIGH, 10.0),
            ("Malformed JSON",
             DataPoisoningProtocol.attack_malformed_json,
             AttackVector.DATA_CORRUPTION,
             Severity.MEDIUM, 10.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.DATA_POISONING,
                vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P5: CASCADE FAILURE
    # =========================================================================
    if ChaosProtocol.CASCADE_FAILURE in protocols_to_run:
        banner("☠️  PROTOCOL 5: CASCADE FAILURE", char="!")
        tests = [
            ("Timeout Cascade (50 concurrent)",
             CascadeFailureProtocol.attack_timeout_cascade,
             AttackVector.TIMING_ATTACK,
             Severity.EXTREME, 15.0),
            ("Exception Propagation",
             CascadeFailureProtocol.attack_exception_propagation,
             AttackVector.RACE_CONDITION,
             Severity.HIGH, 15.0),
            ("Dependency Chain",
             CascadeFailureProtocol.attack_dependency_chain,
             AttackVector.DATA_CORRUPTION,
             Severity.MEDIUM, 30.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.CASCADE_FAILURE,
                vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P6: ENTROPY ATTACK
    # =========================================================================
    if ChaosProtocol.ENTROPY_ATTACK in protocols_to_run:
        banner("☠️  PROTOCOL 6: ENTROPY ATTACK", char="!")
        tests = [
            ("Fuzzing Queries (100 random)",
             EntropyAttackProtocol.attack_fuzzing_queries,
             AttackVector.DATA_CORRUPTION,
             Severity.MEDIUM, 30.0),
            ("Extreme Numbers",
             EntropyAttackProtocol.attack_extreme_numbers,
             AttackVector.OVERFLOW,
             Severity.HIGH, 20.0),
            ("Random Payloads (50)",
             EntropyAttackProtocol.attack_random_payloads,
             AttackVector.UNICODE_BOMB,
             Severity.MEDIUM, 20.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.ENTROPY_ATTACK,
                vector, severity, timeout * quick_factor
            )

    # =========================================================================
    # P7: TIMING ATTACK
    # =========================================================================
    if ChaosProtocol.TIMING_ATTACK in protocols_to_run:
        banner("☠️  PROTOCOL 7: TIMING ATTACK", char="!")
        tests = [
            ("Burst Requests (1000 sequential)",
             TimingAttackProtocol.attack_burst_requests,
             AttackVector.TIMING_ATTACK,
             Severity.EXTREME, 60.0),
            ("Slowloris Attack",
             TimingAttackProtocol.attack_slowloris,
             AttackVector.POOL_EXHAUSTION,
             Severity.EXTREME, 20.0),
            ("Concurrent Burst (100 workers)",
             TimingAttackProtocol.attack_concurrent_burst,
             AttackVector.TIMING_ATTACK,
             Severity.EXTREME, 20.0),
        ]

        for name, func, vector, severity, timeout in tests:
            orchestrator.launch_attack(
                func, name, ChaosProtocol.TIMING_ATTACK,
                vector, severity, timeout * quick_factor
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
    # FINAL REPORT
    # =========================================================================
    print("\n\n")
    report = orchestrator.generate_hell_report()
    print(report)

    # Save reports
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_file = reports_dir / f"hell_report_{timestamp}.txt"
    report_file.write_text(report, encoding="utf-8")
    print(f"\n💾 Report saved: {report_file.relative_to(PROJECT_ROOT)}")

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
    json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print(f"💾 JSON saved: {json_file.relative_to(PROJECT_ROOT)}")

    # Exit code
    critical_kills = sum(
        1 for r in orchestrator.results
        if not r.passed and r.severity in [Severity.CATASTROPHIC, Severity.APOCALYPTIC]
    )

    print()
    if critical_kills > 5:
        print(f"💀 SYSTEM DESTROYED: {critical_kills} catastrophic failures")
        return 3
    elif orchestrator.assessment.kill_rate > 50:
        print(f"☠️  SYSTEM BROKEN: {orchestrator.assessment.kill_rate:.1f}% kill rate")
        return 2
    elif orchestrator.assessment.kill_rate > 20:
        print(f"⚠️  SYSTEM VULNERABLE: {orchestrator.assessment.kill_rate:.1f}% kill rate")
        return 1
    else:
        print(f"✅ SYSTEM HARDENED: {orchestrator.assessment.survival_rate:.1f}% survival rate")
        return 0


if __name__ == "__main__":
    sys.exit(main())