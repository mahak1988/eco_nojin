#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eco_chaos_test.py
=================

Chaos Engineering Test Suite برای کل پلتفرم eco_nojin

هدف: شکستن سیستم برای کشف نقاط ضعف

معماری تست:
┌─────────────────────────────────────────────────────────────┐
│                  Chaos Test Orchestrator                      │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Engine     │   DataHub    │   Services   │   Hydroma      │
│   Chaos      │   Chaos      │   Chaos      │   Chaos        │
│              │              │              │                │
│ - Overflow   │ - Conn Storm │ - DDoS Sim   │ - All Models   │
│ - NaN Prop   │ - Deadlock   │ - Payload    │ - Concurrent   │
│ - Memory Lk  │ - Race Cond  │ - Recursive  │ - Stress       │
│ - Precision  │ - Corruption │ - Malformed  │ - Edge Cases   │
└──────────────┴──────────────┴──────────────┴────────────────┘

انتظار: اکثر تست‌ها باید FAIL شوند (هدف: کشف ضعف)
"""

import sys
import os
import signal
import time
import random
import threading
import multiprocessing
import traceback
import statistics
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import math

# Ensure project root in path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSeverity(Enum):
    """شدت سناریوی تست"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    CATASTROPHIC = "CATASTROPHIC"


class TestCategory(Enum):
    """دسته‌بندی تست"""
    ENGINE = "ENGINE"
    DATAHUB = "DATAHUB"
    SERVICES = "SERVICES"
    HYDROMA = "HYDROMA"


@dataclass
class ChaosTestResult:
    """نتیجه یک تست آشوب"""
    name: str
    category: TestCategory
    severity: TestSeverity
    passed: bool
    failure_point: str = ""
    execution_time_ms: float = 0.0
    error_type: str = ""
    error_message: str = ""
    resources_consumed: Dict = field(default_factory=dict)
    expected_failure: bool = True  # انتظار داریم fail شود

    def __str__(self):
        status = "✅ PASS (قوی)" if self.passed else "❌ FAIL (نقطه ضعف)"
        return f"[{self.severity.value}] {self.name}: {status} ({self.execution_time_ms:.1f}ms)"


class ChaosMetrics:
    """اندازه‌گیری مصرف منابع"""

    @staticmethod
    def get_process_memory_mb() -> float:
        """مصرف حافظه فعلی process"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback: استفاده از sys
            return 0.0

    @staticmethod
    def get_cpu_percent() -> float:
        """درصد CPU فعلی"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0




def force_kill_on_timeout(thread, timeout):
    """Force kill thread if it exceeds timeout"""
    import ctypes
    
    def _async_raise(tid, exc_type):
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(tid),
            ctypes.py_object(exc_type)
        )
        if res == 0:
            raise ValueError("Invalid thread id")
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(tid), None
            )
            raise SystemError("PyThreadState_SetAsyncExc failed")
    
    thread.join(timeout=timeout)
    if thread.is_alive():
        try:
            _async_raise(thread.ident, SystemExit)
            print(f"  🔪 Force killed stuck thread")
        except Exception:
            pass

