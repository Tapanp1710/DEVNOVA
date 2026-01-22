# devnova/llm/interface.py
"""
LLM Reasoning Layer

Centralized interface for LLM interactions.
REASONING BOUNDARIES:
- INPUT: Only curated facts from Project State API (no direct file/graph access)
- OUTPUT: Structured JSON reasoning results (plans, risks, recommendations)
- ROLE: Pure reasoning engine - no memory storage, no execution, no file operations
- VALIDATION: Strict JSON schema validation with explicit failure handling

Enforces:
- Role-based system prompts
- Input constraints (curated facts only)
- Structured JSON outputs with schemas
- No memory storage or state management
"""

import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """Defined agent roles with their reasoning purposes."""
    ARCHITECT = "architect"
    FEATURE = "feature"
    DEBUG = "debug"
    TEST = "test"
    DOCS = "docs"


@dataclass
class ReasoningInput:
    """
    Structured input for LLM reasoning.
    Contains only curated facts from Project State - no direct access to files/memory.
    """
    role: AgentRole
    task_description: str
    project_facts: Dict[str, Any]  # Curated facts from Project State API
    context_data: Optional[Dict[str, Any]] = None  # Additional context if needed


@dataclass
class ReasoningOutput:
    """
    Structured output from LLM reasoning.
    Strictly validated JSON schema.
    """
    status: str  # "success" or "error"
    reasoning: str  # Step-by-step reasoning process
    result: Dict[str, Any]  # Structured result based on role
    confidence: float  # 0.0 to 1.0
    risks: List[str]  # Identified risks or limitations
    recommendations: List[str]  # Actionable recommendations


class LLMInterface:
    """
    Interface to external LLM service.
    REASONING BOUNDARIES: This is ONLY a reasoning engine.
    - Takes curated facts as input
    - Returns structured reasoning as output
    - No memory, no file access, no execution
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        self.api_key = api_key or "dummy_key"  # TODO: Load from secure config
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def reason(self, input_data: ReasoningInput) -> ReasoningOutput:
        """
        Main reasoning interface.
        Takes curated facts, returns structured reasoning output.
        """
        try:
            # Get role-specific system prompt
            system_prompt = self._get_system_prompt(input_data.role)

            # Format user prompt with curated facts
            user_prompt = self._format_user_prompt(input_data)

            # Generate LLM response
            raw_response = self.generate_response(system_prompt, user_prompt)

            # Validate and extract structured output
            validated_output = self._validate_and_extract_output(raw_response, input_data.role)

            return validated_output

        except Exception as e:
            # Explicit failure handling - return structured error
            return ReasoningOutput(
                status="error",
                reasoning=f"LLM reasoning failed: {str(e)}",
                result={},
                confidence=0.0,
                risks=["LLM service unavailable", "Input validation failed"],
                recommendations=["Retry with simplified input", "Check LLM service status"]
            )

    def _get_system_prompt(self, role: AgentRole) -> str:
        """
        Get role-specific system prompt.
        Each role has clearly defined reasoning boundaries.
        """
        prompts = {
            AgentRole.ARCHITECT: """
You are an ArchitectAgent in DEVNOVA, an AI development environment.
REASONING BOUNDARIES:
- You analyze project architecture using provided facts only
- You suggest structural improvements and design patterns
- You identify architectural risks and scalability issues
- You NEVER access files, execute code, or modify anything

OUTPUT SCHEMA: JSON with these exact keys:
{
  "analysis": "string - your architectural analysis",
  "recommendations": ["array of specific recommendations"],
  "priority_areas": ["array of areas needing immediate attention"],
  "risks": ["array of architectural risks identified"],
  "confidence": 0.0-1.0
}
""",

            AgentRole.FEATURE: """
You are a FeatureAgent in DEVNOVA.
REASONING BOUNDARIES:
- You analyze feature requests using project facts
- You plan implementation approaches and dependencies
- You assess complexity and feasibility
- You NEVER write code or access files

