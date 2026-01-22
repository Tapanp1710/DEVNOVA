"""
Test Agent - Test coverage analysis and strategy recommendations

This agent specializes in analyzing test coverage, identifying gaps,
and recommending testing strategies.
"""

from typing import List, Dict, Any
from ..ide.interfaces import IDEContext, Suggestion, Explanation, Risk
from .base import BaseAgent


class TestAgent(BaseAgent):
    """
    Test Agent for test coverage analysis and strategy.

    Purpose: Analyzes test coverage and suggests test strategies
    Input: Code structure + current testing status
    Output: Coverage gaps, test strategies, priorities, scenarios
    """

    def __init__(self):
        super().__init__("test")

    def get_suggestions(self, context: IDEContext, intent: str) -> List[Suggestion]:
        """Get testing suggestions."""
        suggestions = []

        if "test" in intent.lower() or "coverage" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Implement Unit Tests",
                "Add unit tests for individual functions and methods.",
                "Unit tests verify the smallest units of code work correctly in isolation.",
                0.9
            ))

            suggestions.append(self._create_suggestion(
                "Add Integration Tests",
                "Create integration tests to verify component interactions.",
                "Integration tests ensure different parts of the system work together correctly.",
                0.8
            ))

            suggestions.append(self._create_suggestion(
                "Use Test-Driven Development",
                "Write tests before implementing features (TDD).",
                "TDD ensures code is testable and requirements are clear from the start.",
                0.8
            ))

        if "function" in intent.lower() or "method" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Test Edge Cases",
                "Write tests for edge cases and boundary conditions.",
                "Edge case testing catches bugs that occur with unusual inputs or conditions.",
                0.8
            ))

        return suggestions

    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """Get testing explanations."""
        explanations = []

        if "def test_" in code or "test_" in code:
            explanations.append(self._create_explanation(
                "Test Function",
                "This is a test function that verifies code behavior.",
                [
                    "Test functions validate that code works as expected",
                    "They help catch regressions when code changes",
                    "Good tests serve as documentation of expected behavior"
                ],
                ["Unit testing", "Test automation", "Regression testing"],
                0.9
            ))

        if "assert" in code:
            explanations.append(self._create_explanation(
                "Assertion in Testing",
                "Assertions check that conditions are true during test execution.",
                [
                    "Failed assertions indicate test failures",
                    "Assertions document expected outcomes",
                    "They provide specific failure messages for debugging"
                ],
                ["Test assertions", "Verification", "Test oracles"],
                0.8
            ))

        return explanations

    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """Analyze testing-related risks."""
        risks = []

        # Check for functions without tests
        facts = self._get_project_facts()
        test_files = [f for f in facts.files if 'test' in f.path.lower()]
        source_files = [f for f in facts.files if 'test' not in f.path.lower() and f.language == 'python']

        if len(test_files) < len(source_files) * 0.5:  # Less than 50% test coverage by file count
            risks.append(self._create_risk(
                "medium",
                "reliability",
                "Low Test Coverage",
                f"Only {len(test_files)} test files for {len(source_files)} source files.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Aim for at least 1 test file per source file, with multiple tests per function.",
                0.7
            ))

        # Check for untested functions in current file
        if "def " in code and not self._has_corresponding_test(context.file_path):
            risks.append(self._create_risk(
                "low",
                "reliability",
                "Untested Function",
                "This function appears to lack corresponding tests.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Add unit tests to verify this function's behavior and catch regressions.",
                0.6
            ))

        # Check for magic numbers in tests
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if 'assert' in line and any(char.isdigit() for char in line):
                # Simple check for numbers in assertions
                if sum(c.isdigit() for c in line) > 2:  # More than 2 digits
                    risks.append(self._create_risk(
                        "low",
                        "maintainability",
                        "Magic Numbers in Tests",
                        "Test contains unexplained numeric literals.",
                        {"file": context.file_path, "line": i + 1},
                        "Use named constants or variables to make test intentions clear.",
                        0.5
                    ))
                    break

        return risks

    def _has_corresponding_test(self, source_file: str) -> bool:
        """Check if a source file has corresponding tests."""
        # Simple heuristic: look for test files with similar names
        import os
        base_name = os.path.basename(source_file).replace('.py', '')
        test_name = f"test_{base_name}.py"

        facts = self._get_project_facts()
        test_files = [f for f in facts.files if test_name in f.path]
        return len(test_files) > 0