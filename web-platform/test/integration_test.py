# web-platform/test/integration_test.py
"""
Integration Test for DEVNOVA Web Platform

Tests the integration architecture without requiring a running server.
Validates that the web platform can properly interface with DEVNOVA.
"""

import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'devnova'))

def test_devnova_integration():
    """Test that web platform can import and use DEVNOVA interfaces."""
    print("Testing DEVNOVA integration...")

    try:
        from devnova.ide.interfaces import (
            IDEContext, SuggestionRequest, ExplanationRequest,
            create_devnova_integration
        )
        print("✅ DEVNOVA interface imports successful")

        # Test interface creation
        devnova = create_devnova_integration()
        print("✅ DEVNOVA integration instance created")

        # Test context creation
        context = IDEContext(
            workspace_path=str(project_root / 'devnova'),
            active_file='devnova/state/api.py',
            cursor_position={'line': 42, 'column': 8},
            selected_text='def get_architecture_facts(self):'
        )
        print("✅ IDE context creation successful")

        # Test suggestion request
        suggestion_request = SuggestionRequest(
            context=context,
            suggestion_type='refactor',
            user_query='How can I improve this code?'
        )
        print("✅ Suggestion request creation successful")

        # Test DEVNOVA call (will use mock)
        response = devnova.get_suggestions(suggestion_request)
        print("✅ DEVNOVA suggestion call successful")
        print(f"   Response type: {type(response)}")
        print(f"   Has suggestions: {len(response.suggestions) if hasattr(response, 'suggestions') else 'N/A'}")

        # Test explanation request
        explanation_request = ExplanationRequest(
            context=context,
            explanation_type='code_explanation',
            target_code='def get_architecture_facts(self):'
        )
        print("✅ Explanation request creation successful")

        # Test DEVNOVA explanation call
        explanation_response = devnova.get_explanation(explanation_request)
        print("✅ DEVNOVA explanation call successful")
        print(f"   Response type: {type(explanation_response)}")

        return True

    except Exception as e:
        print(f"❌ DEVNOVA integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_platform_imports():
    """Test that web platform components can be imported."""
    print("\nTesting web platform imports...")

    try:
        # Add web platform backend to path
        web_backend_path = Path(__file__).parent.parent / 'backend'
        sys.path.insert(0, str(web_backend_path))

        # Test FastAPI models
        from main import DEVINOVARequest, DEVINOVAResponse
        print("✅ FastAPI models import successful")

        # Test utility functions exist
        from main import validate_path_safety, get_project_snapshot
        print("✅ Utility functions import successful")

        return True

    except Exception as e:
        print(f"❌ Web platform imports test failed: {e}")
        return False

def test_safety_boundaries():
    """Test that safety boundaries are properly implemented."""
    print("\nTesting safety boundaries...")

    try:
        # Add web platform backend to path
        web_backend_path = Path(__file__).parent.parent / 'backend'
        sys.path.insert(0, str(web_backend_path))

        from main import PROJECT_ROOT, validate_path_safety, get_project_snapshot

        # Test path validation
        try:
            # This should work (within sandbox)
            valid_path = validate_path_safety('devnova/state/api.py')
            print("✅ Valid path accepted")
        except:
            print("❌ Valid path rejected")
            return False

        try:
            # This should fail (outside sandbox)
            invalid_path = validate_path_safety('../../../outside.txt')
            print("❌ Invalid path accepted (security issue!)")
            return False
        except:
            print("✅ Invalid path properly rejected")

        # Test project snapshot generation
        snapshot = get_project_snapshot()
        print(f"✅ Project snapshot generated: {len(snapshot.files)} files")

        return True

    except Exception as e:
        print(f"❌ Safety boundary test failed: {e}")
        return False

def test_data_contracts():
    """Test that data contracts are properly defined."""
    print("\nTesting data contracts...")

    try:
        from devnova.ide.interfaces import IDEContext, SuggestionRequest, SuggestionResponse

        # Test data contract creation
        context = IDEContext(
            workspace_path='/test',
            active_file='test.py',
            cursor_position={'line': 1, 'column': 0}
        )

        request = SuggestionRequest(
            context=context,
            suggestion_type='test',
            user_query='test query'
        )

        # Mock response structure
        response = SuggestionResponse(
            request_id='test_123',
            suggestions=[{'type': 'test', 'content': 'test suggestion'}],
            reasoning='test reasoning',
            confidence=0.8,
            processing_time=0.1,
            agent_used='TestAgent'
        )

        print("✅ Data contracts properly defined")
        print(f"   Context fields: {len(context.__dataclass_fields__)}")
        print(f"   Request fields: {len(request.__dataclass_fields__)}")
        print(f"   Response fields: {len(response.__dataclass_fields__)}")

        return True

    except Exception as e:
        print(f"❌ Data contract test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🔗 DEVNOVA Web Platform Integration Tests")
    print("=" * 50)

    tests = [
        ("DEVNOVA Integration", test_devnova_integration),
        ("Web Platform Imports", test_web_platform_imports),
        ("Safety Boundaries", test_safety_boundaries),
        ("Data Contracts", test_data_contracts)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append(result)

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"  {test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("✅ Web Platform + DEVNOVA integration is working correctly")
        print("🔒 Safety boundaries are properly implemented")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Integration may have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())