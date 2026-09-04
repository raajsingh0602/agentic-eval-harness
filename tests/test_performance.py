"""Tests for the Performance Analyzer."""

import os
import sys
import pytest

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
