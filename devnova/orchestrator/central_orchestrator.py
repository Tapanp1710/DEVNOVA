# devnova/orchestrator/central_orchestrator.py
"""
Central Orchestrator

Coordinates multi-agent task execution in DEVNOVA.
Assigns tasks to appropriate agents, validates outputs, ensures safety.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from devnova.agents.base import AgentTask, AgentResult
from devnova.agents.architect_agent import ArchitectAgent
from devnova.agents.feature_agent import FeatureAgent
from devnova.agents.debug_agent import DebugAgent
from devnova.agents.test_agent import TestAgent
from devnova.agents.docs_agent import DocsAgent
from devnova.llm.interface import LLMInterface


@dataclass
class OrchestratorTask:
    """
    Task submitted to the orchestrator.
    Contains task description and metadata.
    """
    task_id: str
    description: str
    task_type: str  # "architect", "feature", "debug", "test", "docs", "auto"
    priority: str = "medium"
    context: Optional[Dict[str, Any]] = None
    submitted_at: datetime = None

    def __post_init__(self):
        if self.submitted_at is None:
            self.submitted_at = datetime.now()


@dataclass
class OrchestratorResult:
    """
    Result from orchestrator task execution.
    Contains agent results and orchestration metadata.
    """
    task: OrchestratorTask
    agent_results: List[AgentResult]
    orchestration_status: str  # "success", "partial", "failed"
    validation_errors: List[str]
    execution_time: float
    completed_at: datetime = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now()


class CentralOrchestrator:
    """
    Central orchestrator for DEVNOVA multi-agent system.

    RESPONSIBILITIES:
    - Assign tasks to appropriate agents based on content analysis
    - Coordinate agent execution and collect results
    - Validate outputs against safety and schema requirements
    - Reject unsafe or invalid actions
    - Provide unified interface for task execution

    SAFETY BOUNDARIES:
    - No auto-execution of code changes
    - All outputs are recommendations/plans only
    - Strict validation of agent outputs
    - Explicit rejection of unsafe operations
    """

    def __init__(self, workspace_path: str, llm_interface: Optional[LLMInterface] = None):
        self.workspace_path = workspace_path
        self.llm = llm_interface or LLMInterface()

        # Initialize all agents
        self.agents = {
            "architect": ArchitectAgent(workspace_path, self.llm),
            "feature": FeatureAgent(workspace_path, self.llm),
            "debug": DebugAgent(workspace_path, self.llm),
            "test": TestAgent(workspace_path, self.llm),
            "docs": DocsAgent(workspace_path, self.llm)
        }

        # Task execution history
        self.task_history: List[OrchestratorResult] = []

    def execute_task(self, task: OrchestratorTask) -> OrchestratorResult:
        """
        Execute a task by assigning it to appropriate agent(s).

        ORCHESTRATION FLOW:
        1. Analyze task to determine appropriate agent(s)
        2. Validate task safety and appropriateness
        3. Execute agent processing
        4. Validate agent outputs
        5. Return structured results
        """
        import time
        start_time = time.time()

        try:
            # Step 1: Determine target agents
            target_agents = self._determine_target_agents(task)

            if not target_agents:
                return OrchestratorResult(
                    task=task,
                    agent_results=[],
                    orchestration_status="failed",
                    validation_errors=["No appropriate agent found for task"],
                    execution_time=time.time() - start_time
                )

            # Step 2: Validate task safety
            safety_check = self._validate_task_safety(task)
            if not safety_check["safe"]:
                return OrchestratorResult(
                    task=task,
                    agent_results=[],
                    orchestration_status="failed",
                    validation_errors=safety_check["reasons"],
                    execution_time=time.time() - start_time
                )

            # Step 3: Execute agent processing
            agent_results = []
            for agent_name in target_agents:
                agent = self.agents[agent_name]
                agent_task = AgentTask(
                    description=task.description,
                    context=task.context,
                    priority=task.priority
                )

                agent_result = agent.process_task(agent_task)
                agent_results.append(agent_result)

            # Step 4: Validate outputs
            validation_errors = self._validate_agent_outputs(agent_results)

            # Step 5: Determine orchestration status
            if validation_errors:
                status = "partial" if agent_results else "failed"
            else:
                status = "success"

            result = OrchestratorResult(
                task=task,
                agent_results=agent_results,
                orchestration_status=status,
                validation_errors=validation_errors,
                execution_time=time.time() - start_time
            )

            # Record in history
            self.task_history.append(result)

            return result

        except Exception as e:
            return OrchestratorResult(
                task=task,
                agent_results=[],
                orchestration_status="failed",
                validation_errors=[f"Orchestration error: {str(e)}"],
                execution_time=time.time() - start_time
            )

    def _determine_target_agents(self, task: OrchestratorTask) -> List[str]:
        """
        Analyze task content to determine which agent(s) should handle it.
        """
        if task.task_type != "auto":
            # Explicit agent assignment
            if task.task_type in self.agents:
                return [task.task_type]
            return []

        # Auto-determination based on content analysis
        description = task.description.lower()

        # Keywords for each agent
        agent_keywords = {
            "architect": ["architecture", "structure", "design pattern", "scalability", "system design", "component", "layered"],
            "feature": ["feature", "implement", "add functionality", "create", "build feature", "enhancement", "capability"],
            "debug": ["bug", "error", "fix", "debug", "issue", "problem", "crash", "exception", "failure"],
            "test": ["test", "testing", "coverage", "spec", "assert", "verify", "quality assurance", "tdd", "bdd"],
            "docs": ["doc", "documentation", "readme", "comment", "api doc", "guide", "tutorial", "explain"]
        }

        matching_agents = []
        for agent_name, keywords in agent_keywords.items():
            if any(keyword in description for keyword in keywords):
                matching_agents.append(agent_name)

        return matching_agents

    def _validate_task_safety(self, task: OrchestratorTask) -> Dict[str, Any]:
        """
        Validate that the task is safe to execute.
        Rejects tasks that could lead to unsafe operations.
        """
        unsafe_patterns = [
            "delete", "remove", "destroy", "format", "wipe",
            "execute", "run", "start", "launch", "deploy",
            "write", "modify", "change", "edit", "update",
            "install", "download", "connect", "access"
        ]

        description = task.description.lower()

        # Check for unsafe keywords
        unsafe_matches = [pattern for pattern in unsafe_patterns if pattern in description]

        if unsafe_matches:
            return {
                "safe": False,
                "reasons": [f"Task contains unsafe operation keywords: {', '.join(unsafe_matches)}"]
            }

        # Additional safety checks
        if "auto" in description and "execute" in description:
            return {
                "safe": False,
                "reasons": ["Auto-execution requests are not allowed"]
            }

        return {"safe": True, "reasons": []}

    def _validate_agent_outputs(self, agent_results: List[AgentResult]) -> List[str]:
        """
        Validate agent outputs for safety and correctness.
        """
        errors = []

        for result in agent_results:
            # Check for unsafe content in recommendations
            if result.reasoning_output.recommendations:
                for rec in result.reasoning_output.recommendations:
                    rec_lower = str(rec).lower()
                    if any(unsafe in rec_lower for unsafe in ["execute", "run", "deploy", "modify", "write"]):
                        errors.append(f"Agent {result.agent_name} output contains unsafe recommendation: {rec}")

            # Check for code content (agents should not output code)
            result_content = json.dumps(result.reasoning_output.result)
            if "```" in result_content or "def " in result_content or "class " in result_content:
                errors.append(f"Agent {result.agent_name} output contains code content (not allowed)")

            # Validate confidence scores
            if not (0.0 <= result.reasoning_output.confidence <= 1.0):
                errors.append(f"Agent {result.agent_name} has invalid confidence score: {result.reasoning_output.confidence}")

        return errors

    def get_agent_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """
        Get capabilities of all available agents.
        """
        return {name: agent.get_capabilities() for name, agent in self.agents.items()}

    def get_task_history(self, limit: int = 10) -> List[OrchestratorResult]:
        """
        Get recent task execution history.
        """
        return self.task_history[-limit:]

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status and statistics.
        """
        total_tasks = len(self.task_history)
        successful_tasks = len([t for t in self.task_history if t.orchestration_status == "success"])
        failed_tasks = len([t for t in self.task_history if t.orchestration_status == "failed"])

        return {
            "total_tasks_executed": total_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "failure_rate": failed_tasks / total_tasks if total_tasks > 0 else 0,
            "active_agents": len(self.agents),
            "agent_types": list(self.agents.keys()),
            "safety_enabled": True,
            "auto_execution_blocked": True
        }


# Convenience functions
def create_orchestrator(workspace_path: str) -> CentralOrchestrator:
    """
    Factory function to create a configured orchestrator.
    """
    return CentralOrchestrator(workspace_path)


def quick_task(orchestrator: CentralOrchestrator, description: str,
               task_type: str = "auto", priority: str = "medium") -> OrchestratorResult:
    """
    Quick task execution helper.
    """
    task = OrchestratorTask(
        task_id=f"quick_{int(datetime.now().timestamp())}",
        description=description,
        task_type=task_type,
        priority=priority
    )
    return orchestrator.execute_task(task)