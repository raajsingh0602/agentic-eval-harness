"""Legacy C++ bridge for compiling and executing C++ code."""

import subprocess
import tempfile
import os
import time
import json
from typing import Optional


class CPPLegacyBridge:
    """Compiles and executes legacy C++ source files with resource monitoring."""

    def __init__(self, compiler: str = "g++", compiler_flags: Optional[list] = None):
        self.compiler = compiler
        self.compiler_flags = compiler_flags or ["-O2", "-std=c++17"]

    def compile(self, source_path: str, output_path: Optional[str] = None) -> bool:
        """Compile a C++ source file.

        Args:
            source_path: Path to the .cpp source file.
            output_path: Path for the output binary. Defaults to source name without extension.

        Returns:
            True if compilation succeeded, False otherwise.
        """
        if not os.path.isfile(source_path):
            return False

        if output_path is None:
            base = os.path.splitext(source_path)[0]
            output_path = base

        cmd = [self.compiler] + self.compiler_flags + [source_path, "-o", output_path]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def run(
        self,
        executable_path: str,
        args: Optional[list] = None,
        timeout_ms: int = 5000,
        input_data: Optional[str] = None,
    ) -> dict:
        """Execute a compiled C++ binary and return performance metrics.

        Args:
            executable_path: Path to the executable.
            args: Command-line arguments.
            timeout_ms: Timeout in milliseconds.
            input_data: Stdin data to pass to the process.

        Returns:
            Dict with stdout, stderr, returncode, exec_time_ms, peak_memory_kb.
        """
        if not os.path.isfile(executable_path):
            return {
                "stdout": "",
                "stderr": "Executable not found",
                "returncode": -1,
                "exec_time_ms": 0,
                "peak_memory_kb": 0,
            }

        cmd = [executable_path] + (args or [])
        timeout_s = max(timeout_ms / 1000.0, 0.1)

        start_time = time.perf_counter()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                input=input_data,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "exec_time_ms": round(elapsed_ms, 3),
                "peak_memory_kb": 0,
            }
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_ms}ms",
                "returncode": -1,
                "exec_time_ms": round(elapsed_ms, 3),
                "peak_memory_kb": 0,
            }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "exec_time_ms": round(elapsed_ms, 3),
                "peak_memory_kb": 0,
            }

    def benchmark(
        self,
        executable_path: str,
        test_inputs: list[str],
        iterations: int = 3,
        timeout_ms: int = 5000,
    ) -> dict:
        """Run a benchmark across multiple inputs and iterations.

        Args:
            executable_path: Path to the executable.
            test_inputs: List of stdin inputs to test with.
            iterations: Number of iterations per input.
            timeout_ms: Timeout per execution in milliseconds.

        Returns:
            Dict with per-input timing statistics.
        """
        results = {}
        for i, inp in enumerate(test_inputs):
            times = []
            for _ in range(iterations):
                run_result = self.run(
                    executable_path, timeout_ms=timeout_ms, input_data=inp
                )
                times.append(run_result["exec_time_ms"])
            results[f"input_{i}"] = {
                "input": inp[:100],
                "times_ms": times,
                "avg_ms": round(sum(times) / len(times), 3),
                "min_ms": round(min(times), 3),
                "max_ms": round(max(times), 3),
            }
        return results
