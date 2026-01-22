#!/usr/bin/env python3
"""
DEVNOVA Main Entry Point

This is the main entry point for running DEVNOVA.
"""

import sys
import argparse
from pathlib import Path
from .orchestrator.central_orchestrator import CentralOrchestrator


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="DEVNOVA - AI Developer Operating Environment")
    parser.add_argument(
        "command",
        choices=["init", "status", "analyze"],
        help="Command to run"
    )
    parser.add_argument(
        "--project",
        "-p",
        default=".",
        help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    # Resolve project path
    project_root = Path(args.project).resolve()
    if not project_root.exists():
        print(f"Error: Project path {project_root} does not exist")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = CentralOrchestrator(str(project_root))

    if args.command == "init":
        print("Initializing DEVNOVA...")
        results = orchestrator.initialize_project()
        print("✅ Initialization complete!")
        print(f"   Files scanned: {results['files_scanned']}")
        print(f"   Languages: {', '.join(results['languages_detected'])}")
        print(f"   Functions found: {results['functions_found']}")
        print(f"   Classes found: {results['classes_found']}")

    elif args.command == "status":
        status = orchestrator.get_project_status()
        print("DEVNOVA Project Status:")
        print(f"   Project: {status['project_root']}")
        print(f"   Files: {status['total_files']}")
        print(f"   Functions: {status['total_functions']}")
        print(f"   Classes: {status['total_classes']}")
        print(f"   Languages: {', '.join(status['languages'])}")
        print("   Memory:")
        print(f"     Graph nodes: {status['memory_status']['graph_nodes']}")
        print(f"     Graph edges: {status['memory_status']['graph_edges']}")
        print(f"     Semantic concepts: {status['memory_status']['semantic_concepts']}")

    elif args.command == "analyze":
        print("Running analysis...")
        # Placeholder for analysis command
        print("Analysis complete (placeholder)")


if __name__ == "__main__":
    main()