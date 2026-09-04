"""Tests for the Legacy C++ Bridge."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.legacy.cpp_bridge import CPPLegacyBridge


@pytest.fixture
def bridge():
    return CPPLegacyBridge()


class TestCPPLegacyBridge:
    def test_compile_nonexistent_file(self, bridge):
        result = bridge.compile("/nonexistent/file.cpp")
        assert result is False

    def test_run_nonexistent_executable(self, bridge):
        result = bridge.run("/nonexistent/executable")
        assert result["returncode"] == -1
        assert "not found" in result["stderr"]

    def test_benchmark_nonexistent(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["1\n"])
        assert len(result) == 1
        assert result["input_0"]["avg_ms"] == 0


class TestCPPLegacyBridgeWithCpp:
    @pytest.fixture
    def sort_executables(self, bridge):
        cpp_dir = os.path.join(os.path.dirname(__file__), "..", "legacy_cpp")
        legacy_src = os.path.join(cpp_dir, "legacy_sort.cpp")
        optimized_src = os.path.join(cpp_dir, "optimized_sort.cpp")

        legacy_bin = os.path.join(cpp_dir, "legacy_sort")
        optimized_bin = os.path.join(cpp_dir, "optimized_sort")

        legacy_ok = bridge.compile(legacy_src, legacy_bin)
        optimized_ok = bridge.compile(optimized_src, optimized_bin)

        yield {
            "legacy": legacy_bin if legacy_ok else None,
            "optimized": optimized_bin if optimized_ok else None,
            "legacy_ok": legacy_ok,
            "optimized_ok": optimized_ok,
        }

        for path in [legacy_bin, optimized_bin]:
            if os.path.isfile(path):
                os.remove(path)

    def test_compile_legacy(self, sort_executables):
        assert sort_executables["legacy_ok"]

    def test_compile_optimized(self, sort_executables):
        assert sort_executables["optimized_ok"]

    def test_run_legacy_sort(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="3 1 2\n")
        assert result["returncode"] == 0
        assert result["stdout"].strip() == "1 2 3"

    def test_run_optimized_sort(self, sort_executables, bridge):
        if not sort_executables["optimized"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["optimized"], input_data="3 1 2\n")
        assert result["returncode"] == 0
        assert result["stdout"].strip() == "1 2 3"

    def test_benchmark_sorts(self, sort_executables, bridge):
        if not sort_executables["legacy"] or not sort_executables["optimized"]:
            pytest.skip("C++ compiler not available")
        inputs = [" ".join(str(i) for i in range(100, 0, -1)) + "\n"]
        legacy_results = bridge.benchmark(sort_executables["legacy"], inputs, iterations=1)
        optimized_results = bridge.benchmark(sort_executables["optimized"], inputs, iterations=1)
        assert legacy_results["input_0"]["avg_ms"] > 0
        assert optimized_results["input_0"]["avg_ms"] > 0
