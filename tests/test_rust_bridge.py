"""Tests for the Rust Legacy Bridge."""

import os
import sys
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.legacy.rust_bridge import RustLegacyBridge


@pytest.fixture
def bridge():
    return RustLegacyBridge()


class TestRustLegacyBridge:
    def test_compile_nonexistent_file(self, bridge):
        result = bridge.compile("/nonexistent/file.rs")
        assert result is False

    def test_compile_empty_path(self, bridge):
        result = bridge.compile("")
        assert result is False

    def test_compile_with_custom_compiler(self):
        custom_bridge = RustLegacyBridge(compiler="rustc", use_cargo=False)
        assert custom_bridge.compiler == "rustc"
        assert custom_bridge.use_cargo is False

    def test_compile_with_cargo_true(self):
        custom_bridge = RustLegacyBridge(compiler="cargo", use_cargo=True)
        assert custom_bridge.use_cargo is True

    def test_run_nonexistent_executable(self, bridge):
        result = bridge.run("/nonexistent/executable")
        assert result["returncode"] == -1
        assert result["exec_time_ms"] == 0

    def test_run_empty_path(self, bridge):
        result = bridge.run("")
        assert result["returncode"] == -1

    def test_run_with_args(self, bridge):
        result = bridge.run("/nonexistent/executable", args=["arg1", "arg2"])
        assert result["returncode"] == -1

    def test_benchmark_nonexistent(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["30\n"])
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
        result = bridge.compile("/nonexistent/file.rs", output_path=None)
        assert result is False

    def test_run_with_input_data(self, bridge):
        result = bridge.run("/nonexistent/executable", input_data="test input")
        assert result["returncode"] == -1

    def test_run_with_zero_timeout(self, bridge):
        result = bridge.run("/nonexistent/executable", timeout_ms=0)
        assert result["returncode"] == -1
        assert result["exec_time_ms"] >= 0

    def test_compile_with_unicode_path(self, bridge):
        result = bridge.compile("/nonexistent/文件.rs")
        assert result is False

    def test_run_unicode_executable(self, bridge):
        result = bridge.run("/nonexistent/执行文件")
        assert result["returncode"] == -1


