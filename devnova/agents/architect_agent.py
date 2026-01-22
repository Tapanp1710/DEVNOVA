# devnova/agents/architect_agent.py
"""
ArchitectAgent

Analyzes project architecture and suggests structural improvements.
Reads from Project State only, uses LLM Reasoning Layer, outputs structured recommendations.
"""

from typing import Dict, Any
from devnova.llm.interface import AgentRole
from .base import BaseAgent, AgentTask


class ArchitectAgent(BaseAgent):
    """
    Agent for architectural analysis and recommendations.

    RESPONSIBILITIES:
    - Analyze overall project structure and patterns
    - Identify architectural risks and scalability issues
    - Suggest structural improvements and design patterns
    - Recommend technology stack optimizations

    BOUNDARIES:
    - Reads: Project State API (architecture facts, file structure)
    - Calls: LLM Reasoning Layer with ARCHITECT role
    - Outputs: Structured analysis and recommendations (no code changes)
    - Restrictions: No memory writes, no file access, no execution
    """

    def _get_agent_role(self) -> AgentRole:
        return AgentRole.ARCHITECT

    def _validate_task(self, task: AgentTask) -> bool:
        """
        Validate that this task is appropriate for architectural analysis.
        """
        architecture_keywords = [
            'architecture', 'structure', 'design', 'pattern', 'scalability',
            'organization', 'modular', 'layer', 'component', 'system'
        ]

        task_text = task.description.lower()
        return any(keyword in task_text for keyword in architecture_keywords)

    def _enhance_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """
        Add architect-specific context from Project State.
        """
        # Get additional architectural insights
        try:
            dependencies = self.state_api.get_dependencies_for_file('devnova/state/api.py')
            file_structure = self.state_api.get_files_by_language()
        except:
            dependencies = []
            file_structure = {}

        return {
            "architectural_focus": "system_design_patterns",
            "analysis_scope": "full_project",
            "key_dependencies": dependencies[:10] if dependencies else [],  # Limit for context
            "file_distribution": file_structure,
            "task_context": task.context or {}
        }

    def _get_capabilities_description(self) -> str:
        return "Analyzes project architecture, identifies structural issues, suggests design improvements and scalability enhancements"

    def analyze_architecture_health(self) -> Dict[str, Any]:
        """
        Specialized method for architecture health assessment.
        Returns structured analysis without requiring a task.
        """
        task = AgentTask(
            description="Perform comprehensive architecture health assessment",
            priority="high"
        )
        result = self.process_task(task)
        return {
            "health_score": result.reasoning_output.confidence,
            "issues": result.reasoning_output.risks,
            "recommendations": result.reasoning_output.recommendations,
            "analysis": result.reasoning_output.result.get("analysis", "")
        }