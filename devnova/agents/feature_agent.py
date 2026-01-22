"""
Feature Agent - Feature planning and implementation strategy

This agent specializes in planning feature implementation and
assessing development complexity.
"""

from typing import List, Dict, Any
from ..ide.interfaces import IDEContext, Suggestion, Explanation, Risk
from .base import BaseAgent


class FeatureAgent(BaseAgent):
    """
    Feature Agent for feature planning and implementation.

    Purpose: Plans feature implementation and assesses complexity
    Input: Project facts + feature requirements
    Output: Implementation plans, dependencies, complexity assessment
    """

    def __init__(self):
        super().__init__("feature")

    def get_suggestions(self, context: IDEContext, intent: str) -> List[Suggestion]:
        """Get feature implementation suggestions."""
        suggestions = []

        # Analyze intent for feature development patterns
        if "add" in intent.lower() or "implement" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Follow TDD Approach",
                "Consider implementing this feature using Test-Driven Development.",
                "TDD ensures features are well-tested and reduces bugs. Write tests first, then implement.",
                0.8
            ))

            suggestions.append(self._create_suggestion(
                "Plan Integration Points",
                "Identify how this feature integrates with existing code.",
                "Consider dependencies, interfaces, and potential breaking changes before implementation.",
                0.9
            ))

        if "api" in intent.lower() or "endpoint" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Design RESTful API",
                "Follow REST principles for API design.",
                "Use appropriate HTTP methods, status codes, and resource naming conventions.",
                0.8
            ))

        return suggestions

    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """Get feature-related explanations."""
        explanations = []

        if "def " in code and ("api" in code.lower() or "endpoint" in code.lower()):
            explanations.append(self._create_explanation(
                "API Endpoint Implementation",
                "This function implements an API endpoint for external communication.",
                [
                    "Handles HTTP requests and responses",
                    "May include validation and error handling",
                    "Connects frontend to backend logic"
                ],
                ["REST API", "HTTP methods", "Request/response cycle"],
                0.9
            ))

        return explanations

    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """Analyze feature implementation risks."""
        risks = []

        # Check for feature flags or conditional logic
        if "if " in code.lower() and ("feature" in code.lower() or "flag" in code.lower()):
            risks.append(self._create_risk(
                "low",
                "maintainability",
                "Feature Flag Detected",
                "Feature flags can accumulate technical debt if not cleaned up.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Plan to remove feature flags after feature stabilization.",
                0.5
            ))

        # Check for hardcoded values
        if "http://localhost" in code or "127.0.0.1" in code:
            risks.append(self._create_risk(
                "medium",
                "reliability",
                "Hardcoded Localhost URL",
                "Hardcoded localhost URLs will break in production environments.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Use environment variables or configuration for URLs.",
                0.8
            ))

        return risks