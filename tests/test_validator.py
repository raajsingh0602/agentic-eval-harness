"""Tests for the Multi-Edge-Case Test Validator."""

import os
import sys
import pytest

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
