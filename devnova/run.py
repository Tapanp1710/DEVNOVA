#!/usr/bin/env python3
"""
DEVNOVA Main Entry Point

This is the main entry point for running DEVNOVA.
"""

import sys
import argparse
import os
from pathlib import Path
from .orchestrator.central_orchestrator import CentralOrchestrator


def main():
    """Main entry point for DEVNOVA core and backend."""
    parser = argparse.ArgumentParser(description="DEVNOVA - AI Developer Operating Environment")
    parser.add_argument(
        "command",
        choices=["init", "status", "analyze", "web"],
        help="Command to run"
    )
    parser.add_argument(
        "--project",
        "-p",
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("DEVNOVA_PORT", "8000")),
        help="Port for FastAPI backend (default from DEVNOVA_PORT env)"
    )

    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    if not project_root.exists():
        print(f"Error: Project path {project_root} does not exist")
        sys.exit(1)

    orchestrator = CentralOrchestrator(str(project_root))

    if args.command == "init":
        print("Initializing DEVNOVA...")
        results = orchestrator.initialize_project()
        print("705 Initialization complete!")
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

    elif args.command == "web":
        # Start FastAPI backend
        import subprocess
        backend_path = Path(__file__).parent.parent / "web-platform" / "backend" / "main.py"
        print(f"Starting DEVNOVA FastAPI backend on port {args.port}...")
        subprocess.run([
            sys.executable,
            str(backend_path),
            "--port", str(args.port)
        ])

    elif args.command == "analyze":
        print("Running analysis...")
        # Placeholder for analysis command
        print("Analysis complete (placeholder)")


if __name__ == "__main__":
    main()