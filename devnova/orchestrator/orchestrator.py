"""
Central Orchestrator - Coordinates multi-agent reasoning

This module implements the central orchestrator that coordinates
the multi-agent system, assigns tasks to appropriate agents,
and ensures safety boundaries are maintained.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..ide.interfaces import (
    IDEContext, Suggestion, Explanation, Risk,
    SuggestionRequest, ExplanationRequest, RiskAnalysisRequest
)


class Orchestrator:
    """
    Central orchestrator for the multi-agent system.

    This class coordinates the different agents (Architect, Feature, Debug, Test, Docs)
    and ensures that all operations maintain safety boundaries.
    """

    def __init__(self):
        # Initialize agents
        from ..agents.base import BaseAgent
        from ..agents.architect_agent import ArchitectAgent
        from ..agents.feature_agent import FeatureAgent
        from ..agents.debug_agent import DebugAgent
        from ..agents.test_agent import TestAgent
        from ..agents.docs_agent import DocsAgent

        self.agents = {
            'architect': ArchitectAgent(),
            'feature': FeatureAgent(),
            'debug': DebugAgent(),
            'test': TestAgent(),
            'docs': DocsAgent()
        }

    def set_project_context(self, project_root: str):
        """
        Set the project context for all agents.

        Args:
            project_root: Root directory of the project
        """
        for agent in self.agents.values():
            agent.set_project_context(project_root)

    def get_suggestions(self, context: IDEContext, intent: str, max_suggestions: int = 5) -> List[Suggestion]:
        """
        Get suggestions by coordinating appropriate agents.

        Args:
            context: IDE context information
            intent: User's intent description
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggestions from relevant agents
        """
        suggestions = []

        # Route to appropriate agent based on intent
        if self._is_architecture_intent(intent):
            agent = self.agents['architect']
            agent_suggestions = agent.get_suggestions(context, intent)
            suggestions.extend(agent_suggestions)

        elif self._is_feature_intent(intent):
            agent = self.agents['feature']
            agent_suggestions = agent.get_suggestions(context, intent)
            suggestions.extend(agent_suggestions)

        elif self._is_debug_intent(intent):
            agent = self.agents['debug']
            agent_suggestions = agent.get_suggestions(context, intent)
            suggestions.extend(agent_suggestions)

        elif self._is_test_intent(intent):
            agent = self.agents['test']
            agent_suggestions = agent.get_suggestions(context, intent)
            suggestions.extend(agent_suggestions)

        # Limit suggestions and add metadata
        limited_suggestions = suggestions[:max_suggestions]
        for i, suggestion in enumerate(limited_suggestions):
            suggestion.id = f"sugg_{i+1}"

        return limited_suggestions

    def get_explanations(self, context: IDEContext, code: str, explanation_type: str) -> List[Explanation]:
        """
        Get explanations by coordinating appropriate agents.

        Args:
            context: IDE context information
            code: Code to explain
            explanation_type: Type of explanation needed

        Returns:
            List of explanations from relevant agents
        """
        explanations = []

        # Route based on explanation type
        if explanation_type == "bug" or explanation_type == "debug":
            agent = self.agents['debug']
            agent_explanations = agent.get_explanations(context, code, explanation_type)
            explanations.extend(agent_explanations)

        elif explanation_type == "architecture":
            agent = self.agents['architect']
            agent_explanations = agent.get_explanations(context, code, explanation_type)
            explanations.extend(agent_explanations)

        else:
            # General explanation - try multiple agents
            for agent_name, agent in self.agents.items():
                if agent_name != 'test':  # Test agent might not be relevant for general explanations
                    agent_explanations = agent.get_explanations(context, code, explanation_type)
                    explanations.extend(agent_explanations)

        # Add metadata to explanations
        for i, explanation in enumerate(explanations):
            explanation.id = f"expl_{i+1}"

        return explanations[:5]  # Limit to 5 explanations

    def analyze_risks(self, context: IDEContext, code: str, analysis_type: str) -> List[Risk]:
        """
        Analyze risks by coordinating appropriate agents.

        Args:
            context: IDE context information
            code: Code to analyze
            analysis_type: Type of risk analysis

        Returns:
            List of identified risks
        """
        risks = []

        # Route based on analysis type
        if analysis_type == "security":
            # Security analysis - multiple agents might contribute
            for agent_name, agent in self.agents.items():
                agent_risks = agent.analyze_risks(context, code, analysis_type)
                risks.extend(agent_risks)

        elif analysis_type == "performance":
            # Performance analysis - architect and debug agents
            architect_risks = self.agents['architect'].analyze_risks(context, code, analysis_type)
            debug_risks = self.agents['debug'].analyze_risks(context, code, analysis_type)
            risks.extend(architect_risks)
            risks.extend(debug_risks)

        elif analysis_type == "maintainability":
            # Maintainability - architect and test agents
            architect_risks = self.agents['architect'].analyze_risks(context, code, analysis_type)
            test_risks = self.agents['test'].analyze_risks(context, code, analysis_type)
            risks.extend(architect_risks)
            risks.extend(test_risks)

        else:
            # General analysis - all agents
            for agent in self.agents.values():
                agent_risks = agent.analyze_risks(context, code, analysis_type)
                risks.extend(agent_risks)

        # Add metadata to risks
        for i, risk in enumerate(risks):
            risk.id = f"risk_{i+1}"

        return risks

    def _is_architecture_intent(self, intent: str) -> bool:
        """Check if intent is architecture-related."""
        architecture_keywords = [
            'architecture', 'structure', 'design', 'refactor', 'organize',
            'pattern', 'component', 'module', 'system', 'framework'
        ]
        return any(keyword in intent.lower() for keyword in architecture_keywords)

    def _is_feature_intent(self, intent: str) -> bool:
        """Check if intent is feature-related."""
        feature_keywords = [
            'feature', 'implement', 'add', 'create', 'build', 'develop',
            'functionality', 'capability', 'enhancement'
        ]
        return any(keyword in intent.lower() for keyword in feature_keywords)

    def _is_debug_intent(self, intent: str) -> bool:
        """Check if intent is debug-related."""
        debug_keywords = [
            'bug', 'fix', 'error', 'debug', 'issue', 'problem', 'broken',
            'crash', 'exception', 'traceback'
        ]
        return any(keyword in intent.lower() for keyword in debug_keywords)

    def _is_test_intent(self, intent: str) -> bool:
        """Check if intent is test-related."""
        test_keywords = [
            'test', 'testing', 'coverage', 'unit', 'integration', 'assert',
            'verify', 'validate', 'check'
        ]
        return any(keyword in intent.lower() for keyword in test_keywords)