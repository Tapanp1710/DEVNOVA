# devnova/agents/debug_agent.py
"""
DebugAgent

Identifies bugs and suggests fixes based on code analysis.
Reads from Project State only, uses LLM Reasoning Layer, outputs structured debugging recommendations.
"""

from typing import Dict, Any
from devnova.llm.interface import AgentRole
from .base import BaseAgent, AgentTask


class DebugAgent(BaseAgent):
    """
    Agent for debugging and issue identification.

    RESPONSIBILITIES:
    - Analyze code for potential bugs and anti-patterns
    - Identify root causes of issues using code facts
    - Suggest specific fixes and improvements
    - Assess debugging complexity and testing needs
    - Recommend verification strategies

    BOUNDARIES:
    - Reads: Project State API (functions, classes, dependencies, call graphs)
    - Calls: LLM Reasoning Layer with DEBUG role
    - Outputs: Structured bug analysis and fix recommendations (no code changes)
    - Restrictions: No memory writes, no file access, no code execution
    """

    def _get_agent_role(self) -> AgentRole:
        return AgentRole.DEBUG

    def _validate_task(self, task: AgentTask) -> bool:
        """
        Validate that this task involves debugging or issue analysis.
        """
        debug_keywords = [
            'bug', 'error', 'fix', 'debug', 'issue', 'problem', 'crash',
            'exception', 'failure', 'broken', 'not working', 'troubleshoot'
        ]

        task_text = task.description.lower()
        return any(keyword in task_text for keyword in debug_keywords)

    def _enhance_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """
        Add debug-specific context from Project State.
        """
        # Get dependency and call graph information for debugging context
        try:
            dependencies = self.state_api.get_dependencies_for_file('devnova/state/api.py')  # Example file
            functions = self.state_api.get_functions()
        except:
            dependencies = []
            functions = []

        return {
            "debug_focus": "root_cause_analysis",
            "code_context": {
                "dependency_count": len(dependencies),
                "function_count": len(functions),
                "complexity_indicators": {
                    "high_dependency_functions": len([f for f in functions if len(f.get("calls", [])) > 5]),
                    "circular_dependencies": False  # Could be enhanced with actual analysis
                }
            },
            "error_context": task.context or {}
        }

    def _get_capabilities_description(self) -> str:
        return "Analyzes code for bugs, identifies root causes, suggests fixes, assesses risks, recommends testing strategies"

    def analyze_bug_report(self, error_description: str, affected_component: str = None) -> Dict[str, Any]:
        """
        Specialized method for bug report analysis.
        """
        task = AgentTask(
            description=f"Analyze bug report: {error_description}",
            context={"affected_component": affected_component},
            priority="high"
        )
        result = self.process_task(task)
        return {
            "root_cause": result.reasoning_output.result.get("root_cause_analysis", ""),
            "fix_suggestions": result.reasoning_output.result.get("fix_suggestions", []),
            "testing_recommendations": result.reasoning_output.result.get("testing_recommendations", []),
            "risks": result.reasoning_output.risks,
            "confidence": result.reasoning_output.confidence
        }