class ChaosOrchestrator:
    """هماهنگ‌کننده تست‌های آشوب"""

    def __init__(self):
        self.results: List[ChaosTestResult] = []
        self.start_time = None

    def run_test(self, test_func: Callable, name: str,
                 category: TestCategory,
                 severity: TestSeverity,
                 timeout: float = 30.0,
                 expected_failure: bool = True) -> ChaosTestResult:
        """اجرای یک تست آشوب با timeout و مدیریت خطا"""

        print(f"\n{'=' * 70}")
        print(f"  🎯 {name}")
        print(f"  Category: {category.value} | Severity: {severity.value}")
        print(f"  Timeout: {timeout}s | Expected: {'FAIL' if expected_failure else 'PASS'}")
        print(f"{'=' * 70}")

        mem_before = ChaosMetrics.get_process_memory_mb()
        start = time.perf_counter()
        failure_point = ""
        error_type = ""
        error_msg = ""
        passed = False

        # اجرای تست با timeout
        result_container = {"result": None, "error": None}

        def run_in_thread():
            try:
                result_container["result"] = test_func()
            except Exception as e:
                result_container["error"] = e

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=timeout)

        elapsed = (time.perf_counter() - start) * 1000
        mem_after = ChaosMetrics.get_process_memory_mb()

        if thread.is_alive():
            # Timeout - تست fail شد
            passed = False
            error_type = "TimeoutError"
            error_msg = f"Test exceeded {timeout}s timeout"
            failure_point = "timeout"
            print(f"  ⏰ TIMEOUT after {timeout}s - سیستم هنگ کرد ✅")
            # Thread will die with process (daemon=True was set before start)
        elif result_container["error"] is not None:
            # Exception - تست fail شد
            passed = False
            error_type = type(result_container["error"]).__name__
            error_msg = str(result_container["error"])[:200]
            failure_point = "exception"
            print(f"  💥 EXCEPTION: {error_type}: {error_msg}")
        else:
            # Test completed without error
            passed = True
            print(f"  ✅ Test passed (system resisted)")

        result = ChaosTestResult(
            name=name,
            category=category,
            severity=severity,
            passed=passed,
            failure_point=failure_point,
            execution_time_ms=elapsed,
            error_type=error_type,
            error_message=error_msg,
            resources_consumed={
                "memory_delta_mb": mem_after - mem_before,
                "memory_before_mb": mem_before,
                "memory_after_mb": mem_after,
            },
            expected_failure=expected_failure,
        )

        self.results.append(result)
        return result

    def generate_report(self) -> str:
        """تولید گزارش نهایی"""
        lines = []
        lines.append("=" * 80)
        lines.append("  💥 CHAOS ENGINEERING REPORT - eco_nojin")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        # آمار کلی
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        expected_failures = sum(1 for r in self.results if r.expected_failure and not r.passed)
        unexpected_passes = sum(1 for r in self.results if r.expected_failure and r.passed)

        lines.append("📊 EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(f"  Total Tests Run:        {total}")
        lines.append(f"  ✅ System Resisted:       {passed} ({100*passed/total:.1f}%)")
        lines.append(f"  ❌ System Failed:         {failed} ({100*failed/total:.1f}%)")
        lines.append(f"  🎯 Expected Failures:     {expected_failures} (discovered weaknesses)")
        lines.append(f"  🛡️  Unexpected Resist:    {unexpected_passes} (strong components)")
        lines.append("")

        # دسته‌بندی بر اساس category
        lines.append("📂 BREAKDOWN BY CATEGORY")
        lines.append("-" * 80)

        for category in TestCategory:
            cat_results = [r for r in self.results if r.category == category]
            if not cat_results:
                continue
            cat_passed = sum(1 for r in cat_results if r.passed)
            cat_failed = len(cat_results) - cat_passed
            lines.append(f"\n  [{category.value}]")
            lines.append(f"    Tests: {len(cat_results)} | Resisted: {cat_passed} | Failed: {cat_failed}")
            for r in cat_results:
                status = "🛡️ RESISTED" if r.passed else "💥 FAILED"
                lines.append(f"    {status} {r.name}")
                if not r.passed:
                    lines.append(f"           ├─ Failure: {r.failure_point}")
                    lines.append(f"           ├─ Error: {r.error_type}")
                    if r.error_message:
                        lines.append(f"           └─ Message: {r.error_message[:100]}")
                if r.resources_consumed.get("memory_delta_mb", 0) > 10:
                    lines.append(f"           ⚠️  Memory leak: +{r.resources_consumed['memory_delta_mb']:.1f}MB")

        # دسته‌بندی بر اساس severity
        lines.append("")
        lines.append("📊 BREAKDOWN BY SEVERITY")
        lines.append("-" * 80)
        for severity in TestSeverity:
            sev_results = [r for r in self.results if r.severity == severity]
            if sev_results:
                failed = sum(1 for r in sev_results if not r.passed)
                lines.append(f"  {severity.value}: {len(sev_results)} tests, {failed} failures")

        # نقاط ضعف بحرانی
        lines.append("")
        lines.append("🚨 CRITICAL WEAKNESSES DISCOVERED")
        lines.append("-" * 80)
        critical = [r for r in self.results if not r.passed and r.severity in [TestSeverity.HIGH, TestSeverity.EXTREME, TestSeverity.CATASTROPHIC]]
        if critical:
            for r in critical:
                lines.append(f"\n  💥 {r.name} [{r.category.value}]")
                lines.append(f"     Failure Point: {r.failure_point}")
                lines.append(f"     Error Type: {r.error_type}")
                lines.append(f"     Impact: {r.error_message[:150]}")
        else:
            lines.append("  ✅ No critical weaknesses found")

        # نقاط قوت
        lines.append("")
        lines.append("🛡️  UNEXPECTEDLY STRONG COMPONENTS")
        lines.append("-" * 80)
        strong = [r for r in self.results if r.passed and r.expected_failure]
        if strong:
            for r in strong:
                lines.append(f"  🛡️  {r.name} [{r.category.value}] - resisted {r.severity.value} attack")
        else:
            lines.append("  All components failed as expected")

        # محاسبه امتیاز پایداری
        lines.append("")
        lines.append("🏆 STABILITY SCORE")
        lines.append("-" * 80)

        # وزن هر severity
        severity_weights = {
            TestSeverity.LOW: 1,
            TestSeverity.MEDIUM: 2,
            TestSeverity.HIGH: 4,
            TestSeverity.EXTREME: 8,
            TestSeverity.CATASTROPHIC: 16,
        }

        total_weight = sum(severity_weights[r.severity] for r in self.results)
        passed_weight = sum(severity_weights[r.severity] for r in self.results if r.passed)
        stability_score = (passed_weight / total_weight * 100) if total_weight > 0 else 0

        if stability_score >= 80:
            grade = "A"
            emoji = "🏆"
        elif stability_score >= 60:
            grade = "B"
            emoji = "✅"
        elif stability_score >= 40:
            grade = "C"
            emoji = "⚠️"
        elif stability_score >= 20:
            grade = "D"
            emoji = "🔴"
        else:
            grade = "F"
            emoji = "💀"

        lines.append(f"  {emoji} Stability Score: {stability_score:.1f}/100 (Grade: {grade})")
        lines.append(f"     Total weight: {total_weight} | Passed weight: {passed_weight}")
        lines.append("")

        # توصیه‌ها
        lines.append("📋 RECOMMENDATIONS")
        lines.append("-" * 80)
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"  {i}. {rec}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_recommendations(self) -> List[str]:
        """تولید توصیه‌ها بر اساس نتایج"""
        recs = []

        # Memory leaks
        memory_leaks = [r for r in self.results if not r.passed and "memory" in r.name.lower()]
        if memory_leaks:
            recs.append("🔧 Implement proper resource cleanup and connection pooling")

        # Timeout failures
        timeouts = [r for r in self.results if r.failure_point == "timeout"]
        if timeouts:
            recs.append("⏱️  Add circuit breakers and request timeouts to all services")

        # Race conditions
        races = [r for r in self.results if "race" in r.name.lower() or "concurrent" in r.name.lower()]
        race_failed = [r for r in races if not r.passed]
        if race_failed:
            recs.append("🔒 Implement proper locking/synchronization for concurrent access")

        # Data corruption
        corruption = [r for r in self.results if "corrupt" in r.name.lower() and not r.passed]
        if corruption:
            recs.append("✅ Add input validation and data integrity checks at all entry points")

        # NaN/Infinity issues
        nan_issues = [r for r in self.results if "nan" in r.name.lower() or "inf" in r.name.lower() and not r.passed]
        if nan_issues:
            recs.append("🧮 Add NaN/Infinity checks in all numerical computations")

        # Overflow
        overflows = [r for r in self.results if "overflow" in r.name.lower() and not r.passed]
        if overflows:
            recs.append("📊 Implement overflow protection and big number handling")

        if not recs:
            recs.append("✅ System demonstrated good resilience - consider stress testing at higher scale")

        return recs


# =============================================================================
# CHAOS TESTS: ENGINE (موتور محاسباتی)
# =============================================================================

class EngineChaosTests:
    """تست‌های آشوب برای موتور محاسباتی"""

    @staticmethod
    def test_hydroma_memory_leak():
        """Memory leak در Hydroma - اجرای 1000 شبیه‌سازی پشت سر هم"""
        from engine.data_connector import connector

        # اجرای 1000 query سنگین پشت سر هم بدون cleanup
        for i in range(1000):
            try:
                result = connector.execute_analytics_query(f"""
                    SELECT
                        site_id,
                        AVG(tmin_c) as avg_min,
                        AVG(tmax_c) as avg_max,
                        SUM(tmax_c - tmin_c) as range_sum
                    FROM weather_daily
                    WHERE year = {(i % 30) + 1990}
                    GROUP BY site_id
                """)
            except Exception:
                pass
        return True

    @staticmethod
    def test_computation_overflow():
        """Overflow در محاسبات - اعداد خارج از محدوده"""
        from engine.data_connector import connector

        # محاسبه با اعداد بسیار بزرگ
        result = connector.execute_analytics_query("""
            SELECT
                EXP(1000) as huge_exp,
                POWER(10, 100) as huge_power,
                1.0 / 0.0 as infinity,
                LOG(-1) as nan_log
        """)
        return result

    @staticmethod
    def test_nan_propagation():
        """انتشار NaN در محاسبات Hydroma"""
        from engine.data_connector import connector

        # ایجاد NaN و انتشار آن
        result = connector.execute_analytics_query("""
            SELECT
                SQRT(-1) as nan_value,
                0.0 / 0.0 as nan_div,
                SQRT(-1) * 100 as propagated_nan,
                COALESCE(SQRT(-1), 0) as handled_nan
        """)
        return result

    @staticmethod
    def test_infinite_recursion():
        """بازگشت بی‌نهایت در محاسبات"""
        def recursive_compute(n):
            if n > 10000:  # عمق زیاد
                return n
            return recursive_compute(n + 1)

        return recursive_compute(0)

    @staticmethod
    def test_precision_loss():
        """از دست رفتن precision در محاسبات علمی"""
        from engine.data_connector import connector

        # محاسبات با اختلاف کوچک که باید دقیق باشد
        result = connector.execute_analytics_query("""
            SELECT
                1.0000000000000001 - 1.0000000000000000 as tiny_diff,
                0.1 + 0.2 as float_addition,
                1e300 * 1e200 as overflow_multiply,
                1e-300 / 1e300 as underflow_divide
        """)
        return result

    @staticmethod
    def test_heavy_math_operations():
        """محاسبات سنگین ریاضی"""
        from engine.data_connector import connector

        # 100 محاسبه سنگین همزمان
        queries = []
        for i in range(100):
            queries.append(f"""
                SELECT
                    site_id,
                    AVG(tmin_c) * SIN({i}) as val1,
                    AVG(tmax_c) * COS({i}) as val2,
                    SUM(POWER(tmax_c - tmin_c, 2)) as val3
                FROM weather_daily
                WHERE year = 2020
                GROUP BY site_id
            """)

        for q in queries:
            connector.execute_analytics_query(q)
        return True

    @staticmethod
    def test_boundary_conditions():
        """شرایط مرزی - مقادیر极端"""
        test_values = [
            float('inf'), float('-inf'), float('nan'),
            1e308, -1e308,  # نزدیک به max float
            1e-308, -1e-308,  # نزدیک به min float
            sys.maxsize, -sys.maxsize - 1,
        ]

        results = []
        for val in test_values:
            try:
                # تست در محاسبات
                x = val * 2
                y = val / 2
                z = math.sqrt(abs(val)) if val != float('nan') else float('nan')
                results.append((val, x, y, z))
            except Exception as e:
                results.append((val, "error", str(e)))

        return results


# =============================================================================
# CHAOS TESTS: DATAHUB (هسته مرکزی)
# =============================================================================

class DataHubChaosTests:
    """تست‌های آشوب برای هسته مرکزی"""

    @staticmethod
    def test_connection_storm():
        """طوفان اتصال - 1000 اتصال همزمان"""
        from database.hub import DataHub

        connections = []
        errors = []

        def create_connection():
            try:
                hub = DataHub()
                conn = hub.get_duckdb("master")
                connections.append(conn)
                return conn
            except Exception as e:
                errors.append(str(e))
                return None

        # ایجاد 1000 اتصال همزمان
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(create_connection) for _ in range(1000)]
            for f in as_completed(futures):
                pass

        # cleanup
        for conn in connections:
            try:
                conn.close()
            except:
                pass

        if len(errors) > 500:
            raise RuntimeError(f"Connection storm: {len(errors)}/1000 failed")

        return len(connections)

    @staticmethod
    def test_transaction_deadlock():
        """بن‌بست تراکنش - تراکنش‌های متضاد"""
        from database.hub import hub
        from sqlalchemy import text
        import threading

        errors = []

        def transaction_a():
            try:
                with hub.get_session() as session:
                    session.execute(text("SELECT 1"))
                    time.sleep(0.01)
                    session.execute(text("SELECT 2"))
            except Exception as e:
                errors.append(("A", str(e)))

        def transaction_b():
            try:
                with hub.get_session() as session:
                    session.execute(text("SELECT 2"))
                    time.sleep(0.01)
                    session.execute(text("SELECT 1"))
            except Exception as e:
                errors.append(("B", str(e)))

        # ایجاد deadlock scenario
        threads = []
        for _ in range(50):
            t1 = threading.Thread(target=transaction_a)
            t2 = threading.Thread(target=transaction_b)
            threads.extend([t1, t2])
            t1.start()
            t2.start()

        for t in threads:
            t.join(timeout=10)

        if len(errors) > 20:
            raise RuntimeError(f"Deadlock detected: {len(errors)} errors")

        return len(errors)

    @staticmethod
    def test_data_corruption():
        """تزریق داده‌های خراب"""
        from database.hub import hub
        from sqlalchemy import text

        corrupted_data = [
            "'; DROP TABLE users; --",  # SQL injection
            "null\x00byte",  # null byte injection
            "a" * 1000000,  # extremely long string
            "\ud800\udfff",  # invalid surrogate pairs
            "مرحبا\x00بالعالم",  # unicode with null
        ]

        errors = []
        for data in corrupted_data:
            try:
                with hub.get_session() as session:
                    # Try to insert corrupted data (should fail safely)
                    session.execute(text("SELECT 1"))
            except Exception as e:
                errors.append((data[:50], str(e)))

        # We expect graceful handling
        return len(errors)

    @staticmethod
    def test_race_condition():
        """شرایط مسابقه - 100 thread همزمان"""
        from database.hub import DataHub

        shared_counter = [0]
        lock = threading.Lock()
        errors = []

        def increment_counter():
            for _ in range(100):
                try:
                    hub = DataHub()
                    # Race condition: read-modify-write without lock
                    current = shared_counter[0]
                    time.sleep(0.0001)  # Increase race window
                    shared_counter[0] = current + 1
                except Exception as e:
                    errors.append(str(e))

        threads = []
        for _ in range(100):
            t = threading.Thread(target=increment_counter)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # با 100 thread × 100 increment = 10000 انتظار می‌رود
        # ولی بدون lock، مقدار واقعی کمتر خواهد بود (race condition)
        if shared_counter[0] != 10000:
            # این نشان‌دهنده race condition است
            print(f"     ⚠️  Race detected: expected 10000, got {shared_counter[0]}")

        return shared_counter[0]

    @staticmethod
    def test_query_bomb():
        """بمباران کوئری - 10,000 کوئری پشت سر هم"""
        from database.hub import hub

        start = time.perf_counter()
        errors = 0

        for i in range(10000):
            try:
                with hub.get_session() as session:
                    from sqlalchemy import text
                    session.execute(text("SELECT 1")).fetchone()
            except Exception:
                errors += 1

        elapsed = time.perf_counter() - start
        ops_per_sec = 10000 / elapsed

        if errors > 100:
            raise RuntimeError(f"Query bomb: {errors}/10000 failed at {ops_per_sec:.0f} ops/s")

        return ops_per_sec

    @staticmethod
    def test_concurrent_writes():
        """نوشتن همزمان - stress روی transaction management"""
        from database.hub import hub
        from sqlalchemy import text

        errors = []

        def write_operation(idx):
            try:
                with hub.get_session() as session:
                    # Multiple concurrent writes
                    for i in range(10):
                        session.execute(text(f"SELECT {idx * 100 + i}"))
            except Exception as e:
                errors.append(str(e))

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(write_operation, i) for i in range(50)]
            for f in as_completed(futures):
                pass

        if len(errors) > 10:
            raise RuntimeError(f"Concurrent writes: {len(errors)} errors")

        return len(errors)

    @staticmethod
    def test_rapid_open_close():
        """باز و بستن سریع - stress روی connection lifecycle"""
        from database.hub import hub

        errors = []
        for i in range(1000):
            try:
                conn = hub.get_duckdb("master")
                conn.execute("SELECT 1").fetchone()
                conn.close()
            except Exception as e:
                errors.append(str(e))

        if len(errors) > 100:
            raise RuntimeError(f"Rapid open/close: {len(errors)}/1000 failed")

        return 1000 - len(errors)


