# devnova/orchestrator/test_orchestrator.py
"""
Test suite for Phase 5: Multi-Agent System and Central Orchestrator
"""

import json
from devnova.orchestrator.central_orchestrator import (
    CentralOrchestrator, OrchestratorTask, create_orchestrator, quick_task
)
from devnova.agents.base import AgentTask


def test_agent_capabilities():
    """Test that all agents report correct capabilities and boundaries."""
    print("Testing Agent Capabilities and Boundaries")
    print("=" * 50)

    orchestrator = create_orchestrator('D:\\\\DEVNOVA\\\\devnova')
    capabilities = orchestrator.get_agent_capabilities()

    expected_agents = ["architect", "feature", "debug", "test", "docs"]
    assert len(capabilities) == len(expected_agents), f"Expected {len(expected_agents)} agents, got {len(capabilities)}"

    for agent_name in expected_agents:
        assert agent_name in capabilities, f"Missing agent: {agent_name}"
        agent_caps = capabilities[agent_name]

        # Check required boundary fields
        boundaries = agent_caps["boundaries"]
        required_reads = ["Project State API"]
        required_calls = ["LLM Reasoning Layer"]
        required_outputs = ["Structured plans/recommendations"]
        forbidden = ["No memory writes", "No code changes", "No file access"]

        assert all(read in boundaries["reads_from"] for read in required_reads), f"Agent {agent_name} missing required reads"
        assert all(call in boundaries["calls"] for call in required_calls), f"Agent {agent_name} missing required calls"
        assert all(out in boundaries["outputs"] for out in required_outputs), f"Agent {agent_name} missing required outputs"
        assert all(restr in boundaries["restrictions"] for restr in forbidden), f"Agent {agent_name} missing required restrictions"

        print(f"✓ Agent {agent_name}: {agent_caps['capabilities']}")


def test_task_assignment():
    """Test automatic task assignment to appropriate agents."""
    print("\nTesting Task Assignment Logic")
    print("=" * 50)

    orchestrator = create_orchestrator('D:\\\\DEVNOVA\\\\devnova')

    test_cases = [
        ("Analyze the project architecture", ["architect"]),
        ("Implement a new feature for user authentication", ["feature"]),
        ("Debug a serialization error in the memory layer", ["debug"]),
        ("Add comprehensive test coverage", ["test"]),
        ("Improve API documentation", ["docs"]),
        ("Fix bug and add tests", ["debug", "test"]),  # Multi-agent
    ]

    for description, expected_agents in test_cases:
        task = OrchestratorTask(
            task_id=f"test_{len(orchestrator.task_history)}",
            description=description,
            task_type="auto"
        )

        result = orchestrator.execute_task(task)

        assigned_agents = [r.agent_name.lower().replace("agent", "") for r in result.agent_results]
        assigned_agents.sort()
        expected_agents.sort()

        assert assigned_agents == expected_agents, f"Task '{description}' assigned to {assigned_agents}, expected {expected_agents}"
        print(f"✓ Task: '{description}' → Agents: {assigned_agents}")


def test_safety_validation():
    """Test that unsafe tasks are rejected."""
    print("\nTesting Safety Validation")
    print("=" * 50)

    orchestrator = create_orchestrator('D:\\\\DEVNOVA\\\\devnova')

    unsafe_tasks = [
        "Delete all files in the project",
        "Execute the following code: rm -rf /",
        "Modify the database directly",
        "Auto-deploy to production",
        "Write changes to memory"
    ]

    for unsafe_description in unsafe_tasks:
        task = OrchestratorTask(
            task_id=f"unsafe_{len(orchestrator.task_history)}",
            description=unsafe_description,
            task_type="auto"
        )

        result = orchestrator.execute_task(task)

        assert result.orchestration_status == "failed", f"Unsafe task '{unsafe_description}' was not rejected"
        assert len(result.validation_errors) > 0, f"Unsafe task '{unsafe_description}' should have validation errors"
        print(f"✓ Rejected unsafe task: '{unsafe_description}'")


