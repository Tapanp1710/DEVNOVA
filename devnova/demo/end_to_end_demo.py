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

    print("\n==============================")
    print("DEVNOVA Interactive AI Demo")
    print("==============================\n")

    # Get user input for code and intent
    file_path = input("Enter file path (relative to project root): ").strip()
    code_snippet = input("Paste code to analyze (or leave blank to skip): ").strip()
    intent = input("Describe your intent (e.g., 'add error handling', 'explain this code'): ").strip()
    explanation_type = input("Request type ('explain' or 'suggest'): ").strip().lower()
    language = file_path.split('.')[-1] if '.' in file_path else "python"

    context = IDEContext(
        file_path=file_path or "devnova/state/api.py",
        cursor_position={"line": 1, "column": 1},
        selected_text=code_snippet if code_snippet else None,
        project_root=str(project_root),
        language=language
    )

    if explanation_type == "explain":
        print("\n🔍 Getting code explanation...")
        explanation_request = ExplanationRequest(
            context=context,
            code_to_explain=code_snippet,
            explanation_type="general"
        )
        try:
            explanation_response = client.get_explanation(explanation_request)
            for expl in explanation_response.explanations:
                print(f"\n--- Explanation ---\nTitle: {expl.title}\nExplanation: {expl.explanation}\nKey Points: {expl.key_points}\nRelated Concepts: {expl.related_concepts}\nConfidence: {expl.confidence:.2f}")
        except Exception as e:
            print(f"   ⚠️  Explanations failed: {e}")
    elif explanation_type == "suggest":
        print("\n💡 Getting AI suggestions...")
        suggestions_request = SuggestionRequest(
            context=context,
            intent=intent,
            max_suggestions=3
        )
        try:
            suggestions_response = client.get_suggestions(suggestions_request)
            for sugg in suggestions_response.suggestions:
                print(f"\n--- Suggestion ---\nTitle: {sugg.title}\nDescription: {sugg.description}\nReasoning: {sugg.reasoning}\nConfidence: {sugg.confidence:.2f}")
        except Exception as e:
            print(f"   ⚠️  Suggestions failed: {e}")
    else:
        print("Invalid request type. Please enter 'explain' or 'suggest'.")


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