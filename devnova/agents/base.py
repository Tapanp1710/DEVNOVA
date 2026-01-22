# devnova/agents/base.py
"""
Base Agent Classes

Defines the base interfaces and common functionality for all DEVNOVA agents.
Agents are pure reasoning entities that use curated facts and LLM reasoning.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from devnova.llm.interface import LLMInterface, AgentRole, ReasoningInput, ReasoningOutput
from devnova.state.api import ProjectStateAPI


@dataclass
class AgentTask:
    """
    Structured task input for agents.
    Contains task description and optional context.
    """
    description: str
    context: Optional[Dict[str, Any]] = None
    priority: str = "medium"  # "low", "medium", "high"


@dataclass
class AgentResult:
    """
    Structured output from agent reasoning.
    Contains the LLM reasoning result plus agent metadata.
    """
    agent_name: str
    task: AgentTask
    reasoning_output: ReasoningOutput
    processing_time: float  # seconds
    validation_status: str  # "valid", "invalid", "error"


class BaseAgent(ABC):
    """
    Base class for all DEVNOVA agents.

    AGENT BOUNDARIES:
    - READ: Only from Project State API (curated facts)
    - CALL: Only LLM Reasoning Layer (structured reasoning)
    - OUTPUT: Structured plans/recommendations (no code changes)
    - STORAGE: No memory or state modifications
    """

    def __init__(self, workspace_path: str, llm_interface: Optional[LLMInterface] = None):
        self.workspace_path = workspace_path
        self.state_api = ProjectStateAPI(workspace_path)
        self.llm = llm_interface or LLMInterface()
        self.agent_role = self._get_agent_role()

    @abstractmethod
    def _get_agent_role(self) -> AgentRole:
        """Return the specific AgentRole for this agent."""
        pass

    @abstractmethod
    def _validate_task(self, task: AgentTask) -> bool:
        """Validate that this agent can handle the given task."""
        pass

    @abstractmethod
    def _enhance_task_context(self, task: AgentTask) -> Dict[str, Any]:
        """Add agent-specific context to the task before LLM reasoning."""
        pass

    def process_task(self, task: AgentTask) -> AgentResult:
        """
        Process a task using curated facts and LLM reasoning.

        AGENT WORKFLOW:
        1. Validate task is appropriate for this agent
        2. Get curated facts from Project State
        3. Enhance task with agent-specific context
        4. Call LLM Reasoning Layer
        5. Return structured result (no side effects)
        """
        import time
        start_time = time.time()

        try:
            # Step 1: Validate task
            if not self._validate_task(task):
                return AgentResult(
                    agent_name=self.__class__.__name__,
                    task=task,
                    reasoning_output=ReasoningOutput(
                        status="error",
                        reasoning=f"Task validation failed: {task.description}",
                        result={},
                        confidence=0.0,
                        risks=["Task not appropriate for this agent"],
                        recommendations=["Use correct agent for this task type"]
                    ),
                    processing_time=time.time() - start_time,
                    validation_status="invalid"
                )

            # Step 2: Get curated facts from Project State
            project_facts = self.state_api.get_architecture_facts()

            # Step 3: Enhance task context
            enhanced_context = self._enhance_task_context(task)

            # Step 4: Call LLM Reasoning Layer
            reasoning_input = ReasoningInput(
                role=self.agent_role,
                task_description=task.description,
                project_facts=project_facts,
                context_data=enhanced_context
            )

            reasoning_output = self.llm.reason(reasoning_input)

            # Step 5: Return structured result
            processing_time = time.time() - start_time
            validation_status = "valid" if reasoning_output.status == "success" else "error"

            return AgentResult(
                agent_name=self.__class__.__name__,
                task=task,
                reasoning_output=reasoning_output,
                processing_time=processing_time,
                validation_status=validation_status
            )

        except Exception as e:
            return AgentResult(
                agent_name=self.__class__.__name__,
                task=task,
                reasoning_output=ReasoningOutput(
                    status="error",
                    reasoning=f"Agent processing failed: {str(e)}",
                    result={},
                    confidence=0.0,
                    risks=["Agent execution error"],
                    recommendations=["Check agent configuration and inputs"]
                ),
                processing_time=time.time() - start_time,
                validation_status="error"
            )

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return agent capabilities and boundaries.
        Used by orchestrator for task assignment.
        """
        return {
            "agent_name": self.__class__.__name__,
            "role": self.agent_role.value,
            "boundaries": {
                "reads_from": ["Project State API"],
                "calls": ["LLM Reasoning Layer"],
                "outputs": ["Structured plans/recommendations"],
                "restrictions": ["No memory writes", "No code changes", "No file access"]
            },
            "capabilities": self._get_capabilities_description()
        }

    @abstractmethod
    def _get_capabilities_description(self) -> str:
        """Return a description of what this agent can do."""
        pass