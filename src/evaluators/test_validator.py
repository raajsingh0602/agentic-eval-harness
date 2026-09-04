"""Multi-edge-case test validator for legacy code evaluation."""

import os
import subprocess
import time
from typing import Any, Optional


class TestResult:
    """Result of a single test case execution."""

    def __init__(
        self,
        test_id: str,
        input_data: str,
        expected_output: str,
        actual_output: str,
        passed: bool,
        execution_time_ms: float,
        description: str = "",
    ):
        self.test_id = test_id
        self.input_data = input_data
        self.expected_output = expected_output
        self.actual_output = actual_output
        self.passed = passed
        self.execution_time_ms = execution_time_ms
        self.description = description

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "input": self.input_data[:200],
            "expected": self.expected_output[:200],
            "actual": self.actual_output[:200],
            "passed": self.passed,
            "execution_time_ms": round(self.execution_time_ms, 3),
            "description": self.description,
        }


class MultiEdgeCaseValidator:
    """Validates legacy code against multiple edge-case test scenarios."""

    def __init__(self, executable_path: Optional[str] = None):
        self.executable_path = executable_path
        self.test_cases: list[dict] = []

    def add_test_case(
        self,
        test_id: str,
        input_data: str,
        expected_output: str,
        description: str = "",
    ) -> None:
        """Add a test case for validation.

        Args:
            test_id: Unique identifier for the test case.
            input_data: Stdin input for the executable.
            expected_output: Expected stdout output.
            description: Human-readable description of the test case.
        """
        self.test_cases.append(
            {
                "id": test_id,
                "input": input_data,
                "expected": expected_output,
                "description": description,
            }
        )

    def add_edge_cases(self, base_input: str, base_expected: str) -> None:
        """Add a set of standard edge cases based on a base case.

        Args:
            base_input: Base input string (e.g., a number or array string).
            base_expected: Expected output for the base case.
        """
        edge_cases = [
            ("empty_input", "", "0\n", "Empty input handling"),
            ("single_element", "1\n", "1\n", "Single element"),
            ("two_elements", "2 1\n", "1 2\n", "Two elements"),
            ("all_same", "5 5 5 5\n", "5 5 5 5\n", "All identical elements"),
            ("already_sorted", "1 2 3 4 5\n", "1 2 3 4 5\n", "Already sorted"),
            ("reverse_sorted", "5 4 3 2 1\n", "1 2 3 4 5\n", "Reverse sorted"),
            ("negative_numbers", "-3 -1 -4\n", "-4 -3 -1\n", "Negative numbers"),
            ("single_negative", "-1\n", "-1\n", "Single negative number"),
            ("large_input", " ".join(str(i) for i in range(100, 0, -1)) + "\n",
             " ".join(str(i) for i in range(1, 101)) + "\n", "100 elements reverse"),
            ("with_zeros", "0 0 5 0 3\n", "0 0 0 3 5\n", "Mixed zeros"),
        ]
        for tid, inp, exp, desc in edge_cases:
            self.add_test_case(tid, inp, exp, desc)

    def validate(
        self,
        executable_path: Optional[str] = None,
        timeout_ms: int = 5000,
    ) -> list[TestResult]:
        """Run all test cases against the executable.

        Args:
            executable_path: Path to executable (overrides self.executable_path).
            timeout_ms: Timeout per test case in milliseconds.

        Returns:
            List of TestResult objects.
        """
        exe = executable_path or self.executable_path
        if not exe or not os.path.isfile(exe):
            return [
                TestResult(
                    test_id=tc["id"],
                    input_data=tc["input"],
                    expected_output=tc["expected"],
                    actual_output="",
                    passed=False,
                    execution_time_ms=0,
                    description=f"Executable not found: {exe}",
                )
                for tc in self.test_cases
            ]

        results = []
        for tc in self.test_cases:
            start = time.perf_counter()
            try:
                proc = subprocess.run(
                    [exe],
                    input=tc["input"],
                    capture_output=True,
                    text=True,
                    timeout=max(timeout_ms / 1000.0, 0.1),
                )
                elapsed_ms = (time.perf_counter() - start) * 1000
                actual = proc.stdout.strip()
                expected = tc["expected"].strip()
                passed = actual == expected
                results.append(
                    TestResult(
                        test_id=tc["id"],
                        input_data=tc["input"],
                        expected_output=tc["expected"],
                        actual_output=proc.stdout,
                        passed=passed,
                        execution_time_ms=elapsed_ms,
                        description=tc.get("description", ""),
                    )
                )
            except subprocess.TimeoutExpired:
                elapsed_ms = (time.perf_counter() - start) * 1000
                results.append(
                    TestResult(
                        test_id=tc["id"],
                        input_data=tc["input"],
                        expected_output=tc["expected"],
                        actual_output="TIMEOUT",
                        passed=False,
                        execution_time_ms=elapsed_ms,
                        description="Execution timed out",
                    )
                )
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                results.append(
                    TestResult(
                        test_id=tc["id"],
                        input_data=tc["input"],
                        expected_output=tc["expected"],
                        actual_output=str(e),
                        passed=False,
                        execution_time_ms=elapsed_ms,
                        description=f"Error: {e}",
                    )
                )

        return results

    def generate_summary(self, results: list[TestResult]) -> dict:
        """Generate a summary of validation results.

        Args:
            results: List of TestResult objects from validate().

        Returns:
            Dict with pass/fail counts and details.
        """
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        total = len(results)

        return {
            "total_tests": total,
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": round(len(passed) / total * 100, 2) if total > 0 else 0,
            "total_time_ms": round(sum(r.execution_time_ms for r in results), 3),
            "avg_time_ms": round(
                sum(r.execution_time_ms for r in results) / total, 3
            )
            if total > 0
            else 0,
            "failed_tests": [r.to_dict() for r in failed],
            "passed_tests": [r.to_dict() for r in passed],
        }
