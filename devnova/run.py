#!/usr/bin/env python3
"""
DEVNOVA Runner

Demonstrates end-to-end functionality of the DEVNOVA system.
"""

import sys
import os
import json
from devnova.ingestion.engine import ProjectIngestionEngine
from devnova.analysis.analyzer import StaticAnalysisLayer
from devnova.memory.memory import ProjectMemory
from devnova.state.api import ProjectStateAPI
from devnova.orchestrator.orchestrator import TaskOrchestrator


def main():
    if len(sys.argv) != 2:
        print("Usage: python run.py <project_path>")
        print("Example: python run.py /path/to/your/python/project")
        sys.exit(1)

    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)

    print("🚀 Starting DEVNOVA analysis...")
    print(f"📁 Project: {project_path}")
    print()

    try:
        # 1. Ingestion
        print("📥 Phase 1: Project Ingestion")
        ingestion_engine = ProjectIngestionEngine(project_path)
        project_state = ingestion_engine.scan_project()
        print(f"   Found {project_state['metadata']['total_files']} files")
        print(f"   Languages: {', '.join(project_state['metadata']['languages'])}")
        print()

        # 2. Analysis
        print("🔍 Phase 2: Static Analysis")
        analysis_layer = StaticAnalysisLayer(project_state)
        analysis_results = analysis_layer.analyze_all_python_files()
        print(f"   Analyzed {analysis_results['summary']['total_files_analyzed']} Python files")
        print()

        # 3. Memory Update
        print("🧠 Phase 3: Memory Update")
        memory = ProjectMemory()
        memory.update_from_analysis(analysis_results)
        memory.save()
        print("   Memory updated and persisted")
        print()

        # 4. State API Demo
        print("📊 Phase 4: State API Demo")
        state_api = ProjectStateAPI(project_path)
        state_api.refresh_state()  # Refresh to populate state
        facts = state_api.get_architecture_facts()
        print(f"   Architecture Facts: {json.dumps(facts, indent=2)}")
        print()

        # 5. Agent Demo
        print("🤖 Phase 5: Agent Demo")
        orchestrator = TaskOrchestrator(project_path)
        
        # Example task
        task = {
            'type': 'architecture_review',
            'description': 'Review the overall project architecture and suggest improvements'
        }
        
        result = orchestrator.process_task(task)
        print(f"   Task processed by {result['agent']}")
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   Result keys: {list(result['result']['result'].keys())}")
        print()

        print("✅ DEVNOVA analysis complete!")
        print("\nTo explore further:")
        print("- Check .devnova/ directory for cached state")
        print("- Run agents with: python -m devnova.orchestrator.orchestrator <project_path> <task_type> <description>")
        print("- Query state with: python -m devnova.state.api <project_path>")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()