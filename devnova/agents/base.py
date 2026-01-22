"""
Base Agent - Foundation for all DEVNOVA agents

This module defines the base agent architecture that all specialized
agents inherit from. It enforces strict boundaries and provides
common functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..ide.interfaces import (
    IDEContext, Suggestion, Explanation, Risk,
    SuggestionRequest, ExplanationRequest, RiskAnalysisRequest
)
from ..state.api import ProjectStateAPI


class BaseAgent(ABC):
    """
    Base class for all DEVNOVA agents.

    All agents must inherit from this class and implement the required
    methods. This ensures consistent behavior and safety boundaries.

    READ: Only Project State API (curated facts)
    CALL: Only LLM Reasoning Layer (structured reasoning)
    OUTPUT: Structured plans/recommendations (no code changes)
    STORAGE: No memory writes, no file access, no state modifications
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.state_api: Optional[ProjectStateAPI] = None

    def set_project_context(self, project_root: str):
        """
        Set the project context for this agent.

        Args:
            project_root: Root directory of the project
        """
        self.state_api = ProjectStateAPI(project_root)

    @abstractmethod
    def get_suggestions(self, context: IDEContext, intent: str) -> List[Suggestion]:
        """
        Get suggestions for the given context and intent.

        Args:
            context: IDE context information
            intent: User's intent description

        Returns:
            List of suggestions
        """
        pass

    @abstractmethod
    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """
        Get explanations for the given code and context.

        Args:
            context: IDE context information
            code: Code to explain
            explanation_type: Type of explanation needed

        Returns:
            List of explanations
        """
        pass

    @abstractmethod
    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """
        Analyze risks in the given code and context.

        Args:
            context: IDE context information
            code: Code to analyze
            analysis_type: Type of risk analysis

        Returns:
            List of identified risks
        """
        pass

    def _get_project_facts(self):
        """Get project facts from state API."""
        if not self.state_api:
            raise RuntimeError("Project context not set. Call set_project_context() first.")
        return self.state_api.get_project_facts()

    def _call_llm_reasoning(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the LLM reasoning layer.

        Args:
            prompt: The reasoning prompt
            context: Context data for reasoning

        Returns:
            Structured reasoning result
        """
        # TODO: Implement actual LLM call
        # For now, return a mock response
        return {
            "reasoning": f"Mock reasoning for {self.agent_name}",
            "confidence": 0.8,
            "recommendations": []
        }

    def _create_suggestion(self, title: str, description: str, reasoning: str,
                          confidence: float = 0.8) -> Suggestion:
        """
        Create a standardized suggestion.

        Args:
            title: Suggestion title
            description: Detailed description
            reasoning: Reasoning behind the suggestion
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            Suggestion object
        """
        return Suggestion(
            id="",  # Will be set by orchestrator
            title=title,
            description=description,
            code_changes=[],  # Agents don't provide code changes
            confidence=confidence,
            reasoning=reasoning
        )

    def _create_explanation(self, title: str, explanation: str, key_points: List[str],
                           related_concepts: List[str], confidence: float = 0.8) -> Explanation:
        """
        Create a standardized explanation.

        Args:
            title: Explanation title
            explanation: Main explanation text
            key_points: Key points to highlight
            related_concepts: Related concepts
            confidence: Confidence score

        Returns:
            Explanation object
        """
        return Explanation(
            id="",  # Will be set by orchestrator
            title=title,
            explanation=explanation,
            key_points=key_points,
            related_concepts=related_concepts,
            confidence=confidence
        )

    def _create_risk(self, severity: str, category: str, title: str, description: str,
                    location: Dict[str, Any], suggestion: str, confidence: float = 0.8) -> Risk:
        """
        Create a standardized risk.

        Args:
            severity: Risk severity ("low", "medium", "high", "critical")
            category: Risk category
            title: Risk title
            description: Risk description
            location: Location information
            suggestion: Suggested fix
            confidence: Confidence score

        Returns:
            Risk object
        """
        return Risk(
            id="",  # Will be set by orchestrator
            severity=severity,
            category=category,
            title=title,
            description=description,
            location=location,
            suggestion=suggestion,
            confidence=confidence
        )