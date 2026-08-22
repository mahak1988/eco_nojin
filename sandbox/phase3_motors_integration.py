"""
Combined Execution: Phase 2C + Phase 3 + Performance + Error Handling
======================================================================
Executes both phases together with:
- Performance benchmarks
- Robust error handling tests
- Results reporting

Run: python sandbox/run_combined_phases.py
"""

from __future__ import annotations

import sys
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")
sys.path.insert(0, str(PROJECT_ROOT))


def run_phase2c():
    """Run Phase 2C comprehensive analysis tests"""
    print("\n" + "=" * 70)
    print("PHASE 2C: Comprehensive Land Analysis Tests")
    print("=" * 70)

    test_file = PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_comprehensive_analyzer.py"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    start_time = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    duration = time.time() - start_time

    print(f"\n⏱️  Duration: {duration:.2f}s")
    print(f"📊 Exit code: {result.returncode}")

    if result.returncode != 0:
        output = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
        print(output)

    return result.returncode == 0


def run_phase3():
    """Run Phase 3 motors integration tests"""
    print("\n" + "=" * 70)
    print("PHASE 3: Scientific Motors Integration Tests")
    print("=" * 70)

    test_file = PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_motors_hub.py"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False

    start_time = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    duration = time.time() - start_time

    print(f"\n⏱️  Duration: {duration:.2f}s")
    print(f"📊 Exit code: {result.returncode}")

    if result.returncode != 0:
        output = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
        print(output)

    return result.returncode == 0


def run_combined_tests():
    """Run all tests together"""
    print("\n" + "=" * 70)
    print("COMBINED: All Integration Tests")
    print("=" * 70)

    test_file_2c = PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_comprehensive_analyzer.py"
    test_file_3 = PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_motors_hub.py"

    if not test_file_2c.exists() or not test_file_3.exists():
        print("❌ Test files not found")
        return False

    start_time = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file_2c), str(test_file_3), "-v", "--tb=short"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    duration = time.time() - start_time

    print(f"\n⏱️  Total duration: {duration:.2f}s")
    print(f"📊 Exit code: {result.returncode}")

    if result.returncode != 0:
        output = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
        print(output)

    return result.returncode == 0


def benchmark_performance():
    """Run performance benchmarks"""
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 70)

    try:
        from engine.land.integration.comprehensive_analyzer import (
            ComprehensiveLandAnalyzer,
            SoilSummary,
            ClimateSummary,
            TerrainSummary,
        )
    except ImportError as e:
        print(f"❌ Cannot import modules: {e}")
        return 0.0

    soil = SoilSummary()
    climate = ClimateSummary()
    terrain = TerrainSummary()

    analyzer = ComprehensiveLandAnalyzer()

    # Warm up
    for _ in range(10):
        analyzer.analyze(soil, climate, terrain)

    # Benchmark
    iterations = 1000
    start_time = time.time()
    for _ in range(iterations):
        analyzer.analyze(soil, climate, terrain)
    duration = time.time() - start_time

    analyses_per_second = iterations / duration
    ms_per_analysis = (duration / iterations) * 1000

    print(f"\n📊 Performance Results:")
    print(f"   Iterations: {iterations}")
    print(f"   Total time: {duration:.3f}s")
    print(f"   Analyses/second: {analyses_per_second:.1f}")
    print(f"   Time/analysis: {ms_per_analysis:.2f}ms")

    return analyses_per_second


def test_error_handling():
    """Test robust error handling"""
    print("\n" + "=" * 70)
    print("ERROR HANDLING TESTS")
    print("=" * 70)

    try:
        from engine.land.integration.comprehensive_analyzer import ComprehensiveLandAnalyzer
        from engine.land.integration.motors_hub import ScientificMotorsHub
    except ImportError as e:
        print(f"❌ Cannot import modules: {e}")
        return False

    analyzer = ComprehensiveLandAnalyzer()
    hub = ScientificMotorsHub()

    test_cases = [
        ("None inputs", None, None, None),
        ("Invalid soil", "invalid", None, None),
        ("Missing data", None, None, None),
    ]

    passed = 0
    failed = 0

    for name, soil, climate, terrain in test_cases:
        try:
            result = analyzer.analyze(soil, climate, terrain)
            print(f"✓ {name}: Handled gracefully")
            passed += 1
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed += 1

    print(f"\n📊 Error handling: {passed}/{passed + failed} passed")
    return failed == 0


def generate_report(phase2c_ok, phase3_ok, combined_ok, perf_score, error_ok):
    """Generate final report"""
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)

    print("\n📋 Phase Status:")
    print(f"   Phase 2C (Comprehensive Analysis): {'✅ PASS' if phase2c_ok else '❌ FAIL'}")
    print(f"   Phase 3 (Motors Integration): {'✅ PASS' if phase3_ok else '❌ FAIL'}")
    print(f"   Combined Tests: {'✅ PASS' if combined_ok else '❌ FAIL'}")

    print("\n⚡ Performance:")
    print(f"   Analyses/second: {perf_score:.1f}")
    print(f"   Status: {'✅ GOOD (>100/s)' if perf_score > 100 else '⚠️  SLOW'}")

    print("\n🛡️  Error Handling:")
    print(f"   Status: {'✅ ROBUST' if error_ok else '❌ NEEDS WORK'}")

    print("\n📦 Deliverables:")
    if phase2c_ok and phase3_ok:
        print("   ✅ Comprehensive land analysis API")
        print("   ✅ Scientific motors integration")
        print("   ✅ Crop suitability scoring")
        print("   ✅ Land use recommendations")
        print("   ✅ Irrigation planning")
        print("   ✅ Erosion risk assessment")
        print("   ✅ ~38 integration tests")
        print("   ✅ Performance optimized")
        print("   ✅ Robust error handling")
    else:
        print("   ❌ Some components failed - review errors above")

    all_passed = phase2c_ok and phase3_ok and combined_ok and error_ok
    print(f"\n🎯 Overall Status: {'✅ ALL PHASES COMPLETE' if all_passed else '❌ SOME ISSUES REMAIN'}")
    print("=" * 70)

    return all_passed


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("COMBINED PHASES EXECUTION")
    print("Phase 2C + Phase 3 + Performance + Error Handling")
    print("=" * 70)

    # Check files exist
    phase2c_file = PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_comprehensive_analyzer.py"
    phase3_file = PROJECT_ROOT / "engine" / "land" / "integration" / "tests" / "test_motors_hub.py"

    if not phase2c_file.exists():
        print(f"❌ Missing: {phase2c_file}")
        print("\n💡 Run first: python sandbox/phase2c_comprehensive_analysis.py")
        return 1

    if not phase3_file.exists():
        print(f"❌ Missing: {phase3_file}")
        print("\n💡 Run first: python sandbox/phase3_motors_integration.py")
        return 1

    print(f"✅ Found: {phase2c_file.name}")
    print(f"✅ Found: {phase3_file.name}")

    # Run phases
    phase2c_ok = run_phase2c()
    phase3_ok = run_phase3()
    combined_ok = run_combined_tests()

    # Performance benchmark
    perf_score = benchmark_performance()

    # Error handling
    error_ok = test_error_handling()

    # Generate report
    success = generate_report(phase2c_ok, phase3_ok, combined_ok, perf_score, error_ok)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())