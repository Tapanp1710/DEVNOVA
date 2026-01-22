# devnova/ide/interfaces.py
"""
IDE Integration Interfaces

Defines clear contracts for IDE integration with DEVNOVA.
These are PLACEHOLDER INTERFACES - no actual VS Code extension implementation.

PURPOSE:
- Define integration points for future IDE extensions
- Specify data contracts between IDE and DEVNOVA
- Enable development of IDE plugins without coupling to specific IDE

BOUNDARIES:
- NO UI logic or rendering
- NO IDE-specific code (VS Code, IntelliJ, etc.)
- NO actual extension implementation
- Pure interface definitions and data contracts
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
from datetime import datetime


# ============================================================================
# DATA CONTRACTS
# ============================================================================

@dataclass
class IDEContext:
    """
    Context information from the IDE environment.

    This represents what the IDE knows about the current state:
    - Open files, cursor position, selection
    - Project structure, active workspace
    - User actions, recent changes
    """
    workspace_path: str
    active_file: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None  # {"line": int, "column": int}
    selected_text: Optional[str] = None
    open_files: List[str] = None
    recent_actions: List[Dict[str, Any]] = None  # [{"action": str, "timestamp": datetime, "details": dict}]
    project_metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.open_files is None:
            self.open_files = []
        if self.recent_actions is None:
            self.recent_actions = []


@dataclass
class SuggestionRequest:
    """
    Request for AI-powered suggestions from DEVNOVA.

    IDE asks DEVNOVA for intelligent suggestions based on current context.
    """
    context: IDEContext
    suggestion_type: str  # "completion", "refactor", "test", "docs", "debug", "architect"
    user_query: Optional[str] = None  # Natural language query from user
    code_context: Optional[str] = None  # Surrounding code for context
    metadata: Optional[Dict[str, Any]] = None  # Additional IDE-specific data


@dataclass
class SuggestionResponse:
    """
    Response containing AI-powered suggestions.

    DEVNOVA provides structured suggestions back to the IDE.
    """
    request_id: str
    suggestions: List[Dict[str, Any]]  # [{"type": str, "content": str, "confidence": float, "metadata": dict}]
    reasoning: str  # Explanation of how suggestions were generated
    processing_time: float
    agent_used: str  # Which agent provided the suggestions
    confidence: float  # Overall confidence in suggestions (0.0-1.0)
    warnings: List[str] = None  # Any warnings or limitations

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class ExplanationRequest:
    """
    Request for detailed explanations of code or suggestions.

    IDE asks DEVNOVA to explain code behavior, architecture, or suggestions.
    """
    context: IDEContext
    explanation_type: str  # "code_explanation", "architecture", "suggestion_rationale", "bug_analysis"
    target_code: Optional[str] = None  # Code to explain
    target_file: Optional[str] = None  # File containing code to explain
    user_question: Optional[str] = None  # Specific question about the code
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExplanationResponse:
    """
    Detailed explanation response from DEVNOVA.

    Provides comprehensive understanding of code, architecture, or suggestions.
    """
    request_id: str
    explanation: str  # Detailed explanation text
    processing_time: float
    agent_used: str
    confidence: float
    code_references: List[Dict[str, Any]] = None  # [{"file": str, "line": int, "code": str, "explanation": str}]
    related_concepts: List[str] = None  # Related programming concepts or patterns
    warnings: List[str] = None

    def __post_init__(self):
        if self.code_references is None:
            self.code_references = []
        if self.related_concepts is None:
            self.related_concepts = []
        if self.warnings is None:
            self.warnings = []


# ============================================================================
# INTERFACE DEFINITIONS
# ============================================================================

class IDEIntegrationInterface(Protocol):
    """
    Main interface that IDE extensions must implement.

    This defines how an IDE extension communicates with DEVNOVA.
    IDE extensions implement this interface to integrate with DEVNOVA.
    """

    @abstractmethod
    def load_context(self) -> IDEContext:
        """
        Load current IDE context.

        Returns information about:
        - Current workspace and open files
        - Cursor position and selection
        - Recent user actions
        - Project metadata
        """
        pass

    @abstractmethod
    def request_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """
        Request AI-powered suggestions from DEVNOVA.

        Args:
            request: Structured request containing context and requirements

        Returns:
            Structured response with suggestions and reasoning
        """
        pass

    @abstractmethod
    def request_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """
        Request detailed explanations from DEVNOVA.

        Args:
            request: Structured request for explanation

        Returns:
            Detailed explanation with code references
        """
        pass

    @abstractmethod
    def validate_context(self, context: IDEContext) -> Dict[str, Any]:
        """
        Validate that the provided context is suitable for DEVNOVA processing.

        Returns:
            {"valid": bool, "issues": [str], "recommendations": [str]}
        """
        pass


class DEVINOVAIntegrationInterface(Protocol):
    """
    Interface that DEVNOVA exposes to IDE extensions.

    This defines what services DEVNOVA provides to IDE integrations.
    IDE extensions call these methods to leverage DEVNOVA capabilities.
    """

    @abstractmethod
    def initialize_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """
        Initialize DEVNOVA for a workspace.

        This triggers:
        - Project ingestion
        - Static analysis
        - Memory population
        - State initialization

        Returns:
            {"success": bool, "stats": dict, "errors": [str]}
        """
        pass

    @abstractmethod
    def get_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """
        Generate AI-powered suggestions based on IDE context.

        Routes to appropriate agents via orchestrator.
        """
        pass

    @abstractmethod
    def get_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """
        Provide detailed explanations of code or architecture.

        Routes to appropriate agents for analysis.
        """
        pass

    @abstractmethod
    def get_workspace_status(self, workspace_path: str) -> Dict[str, Any]:
        """
        Get current status of DEVNOVA for the workspace.

        Returns:
            {
                "initialized": bool,
                "last_updated": datetime,
                "stats": {"files": int, "functions": int, "classes": int},
                "capabilities": [str]
            }
        """
        pass

    @abstractmethod
    def refresh_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """
        Refresh DEVNOVA knowledge for the workspace.

        Re-runs ingestion and analysis for updated files.
        """
        pass


# ============================================================================
# PLACEHOLDER IMPLEMENTATIONS
# ============================================================================

class MockIDEIntegration(IDEIntegrationInterface):
    """
    Mock implementation of IDE integration for testing.

    This simulates how a real IDE extension would work.
    Used for testing the interface contracts.
    """

    def __init__(self, workspace_path: str = "D:\\\\DEVNOVA\\\\devnova"):
        self.workspace_path = workspace_path

    def load_context(self) -> IDEContext:
        """Mock context loading."""
        return IDEContext(
            workspace_path=self.workspace_path,
            active_file="devnova/state/api.py",
            cursor_position={"line": 42, "column": 8},
            selected_text="def get_architecture_facts(self):",
            open_files=["devnova/state/api.py", "devnova/llm/interface.py"],
            recent_actions=[
                {"action": "file_opened", "timestamp": datetime.now(), "details": {"file": "devnova/state/api.py"}},
                {"action": "cursor_moved", "timestamp": datetime.now(), "details": {"line": 42, "column": 8}}
            ]
        )

    def request_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Mock suggestion request - would call DEVNOVA in real implementation."""
        # This would actually call DEVNOVA's get_suggestions method
        return SuggestionResponse(
            request_id=f"mock_{int(datetime.now().timestamp())}",
            suggestions=[
                {
                    "type": "refactor",
                    "content": "Consider extracting this method to improve readability",
                    "confidence": 0.85,
                    "metadata": {"estimated_effort": "low", "impact": "maintainability"}
                }
            ],
            reasoning="Based on code analysis and architectural patterns",
            confidence=0.8,
            processing_time=0.15,
            agent_used="ArchitectAgent",
            warnings=["This is a mock response for testing"]
        )

    def request_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Mock explanation request - would call DEVNOVA in real implementation."""
        return ExplanationResponse(
            request_id=f"mock_{int(datetime.now().timestamp())}",
            explanation="This method retrieves architectural facts from the project state, providing a high-level overview of the codebase structure.",
            code_references=[
                {
                    "file": "devnova/state/api.py",
                    "line": 42,
                    "code": "def get_architecture_facts(self):",
                    "explanation": "Main entry point for architecture queries"
                }
            ],
            related_concepts=["Project State", "Architecture Analysis", "Code Metrics"],
            confidence=0.9,
            processing_time=0.12,
            agent_used="ArchitectAgent",
            warnings=["This is a mock response for testing"]
        )

    def validate_context(self, context: IDEContext) -> Dict[str, Any]:
        """Mock context validation."""
        issues = []
        recommendations = []

        if not context.workspace_path:
            issues.append("No workspace path provided")

        if not context.active_file:
            recommendations.append("Consider providing active file context for better suggestions")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations
        }


class MockDEVINOVAIntegration(DEVINOVAIntegrationInterface):
    """
    Mock implementation of DEVNOVA integration for testing.

    This simulates DEVNOVA services that would be called by IDE extensions.
    """

    def __init__(self):
        self.initialized_workspaces = set()

    def initialize_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """Mock workspace initialization."""
        self.initialized_workspaces.add(workspace_path)
        return {
            "success": True,
            "stats": {"files": 17, "functions": 76, "classes": 28},
            "errors": []
        }

    def get_suggestions(self, request: SuggestionRequest) -> SuggestionResponse:
        """Mock suggestions - would route to orchestrator in real implementation."""
        return SuggestionResponse(
            request_id=f"devnova_{int(datetime.now().timestamp())}",
            suggestions=[
                {
                    "type": request.suggestion_type,
                    "content": f"Mock suggestion for {request.suggestion_type}",
                    "confidence": 0.75,
                    "metadata": {"source": "mock_devnova"}
                }
            ],
            reasoning="Generated via DEVNOVA orchestrator and agents",
            confidence=0.8,
            processing_time=0.2,
            agent_used="MockAgent"
        )

    def get_explanation(self, request: ExplanationRequest) -> ExplanationResponse:
        """Mock explanations - would route to agents in real implementation."""
        return ExplanationResponse(
            request_id=f"devnova_{int(datetime.now().timestamp())}",
            explanation=f"Mock explanation for {request.explanation_type}",
            confidence=0.85,
            processing_time=0.15,
            agent_used="MockAgent"
        )

    def get_workspace_status(self, workspace_path: str) -> Dict[str, Any]:
        """Mock workspace status."""
        return {
            "initialized": workspace_path in self.initialized_workspaces,
            "last_updated": datetime.now(),
            "stats": {"files": 17, "functions": 76, "classes": 28},
            "capabilities": ["architect", "feature", "debug", "test", "docs"]
        }

    def refresh_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """Mock workspace refresh."""
        return {
            "success": True,
            "refreshed_files": 3,
            "processing_time": 0.5
        }


# ============================================================================
# INTEGRATION UTILITIES
# ============================================================================

def create_ide_integration(ide_type: str = "mock") -> IDEIntegrationInterface:
    """
    Factory function to create IDE integration instances.

    Args:
        ide_type: Type of IDE integration ("vscode", "intellij", "mock", etc.)

    Returns:
        IDE integration instance
    """
    if ide_type == "mock":
        return MockIDEIntegration()
    else:
        # Future: implement real IDE integrations
        raise NotImplementedError(f"IDE integration for {ide_type} not implemented yet")


def create_devnova_integration() -> DEVINOVAIntegrationInterface:
    """
    Factory function to create DEVNOVA integration instances.

    Returns:
        DEVNOVA integration instance
    """
    # In real implementation, this would return the actual DEVNOVA service
    return MockDEVINOVAIntegration()


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_ide_integration_workflow():
    """
    Example workflow showing how IDE integration would work.

    This demonstrates the interface contracts without implementing actual IDE code.
    """

    # Step 1: IDE extension loads context
    ide = create_ide_integration("mock")
    context = ide.load_context()

    # Step 2: Validate context is suitable
    validation = ide.validate_context(context)
    if not validation["valid"]:
        print(f"Context issues: {validation['issues']}")
        return

    # Step 3: Request suggestions from DEVNOVA
    suggestion_request = SuggestionRequest(
        context=context,
        suggestion_type="refactor",
        user_query="How can I improve this code?"
    )

    suggestion_response = ide.request_suggestions(suggestion_request)

    # Step 4: Display suggestions in IDE (would be handled by IDE extension)
    print(f"Suggestions: {len(suggestion_response.suggestions)}")
    print(f"Confidence: {suggestion_response.confidence}")
    print(f"Agent used: {suggestion_response.agent_used}")

    # Step 5: Request explanation if needed
    explanation_request = ExplanationRequest(
        context=context,
        explanation_type="code_explanation",
        target_code="def get_architecture_facts(self):"
    )

    explanation_response = ide.request_explanation(explanation_request)

    print(f"Explanation: {explanation_response.explanation[:100]}...")


if __name__ == "__main__":
    example_ide_integration_workflow()