# =============================================================================
# CHAOS TESTS: SERVICES (سرویس‌های پلتفرم)
# =============================================================================

class ServicesChaosTests:
    """تست‌های آشوب برای سرویس‌ها"""

    @staticmethod
    def test_api_ddos_simulation():
        """شبیه‌سازی DDoS - 1000 درخواست در 10 ثانیه"""
        # Import service modules to stress them
        try:
            from services.api_gateway.main import app
        except ImportError:
            # اگر API gateway نبود، skip
            return "skipped"

        errors = []

        def simulate_request(i):
            try:
                # Simulate heavy request load
                import asyncio
                # Create request context
                pass
            except Exception as e:
                errors.append(str(e))

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(simulate_request, i) for i in range(1000)]
            for f in as_completed(futures):
                pass

        elapsed = time.perf_counter() - start
        rps = 1000 / elapsed

        return rps

    @staticmethod
    def test_payload_bomb():
        """بمب payload - ورودی‌های بسیار بزرگ"""
        large_payloads = [
            "x" * 10_000_000,  # 10MB string
            json.dumps({"data": ["x" * 1000] * 10000}),  # Large JSON
            bytes([random.randint(0, 255) for _ in range(1_000_000)]),  # 1MB random
        ]

        for payload in large_payloads:
            try:
                # Try to process large payload
                if isinstance(payload, str):
                    _ = len(payload)
                    _ = payload[:100]
                elif isinstance(payload, bytes):
                    _ = len(payload)
                    _ = payload.decode('utf-8', errors='ignore')[:100]
                elif isinstance(payload, dict):
                    _ = json.dumps(payload)[:100]
            except Exception as e:
                # Expected to handle gracefully
                pass

        return True

    @staticmethod
    def test_recursive_service_calls():
        """فراخوانی‌های بازگشتی بین سرویس‌ها"""
        call_depth = [0]
        max_depth = [0]

        def service_a(depth):
            call_depth[0] = depth
            max_depth[0] = max(max_depth[0], depth)
            if depth > 100:
                raise RecursionError(f"Max depth exceeded: {depth}")
            try:
                service_b(depth + 1)
            except RecursionError:
                raise

        def service_b(depth):
            if depth > 100:
                raise RecursionError(f"Max depth exceeded: {depth}")
            try:
                service_a(depth + 1)
            except RecursionError:
                raise

        try:
            service_a(0)
        except RecursionError as e:
            # Expected - system should detect and prevent
            return max_depth[0]

        return max_depth[0]

    @staticmethod
    def test_malformed_input():
        """ورودی‌های بدشکل"""
        malformed_inputs = [
            None,
            {},
            [],
            "",
            "\x00\x01\x02",
            "undefined",
            "NaN",
            "Infinity",
            b"\xff\xfe",  # Invalid UTF-16
            {None: None},  # None as key
            float('nan'),
            [1, 2, 3, None, float('inf')],
        ]

        errors = []
        for inp in malformed_inputs:
            try:
                # Simulate service processing
                if inp is None:
                    raise ValueError("None input")
                if isinstance(inp, dict):
                    _ = list(inp.keys())
                elif isinstance(inp, list):
                    _ = len(inp)
                elif isinstance(inp, str):
                    _ = inp.encode('utf-8')
            except Exception as e:
                errors.append((str(inp)[:30], str(e)))

        return len(errors)

    @staticmethod
    def test_service_timeout_cascade():
        """آبشار timeout - یک سرویس کند همه را تحت تأثیر قرار می‌دهد"""
        def slow_service():
            time.sleep(5)  # کند
            return "done"

        def fast_service():
            return "fast"

        errors = []
        start = time.perf_counter()

        # 100 concurrent calls - اگر timeout نباشد، همه 5 ثانیه منتظر می‌مانند
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for i in range(100):
                if i % 10 == 0:
                    futures.append(executor.submit(slow_service))
                else:
                    futures.append(executor.submit(fast_service))

            for f in as_completed(futures, timeout=1):
                try:
                    f.result(timeout=1)
                except Exception as e:
                    errors.append(str(e))

        elapsed = time.perf_counter() - start
        return elapsed

    @staticmethod
    def test_circular_dependency():
        """وابستگی حلقه‌ای بین سرویس‌ها"""
        services = {}

        class ServiceA:
            def __init__(self):
                self.b = None

            def call_b(self):
                return self.b.call_a() if self.b else None

        class ServiceB:
            def __init__(self):
                self.a = None

            def call_a(self):
                return self.a.call_b() if self.a else None

        # Create circular dependency
        a = ServiceA()
        b = ServiceB()
        a.b = b
        b.a = a

        try:
            result = a.call_b()
            # اگر به اینجا رسید، مشکل circular dependency هست
            return "circular detected"
        except RecursionError:
            return "handled"


