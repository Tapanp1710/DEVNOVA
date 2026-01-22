#!/usr/bin/env python3
"""
End-to-End Demo for DEVNOVA

This script demonstrates the complete DEVNOVA workflow:
1. Project initialization and ingestion
2. Code analysis and memory building
3. Agent coordination and reasoning
4. IDE integration simulation
"""

import sys
import os
from pathlib import Path

# Add devnova to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from devnova.orchestrator.central_orchestrator import CentralOrchestrator
from devnova.ide.interfaces import (
    DEVNovaClient, IDEContext, SuggestionRequest, 
    ExplanationRequest, RiskAnalysisRequest
)


def demo_project_initialization():
    """Demonstrate project initialization."""
    print("🚀 DEVNOVA End-to-End Demo")
    print("=" * 50)

    # Use the current DEVNOVA project as the demo project
    project_root = Path(__file__).parent.parent

    print(f"📁 Initializing project: {project_root}")
    orchestrator = CentralOrchestrator(str(project_root))

    # Initialize project
    results = orchestrator.initialize_project()

    print("✅ Project initialized successfully!")
    print(f"   📊 Files scanned: {results['files_scanned']}")
    print(f"   🏷️  Languages detected: {', '.join(results['languages_detected'])}")
    print(f"   🔧 Functions found: {results['functions_found']}")
    print(f"   📦 Classes found: {results['classes_found']}")
    print()


def demo_ide_integration():
    """Demonstrate IDE integration capabilities."""
    print("🖥️  IDE Integration Demo")
    print("-" * 30)

    project_root = Path(__file__).parent.parent
    client = DEVNovaClient(str(project_root))

    # Simulate IDE context
    context = IDEContext(
        file_path="devnova/state/api.py",
        cursor_position={"line": 50, "column": 10},
        selected_text="def get_project_facts(self)",
        project_root=str(project_root),
        language="python"
    )

    # Test suggestions
    print("💡 Getting code suggestions...")
    suggestions_request = SuggestionRequest(
        context=context,
        intent="add error handling to this function",
        max_suggestions=3
    )

    try:
        suggestions_response = client.get_suggestions(suggestions_request)
        print(f"   📝 Generated {len(suggestions_response.suggestions)} suggestions")
        for i, suggestion in enumerate(suggestions_response.suggestions[:2], 1):
            print(f"      {i}. {suggestion.title}")
    except Exception as e:
        print(f"   ⚠️  Suggestions demo failed: {e}")

    # Test explanations
    print("\n🔍 Getting code explanations...")
    explanation_request = ExplanationRequest(
        context=context,
        code_to_explain="def get_project_facts(self, force_reload: bool = False) -> ProjectFacts:",
        explanation_type="general"
    )

    try:
        explanation_response = client.get_explanation(explanation_request)
        print(f"   📖 Generated {len(explanation_response.explanations)} explanations")
        if explanation_response.explanations:
            print(f"      Title: {explanation_response.explanations[0].title}")
    except Exception as e:
        print(f"   ⚠️  Explanations demo failed: {e}")

    # Test risk analysis
    print("\n⚠️  Analyzing code risks...")
    risk_request = RiskAnalysisRequest(
        context=context,
        code_to_analyze="if True: pass",
        analysis_type="general"
    )

    try:
        risk_response = client.analyze_risks(risk_request)
        print(f"   🚨 Found {len(risk_response.risks)} risks")
        print(f"   📊 Overall risk score: {risk_response.overall_score:.2f}")
    except Exception as e:
        print(f"   ⚠️  Risk analysis demo failed: {e}")

    print()


def demo_agent_coordination():
    """Demonstrate agent coordination."""
    print("🤖 Agent Coordination Demo")
    print("-" * 30)

    project_root = Path(__file__).parent.parent
    orchestrator = CentralOrchestrator(str(project_root))

    # Test different types of requests
    test_requests = [
        ("architecture", "how should I structure this codebase?"),
        ("feature", "add user authentication"),
        ("debug", "fix this null pointer exception"),
        ("test", "add unit tests for this function"),
        ("docs", "document this API endpoint")
    ]

    for agent_type, intent in test_requests:
        print(f"🎯 Testing {agent_type} agent with: '{intent}'")
        # Note: This would normally go through the orchestrator's process_request
        # but for demo purposes, we'll just show the routing logic
        print(f"   → Would route to: {agent_type} agent")

    print()


def main():
    """Run the complete demo."""
    try:
        demo_project_initialization()
        demo_ide_integration()
        demo_agent_coordination()

        print("🎉 Demo completed successfully!")
        print("\n💡 DEVNOVA is now ready for development assistance.")
        print("   Use the web platform for interactive coding support,")
        print("   or integrate directly with your IDE/editor.")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())