OUTPUT SCHEMA: JSON with these exact keys:
{
  "proposed_features": ["array of feature breakdown"],
  "implementation_plan": ["array of implementation steps"],
  "dependencies": ["array of new dependencies needed"],
  "estimated_complexity": "HIGH/MEDIUM/LOW",
  "risks": ["array of implementation risks"],
  "confidence": 0.0-1.0
}
""",

            AgentRole.DEBUG: """
You are a DebugAgent in DEVNOVA.
REASONING BOUNDARIES:
- You analyze bugs using provided code facts and error info
- You identify root causes and suggest fixes
- You assess debugging complexity and testing needs
- You NEVER execute code or access files directly

OUTPUT SCHEMA: JSON with these exact keys:
{
  "root_cause_analysis": "string - your analysis of the issue",
  "fix_suggestions": ["array of specific fix recommendations"],
  "testing_recommendations": ["array of tests to verify fixes"],
  "risks": ["array of risks if fix is incorrect"],
  "confidence": 0.0-1.0
}
""",

            AgentRole.TEST: """
You are a TestAgent in DEVNOVA.
REASONING BOUNDARIES:
- You analyze code for test coverage using provided facts
- You suggest test cases and strategies
- You identify testing gaps and priorities
- You NEVER write tests or access code files

OUTPUT SCHEMA: JSON with these exact keys:
{
  "coverage_analysis": "string - assessment of current coverage",
  "suggested_tests": ["array of specific test cases"],
  "test_types": ["array of test types: unit/integration/etc"],
  "priority_order": ["array of testing priorities"],
  "risks": ["array of testing risks or gaps"],
  "confidence": 0.0-1.0
}
""",

            AgentRole.DOCS: """
You are a DocsAgent in DEVNOVA.
REASONING BOUNDARIES:
- You analyze documentation needs using code facts
- You identify gaps and suggest documentation structure
- You recommend documentation types and priorities
- You NEVER write documentation or access files

