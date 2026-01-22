# devnova/agents/feature_agent.py
"""
FeatureAgent

Analyzes feature requests and plans implementations.
Reads from Project State only, uses LLM Reasoning Layer, outputs structured feature plans.
"""

from typing import Dict, Any
from devnova.llm.interface import AgentRole
from .base import BaseAgent, AgentTask


class FeatureAgent(BaseAgent):
    """
    Agent for feature analysis and implementation planning.

    RESPONSIBILITIES:
    - Analyze feature requests and requirements
    - Assess technical feasibility using project facts
    - Plan implementation approaches and dependencies
    - Estimate complexity and resource requirements
    - Identify integration points with existing code

    BOUNDARIES:
    - Reads: Project State API (architecture facts, existing functions/classes)
    - Calls: LLM Reasoning Layer with FEATURE role
    - Outputs: Structured feature plans and implementation strategies (no code)
    - Restrictions: No memory writes, no file access, no code generation
    """

    def _get_agent_role(self) -> AgentRole:
        return AgentRole.FEATURE

    def _validate_task(self, task: AgentTask) -> bool:
        """
        Validate that this task is a feature request or implementation planning.
        """
        feature_keywords = [
            'feature', 'implement', 'add', 'create', 'build', 'develop',
            'functionality', 'capability', 'requirement', 'enhancement'
        ]

        task_text = task.description.lower()
        return any(keyword in task_text for keyword in feature_keywords)

    def _enhance_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """
        Add feature-specific context from Project State.
        """
        # Get existing functionality to understand integration points
        try:
            functions = self.state_api.get_functions()
            classes = self.state_api.get_classes()
        except:
            functions = []
            classes = []

        return {
            "feature_focus": "implementation_planning",
            "existing_functionality": {
                "function_count": len(functions),
                "class_count": len(classes),
                "sample_functions": [f.get("name", "") for f in functions[:5]],
                "sample_classes": [c.get("name", "") for c in classes[:5]]
            },
            "task_context": task.context or {}
        }

    def _get_capabilities_description(self) -> str:
        return "Analyzes feature requests, plans implementations, assesses complexity, identifies dependencies and integration points"

    def plan_feature_implementation(self, feature_description: str, requirements: list = None) -> Dict[str, Any]:
        """
        Specialized method for feature implementation planning.
        """
        task = AgentTask(
            description=f"Plan implementation for feature: {feature_description}",
            context={"requirements": requirements or []},
            priority="high"
        )
        result = self.process_task(task)
        return {
            "feature_plan": result.reasoning_output.result,
            "complexity": result.reasoning_output.result.get("estimated_complexity", "UNKNOWN"),
            "dependencies": result.reasoning_output.result.get("dependencies", []),
            "risks": result.reasoning_output.risks,
            "confidence": result.reasoning_output.confidence
        }