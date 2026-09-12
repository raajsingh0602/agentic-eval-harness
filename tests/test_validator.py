"""Tests for the Multi-Edge-Case Test Validator."""

import os
import sys
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.evaluators.test_validator import MultiEdgeCaseValidator, ValidationResult


class TestMultiEdgeCaseValidator:
    def test_add_test_case(self):
        validator = MultiEdgeCaseValidator()
        validator.add_test_case("t1", "1\n", "1\n", "Single element")
        assert len(validator.test_cases) == 1
        assert validator.test_cases[0]["id"] == "t1"

    def test_add_edge_cases(self):
        validator = MultiEdgeCaseValidator()
        validator.add_edge_cases("3 1 2\n", "1 2 3\n")
        assert len(validator.test_cases) == 10

    def test_validate_no_executable(self):
        validator = MultiEdgeCaseValidator()
        validator.add_test_case("t1", "1\n", "1\n")
        results = validator.validate("/nonexistent/executable")
        assert len(results) == 1
        assert not results[0].passed

    def test_generate_summary_empty(self):
        validator = MultiEdgeCaseValidator()
        summary = validator.generate_summary([])
        assert summary["total_tests"] == 0
        assert summary["pass_rate"] == 0

    def test_generate_summary(self):
        validator = MultiEdgeCaseValidator()
        results = [
            ValidationResult("t1", "1", "1", "1", True, 1.0),
            ValidationResult("t2", "2", "2", "3", False, 1.0),
            ValidationResult("t3", "3", "3", "3", True, 1.0),
        ]
        summary = validator.generate_summary(results)
        assert summary["total_tests"] == 3
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        assert summary["pass_rate"] == pytest.approx(66.67, rel=0.01)

    def test_test_result_to_dict(self):
        tr = ValidationResult("t1", "input", "expected", "actual", True, 5.5, "desc")
        d = tr.to_dict()
        assert d["test_id"] == "t1"
        assert d["passed"] is True
        assert d["execution_time_ms"] == 5.5

    def test_validation_result_immutability(self):
        tr = ValidationResult("t1", "in", "exp", "act", True, 1.0)
        d1 = tr.to_dict()
        d2 = tr.to_dict()
        assert d1 == d2
        assert d1 is not d2

    def test_validation_result_truncation(self):
        long_input = "x" * 500
        long_expected = "y" * 500
        long_actual = "z" * 500
        tr = ValidationResult("t1", long_input, long_expected, long_actual, True, 1.0)
        d = tr.to_dict()
        assert len(d["input"]) == 200
        assert len(d["expected"]) == 200
        assert len(d["actual"]) == 200

    def test_validation_result_negative_time(self):
        tr = ValidationResult("t1", "in", "exp", "act", True, -1.0)
        assert tr.execution_time_ms == -1.0

    def test_validation_result_zero_time(self):
        tr = ValidationResult("t1", "in", "exp", "act", True, 0.0)
        assert tr.execution_time_ms == 0.0

    def test_add_duplicate_test_id(self):
        validator = MultiEdgeCaseValidator()
        validator.add_test_case("t1", "1\n", "1\n")
        validator.add_test_case("t1", "2\n", "2\n")
        assert len(validator.test_cases) == 2

    def test_edge_cases_content(self):
        validator = MultiEdgeCaseValidator()
        validator.add_edge_cases("3 1 2\n", "1 2 3\n")
        test_ids = [tc["id"] for tc in validator.test_cases]
        expected_ids = [
            "empty_input", "single_element", "two_elements", "all_same",
            "already_sorted", "reverse_sorted", "negative_numbers",
            "single_negative", "large_input", "with_zeros"
        ]
        assert test_ids == expected_ids

    def test_large_input_edge_case(self):
        validator = MultiEdgeCaseValidator()
        validator.add_edge_cases("3 1 2\n", "1 2 3\n")
        large_case = next(tc for tc in validator.test_cases if tc["id"] == "large_input")
        assert "100" in large_case["input"]
        assert "1 2 3" in large_case["expected"]

    def test_generate_summary_all_passed(self):
        validator = MultiEdgeCaseValidator()
        results = [ValidationResult(f"t{i}", str(i), str(i), str(i), True, 1.0) for i in range(100)]
        summary = validator.generate_summary(results)
        assert summary["total_tests"] == 100
        assert summary["passed"] == 100
        assert summary["failed"] == 0
        assert summary["pass_rate"] == 100.0

    def test_generate_summary_all_failed(self):
        validator = MultiEdgeCaseValidator()
        results = [ValidationResult(f"t{i}", str(i), str(i), str(i+1), False, 1.0) for i in range(50)]
        summary = validator.generate_summary(results)
        assert summary["total_tests"] == 50
        assert summary["passed"] == 0
        assert summary["failed"] == 50
        assert summary["pass_rate"] == 0.0

    def test_generate_summary_timing_accuracy(self):
        validator = MultiEdgeCaseValidator()
        results = [
            ValidationResult("t1", "1", "1", "1", True, 10.0),
            ValidationResult("t2", "2", "2", "2", True, 20.0),
            ValidationResult("t3", "3", "3", "3", True, 30.0),
        ]
        summary = validator.generate_summary(results)
        assert summary["total_time_ms"] == 60.0
        assert summary["avg_time_ms"] == 20.0

    def test_validate_timeout_handling(self):
        validator = MultiEdgeCaseValidator()
        validator.add_test_case("t1", "input", "expected")
        validator.executable_path = "/nonexistent"
        results = validator.validate(timeout_ms=1)
        assert len(results) == 1
        assert not results[0].passed

    def test_validate_empty_input(self):
        validator = MultiEdgeCaseValidator()
        validator.add_test_case("empty", "", "output")
        results = validator.validate("/nonexistent/executable")
        assert len(results) == 1
        assert results[0].input_data == ""

    def test_validate_unicode_input(self):
        validator = MultiEdgeCaseValidator()
        validator.add_test_case("unicode", "🦀\n", "🦀\n")
        results = validator.validate("/nonexistent/executable")
        assert results[0].input_data == "🦀\n"

    def test_validate_multiline_input(self):
        validator = MultiEdgeCaseValidator()
        multi_input = "line1\nline2\nline3\n"
        validator.add_test_case("multi", multi_input, multi_input)
        results = validator.validate("/nonexistent/executable")
        assert results[0].input_data == multi_input

    def test_add_edge_cases_deterministic(self):
        v1 = MultiEdgeCaseValidator()
        v2 = MultiEdgeCaseValidator()
        v1.add_edge_cases("3 1 2\n", "1 2 3\n")
        v2.add_edge_cases("3 1 2\n", "1 2 3\n")
        assert len(v1.test_cases) == len(v2.test_cases)
        for tc1, tc2 in zip(v1.test_cases, v2.test_cases):
            assert tc1 == tc2

    def test_concurrent_validation(self):
        validator = MultiEdgeCaseValidator()
        for i in range(20):
            validator.add_test_case(f"t{i}", f"{i}\n", f"{i}\n")
        def validate_chunk():
            return validator.validate("/nonexistent/executable")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(validate_chunk) for _ in range(5)]
            for future in as_completed(futures):
                results = future.result()
                assert len(results) == 20
                assert all(not r.passed for r in results)

    def test_validate_preserves_order(self):
        validator = MultiEdgeCaseValidator()
        for i in range(10):
            validator.add_test_case(f"t{i}", f"{i}\n", f"{i}\n")
        results = validator.validate("/nonexistent/executable")
        assert [r.test_id for r in results] == [f"t{i}" for i in range(10)]

    def test_edge_cases_cover_all_sorts(self):
        validator = MultiEdgeCaseValidator()
        validator.add_edge_cases("", "")
        edge_descriptions = [tc["description"] for tc in validator.test_cases]
        assert "Empty input handling" in edge_descriptions
        assert "Single element" in edge_descriptions
        assert "Two elements" in edge_descriptions
        assert "All identical elements" in edge_descriptions
        assert "Already sorted" in edge_descriptions
        assert "Reverse sorted" in edge_descriptions
        assert "Negative numbers" in edge_descriptions
        assert "Single negative number" in edge_descriptions
        assert "100 elements reverse" in edge_descriptions
        assert "Mixed zeros" in edge_descriptions


