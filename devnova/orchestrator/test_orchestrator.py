"""
Test Orchestrator - Testing utilities for orchestration

This module provides testing utilities for the orchestrator
and agent coordination.
"""

import unittest
from typing import Dict, Any
from .orchestrator import Orchestrator


class TestOrchestrator(unittest.TestCase):
    """Test cases for the Orchestrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = Orchestrator()

    def test_initialization(self):
        """Test orchestrator initialization."""
        self.assertIsInstance(self.orchestrator.agents, dict)
        self.assertIn('architect', self.orchestrator.agents)
        self.assertIn('feature', self.orchestrator.agents)
        self.assertIn('debug', self.orchestrator.agents)
        self.assertIn('test', self.orchestrator.agents)
        self.assertIn('docs', self.orchestrator.agents)

    def test_intent_routing(self):
        """Test that intents are routed to appropriate agents."""
        # Test architecture intent
        self.assertTrue(self.orchestrator._is_architecture_intent("refactor this code"))
        self.assertTrue(self.orchestrator._is_architecture_intent("design pattern"))

        # Test feature intent
        self.assertTrue(self.orchestrator._is_feature_intent("add new feature"))
        self.assertTrue(self.orchestrator._is_feature_intent("implement api"))

        # Test debug intent
        self.assertTrue(self.orchestrator._is_debug_intent("fix this bug"))
        self.assertTrue(self.orchestrator._is_debug_intent("error handling"))

        # Test test intent
        self.assertTrue(self.orchestrator._is_test_intent("add unit tests"))
        self.assertTrue(self.orchestrator._is_test_intent("test coverage"))


if __name__ == '__main__':
    unittest.main()