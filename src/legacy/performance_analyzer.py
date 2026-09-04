"""Performance analyzer for comparing legacy vs optimized codebases."""

import os
import time
import json
from typing import Optional
from .cpp_bridge import CPPLegacyBridge
from .rust_bridge import RustLegacyBridge


class PerformanceAnalyzer:
    """Compares performance between baseline and optimized binaries."""

    def __init__(self):
        self.cpp_bridge = CPPLegacyBridge()
        self.rust_bridge = RustLegacyBridge()

    def analyze_execution(
        self,
        baseline_path: str,
        optimized_path: str,
        test_inputs: list[str],
        language: str = "cpp",
        iterations: int = 5,
        timeout_ms: int = 10000,
    ) -> dict:
        """Compare execution performance between baseline and optimized binaries.

        Args:
            baseline_path: Path to the baseline executable.
            optimized_path: Path to the optimized executable.
            test_inputs: List of stdin inputs for testing.
            language: 'cpp' or 'rust'.
            iterations: Number of iterations per test input.
            timeout_ms: Timeout per execution in milliseconds.

        Returns:
            Dict with comparison results including speedup ratios.
        """
        bridge = self.cpp_bridge if language == "cpp" else self.rust_bridge

        baseline_results = bridge.benchmark(
            baseline_path, test_inputs, iterations, timeout_ms
        )
        optimized_results = bridge.benchmark(
            optimized_path, test_inputs, iterations, timeout_ms
        )

        comparisons = []
        for key in baseline_results:
            baseline_avg = baseline_results[key]["avg_ms"]
            optimized_avg = optimized_results[key]["avg_ms"]
            speedup = (
                round(baseline_avg / optimized_avg, 2)
                if optimized_avg > 0
                else float("inf")
            )
            comparisons.append(
                {
                    "input_key": key,
                    "baseline_avg_ms": baseline_avg,
                    "optimized_avg_ms": optimized_avg,
                    "speedup": speedup,
                    "time_saved_ms": round(baseline_avg - optimized_avg, 3),
                }
            )

        overall_baseline = sum(c["baseline_avg_ms"] for c in comparisons)
        overall_optimized = sum(c["optimized_avg_ms"] for c in comparisons)
        overall_speedup = (
            round(overall_baseline / overall_optimized, 2)
            if overall_optimized > 0
            else float("inf")
        )

        return {
            "baseline": baseline_results,
            "optimized": optimized_results,
            "comparisons": comparisons,
            "overall_speedup": overall_speedup,
            "total_time_saved_ms": round(overall_baseline - overall_optimized, 3),
        }

    def detect_bottlenecks(self, execution_trace: list[dict]) -> list[dict]:
        """Identify slow code paths from execution trace data.

        Args:
            execution_trace: List of dicts with 'function_name' and 'time_ms'.

        Returns:
            List of bottleneck entries sorted by severity.
        """
        if not execution_trace:
            return []

        total_time = sum(entry.get("time_ms", 0) for entry in execution_trace)
        if total_time == 0:
            return []

        bottlenecks = []
        for entry in execution_trace:
            time_ms = entry.get("time_ms", 0)
            percentage = (time_ms / total_time) * 100
            severity = "critical" if percentage > 40 else "high" if percentage > 25 else "medium" if percentage > 10 else "low"
            bottlenecks.append(
                {
                    "function_name": entry.get("function_name", "unknown"),
                    "time_ms": time_ms,
                    "percentage": round(percentage, 2),
                    "severity": severity,
                }
            )

        bottlenecks.sort(key=lambda x: x["time_ms"], reverse=True)
        return bottlenecks

    @staticmethod
    def compute_speedup(baseline_ms: float, optimized_ms: float) -> float:
        """Compute speedup ratio.

        Args:
            baseline_ms: Baseline execution time in milliseconds.
            optimized_ms: Optimized execution time in milliseconds.

        Returns:
            Speedup ratio (baseline / optimized). Returns inf if optimized is 0.
        """
        if optimized_ms <= 0:
            return float("inf")
        return round(baseline_ms / optimized_ms, 2)

    @staticmethod
    def generate_optimization_report(results: dict) -> str:
        """Generate a formatted optimization report.

        Args:
            results: Output from analyze_execution().

        Returns:
            Formatted string report.
        """
        lines = [
            "=" * 60,
            "  Performance Optimization Report",
            "=" * 60,
            "",
        ]

        for comp in results.get("comparisons", []):
            lines.append(f"  Test: {comp['input_key']}")
            lines.append(f"    Baseline:    {comp['baseline_avg_ms']:.3f} ms")
            lines.append(f"    Optimized:   {comp['optimized_avg_ms']:.3f} ms")
            lines.append(f"    Speedup:     {comp['speedup']}x")
            lines.append(f"    Time Saved:  {comp['time_saved_ms']:.3f} ms")
            lines.append("")

        lines.append("-" * 60)
        lines.append(f"  Overall Speedup:       {results.get('overall_speedup', 0)}x")
        lines.append(
            f"  Total Time Saved:      {results.get('total_time_saved_ms', 0):.3f} ms"
        )
        lines.append("=" * 60)

        return "\n".join(lines)