def test_output_validation():
    """Test that agent outputs are properly validated."""
    print("\nTesting Output Validation")
    print("=" * 50)

    orchestrator = create_orchestrator('D:\\\\DEVNOVA\\\\devnova')

    # Test safe architectural task
    task = OrchestratorTask(
        task_id="validation_test",
        description="Analyze project architecture for improvements",
        task_type="architect"
    )

    result = orchestrator.execute_task(task)

    assert result.orchestration_status in ["success", "partial"], f"Task failed: {result.validation_errors}"

    if result.agent_results:
        agent_result = result.agent_results[0]

        # Validate result structure
        assert hasattr(agent_result, 'reasoning_output'), "Missing reasoning_output"
        assert hasattr(agent_result.reasoning_output, 'status'), "Missing status"
        assert hasattr(agent_result.reasoning_output, 'confidence'), "Missing confidence"
        assert hasattr(agent_result.reasoning_output, 'risks'), "Missing risks"
        assert hasattr(agent_result.reasoning_output, 'recommendations'), "Missing recommendations"

        # Validate confidence range
        assert 0.0 <= agent_result.reasoning_output.confidence <= 1.0, f"Invalid confidence: {agent_result.reasoning_output.confidence}"

        # Validate no code in output
        result_json = json.dumps(agent_result.reasoning_output.result)
        assert "```" not in result_json, "Output contains code blocks"
        assert "def " not in result_json, "Output contains function definitions"
        assert "class " not in result_json, "Output contains class definitions"

        print("✓ Output validation passed")
        print(f"  Status: {agent_result.reasoning_output.status}")
        print(f"  Confidence: {agent_result.reasoning_output.confidence}")
        print(f"  Risks: {len(agent_result.reasoning_output.risks)}")
        print(f"  Recommendations: {len(agent_result.reasoning_output.recommendations)}")


def test_orchestrator_status():
    """Test orchestrator status reporting."""
    print("\nTesting Orchestrator Status")
    print("=" * 50)

    orchestrator = create_orchestrator('D:\\\\DEVNOVA\\\\devnova')
    status = orchestrator.get_system_status()

    required_fields = [
        "total_tasks_executed", "success_rate", "failure_rate",
        "active_agents", "agent_types", "safety_enabled", "auto_execution_blocked"
    ]

    for field in required_fields:
        assert field in status, f"Missing status field: {field}"

    assert status["active_agents"] == 5, f"Expected 5 agents, got {status['active_agents']}"
    assert status["safety_enabled"] == True, "Safety should be enabled"
    assert status["auto_execution_blocked"] == True, "Auto-execution should be blocked"

    print("✓ Orchestrator status:")
    print(f"  Active agents: {status['active_agents']}")
    print(f"  Safety enabled: {status['safety_enabled']}")
    print(f"  Auto-execution blocked: {status['auto_execution_blocked']}")


def test_quick_task_interface():
    """Test the quick task convenience interface."""
    print("\nTesting Quick Task Interface")
    print("=" * 50)

    orchestrator = create_orchestrator('D:\\\\DEVNOVA\\\\devnova')

    result = quick_task(orchestrator, "Analyze test coverage", "test")

    assert result.orchestration_status in ["success", "partial"], "Quick task failed"
    assert len(result.agent_results) > 0, "No agent results from quick task"
    assert result.agent_results[0].agent_name == "TestAgent", f"Wrong agent assigned: {result.agent_results[0].agent_name}"

    print("✓ Quick task interface working")
    print(f"  Task: '{result.task.description}'")
    print(f"  Agent: {result.agent_results[0].agent_name}")
    print(f"  Status: {result.orchestration_status}")


def run_all_tests():
    """Run all Phase 5 tests."""
    print("PHASE 5 TESTING: Multi-Agent System and Central Orchestrator")
    print("=" * 70)

    try:
        test_agent_capabilities()
        test_task_assignment()
        test_safety_validation()
        test_output_validation()
        test_orchestrator_status()
        test_quick_task_interface()

        print("\n" + "=" * 70)
        print("🎉 ALL PHASE 5 TESTS PASSED!")
        print("✅ Multi-Agent System properly implemented")
        print("✅ Central Orchestrator working correctly")
        print("✅ Safety boundaries enforced")
        print("✅ Agent boundaries respected")
        print("✅ No auto-execution of code")

    except Exception as e:
        print(f"\n❌ TEST FAILURE: {str(e)}")
        raise


if __name__ == '__main__':
    run_all_tests()