class TestValidationResultEdgeCases:
    def test_equality(self):
        tr1 = ValidationResult("t1", "in", "exp", "act", True, 1.0)
        tr2 = ValidationResult("t1", "in", "exp", "act", True, 1.0)
        tr3 = ValidationResult("t2", "in", "exp", "act", True, 1.0)
        assert tr1.to_dict() == tr2.to_dict()
        assert tr1.to_dict() != tr3.to_dict()

    def test_repr(self):
        tr = ValidationResult("t1", "input", "expected", "actual", True, 1.5)
        d = tr.to_dict()
        assert d["test_id"] == "t1"
        assert d["execution_time_ms"] == 1.5

    def test_failed_result_details(self):
        tr = ValidationResult("t1", "input", "expected", "actual_diff", False, 2.5, "mismatch")
        assert not tr.passed
        assert tr.description == "mismatch"
        assert tr.actual_output == "actual_diff"

    def test_large_execution_time(self):
        tr = ValidationResult("t1", "in", "exp", "act", True, 1e6)
        assert tr.execution_time_ms == 1e6


class TestValidatorStressTests:
    def test_many_test_cases(self):
        validator = MultiEdgeCaseValidator()
        for i in range(1000):
            validator.add_test_case(f"t{i}", f"{i}\n", f"{i}\n")
        assert len(validator.test_cases) == 1000

    def test_very_long_input(self):
        validator = MultiEdgeCaseValidator()
        long_input = " ".join(str(i) for i in range(10000)) + "\n"
        validator.add_test_case("large", long_input, long_input)
        results = validator.validate("/nonexistent/executable")
        assert results[0].input_data == long_input

    def test_many_edge_cases_sets(self):
        validator = MultiEdgeCaseValidator()
        for i in range(100):
            validator.add_edge_cases(f"{i} {i-1}\n", f"{i-1} {i}\n")
        assert len(validator.test_cases) == 1000


