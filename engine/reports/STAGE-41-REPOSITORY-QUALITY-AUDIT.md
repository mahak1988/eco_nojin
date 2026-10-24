# Stage 41 — Repository Quality Audit

## Summary

| Item | Value |
|---|---|
| Tests run | 3835 |
| Passed | 3732 |
| Failed | 103 |
| Errors | 48 |
| Collected | None |

## Failures by class

| Class | Count |
|---|---:|
| coverage_gate | 1 |
| cpp_parity | 2 |
| dependency_graph | 1 |
| ewsi_contract | 2 |
| file_lock | 1 |
| gdd_lai_fallback | 5 |
| lazy_module_resolution | 1 |
| missing_artifact | 3 |
| path_naming | 8 |
| provenance_table | 58 |
| science_scan | 1 |
| scratch_file | 7 |
| service_boundaries | 1 |
| unclassified | 1 |
| unit_gate | 1 |
| weather_input | 10 |

## Detail

| Test | File | Attributed cause |
|---|---|---|
| test_result_type_can_declare_provenance[EWSIOutputSeries] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[QualityMaskResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[CompositeResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[SoilMoistureOutput] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[VPDOutput] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestSensitivityAnalysis] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestQualityReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestPredictionResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestScenarioResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestOperationalReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestProduceValidationReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestValidationOutputSerialization] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestDataIndependenceInReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestBootstrapResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestUncertaintyAssessment] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestCreateBlockedReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | path_naming |
| test_result_type_can_declare_provenance[TestReportSerialization] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestBenchmarkReportStructure] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestReportNoRealData] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestBlockedReportNoData] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestReadyReportWithRealData] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestBenchmarkReportWithManifestData] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestBenchmarkResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestStage33Results] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[TestCSVOutput] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | ewsi_contract |
| test_result_type_can_declare_provenance[TestReportFiles] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_ndvi_numba_equals_python_reference | engine/strict_tests/test_s16_gateway_strict_contracts.py::TestPythonNumbaParity | ewsi_contract |
| test_ndvi_benchmark | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestIndicesBenchmarks | cpp_parity |
| test_evi_benchmark | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestIndicesBenchmarks | cpp_parity |
| test_savi_benchmark | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestIndicesBenchmarks | path_naming |
| test_nbr_benchmark | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestIndicesBenchmarks | provenance_table |
| test_telemetry_overhead | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestTelemetryBenchmarks | provenance_table |
| test_no_memory_leak_repeated_calls | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestMemoryEfficiency | provenance_table |
| test_ndvi_vs_numba | engine/hydroma/cpp_bridge/tests/test_benchmarks.py::TestComparisonWithNumba | path_naming |
| test_ndvi_array | engine/hydroma/cpp_bridge/tests/test_parity.py::TestIndicesParity | provenance_table |
| test_ndvi_broadcasting | engine/hydroma/cpp_bridge/tests/test_parity.py::TestArrayOperations | provenance_table |
| test_ndvi_large_array | engine/hydroma/cpp_bridge/tests/test_parity.py::TestArrayOperations | provenance_table |
| test_ndvi_performance | engine/hydroma/cpp_bridge/tests/test_parity.py::TestPerformance | provenance_table |
| test_evi_performance | engine/hydroma/cpp_bridge/tests/test_parity.py::TestPerformance | provenance_table |
| test_result_type_can_declare_provenance[OperationProfile] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[ProfilerResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[BenchmarkProfiler] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[BenchmarkReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[ConsistencyReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[QualityReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[IngestionResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[QualityCheckResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[DataQualityReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[CalibrationRecordResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[CalibrationResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[UncertaintyResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[EvaluationResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[ScenarioResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[UncertaintyReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[SensitivityResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[SensitivityAnalysisReport] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[ValidationSummary] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[CrossValidationResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[MetricResult] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |
| test_result_type_can_declare_provenance[ValidationOutput] | engine/strict_tests/test_s15_provenance.py::TestProvenanceIsDeclared | provenance_table |

## Policy applied

* Failures that are **stale test expectations** against a deliberately
  changed scientific contract were corrected only after the *new*
  contract was documented, and only where the new behaviour is
  demonstrably correct. The assertion was updated to assert the new
  behaviour, not weakened.
* Failures in **Stage 40/41 code** were fixed and covered with a new
  regression test.
* No test was deleted, skipped, or weakened to make a suite green.
* Changes in code that another agent is actively developing were not
  rewritten.

## Coordination

The tree is live: several modules were being edited concurrently during
this stage. The audit therefore attributes each failure to the file
that changed most recently and to the contract it violates, rather than
assuming a single cause. Where a failure was ambiguous, it is reported
as unresolved rather than "fixed" by suppressing it.
