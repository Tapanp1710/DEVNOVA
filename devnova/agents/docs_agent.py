"""
Docs Agent - Documentation generation and analysis

This agent specializes in analyzing documentation needs,
suggesting improvements, and generating documentation.
"""

from typing import List, Dict, Any
from ..ide.interfaces import IDEContext, Suggestion, Explanation, Risk
from .base import BaseAgent


class DocsAgent(BaseAgent):
    """
    Docs Agent for documentation generation and analysis.

    Purpose: Analyzes documentation and suggests improvements
    Input: Code structure and existing documentation
    Output: Documentation recommendations, generation suggestions
    """

    def __init__(self):
        super().__init__("docs")

    def get_suggestions(self, context: IDEContext, intent: str) -> List[Suggestion]:
        """Get documentation suggestions."""
        suggestions = []

        if "doc" in intent.lower() or "document" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Add Docstrings",
                "Add comprehensive docstrings to all public functions and classes.",
                "Docstrings serve as inline documentation and can be used by documentation tools.",
                0.9
            ))

            suggestions.append(self._create_suggestion(
                "Use Type Hints",
                "Add type hints to function parameters and return values.",
                "Type hints improve code readability and enable better IDE support and documentation.",
                0.8
            ))

            suggestions.append(self._create_suggestion(
                "Create README",
                "Create a comprehensive README.md file for the project.",
                "README files help others understand and contribute to the project.",
                0.8
            ))

        if "function" in intent.lower() or "method" in intent.lower():
            suggestions.append(self._create_suggestion(
                "Document Parameters and Returns",
                "Document all parameters, their types, and return values.",
                "Clear parameter documentation helps users understand how to use the function correctly.",
                0.8
            ))

        return suggestions

    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """Get documentation explanations."""
        explanations = []

        if '"""' in code or "'''" in code:
            explanations.append(self._create_explanation(
                "Docstring Documentation",
                "This is a docstring that documents the code element.",
                [
                    "Docstrings explain what the code does",
                    "They can include parameter descriptions and examples",
                    "Tools like Sphinx can generate documentation from docstrings"
                ],
                ["Documentation", "Docstrings", "API documentation"],
                0.9
            ))

        if "def " in code and ":" in code:
            # Check for type hints
            if "->" in code or ":" in code.split("def ")[1].split("(")[1]:
                explanations.append(self._create_explanation(
                    "Type Hints",
                    "Type hints specify the expected types of parameters and return values.",
                    [
                        "Help catch type-related bugs",
                        "Improve IDE support and autocomplete",
                        "Serve as inline documentation"
                    ],
                    ["Type annotations", "Static typing", "PEP 484"],
                    0.8
                ))

        return explanations

    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """Analyze documentation-related risks."""
        risks = []

        # Check for functions without docstrings
        if "def " in code:
            lines = code.split('\n')
            func_line_idx = next((i for i, line in enumerate(lines) if "def " in line), -1)
            if func_line_idx >= 0:
                # Check next few lines for docstring
                has_docstring = False
                for i in range(func_line_idx + 1, min(func_line_idx + 4, len(lines))):
                    line = lines[i].strip()
                    if '"""' in line or "'''" in line:
                        has_docstring = True
                        break

                if not has_docstring:
                    risks.append(self._create_risk(
                        "low",
                        "maintainability",
                        "Missing Docstring",
                        "Function lacks a docstring for documentation.",
                        {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                        "Add a docstring describing what the function does, its parameters, and return value.",
                        0.6
                    ))

        # Check for undocumented parameters
        if "def " in code and "(" in code:
            # Simple check for parameters without type hints
            if ":" not in code.split("(")[1].split(")")[0] and "self" not in code:
                risks.append(self._create_risk(
                    "low",
                    "maintainability",
                    "Missing Type Hints",
                    "Function parameters lack type hints.",
                    {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                    "Add type hints to parameters and return values for better documentation and IDE support.",
                    0.5
                ))

        # Check for TODO comments (documentation debt)
        if "TODO" in code.upper() or "FIXME" in code.upper():
            risks.append(self._create_risk(
                "low",
                "maintainability",
                "Documentation Debt",
                "TODO/FIXME comments indicate incomplete documentation or code.",
                {"file": context.file_path, "line": context.cursor_position.get("line", 0)},
                "Address TODO items and update documentation accordingly.",
                0.4
            ))

        return risks