"""
Central Orchestrator - Main entry point for DEVNOVA orchestration

This module provides the main orchestrator class that coordinates
all DEVNOVA subsystems and provides the primary API.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from .orchestrator import Orchestrator
from ..ingestion.engine import IngestionEngine
from ..analysis.analyzer import AnalysisEngine
from ..memory.memory import MemorySystem
from ..state.api import ProjectStateAPI


class CentralOrchestrator:
    """
    Central orchestrator for the DEVNOVA system.

    This is the main entry point that coordinates all subsystems:
    ingestion, analysis, memory, state, and agent orchestration.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.memory = MemorySystem()

        # Initialize subsystems
        self.ingestion = IngestionEngine()
        self.analysis = AnalysisEngine()
        self.state_api = ProjectStateAPI(str(project_root))
        self.orchestrator = Orchestrator()

        # Set project context for agents
        self.orchestrator.set_project_context(str(project_root))

    def initialize_project(self) -> Dict[str, Any]:
        """
        Initialize DEVNOVA for a project.

        This performs initial ingestion and analysis to build
        the project understanding.

        Returns:
            Project initialization results
        """
        print(f"Initializing DEVNOVA for project: {self.project_root}")

        # Step 1: Ingest project
        print("Step 1: Ingesting project...")
        project_metadata = self.ingestion.scan_project(str(self.project_root))

        # Step 2: Analyze code
        print("Step 2: Analyzing code...")
        analyzers = self.analysis.analyze_directory(str(self.project_root))

        # Step 3: Build memory
        print("Step 3: Building memory...")
        self._build_memory_from_analysis(analyzers)

        # Step 4: Update state
        print("Step 4: Updating project state...")
        # State API automatically loads from memory

        results = {
            "project_root": str(self.project_root),
            "files_scanned": project_metadata["total_files"],
            "languages_detected": project_metadata["languages"],
            "functions_found": len(self.analysis.get_all_functions(analyzers)),
            "classes_found": len(self.analysis.get_all_classes(analyzers)),
            "status": "initialized"
        }

        print(f"DEVNOVA initialization complete: {results}")
        return results

    def _build_memory_from_analysis(self, analyzers: Dict[str, Any]):
        """Build memory structures from analysis results."""
        # Add files to graph memory
        for file_path, analyzer in analyzers.items():
            self.memory.graph_memory.add_node(
                file_path,
                "file",
                {"language": "python", "path": file_path}
            )

            # Add functions
            for func in analyzer.functions:
                func_id = f"{file_path}::{func.name}"
                self.memory.graph_memory.add_node(
                    func_id,
                    "function",
                    {
                        "name": func.name,
                        "file": file_path,
                        "line_start": func.line_start,
                        "parameters": func.parameters,
                        "complexity": func.complexity
                    }
                )

                # Connect function to file
                self.memory.graph_memory.add_edge(
                    file_path, func_id, "contains"
                )

            # Add classes
            for cls in analyzer.classes:
                class_id = f"{file_path}::{cls.name}"
                self.memory.graph_memory.add_node(
                    class_id,
                    "class",
                    {
                        "name": cls.name,
                        "file": file_path,
                        "methods": cls.methods,
                        "inherits_from": cls.inherits_from
                    }
                )

                # Connect class to file
                self.memory.graph_memory.add_edge(
                    file_path, class_id, "contains"
                )

                # Connect methods to class
                for method_name in cls.methods:
                    method_id = f"{file_path}::{method_name}"
                    if self.memory.graph_memory.get_node(method_id):
                        self.memory.graph_memory.add_edge(
                            class_id, method_id, "has_method"
                        )

        # Save memory
        self.memory.save_all()

    def get_project_status(self) -> Dict[str, Any]:
        """
        Get current project status and understanding.

        Returns:
            Project status information
        """
        facts = self.state_api.get_project_facts()

        return {
            "project_root": str(self.project_root),
            "total_files": len(facts.files),
            "total_functions": len(facts.functions),
            "total_classes": len(facts.classes),
            "languages": list(set(f.language for f in facts.files)),
            "memory_status": {
                "graph_nodes": len(self.memory.graph_memory.graph.nodes),
                "graph_edges": len(self.memory.graph_memory.graph.edges),
                "semantic_concepts": len(self.memory.semantic_memory.concepts)
            }
        }

    def process_request(self, request_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user request through the orchestrator.

        Args:
            request_type: Type of request (suggest, explain, analyze)
            context: Request context and parameters

        Returns:
            Response from the appropriate agents
        """
        if request_type == "suggest":
            return self._handle_suggestion_request(context)
        elif request_type == "explain":
            return self._handle_explanation_request(context)
        elif request_type == "analyze":
            return self._handle_analysis_request(context)
        else:
            return {"error": f"Unknown request type: {request_type}"}

    def _handle_suggestion_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle suggestion requests."""
        # This would integrate with the web platform interface
        # For now, return a placeholder
        return {
            "type": "suggestions",
            "suggestions": ["Implement error handling", "Add logging"],
            "confidence": 0.8
        }

    def _handle_explanation_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle explanation requests."""
        return {
            "type": "explanations",
            "explanations": ["This code implements a function"],
            "confidence": 0.7
        }

    def _handle_analysis_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis requests."""
        return {
            "type": "analysis",
            "risks": [],
            "overall_score": 0.8
        }