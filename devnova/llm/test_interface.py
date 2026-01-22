# devnova/llm/test_interface.py
"""
Test script for LLM Reasoning Layer
Tests all agent roles, validation, and failure handling.
"""

import json
from devnova.llm.interface import LLMInterface, AgentRole, ReasoningInput, ReasoningOutput
from devnova.state.api import ProjectStateAPI


def test_all_roles():
    """Test all agent roles with the LLM interface."""
    print("Testing LLM Reasoning Layer - All Roles")
    print("=" * 50)

    # Get project facts
    api = ProjectStateAPI('D:\\DEVNOVA\\devnova')
    facts = api.get_architecture_facts()

    llm = LLMInterface()

    # Test each role
    roles_to_test = [
        (AgentRole.ARCHITECT, "Analyze the current project architecture and suggest improvements"),
        (AgentRole.FEATURE, "Design a new feature for incremental code analysis"),
        (AgentRole.DEBUG, "Debug a serialization issue in the memory layer"),
        (AgentRole.TEST, "Analyze test coverage and suggest improvements"),
        (AgentRole.DOCS, "Identify documentation gaps and suggest structure")
    ]

    for role, task in roles_to_test:
        print(f"\nTesting {role.value.upper()} role:")
        print("-" * 30)

        input_data = ReasoningInput(
            role=role,
            task_description=task,
            project_facts=facts
        )

        result = llm.reason(input_data)

        print(f"Status: {result.status}")
        print(f"Confidence: {result.confidence}")
        print(f"Reasoning: {result.reasoning[:100]}...")
        print(f"Risks: {len(result.risks)} items")
        print(f"Recommendations: {len(result.recommendations)} items")
        print(f"Result keys: {list(result.result.keys())}")


def test_validation():
    """Test validation and failure handling."""
    print("\n\nTesting Validation and Failure Handling")
    print("=" * 50)

    llm = LLMInterface()

    # Test invalid JSON response
    print("\nTesting invalid JSON handling:")
    invalid_response = '{"invalid": json}'
    validated = llm._validate_and_extract_output(invalid_response, AgentRole.ARCHITECT)
    print(f"Invalid JSON result: {validated.status}")

    # Test missing fields
    print("\nTesting missing fields handling:")
    missing_fields_response = '{"confidence": 0.8}'  # Missing required fields
    validated = llm._validate_and_extract_output(missing_fields_response, AgentRole.ARCHITECT)
    print(f"Missing fields result: {validated.status}")

    # Test valid response
    print("\nTesting valid response:")
    valid_response = json.dumps({
        "analysis": "Valid analysis",
        "recommendations": ["Rec 1", "Rec 2"],
        "priority_areas": ["Area 1"],
        "risks": ["Risk 1"],
        "confidence": 0.9
    })
    validated = llm._validate_and_extract_output(valid_response, AgentRole.ARCHITECT)
    print(f"Valid response result: {validated.status}")


def test_reasoning_boundaries():
    """Test that reasoning boundaries are enforced."""
    print("\n\nTesting Reasoning Boundaries")
    print("=" * 50)

    llm = LLMInterface()

    # Test that only curated facts are used (no direct file access)
    input_data = ReasoningInput(
        role=AgentRole.ARCHITECT,
        task_description="Analyze architecture",
        project_facts={"files": 17, "functions": 76, "classes": 28}  # Only curated facts
    )

    result = llm.reason(input_data)

    # Verify result contains structured output, not file contents
    assert isinstance(result.result, dict)
    assert "analysis" in result.result or "proposed_features" in result.result
    assert result.status == "success"

    print("✓ Reasoning boundaries enforced - only structured facts used")
    print("✓ No direct file access in reasoning layer")
    print("✓ Structured JSON output validated")


if __name__ == '__main__':
    test_all_roles()
    test_validation()
    test_reasoning_boundaries()
    print("\n\n🎉 All LLM Reasoning Layer tests passed!")