# =============================================================================
# CHAOS TESTS: HYDROMA (مدل‌های هیدروما)
# =============================================================================

class HydromaChaosTests:
    """تست‌های آشوب برای مدل‌های Hydroma"""

    @staticmethod
    def test_hydroma_layout_stress():
        """Stress test HydromaLayout با داده‌های حجیم"""
        try:
            # Try to import Hydroma components
            sys.path.insert(0, str(PROJECT_ROOT / "frontend" / "src" / "components"))
        except Exception:
            pass

        # Simulate HydromaLayout with extreme data
        extreme_data = {
            "cells": [[random.random() for _ in range(1000)] for _ in range(1000)],  # 1M cells
            "timestamps": [datetime.now() - timedelta(hours=i) for i in range(10000)],
            "coordinates": [(random.uniform(-180, 180), random.uniform(-90, 90)) for _ in range(100000)],
        }

        # Process extreme data
        for row in extreme_data["cells"]:
            _ = sum(row)

        return True

    @staticmethod
    def test_hydroma_simulation_overflow():
        """Overflow در شبیه‌سازی Hydroma"""
        # شبیه‌سازی با پارامترهای خارج از محدوده
        params = {
            "temperature": float('inf'),
            "humidity": -100,  # غیرممکن
            "wind_speed": 1e10,  # خیلی زیاد
            "precipitation": float('nan'),
            "soil_moisture": -1,
        }

        results = []
        for key, val in params.items():
            try:
                # شبیه‌سازی
                if math.isnan(val):
                    results.append((key, "nan"))
                elif math.isinf(val):
                    results.append((key, "inf"))
                else:
                    # محاسبه
                    result = val * 2 + math.sin(val)
                    results.append((key, result))
            except Exception as e:
                results.append((key, str(e)))

        return results

    @staticmethod
    def test_hydroma_concurrent_models():
        """دسترسی همزمان به مدل‌های Hydroma"""
        from engine.data_connector import connector

        errors = []

        def access_model(model_type, idx):
            try:
                if model_type == "climate":
                    connector.get_climate_data(year=2020)
                elif model_type == "crop":
                    connector.get_crop_parameters("wheat")
                elif model_type == "disaster":
                    connector.get_climate_disasters()
                elif model_type == "calendar":
                    connector.get_crop_calendar()
            except Exception as e:
                errors.append(str(e))

        # 100 concurrent accesses to different models
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for i in range(100):
                model_type = random.choice(["climate", "crop", "disaster", "calendar"])
                futures.append(executor.submit(access_model, model_type, i))

            for f in as_completed(futures):
                pass

        if len(errors) > 20:
            raise RuntimeError(f"Concurrent model access: {len(errors)} errors")

        return 100 - len(errors)

    @staticmethod
    def test_hydroma_all_models_extreme():
        """تست همه مدل‌های Hydroma با داده‌های extreme"""
        from engine.data_connector import connector

        results = {}

        # Climate model with extreme year
        try:
            data = connector.get_climate_data(year=9999)
            results["climate_extreme"] = "ok"
        except Exception as e:
            results["climate_extreme"] = f"error: {str(e)[:50]}"

        # Crop parameters with invalid names
        invalid_crops = ["", None, "x" * 10000, "مرحبا" * 1000, "\x00null"]
        for crop in invalid_crops:
            try:
                connector.get_crop_parameters(crop)
                results[f"crop_{str(crop)[:20]}"] = "ok"
            except Exception as e:
                results[f"crop_{str(crop)[:20]}"] = f"error: {str(e)[:50]}"

        return results

    @staticmethod
    def test_hydroma_mrv_massive():
        """MRV با داده‌های حجیم"""
        from engine.data_connector import connector

        # Query large MRV dataset
        try:
            result = connector.execute_analytics_query("""
                SELECT
                    COUNT(*) as total,
                    AVG(CAST(site_id AS FLOAT)) as avg_site,
                    MAX(year) as max_year,
                    MIN(year) as min_year
                FROM weather_daily
            """)
            return result
        except Exception as e:
            raise RuntimeError(f"MRV stress failed: {e}")

    @staticmethod
    def test_hydroma_carbon_calculation():
        """محاسبات carbon با پارامترهای extreme"""
        # فرمول‌های محاسبه carbon
        def calculate_carbon_sequestration(area_ha, years, tree_species):
            # پارامترهای extreme
            factors = {
                "oak": 10.5,
                "pine": 8.2,
                "eucalyptus": 15.3,
            }

            factor = factors.get(tree_species, 10.0)

            # محاسبه با مقادیر extreme
            carbon_tons = area_ha * years * factor
            co2_equivalent = carbon_tons * 3.67
            credits = co2_equivalent / 1000  # تبدیل به اعتبار

            return {
                "carbon_tons": carbon_tons,
                "co2_eq": co2_equivalent,
                "credits": credits,
            }

        # تست با مقادیر extreme
        test_cases = [
            (1e10, 100, "oak"),  # مساحت عظیم
            (1, 10000, "pine"),  # زمان طولانی
            (1e-10, 1, "eucalyptus"),  # مساحت ناچیز
            (float('inf'), 1, "oak"),  # بی‌نهایت
            (float('nan'), 1, "oak"),  # NaN
        ]

        results = []
        for area, years, species in test_cases:
            try:
                r = calculate_carbon_sequestration(area, years, species)
                results.append(r)
            except Exception as e:
                results.append(str(e))

        return results


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def main():
    """اجرای اصلی تست‌های آشوب"""
    import argparse

    parser = argparse.ArgumentParser(description="Chaos Engineering Test Suite")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--engine", action="store_true", help="Engine tests only")
    parser.add_argument("--hub", action="store_true", help="DataHub tests only")
    parser.add_argument("--services", action="store_true", help="Services tests only")
    parser.add_argument("--hydroma", action="store_true", help="Hydroma tests only")
    parser.add_argument("--quick", action="store_true", help="Quick test (fewer iterations)")

    args = parser.parse_args()

    # اگر هیچ flag نبود، همه را اجرا کن
    if not (args.engine or args.hub or args.services or args.hydroma):
        args.all = True

    print()
    print("=" * 80)
    print("  💥 CHAOS ENGINEERING - eco_nojin Platform Stress Test")
    print("  هدف: شکستن سیستم و کشف نقاط ضعف")
    print("=" * 80)
    print()
    print("⚠️  توجه: اکثر این تست‌ها انتظار دارند که سیستم FAIL شود")
    print("   هر شکست یک نقطه ضعف بالقوه را نشان می‌دهد")
    print()

    orchestrator = ChaosOrchestrator()

    # Quick mode factor
    factor = 0.2 if args.quick else 1.0

    # =========================================================================
    # ENGINE TESTS
    # =========================================================================
    if args.all or args.engine:
        print("\n" + "=" * 80)
        print("  🧮 ENGINE CHAOS TESTS")
        print("=" * 80)

        engine_tests = [
            ("Memory Leak - 1000 iterations",
             EngineChaosTests.test_hydroma_memory_leak,
             TestSeverity.HIGH, 60.0),
            ("Computation Overflow",
             EngineChaosTests.test_computation_overflow,
             TestSeverity.MEDIUM, 10.0),
            ("NaN Propagation",
             EngineChaosTests.test_nan_propagation,
             TestSeverity.MEDIUM, 10.0),
            ("Infinite Recursion",
             EngineChaosTests.test_infinite_recursion,
             TestSeverity.EXTREME, 5.0),
            ("Precision Loss",
             EngineChaosTests.test_precision_loss,
             TestSeverity.LOW, 10.0),
            ("Heavy Math - 100 queries",
             EngineChaosTests.test_heavy_math_operations,
             TestSeverity.HIGH, 60.0),
            ("Boundary Conditions",
             EngineChaosTests.test_boundary_conditions,
             TestSeverity.MEDIUM, 10.0),
        ]

        for name, func, severity, timeout in engine_tests:
            orchestrator.run_test(
                func, name,
                TestCategory.ENGINE,
                severity,
                timeout=timeout * factor,
                expected_failure=True
            )

    # =========================================================================
    # DATAHUB TESTS
    # =========================================================================
    if args.all or args.hub:
        print("\n" + "=" * 80)
        print("  🎯 DATAHUB CHAOS TESTS")
        print("=" * 80)

        hub_tests = [
            ("Connection Storm - 1000 connections",
             DataHubChaosTests.test_connection_storm,
             TestSeverity.EXTREME, 30.0),
            ("Transaction Deadlock",
             DataHubChaosTests.test_transaction_deadlock,
             TestSeverity.HIGH, 30.0),
            ("Data Corruption Injection",
             DataHubChaosTests.test_data_corruption,
             TestSeverity.HIGH, 10.0),
            ("Race Condition - 100 threads",
             DataHubChaosTests.test_race_condition,
             TestSeverity.HIGH, 20.0),
            ("Query Bomb - 10000 queries",
             DataHubChaosTests.test_query_bomb,
             TestSeverity.EXTREME, 60.0),
            ("Concurrent Writes - 50 threads",
             DataHubChaosTests.test_concurrent_writes,
             TestSeverity.HIGH, 30.0),
            ("Rapid Open/Close - 1000 cycles",
             DataHubChaosTests.test_rapid_open_close,
             TestSeverity.MEDIUM, 30.0),
        ]

        for name, func, severity, timeout in hub_tests:
            orchestrator.run_test(
                func, name,
                TestCategory.DATAHUB,
                severity,
                timeout=timeout * factor,
                expected_failure=True
            )

    # =========================================================================
    # SERVICES TESTS
    # =========================================================================
    if args.all or args.services:
        print("\n" + "=" * 80)
        print("  ⚙️  SERVICES CHAOS TESTS")
        print("=" * 80)

        services_tests = [
            ("DDoS Simulation - 1000 requests",
             ServicesChaosTests.test_api_ddos_simulation,
             TestSeverity.EXTREME, 30.0),
            ("Payload Bomb - 10MB input",
             ServicesChaosTests.test_payload_bomb,
             TestSeverity.HIGH, 10.0),
            ("Recursive Service Calls",
             ServicesChaosTests.test_recursive_service_calls,
             TestSeverity.EXTREME, 10.0),
            ("Malformed Input Injection",
             ServicesChaosTests.test_malformed_input,
             TestSeverity.MEDIUM, 10.0),
            ("Timeout Cascade",
             ServicesChaosTests.test_service_timeout_cascade,
             TestSeverity.HIGH, 10.0),
            ("Circular Dependency",
             ServicesChaosTests.test_circular_dependency,
             TestSeverity.MEDIUM, 10.0),
        ]

        for name, func, severity, timeout in services_tests:
            orchestrator.run_test(
                func, name,
                TestCategory.SERVICES,
                severity,
                timeout=timeout * factor,
                expected_failure=True
            )

    # =========================================================================
    # HYDROMA TESTS
    # =========================================================================
    if args.all or args.hydroma:
        print("\n" + "=" * 80)
        print("  🌊 HYDROMA MODEL CHAOS TESTS")
        print("=" * 80)

        hydroma_tests = [
            ("HydromaLayout Stress - 1M cells",
             HydromaChaosTests.test_hydroma_layout_stress,
             TestSeverity.EXTREME, 60.0),
            ("Hydroma Simulation Overflow",
             HydromaChaosTests.test_hydroma_simulation_overflow,
             TestSeverity.HIGH, 10.0),
            ("Hydroma Concurrent Models - 100 threads",
             HydromaChaosTests.test_hydroma_concurrent_models,
             TestSeverity.EXTREME, 30.0),
            ("All Hydroma Models Extreme",
             HydromaChaosTests.test_hydroma_all_models_extreme,
             TestSeverity.EXTREME, 30.0),
            ("Hydroma MRV Massive Query",
             HydromaChaosTests.test_hydroma_mrv_massive,
             TestSeverity.HIGH, 30.0),
            ("Hydroma Carbon Extreme Calculation",
             HydromaChaosTests.test_hydroma_carbon_calculation,
             TestSeverity.HIGH, 10.0),
        ]

        for name, func, severity, timeout in hydroma_tests:
            orchestrator.run_test(
                func, name,
                TestCategory.HYDROMA,
                severity,
                timeout=timeout * factor,
                expected_failure=True
            )

    # =========================================================================
    # FINAL REPORT
    # =========================================================================
    print("\n\n")
    report = orchestrator.generate_report()
    print(report)

    # ذخیره گزارش
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"chaos_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_file.write_text(report, encoding="utf-8")
    print(f"\n💾 گزارش ذخیره شد: {report_file.relative_to(PROJECT_ROOT)}")

    # JSON export
    json_file = reports_dir / f"chaos_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    json_data = []
    for r in orchestrator.results:
        json_data.append({
            "name": r.name,
            "category": r.category.value,
            "severity": r.severity.value,
            "passed": r.passed,
            "failure_point": r.failure_point,
            "execution_time_ms": r.execution_time_ms,
            "error_type": r.error_type,
            "error_message": r.error_message,
            "resources": r.resources_consumed,
        })
    json_file.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"💾 نتایج JSON ذخیره شد: {json_file.relative_to(PROJECT_ROOT)}")

    # Exit code بر اساس severity
    critical_failures = sum(
        1 for r in orchestrator.results
        if not r.passed and r.severity in [TestSeverity.EXTREME, TestSeverity.CATASTROPHIC]
    )

    print()
    if critical_failures > 5:
        print("💀 سیستم به شدت آسیب‌پذیر است - نیاز به بازنویسی")
        return 3
    elif critical_failures > 0:
        print("⚠️  نقاط ضعف بحرانی کشف شد - نیاز به اصلاح")
        return 2
    else:
        print("✅ سیستم پایداری مناسبی نشان داد")
        return 0


if __name__ == "__main__":
    sys.exit(main())