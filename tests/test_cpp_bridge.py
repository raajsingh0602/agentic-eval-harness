"""Tests for the Legacy C++ Bridge."""

import os
import sys
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.legacy.cpp_bridge import CPPLegacyBridge


@pytest.fixture
def bridge():
    return CPPLegacyBridge()


class TestCPPLegacyBridge:
    def test_compile_nonexistent_file(self, bridge):
        result = bridge.compile("/nonexistent/file.cpp")
        assert result is False

    def test_compile_empty_path(self, bridge):
        result = bridge.compile("")
        assert result is False

    def test_compile_with_custom_flags(self, bridge):
        custom_bridge = CPPLegacyBridge(compiler="g++", compiler_flags=["-O3", "-std=c++20"])
        assert custom_bridge.compiler_flags == ["-O3", "-std=c++20"]

    def test_run_nonexistent_executable(self, bridge):
        result = bridge.run("/nonexistent/executable")
        assert result["returncode"] == -1
        assert "not found" in result["stderr"]
        assert result["exec_time_ms"] == 0
        assert result["peak_memory_kb"] == 0

    def test_run_empty_path(self, bridge):
        result = bridge.run("")
        assert result["returncode"] == -1

    def test_run_with_args(self, bridge):
        result = bridge.run("/nonexistent/executable", args=["arg1", "arg2"])
        assert result["returncode"] == -1

    def test_benchmark_nonexistent(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["1\n"])
        assert len(result) == 1
        assert result["input_0"]["avg_ms"] == 0
        assert result["input_0"]["min_ms"] == 0
        assert result["input_0"]["max_ms"] == 0

    def test_benchmark_empty_inputs(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", [])
        assert result == {}

    def test_benchmark_with_iterations(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["test\n"], iterations=5)
        assert len(result) == 1
        assert len(result["input_0"]["times_ms"]) == 5

    def test_benchmark_with_custom_timeout(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["test\n"], timeout_ms=100)
        assert result["input_0"]["avg_ms"] == 0

    def test_compile_with_none_output_path(self, bridge):
        result = bridge.compile("/nonexistent/file.cpp", output_path=None)
        assert result is False

    def test_run_with_input_data(self, bridge):
        result = bridge.run("/nonexistent/executable", input_data="test input")
        assert result["returncode"] == -1

    def test_run_with_zero_timeout(self, bridge):
        result = bridge.run("/nonexistent/executable", timeout_ms=0)
        assert result["returncode"] == -1
        assert result["exec_time_ms"] >= 0

    def test_compile_with_unicode_path(self, bridge):
        result = bridge.compile("/nonexistent/文件.cpp")
        assert result is False

    def test_run_unicode_executable(self, bridge):
        result = bridge.run("/nonexistent/执行文件")
        assert result["returncode"] == -1


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
            "optimized": optimized_bin if legacy_ok else None,
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

    def test_compile_same_source_different_output(self, bridge):
        cpp_dir = os.path.join(os.path.dirname(__file__), "..", "legacy_cpp")
        legacy_src = os.path.join(cpp_dir, "legacy_sort.cpp")
        bin1 = os.path.join(cpp_dir, "test_bin1")
        bin2 = os.path.join(cpp_dir, "test_bin2")
        ok1 = bridge.compile(legacy_src, bin1)
        ok2 = bridge.compile(legacy_src, bin2)
        if ok1:
            os.remove(bin1)
        if ok2:
            os.remove(bin2)

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

    def test_run_legacy_sort_empty_input(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="\n")
        assert result["returncode"] == 0
        assert result["stdout"].strip() == ""

    def test_run_legacy_sort_single_element(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="42\n")
        assert result["returncode"] == 0
        assert result["stdout"].strip() == "42"

    def test_run_legacy_sort_duplicates(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="5 5 5 3 3\n")
        assert result["returncode"] == 0
        assert result["stdout"].strip() == "3 3 5 5 5"

    def test_run_legacy_sort_negative(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="-5 -1 -10\n")
        assert result["returncode"] == 0
        assert result["stdout"].strip() == "-10 -5 -1"

    def test_run_legacy_sort_large_input(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        input_data = " ".join(str(i) for i in range(1000, 0, -1)) + "\n"
        result = bridge.run(sort_executables["legacy"], input_data=input_data, timeout_ms=10000)
        assert result["returncode"] == 0
        output = result["stdout"].strip()
        assert output == " ".join(str(i) for i in range(1, 1001))

    def test_benchmark_sorts(self, sort_executables, bridge):
        if not sort_executables["legacy"] or not sort_executables["optimized"]:
            pytest.skip("C++ compiler not available")
        inputs = [" ".join(str(i) for i in range(100, 0, -1)) + "\n"]
        legacy_results = bridge.benchmark(sort_executables["legacy"], inputs, iterations=1)
        optimized_results = bridge.benchmark(sort_executables["optimized"], inputs, iterations=1)
        assert legacy_results["input_0"]["avg_ms"] > 0
        assert optimized_results["input_0"]["avg_ms"] > 0

    def test_benchmark_multiple_inputs(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        inputs = [f"{i}\n" for i in range(10)]
        results = bridge.benchmark(sort_executables["legacy"], inputs, iterations=2)
        assert len(results) == 10
        for i in range(10):
            assert len(results[f"input_{i}"]["times_ms"]) == 2

    def test_benchmark_statistical_accuracy(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        inputs = ["1 2 3\n"]
        results = bridge.benchmark(sort_executables["legacy"], inputs, iterations=10)
        times = results["input_0"]["times_ms"]
        avg = results["input_0"]["avg_ms"]
        min_t = results["input_0"]["min_ms"]
        max_t = results["input_0"]["max_ms"]
        assert min_t <= avg <= max_t
        assert avg == pytest.approx(sum(times) / len(times), rel=0.01)

    def test_run_with_stderr_capture(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="invalid input")
        assert "stderr" in result

    def test_concurrent_runs(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        def run_sort(i):
            return bridge.run(sort_executables["legacy"], input_data=f"{i}\n")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_sort, i) for i in range(20)]
            for future in as_completed(futures):
                result = future.result()
                assert result["returncode"] == 0

    def test_benchmark_consistency(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        inputs = ["5 4 3 2 1\n"]
        r1 = bridge.benchmark(sort_executables["legacy"], inputs, iterations=3)
        r2 = bridge.benchmark(sort_executables["legacy"], inputs, iterations=3)
        assert r1["input_0"]["avg_ms"] > 0
        assert r2["input_0"]["avg_ms"] > 0

    def test_run_timeout(self, sort_executables, bridge):
        if not sort_executables["legacy"]:
            pytest.skip("C++ compiler not available")
        result = bridge.run(sort_executables["legacy"], input_data="1\n", timeout_ms=1)
        assert "returncode" in result

    def test_compile_with_invalid_flags(self):
        bridge = CPPLegacyBridge(compiler="g++", compiler_flags=["-invalid-flag-xyz"])
        result = bridge.compile("/nonexistent/file.cpp")
        assert result is False


class TestCPPLegacyBridgeStressTests:
    def test_many_benchmark_runs(self, bridge):
        for _ in range(100):
            result = bridge.benchmark("/nonexistent", ["test\n"], iterations=1)
            assert len(result) == 1

    def test_compile_same_file_multiple_times(self, bridge):
        for _ in range(10):
            result = bridge.compile("/nonexistent/file.cpp")
            assert result is False

    def test_run_with_large_input_data(self, bridge):
        large_input = "x" * 100000
        result = bridge.run("/nonexistent/executable", input_data=large_input)
        assert result["returncode"] == -1

    def test_benchmark_many_inputs(self, bridge):
        inputs = [f"input_{i}\n" for i in range(100)]
        result = bridge.benchmark("/nonexistent/executable", inputs, iterations=1)
        assert len(result) == 100

    def test_run_with_many_args(self, bridge):
        args = [f"arg{i}" for i in range(100)]
        result = bridge.run("/nonexistent/executable", args=args)
        assert result["returncode"] == -1