class TestValidatorSummaryEdgeCases:
    def test_pass_rate_precision(self):
        validator = MultiEdgeCaseValidator()
        results = [
            ValidationResult("t1", "1", "1", "1", True, 1.0),
            ValidationResult("t2", "2", "2", "3", False, 1.0),
        ]
        summary = validator.generate_summary(results)
        assert summary["pass_rate"] == 50.0

    def test_pass_rate_three_decimal(self):
        validator = MultiEdgeCaseValidator()
        results = [ValidationResult(f"t{i}", "1", "1", "1", True, 1.0) for i in range(3)]
        results.append(ValidationResult("t3", "1", "1", "2", False, 1.0))
        summary = validator.generate_summary(results)
        assert summary["pass_rate"] == pytest.approx(75.0, rel=0.01)

    def test_summary_failed_tests_detail(self):
        validator = MultiEdgeCaseValidator()
        results = [
            ValidationResult("t1", "in1", "exp1", "act1", False, 1.0, "desc1"),
            ValidationResult("t2", "in2", "exp2", "act2", True, 1.0, "desc2"),
        ]
        summary = validator.generate_summary(results)
        assert len(summary["failed_tests"]) == 1
        assert summary["failed_tests"][0]["test_id"] == "t1"
        assert summary["failed_tests"][0]["description"] == "desc1"

    def test_summary_passed_tests_detail(self):
        validator = MultiEdgeCaseValidator()
        results = [
            ValidationResult("t1", "in1", "exp1", "act1", True, 1.0, "desc1"),
            ValidationResult("t2", "in2", "exp2", "act2", False, 1.0, "desc2"),
        ]
        summary = validator.generate_summary(results)
        assert len(summary["passed_tests"]) == 1
        assert summary["passed_tests"][0]["test_id"] == "t1"