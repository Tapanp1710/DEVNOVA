"""
Architect Agent - Architecture analysis and recommendations

This agent specializes in analyzing project architecture, suggesting
structural improvements, and providing architectural guidance.
"""

from typing import List, Dict, Any
from ..ide.interfaces import IDEContext, Suggestion, Explanation, Risk
from .base import BaseAgent


class ArchitectAgent(BaseAgent):
    """
    Architect Agent for architecture analysis and recommendations.

    Purpose: Analyzes project architecture and suggests structural improvements
    Input: Architecture facts (files, functions, classes, dependencies)
    Output: Analysis, recommendations, priority areas, risks
    """

    def __init__(self):
        super().__init__("architect")

    def get_suggestions(self, context: IDEContext, intent: str) -> List[Suggestion]:
        """Get architecture-related suggestions."""
        suggestions = []

        # Analyze current file structure
        facts = self._get_project_facts()

        # Check for common architectural issues
        if len(facts.files) > 50:
            suggestions.append(self._create_suggestion(
                "Consider Modular Architecture",
                "Large codebase detected. Consider breaking into modules/packages for better maintainability.",
                "Projects with many files benefit from modular organization to reduce complexity and improve maintainability.",
                0.9
            ))

        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(facts.dependencies)
        if circular_deps:
            suggestions.append(self._create_suggestion(
                "Resolve Circular Dependencies",
                f"Found circular dependencies: {', '.join(circular_deps[:3])}",
                "Circular dependencies make code harder to test and maintain. Consider introducing interfaces or dependency injection.",
                0.8
            ))

        # Check for large files
        large_files = [f for f in facts.files if f.size > 10000]  # > 10KB
        if large_files:
            suggestions.append(self._create_suggestion(
                "Refactor Large Files",
                f"Found {len(large_files)} large files that may need refactoring.",
                "Large files are harder to understand and maintain. Consider splitting into smaller, focused modules.",
                0.7
            ))

        return suggestions

    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """Get architecture-related explanations."""
        explanations = []

        if "class" in code.lower() or "def " in code:
            explanations.append(self._create_explanation(
                "Code Structure Analysis",
                "This code defines a structural element of your application architecture.",
                [
                    "Classes define data structures and behavior",
                    "Functions implement specific functionality",
                    "Modules organize related code together"
                ],
                ["Object-oriented design", "Modular programming", "Separation of concerns"],
                0.9
            ))

        return explanations

    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """Analyze architectural risks."""
        risks = []

        # Check for tight coupling
        if "import *" in code:
            risks.append(self._create_risk(
                "medium",
                "maintainability",
                "Wildcard Import Detected",
                "Using 'import *' creates tight coupling and makes dependencies unclear.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Use explicit imports instead of wildcard imports.",
                0.8
            ))

        # Check for long functions (potential complexity)
        lines = code.split('\n')
        if len(lines) > 50:
            risks.append(self._create_risk(
                "low",
                "maintainability",
                "Long Function Detected",
                f"Function is {len(lines)} lines long, which may indicate high complexity.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Consider breaking this function into smaller, focused functions.",
                0.6
            ))

        return risks

    def _detect_circular_dependencies(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """Detect circular dependencies in the dependency graph."""
        # Simple circular dependency detection
        circular = []
        for module, deps in dependencies.items():
            for dep in deps:
                if dep in dependencies and module in dependencies.get(dep, []):
                    circular.append(f"{module} ↔ {dep}")
        return list(set(circular))  # Remove duplicates