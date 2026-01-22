"""
Test LLM Interface - Testing utilities for LLM interactions

This module provides testing utilities and mock implementations
for LLM interactions during development and testing.
"""

import json
from typing import Dict, Any
from .interface import LLMInterface, LLMProvider


class TestLLMProvider(LLMProvider):
    """Test LLM provider with predictable responses."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_prompt = ""

    def generate_response(self, prompt: str, **kwargs) -> str:
        """Return test response based on prompt content."""
        self.call_count += 1
        self.last_prompt = prompt

        # Return specific responses based on prompt content
        if "architecture" in prompt.lower():
            return json.dumps({
                "reasoning": "Test architecture analysis",
                "confidence": 0.9,
                "recommendations": ["Consider modular design", "Add error handling"]
            })

        elif "feature" in prompt.lower():
            return json.dumps({
                "reasoning": "Test feature planning",
                "confidence": 0.8,
                "recommendations": ["Implement incrementally", "Add unit tests"]
            })

        elif "debug" in prompt.lower():
            return json.dumps({
                "reasoning": "Test debugging analysis",
                "confidence": 0.7,
                "recommendations": ["Check input validation", "Add logging"]
            })

        elif "test" in prompt.lower():
            return json.dumps({
                "reasoning": "Test coverage analysis",
                "confidence": 0.8,
                "recommendations": ["Add unit tests", "Increase coverage"]
            })

        else:
            return json.dumps({
                "reasoning": "Generic test response",
                "confidence": 0.5,
                "recommendations": ["Review implementation"]
            })


class TestLLMInterface(LLMInterface):
    """Test interface for LLM interactions."""

    def __init__(self):
        super().__init__(TestLLMProvider())

    def get_call_stats(self) -> Dict[str, Any]:
        """Get statistics about LLM calls."""
        provider = self.provider
        if hasattr(provider, 'call_count'):
            return {
                "total_calls": provider.call_count,
                "last_prompt": provider.last_prompt[:100] + "..." if len(provider.last_prompt) > 100 else provider.last_prompt
            }
        return {"total_calls": 0, "last_prompt": ""}