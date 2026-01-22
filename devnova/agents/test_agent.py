# devnova/agents/test_agent.py
"""
TestAgent

Analyzes code and suggests comprehensive test strategies.
Reads from Project State only, uses LLM Reasoning Layer, outputs structured test recommendations.
"""

from typing import Dict, Any
from devnova.llm.interface import AgentRole
from .base import BaseAgent, AgentTask


class TestAgent(BaseAgent):
    """
    Agent for test analysis and test case generation planning.

    RESPONSIBILITIES:
    - Analyze code for test coverage gaps
    - Suggest comprehensive test strategies
    - Identify critical test scenarios and edge cases
    - Recommend testing priorities and approaches
    - Assess testing complexity and resource needs

    BOUNDARIES:
    - Reads: Project State API (functions, classes, dependencies)
    - Calls: LLM Reasoning Layer with TEST role
    - Outputs: Structured test plans and coverage recommendations (no test code)
    - Restrictions: No memory writes, no file access, no test execution
    """

    def _get_agent_role(self) -> AgentRole:
        return AgentRole.TEST

    def _validate_task(self, task: AgentTask) -> bool:
        """
        Validate that this task involves testing or test coverage.
        """
        test_keywords = [
            'test', 'testing', 'coverage', 'spec', 'assert', 'verify',
            'validate', 'check', 'quality', 'tdd', 'bdd'
        ]

        task_text = task.description.lower()
        return any(keyword in task_text for keyword in test_keywords)

    def _enhance_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """
        Add test-specific context from Project State.
        """
        # Get code complexity indicators for testing context
        try:
            functions = self.state_api.get_functions()
            classes = self.state_api.get_classes()
        except:
            functions = []
            classes = []

        # Calculate basic complexity metrics
        complex_functions = [f for f in functions if len(f.get("calls", [])) > 3]
        large_classes = [c for c in classes if len(c.get("methods", [])) > 5]

        return {
            "test_focus": "coverage_analysis",
            "code_complexity": {
                "total_functions": len(functions),
                "complex_functions": len(complex_functions),
                "total_classes": len(classes),
                "large_classes": len(large_classes),
                "testability_indicators": {
                    "high_complexity_functions": len([f for f in functions if len(f.get("calls", [])) > 5]),
                    "classes_needing_mocking": len([c for c in classes if len(c.get("dependencies", [])) > 3])
                }
            },
            "task_context": task.context or {}
        }

    def _get_capabilities_description(self) -> str:
        return "Analyzes test coverage gaps, suggests test strategies, identifies critical scenarios, recommends testing priorities"

    def analyze_test_coverage(self, target_component: str = None) -> Dict[str, Any]:
        """
        Specialized method for test coverage analysis.
        """
        task = AgentTask(
            description=f"Analyze test coverage for {target_component or 'entire project'}",
            context={"target_component": target_component},
            priority="medium"
        )
        result = self.process_task(task)
        return {
            "coverage_analysis": result.reasoning_output.result.get("coverage_analysis", ""),
            "suggested_tests": result.reasoning_output.result.get("suggested_tests", []),
            "test_types": result.reasoning_output.result.get("test_types", []),
            "priority_order": result.reasoning_output.result.get("priority_order", []),
            "risks": result.reasoning_output.risks,
            "confidence": result.reasoning_output.confidence
        }