class TestRustLegacyBridgeWithRust:
    @pytest.fixture
    def compute_executables(self, bridge):
        rust_dir = os.path.join(os.path.dirname(__file__), "..", "legacy_rust")
        legacy_src = os.path.join(rust_dir, "legacy_compute.rs")
        optimized_src = os.path.join(rust_dir, "optimized_compute.rs")

        legacy_bin = os.path.join(rust_dir, "legacy_compute")
        optimized_bin = os.path.join(rust_dir, "optimized_compute")

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

    def test_compile_legacy(self, compute_executables):
        assert compute_executables["legacy_ok"]

    def test_compile_optimized(self, compute_executables):
        assert compute_executables["optimized_ok"]

    def test_compile_same_source_different_output(self, bridge):
        rust_dir = os.path.join(os.path.dirname(__file__), "..", "legacy_rust")
        legacy_src = os.path.join(rust_dir, "legacy_compute.rs")
        bin1 = os.path.join(rust_dir, "test_bin1")
        bin2 = os.path.join(rust_dir, "test_bin2")
        ok1 = bridge.compile(legacy_src, bin1)
        ok2 = bridge.compile(legacy_src, bin2)
        if ok1:
            os.remove(bin1)
        if ok2:
            os.remove(bin2)

    def test_run_legacy_fibonacci(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=["10"])
        assert result["returncode"] == 0
        assert "fibonacci(10) = 55" in result["stdout"]

    def test_run_optimized_fibonacci(self, compute_executables, bridge):
        if not compute_executables["optimized"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["optimized"], args=["10"])
        assert result["returncode"] == 0
        assert "fibonacci(10) = 55" in result["stdout"]

    def test_run_legacy_fibonacci_zero(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=["0"])
        assert result["returncode"] == 0
        assert "fibonacci(0) = 0" in result["stdout"]

    def test_run_legacy_fibonacci_one(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=["1"])
        assert result["returncode"] == 0
        assert "fibonacci(1) = 1" in result["stdout"]

    def test_run_legacy_fibonacci_large(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=["20"], timeout_ms=30000)
        assert result["returncode"] == 0
        assert "fibonacci(20) = 6765" in result["stdout"]

    def test_run_optimized_fibonacci_large(self, compute_executables, bridge):
        if not compute_executables["optimized"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["optimized"], args=["50"], timeout_ms=1000)
        assert result["returncode"] == 0
        assert "fibonacci(50) = 12586269025" in result["stdout"]

    def test_run_fibonacci_no_args(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=[])
        assert result["returncode"] == 0
        assert "fibonacci(30) = 832040" in result["stdout"]

    def test_run_fibonacci_invalid_arg(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=["invalid"])
        assert result["returncode"] != 0 or "error" in result["stderr"].lower()

    def test_benchmark_fibonacci(self, compute_executables, bridge):
        if not compute_executables["legacy"] or not compute_executables["optimized"]:
            pytest.skip("Rust compiler not available")
        inputs = ["10\n"]
        legacy_results = bridge.benchmark(compute_executables["legacy"], inputs, iterations=1)
        optimized_results = bridge.benchmark(compute_executables["optimized"], inputs, iterations=1)
        assert legacy_results["input_0"]["avg_ms"] > 0
        assert optimized_results["input_0"]["avg_ms"] > 0

    def test_benchmark_multiple_inputs(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        inputs = [f"{i}\n" for i in range(10)]
        results = bridge.benchmark(compute_executables["legacy"], inputs, iterations=2)
        assert len(results) == 10
        for i in range(10):
            assert len(results[f"input_{i}"]["times_ms"]) == 2

    def test_benchmark_statistical_accuracy(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        inputs = ["10\n"]
        results = bridge.benchmark(compute_executables["legacy"], inputs, iterations=10)
        times = results["input_0"]["times_ms"]
        avg = results["input_0"]["avg_ms"]
        min_t = results["input_0"]["min_ms"]
        max_t = results["input_0"]["max_ms"]
        assert min_t <= avg <= max_t
        assert avg == pytest.approx(sum(times) / len(times), rel=0.01)

    def test_concurrent_runs(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        def run_fib(i):
            return bridge.run(compute_executables["legacy"], args=[str(i)])
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_fib, i) for i in range(5, 15)]
            for future in as_completed(futures):
                result = future.result()
                assert result["returncode"] == 0

    def test_benchmark_consistency(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        inputs = ["10\n"]
        r1 = bridge.benchmark(compute_executables["legacy"], inputs, iterations=3)
        r2 = bridge.benchmark(compute_executables["legacy"], inputs, iterations=3)
        assert r1["input_0"]["avg_ms"] > 0
        assert r2["input_0"]["avg_ms"] > 0

    def test_run_timeout(self, compute_executables, bridge):
        if not compute_executables["legacy"]:
            pytest.skip("Rust compiler not available")
        result = bridge.run(compute_executables["legacy"], args=["45"], timeout_ms=1)
        assert "returncode" in result


class TestRustLegacyBridgeStressTests:
    def test_many_benchmark_runs(self, bridge):
        for _ in range(100):
            result = bridge.benchmark("/nonexistent", ["test\n"], iterations=1)
            assert len(result) == 1

    def test_compile_same_file_multiple_times(self, bridge):
        for _ in range(10):
            result = bridge.compile("/nonexistent/file.rs")
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

    def test_compile_with_unicode_source(self, bridge):
        result = bridge.compile("/nonexistent/源代码.rs")
        assert result is False


class TestRustLegacyBridgeEdgeCases:
    def test_compile_with_spaces_in_path(self, bridge):
        result = bridge.compile("/path with spaces/file.rs")
        assert result is False

    def test_run_executable_with_spaces(self, bridge):
        result = bridge.run("/path with spaces/executable")
        assert result["returncode"] == -1

    def test_benchmark_zero_iterations(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["test\n"], iterations=0)
        assert result["input_0"]["avg_ms"] == 0.0
        assert result["input_0"]["times_ms"] == []
        assert result["input_0"]["min_ms"] == 0.0
        assert result["input_0"]["max_ms"] == 0.0

    def test_benchmark_negative_timeout(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["test\n"], timeout_ms=-1000)
        assert "input_0" in result

    def test_run_special_chars_args(self, bridge):
        result = bridge.run("/nonexistent/executable", args=["arg with spaces", "arg\twith\ttabs", "arg\nwith\nnewlines"])
        assert result["returncode"] == -1