"""Tests for the Performance Analyzer."""

import os
import sys
import pytest
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.legacy.performance_analyzer import PerformanceAnalyzer


@pytest.fixture
def analyzer():
    return PerformanceAnalyzer()


class TestPerformanceAnalyzer:
    def test_compute_speedup_equal(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(100.0, 100.0) == 1.0

    def test_compute_speedup_faster(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(100.0, 50.0) == 2.0

    def test_compute_speedup_slower(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(100.0, 200.0) == 0.5

    def test_compute_speedup_zero_optimized(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(100.0, 0.0) == float("inf")

    def test_compute_speedup_zero_baseline(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(0.0, 100.0) == 0.0

    def test_compute_speedup_negative_baseline(self, analyzer):
        result = PerformanceAnalyzer.compute_speedup(-100.0, 50.0)
        assert result == -2.0

    def test_compute_speedup_very_small_optimized(self, analyzer):
        result = PerformanceAnalyzer.compute_speedup(100.0, 1e-10)
        assert result > 1e10

    def test_compute_speedup_large_numbers(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(1e12, 1e10) == 100.0

    def test_compute_speedup_precision(self, analyzer):
        assert PerformanceAnalyzer.compute_speedup(100.0, 33.33) == pytest.approx(3.0, rel=0.01)

    def test_detect_bottlenecks_empty(self, analyzer):
        assert analyzer.detect_bottlenecks([]) == []

    def test_detect_bottlenecks(self, analyzer):
        trace = [
            {"function_name": "parse", "time_ms": 10},
            {"function_name": "sort", "time_ms": 80},
            {"function_name": "write", "time_ms": 10},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert len(bottlenecks) == 3
        assert bottlenecks[0]["function_name"] == "sort"
        assert bottlenecks[0]["severity"] == "critical"

    def test_detect_bottlenecks_zero_total(self, analyzer):
        trace = [
            {"function_name": "a", "time_ms": 0},
            {"function_name": "b", "time_ms": 0},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert bottlenecks == []

    def test_detect_bottlenecks_single_function(self, analyzer):
        trace = [{"function_name": "only", "time_ms": 100}]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert len(bottlenecks) == 1
        assert bottlenecks[0]["percentage"] == 100.0
        assert bottlenecks[0]["severity"] == "critical"

    def test_detect_bottlenecks_severity_thresholds(self, analyzer):
        trace = [
            {"function_name": "critical", "time_ms": 50},
            {"function_name": "high", "time_ms": 30},
            {"function_name": "medium", "time_ms": 15},
            {"function_name": "low", "time_ms": 5},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert bottlenecks[0]["severity"] == "critical"
        assert bottlenecks[1]["severity"] == "high"
        assert bottlenecks[2]["severity"] == "medium"
        assert bottlenecks[3]["severity"] == "low"

    def test_detect_bottlenecks_sorted_by_time(self, analyzer):
        trace = [
            {"function_name": "a", "time_ms": 10},
            {"function_name": "b", "time_ms": 50},
            {"function_name": "c", "time_ms": 20},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        times = [b["time_ms"] for b in bottlenecks]
        assert times == sorted(times, reverse=True)

    def test_detect_bottlenecks_missing_keys(self, analyzer):
        trace = [
            {"function_name": "a", "time_ms": 10},
            {"time_ms": 20},
            {},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert len(bottlenecks) == 3
        # Results sorted by time_ms descending: 20, 10, 0
        assert bottlenecks[0]["function_name"] == "unknown"
        assert bottlenecks[0]["time_ms"] == 20
        assert bottlenecks[1]["function_name"] == "a"
        assert bottlenecks[2]["time_ms"] == 0

    def test_detect_bottlenecks_negative_time(self, analyzer):
        trace = [
            {"function_name": "a", "time_ms": -10},
            {"function_name": "b", "time_ms": 50},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert len(bottlenecks) == 2

    def test_generate_report(self, analyzer):
        results = {
            "comparisons": [
                {
                    "input_key": "input_0",
                    "baseline_avg_ms": 100.0,
                    "optimized_avg_ms": 50.0,
                    "speedup": 2.0,
                    "time_saved_ms": 50.0,
                }
            ],
            "overall_speedup": 2.0,
            "total_time_saved_ms": 50.0,
        }
        report = PerformanceAnalyzer.generate_optimization_report(results)
        assert "Speedup:     2.0x" in report
        assert "Overall Speedup:       2.0x" in report

    def test_generate_report_multiple_comparisons(self, analyzer):
        results = {
            "comparisons": [
                {
                    "input_key": "input_0",
                    "baseline_avg_ms": 100.0,
                    "optimized_avg_ms": 50.0,
                    "speedup": 2.0,
                    "time_saved_ms": 50.0,
                },
                {
                    "input_key": "input_1",
                    "baseline_avg_ms": 200.0,
                    "optimized_avg_ms": 100.0,
                    "speedup": 2.0,
                    "time_saved_ms": 100.0,
                },
            ],
            "overall_speedup": 2.0,
            "total_time_saved_ms": 150.0,
        }
        report = PerformanceAnalyzer.generate_optimization_report(results)
        assert report.count("Speedup:") == 3
        assert "Overall Speedup:       2.0x" in report

    def test_generate_report_zero_speedup(self, analyzer):
        results = {
            "comparisons": [
                {
                    "input_key": "input_0",
                    "baseline_avg_ms": 100.0,
                    "optimized_avg_ms": 100.0,
                    "speedup": 1.0,
                    "time_saved_ms": 0.0,
                }
            ],
            "overall_speedup": 1.0,
            "total_time_saved_ms": 0.0,
        }
        report = PerformanceAnalyzer.generate_optimization_report(results)
        assert "Speedup:     1.0x" in report

    def test_generate_report_infinite_speedup(self, analyzer):
        results = {
            "comparisons": [
                {
                    "input_key": "input_0",
                    "baseline_avg_ms": 100.0,
                    "optimized_avg_ms": 0.0,
                    "speedup": float("inf"),
                    "time_saved_ms": 100.0,
                }
            ],
            "overall_speedup": float("inf"),
            "total_time_saved_ms": 100.0,
        }
        report = PerformanceAnalyzer.generate_optimization_report(results)
        assert "inf" in report.lower() or "infinite" in report.lower() or "∞" in report

    def test_generate_report_empty(self, analyzer):
        results = {
            "comparisons": [],
            "overall_speedup": 0.0,
            "total_time_saved_ms": 0.0,
        }
        report = PerformanceAnalyzer.generate_optimization_report(results)
        assert "Performance Optimization Report" in report

    def test_analyze_execution_structure(self, analyzer):
        results = analyzer.analyze_execution(
            baseline_path="/nonexistent/baseline",
            optimized_path="/nonexistent/optimized",
            test_inputs=["test"],
            language="cpp",
            iterations=1,
            timeout_ms=100,
        )
        assert "baseline" in results
        assert "optimized" in results
        assert "comparisons" in results
        assert "overall_speedup" in results
        assert "total_time_saved_ms" in results

    def test_analyze_execution_invalid_language(self, analyzer):
        results = analyzer.analyze_execution(
            baseline_path="/nonexistent/baseline",
            optimized_path="/nonexistent/optimized",
            test_inputs=["test"],
            language="invalid",
            iterations=1,
            timeout_ms=100,
        )
        assert "baseline" in results
        assert "optimized" in results

    def test_analyze_execution_zero_iterations(self, analyzer):
        results = analyzer.analyze_execution(
            baseline_path="/nonexistent/baseline",
            optimized_path="/nonexistent/optimized",
            test_inputs=["test"],
            language="cpp",
            iterations=0,
            timeout_ms=100,
        )
        assert results["comparisons"][0]["baseline_avg_ms"] == 0
        assert results["comparisons"][0]["speedup"] == float("inf")

    def test_analyze_execution_many_inputs(self, analyzer):
        inputs = [f"input_{i}\n" for i in range(50)]
        results = analyzer.analyze_execution(
            baseline_path="/nonexistent/baseline",
            optimized_path="/nonexistent/optimized",
            test_inputs=inputs,
            language="cpp",
            iterations=1,
            timeout_ms=100,
        )
        assert len(results["comparisons"]) == 50

    def test_analyze_execution_many_iterations(self, analyzer):
        results = analyzer.analyze_execution(
            baseline_path="/nonexistent/baseline",
            optimized_path="/nonexistent/optimized",
            test_inputs=["test\n"],
            language="cpp",
            iterations=100,
            timeout_ms=100,
        )
        assert len(results["comparisons"]) == 1


class TestPerformanceAnalyzerBoundaryConditions:
    def test_compute_speedup_float_precision(self, analyzer):
        for _ in range(100):
            b = float(100 + _)
            o = float(50 + _)
            result = PerformanceAnalyzer.compute_speedup(b, o)
            expected = round(b / o, 2)
            assert result == expected

    def test_detect_bottlenecks_large_trace(self, analyzer):
        trace = [{"function_name": f"fn_{i}", "time_ms": i} for i in range(1000)]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        assert len(bottlenecks) == 1000
        assert bottlenecks[0]["function_name"] == "fn_999"

    def test_generate_report_unicode(self, analyzer):
        results = {
            "comparisons": [
                {
                    "input_key": "输入",
                    "baseline_avg_ms": 100.0,
                    "optimized_avg_ms": 50.0,
                    "speedup": 2.0,
                    "time_saved_ms": 50.0,
                }
            ],
            "overall_speedup": 2.0,
            "total_time_saved_ms": 50.0,
        }
        report = PerformanceAnalyzer.generate_optimization_report(results)
        assert "输入" in report

    def test_analyze_execution_rust_language(self, analyzer):
        results = analyzer.analyze_execution(
            baseline_path="/nonexistent/baseline",
            optimized_path="/nonexistent/optimized",
            test_inputs=["test"],
            language="rust",
            iterations=1,
            timeout_ms=100,
        )
        assert "baseline" in results
        assert "optimized" in results


class TestPerformanceAnalyzerIntegration:
    def test_full_pipeline_consistency(self, analyzer):
        trace = [
            {"function_name": "parse", "time_ms": 10},
            {"function_name": "compute", "time_ms": 80},
            {"function_name": "write", "time_ms": 10},
        ]
        bottlenecks = analyzer.detect_bottlenecks(trace)
        total_pct = sum(b["percentage"] for b in bottlenecks)
        assert abs(total_pct - 100.0) < 0.01

    def test_speedup_consistency(self, analyzer):
        baseline = 1000.0
        for optimized in [1.0, 10.0, 100.0, 500.0, 1000.0, 2000.0]:
            speedup = PerformanceAnalyzer.compute_speedup(baseline, optimized)
            if optimized > 0:
                assert speedup == round(baseline / optimized, 2)


class TestPerformanceAnalyzerStressTests:
    def test_compute_speedup_many_calls(self, analyzer):
        for i in range(10000):
            result = PerformanceAnalyzer.compute_speedup(100.0, 50.0)
            assert result == 2.0

    def test_detect_bottlenecks_many_calls(self, analyzer):
        trace = [{"function_name": "a", "time_ms": 10}, {"function_name": "b", "time_ms": 90}]
        for _ in range(1000):
            bottlenecks = analyzer.detect_bottlenecks(trace)
            assert len(bottlenecks) == 2

    def test_generate_report_many_calls(self, analyzer):
        results = {
            "comparisons": [{"input_key": "i", "baseline_avg_ms": 100.0, "optimized_avg_ms": 50.0, "speedup": 2.0, "time_saved_ms": 50.0}],
            "overall_speedup": 2.0,
            "total_time_saved_ms": 50.0,
        }
        for _ in range(100):
            report = PerformanceAnalyzer.generate_optimization_report(results)
            assert "2.0x" in report