# devnova/agents/docs_agent.py
"""
DocsAgent

Analyzes code and suggests documentation improvements.
Reads from Project State only, uses LLM Reasoning Layer, outputs structured documentation recommendations.
"""

from typing import Dict, Any
from devnova.llm.interface import AgentRole
from .base import BaseAgent, AgentTask


class DocsAgent(BaseAgent):
    """
    Agent for documentation analysis and improvement recommendations.

    RESPONSIBILITIES:
    - Analyze code for documentation gaps and needs
    - Identify missing API documentation and usage examples
    - Suggest documentation structure and organization
    - Recommend documentation types and priorities
    - Assess documentation completeness and quality

    BOUNDARIES:
    - Reads: Project State API (functions, classes, file structure)
    - Calls: LLM Reasoning Layer with DOCS role
    - Outputs: Structured documentation plans and gap analysis (no documentation writing)
    - Restrictions: No memory writes, no file access, no documentation generation
    """

    def _get_agent_role(self) -> AgentRole:
        return AgentRole.DOCS

    def _validate_task(self, task: AgentTask) -> bool:
        """
        Validate that this task involves documentation or docs.
        """
        docs_keywords = [
            'doc', 'documentation', 'readme', 'comment', 'api', 'guide',
            'tutorial', 'example', 'explain', 'describe', 'document'
        ]

        task_text = task.description.lower()
        return any(keyword in task_text for keyword in docs_keywords)

    def _enhance_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """
        Add documentation-specific context from Project State.
        """
        # Get code structure for documentation context
        try:
            functions = self.state_api.get_functions()
            classes = self.state_api.get_classes()
            files = self.state_api.get_files()
        except:
            functions = []
            classes = []
            files = []

        # Analyze documentation indicators
        public_functions = [f for f in functions if not f.get("name", "").startswith("_")]
        public_classes = [c for c in classes if not c.get("name", "").startswith("_")]

        return {
            "docs_focus": "gap_analysis",
            "code_structure": {
                "total_files": len(files),
                "public_functions": len(public_functions),
                "public_classes": len(public_classes),
                "documentation_indicators": {
                    "api_surface": len(public_functions) + len(public_classes),
                    "complex_functions": len([f for f in functions if len(f.get("calls", [])) > 3]),
                    "large_classes": len([c for c in classes if len(c.get("methods", [])) > 5])
                }
            },
            "task_context": task.context or {}
        }

    def _get_capabilities_description(self) -> str:
        return "Analyzes documentation gaps, suggests documentation structure, identifies API docs needs, recommends documentation priorities"

    def analyze_documentation_needs(self, focus_area: str = None) -> Dict[str, Any]:
        """
        Specialized method for documentation gap analysis.
        """
        task = AgentTask(
            description=f"Analyze documentation needs{f' for {focus_area}' if focus_area else ''}",
            context={"focus_area": focus_area},
            priority="medium"
        )
        result = self.process_task(task)
        return {
            "documentation_gaps": result.reasoning_output.result.get("documentation_gaps", []),
            "suggested_structure": result.reasoning_output.result.get("suggested_structure", []),
            "priority_order": result.reasoning_output.result.get("priority_order", []),
            "examples_needed": result.reasoning_output.result.get("examples_needed", []),
            "risks": result.reasoning_output.risks,
            "confidence": result.reasoning_output.confidence
        }