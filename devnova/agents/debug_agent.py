"""
Debug Agent - Bug analysis and fix recommendations

This agent specializes in analyzing bugs, understanding error patterns,
and suggesting fixes based on code analysis.
"""

from typing import List, Dict, Any
from ..ide.interfaces import IDEContext, Suggestion, Explanation, Risk
from .base import BaseAgent


class DebugAgent(BaseAgent):
    """
    Debug Agent for bug analysis and fix recommendations.

    Purpose: Analyzes bugs and suggests fixes using code facts
    Input: Code facts + error information
    Output: Root cause analysis, fix suggestions, testing recommendations
    """

    def __init__(self):
        super().__init__("debug")

    def get_suggestions(self, context: IDEContext, intent: str) -> List[Suggestion]:
        """Get debugging suggestions."""
        suggestions = []

        if "error" in intent.lower() or "bug" in intent.lower() or "fix" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Add Error Handling",
                "Consider adding try-except blocks around error-prone operations.",
                "Proper error handling prevents crashes and provides better debugging information.",
                0.8
            ))

            suggestions.append(self._create_suggestion(
                "Add Logging",
                "Add logging statements to track execution flow and variable values.",
                "Logging helps identify where issues occur and what the state is at each step.",
                0.9
            ))

            suggestions.append(self._create_suggestion(
                "Use Debugger",
                "Use a debugger to step through the code and inspect variables.",
                "Interactive debugging allows you to see exactly what happens at each step.",
                0.8
            ))

        if "performance" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Profile Code Execution",
                "Use a profiler to identify performance bottlenecks.",
                "Profiling shows which parts of code consume the most time and resources.",
                0.8
            ))

        return suggestions

    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """Get debugging explanations."""
        explanations = []

        if "try:" in code or "except" in code:
            explanations.append(self._create_explanation(
                "Error Handling Pattern",
                "This code implements error handling to gracefully manage exceptions.",
                [
                    "try block contains code that might raise exceptions",
                    "except blocks catch and handle specific exception types",
                    "finally blocks execute cleanup code regardless of exceptions"
                ],
                ["Exception handling", "Error propagation", "Resource cleanup"],
                0.9
            ))

        if "assert" in code:
            explanations.append(self._create_explanation(
                "Assertion for Debugging",
                "Assertions check conditions that should always be true during development.",
                [
                    "Assertions help catch bugs early in development",
                    "They can be disabled in production for performance",
                    "Failed assertions provide immediate feedback"
                ],
                ["Defensive programming", "Contract programming", "Debugging techniques"],
                0.8
            ))

        return explanations

    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """Analyze debugging-related risks."""
        risks = []

        # Check for bare except clauses
        if "except:" in code and "Exception" not in code:
            risks.append(self._create_risk(
                "high",
                "reliability",
                "Bare Except Clause",
                "Bare 'except:' clauses catch all exceptions, including system exits and keyboard interrupts.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Specify exception types explicitly (e.g., 'except ValueError:' or 'except Exception:').",
                0.9
            ))

        # Check for print statements instead of logging
        if "print(" in code and "import logging" not in code:
            risks.append(self._create_risk(
                "low",
                "maintainability",
                "Print Statements for Debugging",
                "Using print() for debugging instead of proper logging.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Use the logging module for better debugging and production monitoring.",
                0.6
            ))

        # Check for potential infinite loops
        if "while True:" in code and "break" not in code:
            risks.append(self._create_risk(
                "high",
                "reliability",
                "Potential Infinite Loop",
                "While loop without break condition may run indefinitely.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Ensure loops have proper exit conditions or use timeouts.",
                0.8
            ))

        # Check for None comparisons
        if "== None" in code:
            risks.append(self._create_risk(
                "low",
                "reliability",
                "None Comparison",
                "Using '== None' instead of 'is None' can cause issues with custom __eq__ methods.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Use 'is None' or 'is not None' for None comparisons.",
                0.7
            ))

        return risks