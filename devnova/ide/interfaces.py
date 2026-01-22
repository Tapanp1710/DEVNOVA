"""
IDE Integration Interfaces

This module defines the interfaces for IDE integration, providing
a clean boundary between DEVNOVA's reasoning capabilities and
external IDE/editor systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


class IDEContext(BaseModel):
    """Context information from the IDE."""
    file_path: str
    cursor_position: Dict[str, int]  # {"line": int, "column": int}
    selected_text: Optional[str] = None
    visible_range: Optional[Dict[str, int]] = None  # {"start": int, "end": int}
    project_root: str
    language: str


class SuggestionRequest(BaseModel):
    """Request for code suggestions."""
    context: IDEContext
    intent: str  # User's intent/description of what they want
    max_suggestions: int = 5


class Suggestion(BaseModel):
    """A code suggestion."""
    id: str
    title: str
    description: str
    code_changes: List[Dict[str, Any]]  # [{"file": str, "line": int, "old_code": str, "new_code": str}]
    confidence: float
    reasoning: str


class SuggestionResponse(BaseModel):
    """Response containing suggestions."""
    request_id: str
    suggestions: List[Suggestion]
    generated_at: datetime


class ExplanationRequest(BaseModel):
    """Request for code explanation."""
    context: IDEContext
    code_to_explain: str
    explanation_type: str = "general"  # "general", "bug", "performance", "security"


class Explanation(BaseModel):
    """A code explanation."""
    id: str
    title: str
    explanation: str
    key_points: List[str]
    related_concepts: List[str]
    confidence: float


class ExplanationResponse(BaseModel):
    """Response containing explanations."""
    request_id: str
    explanations: List[Explanation]
    generated_at: datetime


class RiskAnalysisRequest(BaseModel):
    """Request for risk analysis."""
    context: IDEContext
    code_to_analyze: str
    analysis_type: str = "general"  # "security", "performance", "maintainability"


class Risk(BaseModel):
    """A identified risk."""
    id: str
    severity: str  # "low", "medium", "high", "critical"
    category: str  # "security", "performance", "maintainability", "reliability"
    title: str
    description: str
    location: Dict[str, Any]  # {"file": str, "line": int, "column": int}
    suggestion: str
    confidence: float


class RiskAnalysisResponse(BaseModel):
    """Response containing risk analysis."""
    request_id: str
    risks: List[Risk]
    overall_score: float  # 0.0 to 1.0, higher is riskier
    generated_at: datetime


class DEVNovaInterface(ABC):
    """
    Abstract interface for DEVNOVA IDE integration.

    This defines the contract that IDEs/editors must implement to
    communicate with DEVNOVA's reasoning capabilities.
    """

    @abstractmethod
    def get_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """
        Get code suggestions based on context and intent.

        Args:
            request: The suggestion request with context and intent

        Returns:
            SuggestionResponse: Structured suggestions with reasoning
        """
        pass

    @abstractmethod
    def get_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """
        Get explanation for code based on context.

        Args:
            request: The explanation request with code and context

        Returns:
            ExplanationResponse: Structured explanations
        """
        pass

    @abstractmethod
    def analyze_risks(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """
        Analyze code for potential risks.

        Args:
            request: The risk analysis request

        Returns:
            RiskAnalysisResponse: Identified risks with severity
        """
        pass


class DEVNovaClient(DEVNovaInterface):
    """
    Client implementation for DEVNOVA integration.

    This provides the actual implementation that connects to DEVNOVA's
    reasoning agents and orchestrator.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        # Initialize connections to DEVNOVA subsystems
        from ..state.api import ProjectStateAPI
        from ..orchestrator.orchestrator import Orchestrator

        self.state_api = ProjectStateAPI(project_root)
        self.orchestrator = Orchestrator()
        self.orchestrator.set_project_context(project_root)

    def get_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Get suggestions from DEVNOVA agents."""
        # Use orchestrator to coordinate agent responses
        suggestions = self.orchestrator.get_suggestions(
            context=request.context,
            intent=request.intent,
            max_suggestions=request.max_suggestions
        )

        return SuggestionResponse(
            request_id=f"req_{datetime.now().isoformat()}",
            suggestions=suggestions,
            generated_at=datetime.now()
        )

    def get_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Get explanations from DEVNOVA agents."""
        explanations = self.orchestrator.get_explanations(
            context=request.context,
            code=request.code_to_explain,
            explanation_type=request.explanation_type
        )

        return ExplanationResponse(
            request_id=f"req_{datetime.now().isoformat()}",
            explanations=explanations,
            generated_at=datetime.now()
        )

    def analyze_risks(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """Analyze risks using DEVNOVA agents."""
        risks = self.orchestrator.analyze_risks(
            context=request.context,
            code=request.code_to_analyze,
            analysis_type=request.analysis_type
        )

        # Calculate overall risk score
        if risks:
            overall_score = sum(r.confidence for r in risks) / len(risks)
        else:
            overall_score = 0.0

        return RiskAnalysisResponse(
            request_id=f"req_{datetime.now().isoformat()}",
            risks=risks,
            overall_score=overall_score,
            generated_at=datetime.now()
        )


class MockDEVINOVAIntegration(DEVNovaInterface):
    """
    Mock implementation for testing and development.

    This provides predictable responses for testing the integration
    without requiring the full DEVNOVA system.
    """

    def get_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Return mock suggestions."""
        suggestions = [
            Suggestion(
                id="mock_sugg_1",
                title="Add Error Handling",
                description="Consider adding try-except blocks around operations that might fail.",
                code_changes=[],
                confidence=0.8,
                reasoning="Error handling improves code reliability and debugging."
            )
        ]

        return SuggestionResponse(
            request_id=f"mock_{datetime.now().isoformat()}",
            suggestions=suggestions,
            generated_at=datetime.now()
        )

    def get_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Return mock explanations."""
        explanations = [
            Explanation(
                id="mock_expl_1",
                title="Code Structure Analysis",
                explanation="This code defines a function that performs a specific operation.",
                key_points=["Function definition", "Parameter handling", "Return values"],
                related_concepts=["Functions", "Parameters", "Return statements"],
                confidence=0.9
            )
        ]

        return ExplanationResponse(
            request_id=f"mock_{datetime.now().isoformat()}",
            explanations=explanations,
            generated_at=datetime.now()
        )

    def analyze_risks(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """Return mock risk analysis."""
        risks = [
            Risk(
                id="mock_risk_1",
                severity="low",
                category="maintainability",
                title="Consider Adding Docstrings",
                description="Functions without docstrings are harder to understand and maintain.",
                location={"file": request.context.file_path, "line": 1},
                suggestion="Add a docstring explaining what this function does.",
                confidence=0.7
            )
        ]

        return RiskAnalysisResponse(
            request_id=f"mock_{datetime.now().isoformat()}",
            risks=risks,
            overall_score=0.3,
            generated_at=datetime.now()
        )


def create_devnova_integration(project_root: str) -> DEVNovaInterface:
    """
    Factory function to create DEVNOVA integration.

    Args:
        project_root: Root directory of the project

    Returns:
        DEVNovaInterface: Integration instance (real or mock)
    """
    try:
        # Try to create real integration
        return DEVNovaClient(project_root)
    except Exception as e:
        print(f"Warning: Could not create real DEVNOVA integration: {e}")
        print("Falling back to mock integration for testing.")
        # Fall back to mock integration
        return MockDEVINOVAIntegration()