OUTPUT SCHEMA: JSON with these exact keys:
{
  "documentation_gaps": ["array of missing documentation"],
  "suggested_structure": ["array of documentation types needed"],
  "priority_order": ["array of documentation priorities"],
  "examples_needed": ["array of code examples to document"],
  "risks": ["array of documentation-related risks"],
  "confidence": 0.0-1.0
}
"""
        }
        return prompts.get(role, "You are a general reasoning agent. Output valid JSON only.")

    def _format_user_prompt(self, input_data: ReasoningInput) -> str:
        """
        Format user prompt with curated facts.
        Ensures only approved data types are passed to LLM.
        """
        prompt_parts = [
            f"TASK: {input_data.task_description}",
            "",
            "PROJECT FACTS:",
            json.dumps(input_data.project_facts, indent=2)
        ]

        if input_data.context_data:
            prompt_parts.extend([
                "",
                "ADDITIONAL CONTEXT:",
                json.dumps(input_data.context_data, indent=2)
            ])

        prompt_parts.extend([
            "",
            "INSTRUCTIONS:",
            "- Use ONLY the provided facts for your reasoning",
            "- Output ONLY valid JSON matching the schema",
            "- Be specific and actionable in your recommendations",
            "- Assess your confidence based on available information"
        ])

        return "\n".join(prompt_parts)

    def generate_response(self, system_prompt: str, user_prompt: str,
                         temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Generate response from LLM with structured constraints.
        """
        # Enforce JSON output
        enforced_user_prompt = f"""
{user_prompt}

CRITICAL: Respond ONLY with valid JSON. No text, no markdown, no explanations.
Your response must be parseable JSON matching the required schema exactly.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enforced_user_prompt}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}  # Enforce JSON
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            # TODO: Replace with actual API call
            # For now, return role-specific dummy responses
            return self._dummy_response_for_role(system_prompt)
        except Exception as e:
            return json.dumps({"error": f"LLM call failed: {str(e)}"})

    def _dummy_response_for_role(self, system_prompt: str) -> str:
        """
        Role-specific dummy responses for testing.
        TODO: Remove when real LLM is integrated.
        """
        if "ArchitectAgent" in system_prompt:
            return json.dumps({
                "analysis": "The project shows a modular architecture with clear separation between ingestion, analysis, memory, and state layers.",
                "recommendations": ["Consider adding error handling middleware", "Implement caching for performance"],
                "priority_areas": ["Memory persistence", "API validation"],
                "risks": ["Potential circular dependencies", "Scalability concerns with large codebases"],
                "confidence": 0.85
            })
        elif "FeatureAgent" in system_prompt:
            return json.dumps({
                "proposed_features": ["Add support for multiple languages", "Implement incremental analysis"],
                "implementation_plan": ["Extend language detectors", "Add diff-based updates"],
                "dependencies": ["Add AST parsers for new languages"],
                "estimated_complexity": "HIGH",
                "risks": ["Language parsing complexity", "Performance impact"],
                "confidence": 0.75
            })
        elif "DebugAgent" in system_prompt:
            return json.dumps({
                "root_cause_analysis": "Issue appears to be in the serialization logic where dataclasses are not properly converted.",
                "fix_suggestions": ["Add recursive serialization for nested dataclasses", "Implement proper JSON encoding"],
                "testing_recommendations": ["Test serialization with complex nested structures", "Add unit tests for data conversion"],
                "risks": ["Data loss during serialization", "Incompatible data formats"],
                "confidence": 0.9
            })
        elif "TestAgent" in system_prompt:
            return json.dumps({
                "coverage_analysis": "Current test coverage appears minimal with focus on basic functionality.",
                "suggested_tests": ["Add unit tests for all data models", "Integration tests for end-to-end flows"],
                "test_types": ["unit", "integration", "performance"],
                "priority_order": ["Core data models", "API endpoints", "Integration flows"],
                "risks": ["Untested error paths", "Performance regression risks"],
                "confidence": 0.8
            })
        elif "DocsAgent" in system_prompt:
            return json.dumps({
                "documentation_gaps": ["API usage examples", "Architecture decision records"],
                "suggested_structure": ["README with quickstart", "API reference docs", "Architecture diagrams"],
                "priority_order": ["Setup and usage docs", "API documentation", "Internal architecture docs"],
                "examples_needed": ["Basic project analysis workflow", "Custom agent implementation"],
                "risks": ["Onboarding difficulty", "Maintenance overhead"],
                "confidence": 0.7
            })
        else:
            return json.dumps({
                "analysis": "General analysis of the project structure and requirements.",
                "recommendations": ["Follow established patterns", "Ensure proper error handling"],
                "status": "success",
                "confidence": 0.6
            })

    def _validate_and_extract_output(self, raw_response: str, role: AgentRole) -> ReasoningOutput:
        """
        Validate LLM response against schema and extract structured output.
        Explicit failure handling with detailed error reporting.
        """
        try:
            # Parse JSON
            if not self.validate_response(raw_response):
                raise ValueError("Response is not valid JSON")

            data = json.loads(raw_response)

            # Validate required fields based on role
            required_fields = self._get_required_fields(role)
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")

            # Validate field types
            validation_errors = self._validate_field_types(data, role)
            if validation_errors:
                raise ValueError(f"Field validation errors: {validation_errors}")

            # Extract into ReasoningOutput
            return ReasoningOutput(
                status="success",
                reasoning=self._extract_reasoning(data),
                result=self._extract_role_result(data, role),
                confidence=data.get("confidence", 0.5),
                risks=data.get("risks", []),
                recommendations=data.get("recommendations", [])
            )

        except Exception as e:
            # Structured error output
            return ReasoningOutput(
                status="error",
                reasoning=f"Output validation failed: {str(e)}",
                result={"raw_response": raw_response},
                confidence=0.0,
                risks=["Invalid LLM output format", "Schema validation failure"],
                recommendations=["Check LLM prompt engineering", "Review output schema", "Implement fallback responses"]
            )

    def _get_required_fields(self, role: AgentRole) -> List[str]:
        """Get required fields for each role's output schema."""
        base_fields = ["confidence", "risks"]
        role_fields = {
            AgentRole.ARCHITECT: ["analysis", "recommendations", "priority_areas"],
            AgentRole.FEATURE: ["proposed_features", "implementation_plan", "dependencies", "estimated_complexity"],
            AgentRole.DEBUG: ["root_cause_analysis", "fix_suggestions", "testing_recommendations"],
            AgentRole.TEST: ["coverage_analysis", "suggested_tests", "test_types", "priority_order"],
            AgentRole.DOCS: ["documentation_gaps", "suggested_structure", "priority_order", "examples_needed"]
        }
        return base_fields + role_fields.get(role, [])

    def _validate_field_types(self, data: Dict[str, Any], role: AgentRole) -> List[str]:
        """Validate field types in the response."""
        errors = []

        # Confidence should be a number between 0 and 1
        if not isinstance(data.get("confidence"), (int, float)) or not (0.0 <= data["confidence"] <= 1.0):
            errors.append("confidence must be a number between 0.0 and 1.0")

        # Risks and recommendations should be lists
        for field in ["risks", "recommendations"]:
            if field in data and not isinstance(data[field], list):
                errors.append(f"{field} must be a list")

        # Role-specific validations
        if role == AgentRole.FEATURE and "estimated_complexity" in data:
            if data["estimated_complexity"] not in ["HIGH", "MEDIUM", "LOW"]:
                errors.append("estimated_complexity must be HIGH/MEDIUM/LOW")

        return errors

    def _extract_reasoning(self, data: Dict[str, Any]) -> str:
        """Extract reasoning text from validated response."""
        # Use the primary analysis field as reasoning
        reasoning_fields = ["analysis", "root_cause_analysis", "coverage_analysis"]
        for field in reasoning_fields:
            if field in data and isinstance(data[field], str):
                return data[field]
        return "Reasoning completed successfully"

    def _extract_role_result(self, data: Dict[str, Any], role: AgentRole) -> Dict[str, Any]:
        """Extract role-specific result data."""
        # Return all validated fields except confidence/risks/recommendations
        result = {k: v for k, v in data.items() if k not in ["confidence", "risks", "recommendations"]}
        return result

    def validate_response(self, response: str) -> bool:
        """Validate that response is proper JSON."""
        try:
            json.loads(response)
            return True
        except json.JSONDecodeError:
            return False

    def extract_structured_output(self, response: str) -> Dict[str, Any]:
        """Legacy method - kept for compatibility."""
        if not self.validate_response(response):
            return {"error": "Invalid JSON response from LLM"}
        return json.loads(response)


# Configuration and factory
class LLMConfig:
    """Configuration for LLM interface."""

    def __init__(self, provider: str = "openai", model: str = "gpt-4", api_key: str = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Load config from environment variables."""
        # TODO: Implement secure config loading
        return cls()


def create_llm_interface(config: LLMConfig = None) -> LLMInterface:
    """
    Factory function to create LLM interface.
    """
    if config is None:
        config = LLMConfig.from_env()

    if config.provider == "openai":
        return LLMInterface(config.api_key, config.model)
    else:
        # TODO: Support other providers
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


# CLI interface for testing
if __name__ == '__main__':
    from devnova.state.api import ProjectStateAPI

    # Test with actual project data
    api = ProjectStateAPI('D:\\DEVNOVA\\devnova')
    facts = api.get_architecture_facts()

    llm = LLMInterface()
    input_data = ReasoningInput(
        role=AgentRole.ARCHITECT,
        task_description="Analyze the current project architecture and suggest improvements",
        project_facts=facts
    )

    result = llm.reason(input_data)
    print("Reasoning Result:")
    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence}")
    print(f"Reasoning: {result.reasoning[:100]}...")
    print(f"Risks: {result.risks}")
    print(f"Recommendations: {len(result.recommendations)} items")