"""
LLM Interface - Centralized interface for LLM interactions

This module provides a centralized interface for all LLM interactions,
enforcing role prompts, input constraints, and structured JSON outputs.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


import os
import requests
import time

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            Raw response string from the LLM
        """
        pass


class OpenRouterLLMProvider(LLMProvider):
    """OpenRouter LLM provider implementation."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("LLM_MODEL", "openrouter/auto")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "60"))
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set in environment variables.")

    def generate_response(self, prompt: str, **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get("max_tokens", 1024)
        }
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                # OpenRouter returns choices[0].message.content
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return json.dumps({
                    "reasoning": f"LLM API error: {str(e)}",
                    "confidence": 0.0,
                    "recommendations": ["Check API key, network, or provider status"],
                    "structured_output": False
                })

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and development."""

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Return a mock response."""
        return json.dumps({
            "reasoning": "This is a mock response for development purposes.",
            "confidence": 0.8,
            "recommendations": ["Consider implementing this feature", "Add proper error handling"],
            "structured_output": True
        })


class LLMInterface:
    """
    Centralized interface for LLM interactions.

    This class enforces role prompts, input constraints, and structured
    JSON outputs. It never stores memory and acts purely as a reasoning layer.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        provider_name = os.getenv("LLM_PROVIDER", "openrouter").lower()
        if provider:
            self.provider = provider
        elif provider_name == "openrouter":
            self.provider = OpenRouterLLMProvider()
        else:
            self.provider = MockLLMProvider()

    def reason_about_architecture(self, facts: Dict[str, Any], question: str) -> Dict[str, Any]:
        """
        Get architectural reasoning from the LLM.

        Args:
            facts: Curated project facts
            question: Specific architectural question

        Returns:
            Structured reasoning response
        """
        prompt = self._build_architecture_prompt(facts, question)
        response = self.provider.generate_response(prompt)
        return self._parse_structured_response(response)

    def reason_about_feature(self, facts: Dict[str, Any], feature_request: str) -> Dict[str, Any]:
        """
        Get feature planning reasoning from the LLM.

        Args:
            facts: Curated project facts
            feature_request: Feature implementation request

        Returns:
            Structured reasoning response
        """
        prompt = self._build_feature_prompt(facts, feature_request)
        response = self.provider.generate_response(prompt)
        return self._parse_structured_response(response)

    def reason_about_debug(self, facts: Dict[str, Any], error_info: str) -> Dict[str, Any]:
        """
        Get debugging reasoning from the LLM.

        Args:
            facts: Curated project facts
            error_info: Error or bug information

        Returns:
            Structured reasoning response
        """
        prompt = self._build_debug_prompt(facts, error_info)
        response = self.provider.generate_response(prompt)
        return self._parse_structured_response(response)

    def reason_about_testing(self, facts: Dict[str, Any], test_context: str) -> Dict[str, Any]:
        """
        Get testing reasoning from the LLM.

        Args:
            facts: Curated project facts
            test_context: Testing context or requirements

        Returns:
            Structured reasoning response
        """
        prompt = self._build_test_prompt(facts, test_context)
        response = self.provider.generate_response(prompt)
        return self._parse_structured_response(response)

    def reason_about_docs(self, facts: Dict[str, Any], docs_context: str) -> Dict[str, Any]:
        """
        Get documentation reasoning from the LLM.

        Args:
            facts: Curated project facts
            docs_context: Documentation context or requirements

        Returns:
            Structured reasoning response
        """
        prompt = self._build_docs_prompt(facts, docs_context)
        response = self.provider.generate_response(prompt)
        return self._parse_structured_response(response)

    def _build_architecture_prompt(self, facts: Dict[str, Any], question: str) -> str:
        """Build architecture reasoning prompt."""
        return f"""
You are an expert software architect analyzing a codebase.

PROJECT FACTS:
- Total files: {facts.get('total_files', 0)}
- Languages: {', '.join(facts.get('languages', []))}
- Total functions: {facts.get('total_functions', 0)}
- Total classes: {facts.get('total_classes', 0)}

QUESTION: {question}

Provide a structured analysis with:
1. Key architectural insights
2. Potential issues or improvements
3. Recommended actions
4. Risk assessment

Respond in JSON format with keys: reasoning, confidence (0-1), recommendations (array)
"""

    def _build_feature_prompt(self, facts: Dict[str, Any], feature_request: str) -> str:
        """Build feature planning prompt."""
        return f"""
You are a senior software engineer planning feature implementation.

PROJECT CONTEXT:
- Total files: {facts.get('total_files', 0)}
- Languages: {', '.join(facts.get('languages', []))}
- Existing functions: {facts.get('total_functions', 0)}

FEATURE REQUEST: {feature_request}

Provide implementation planning with:
1. Technical approach
2. Required components/modules
3. Integration points
4. Complexity assessment
5. Testing strategy

Respond in JSON format with keys: reasoning, confidence (0-1), recommendations (array)
"""

    def _build_debug_prompt(self, facts: Dict[str, Any], error_info: str) -> str:
        """Build debugging prompt."""
        return f"""
You are an expert debugger analyzing a software issue.

PROJECT CONTEXT:
- Languages: {', '.join(facts.get('languages', []))}
- Code structure: {facts.get('total_functions', 0)} functions, {facts.get('total_classes', 0)} classes

ERROR/BUG INFO: {error_info}

Provide debugging analysis with:
1. Likely root causes
2. Debugging steps
3. Fix suggestions
4. Prevention measures

Respond in JSON format with keys: reasoning, confidence (0-1), recommendations (array)
"""

    def _build_test_prompt(self, facts: Dict[str, Any], test_context: str) -> str:
        """Build testing prompt."""
        return f"""
You are a testing expert analyzing test coverage and strategy.

PROJECT CONTEXT:
- Total files: {facts.get('total_files', 0)}
- Languages: {', '.join(facts.get('languages', []))}
- Existing functions: {facts.get('total_functions', 0)}

TEST CONTEXT: {test_context}

Provide testing recommendations with:
1. Coverage gaps
2. Test types needed
3. Test priorities
4. Best practices

Respond in JSON format with keys: reasoning, confidence (0-1), recommendations (array)
"""

    def _build_docs_prompt(self, facts: Dict[str, Any], docs_context: str) -> str:
        """Build documentation prompt."""
        return f"""
You are a technical writer analyzing documentation needs.

PROJECT CONTEXT:
- Total files: {facts.get('total_files', 0)}
- Languages: {', '.join(facts.get('languages', []))}
- Code elements: {facts.get('total_functions', 0)} functions, {facts.get('total_classes', 0)} classes

DOCS CONTEXT: {docs_context}

Provide documentation recommendations with:
1. Documentation gaps
2. Documentation types needed
3. Best practices
4. Tool recommendations

Respond in JSON format with keys: reasoning, confidence (0-1), recommendations (array)
"""

    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format.

        Args:
            response: Raw LLM response (may be JSON, or JSON inside markdown code block)

        Returns:
            Structured response dict
        """
        import re, json
        raw = response.strip() if isinstance(response, str) else response
        # Try to extract JSON from markdown code block
        if isinstance(raw, str):
            # Match ```json ... ``` or ``` ... ```
            codeblock = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", raw, re.IGNORECASE)
            if codeblock:
                raw = codeblock.group(1).strip()
        try:
            result = json.loads(raw)
            # Clamp confidence if present
            if isinstance(result, dict) and "confidence" in result:
                result["confidence"] = self._clamp_confidence(result["confidence"])
            return result
        except Exception:
            # Fallback for non-JSON responses
            return {
                "reasoning": response,
                "confidence": self._clamp_confidence(0.7),
                "recommendations": ["Response parsing failed - review manually"],
                "structured_output": False
            }

    def _clamp_confidence(self, confidence: float) -> float:
        """
        Clamp confidence to the allowed range [0.70, 0.95].
        """
        try:
            c = float(confidence)
        except Exception:
            return 0.7
        if c > 0.95:
            return 0.95
        if c < 0.70:
            return 0.70
        return c