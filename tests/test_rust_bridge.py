"""Tests for the Rust Legacy Bridge."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.legacy.rust_bridge import RustLegacyBridge


@pytest.fixture
def bridge():
    return RustLegacyBridge()


class TestRustLegacyBridge:
    def test_compile_nonexistent_file(self, bridge):
        result = bridge.compile("/nonexistent/file.rs")
        assert result is False

    def test_run_nonexistent_executable(self, bridge):
        result = bridge.run("/nonexistent/executable")
        assert result["returncode"] == -1

    def test_benchmark_nonexistent(self, bridge):
        result = bridge.benchmark("/nonexistent/executable", ["30\n"])
        assert len(result) == 1


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
