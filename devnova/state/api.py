"""
Project State API - Single source of truth for project data

This module provides a unified interface to access project facts,
architecture information, and dependency queries. It serves as the
bridge between raw project data and the reasoning agents.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileInfo:
    """Represents a file in the project."""
    path: str
    language: str
    size: int
    last_modified: datetime
    is_binary: bool = False


@dataclass
class FunctionInfo:
    """Represents a function or method."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    complexity: int = 0


@dataclass
class ClassInfo:
    """Represents a class definition."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    methods: List[str] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ImportInfo:
    """Represents an import statement."""
    module: str
    file_path: str
    line_number: int
    import_type: str  # 'import', 'from'
    alias: Optional[str] = None


@dataclass
class ProjectFacts:
    """Curated facts about the project for reasoning agents."""
    files: List[FileInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    call_graph: Dict[str, List[str]] = field(default_factory=dict)


class ProjectStateAPI:
    """
    Single source of truth for project data.

    This class provides access to project facts, architecture information,
    and dependency queries. It loads data from the memory system and
    provides structured access for reasoning agents.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._facts_cache: Optional[ProjectFacts] = None
        self._last_loaded: Optional[datetime] = None

    def get_project_facts(self, force_reload: bool = False) -> ProjectFacts:
        """
        Get curated project facts for reasoning.

        Args:
            force_reload: If True, reload from memory instead of using cache

        Returns:
            ProjectFacts: Structured project information
        """
        if not force_reload and self._facts_cache and self._is_cache_valid():
            return self._facts_cache

        # Load from memory system
        self._facts_cache = self._load_project_facts()
        self._last_loaded = datetime.now()
        return self._facts_cache

    def _is_cache_valid(self) -> bool:
        """Check if cached facts are still valid."""
        if not self._last_loaded:
            return False

        # Check if any source files have been modified since last load
        cache_age = datetime.now() - self._last_loaded
        return cache_age.total_seconds() < 300  # 5 minute cache

    def _load_project_facts(self) -> ProjectFacts:
        """Load project facts from memory system."""
        facts = ProjectFacts()

        # Load file information
        facts.files = self._load_file_info()

        # Load code analysis results
        facts.functions = self._load_function_info()
        facts.classes = self._load_class_info()
        facts.imports = self._load_import_info()

        # Load dependency and call graph information
        facts.dependencies = self._load_dependencies()
        facts.call_graph = self._load_call_graph()

        return facts

    def _load_file_info(self) -> List[FileInfo]:
        """Load file information from project scan."""
        files = []
        try:
            # Scan Python files in project
            for py_file in self.project_root.rglob("*.py"):
                if self._is_project_file(py_file):
                    stat = py_file.stat()
                    files.append(FileInfo(
                        path=str(py_file.relative_to(self.project_root)),
                        language="python",
                        size=stat.st_size,
                        last_modified=datetime.fromtimestamp(stat.st_mtime),
                        is_binary=False
                    ))
        except Exception as e:
            print(f"Warning: Could not load file info: {e}")

        return files

    def _load_function_info(self) -> List[FunctionInfo]:
        """Load function information from analysis."""
        functions = []
        # TODO: Implement AST-based function extraction
        # For now, return empty list
        return functions

    def _load_class_info(self) -> List[ClassInfo]:
        """Load class information from analysis."""
        classes = []
        # TODO: Implement AST-based class extraction
        # For now, return empty list
        return classes

    def _load_import_info(self) -> List[ImportInfo]:
        """Load import information from analysis."""
        imports = []
        # TODO: Implement import analysis
        # For now, return empty list
        return imports

    def _load_dependencies(self) -> Dict[str, List[str]]:
        """Load dependency information."""
        # TODO: Implement dependency analysis
        return {}

    def _load_call_graph(self) -> Dict[str, List[str]]:
        """Load call graph information."""
        # TODO: Implement call graph analysis
        return {}

    def _is_project_file(self, file_path: Path) -> bool:
        """Check if file is part of the project (not in excluded directories)."""
        excluded = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.dist'}
        parts = file_path.relative_to(self.project_root).parts
        return not any(part in excluded for part in parts)

    def get_architecture_facts(self) -> Dict[str, Any]:
        """
        Get high-level architecture facts for reasoning agents.

        Returns:
            Dict containing architecture information
        """
        facts = self.get_project_facts()

        return {
            "total_files": len(facts.files),
            "languages": list(set(f.language for f in facts.files)),
            "total_functions": len(facts.functions),
            "total_classes": len(facts.classes),
            "dependency_count": len(facts.dependencies),
            "files_by_language": self._group_files_by_language(facts.files)
        }

    def _group_files_by_language(self, files: List[FileInfo]) -> Dict[str, int]:
        """Group files by programming language."""
        result = {}
        for file in files:
            result[file.language] = result.get(file.language, 0) + 1
        return result

    def query_dependencies(self, module: str) -> List[str]:
        """
        Query dependencies of a specific module.

        Args:
            module: Module name to query

        Returns:
            List of modules that this module depends on
        """
        facts = self.get_project_facts()
        return facts.dependencies.get(module, [])

    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get content of a specific file.

        Args:
            file_path: Relative path to the file

        Returns:
            File content as string, or None if file not found
        """
        full_path = self.project_root / file_path
        if full_path.exists() and full_path.is_file():
            try:
                return full_path.read_text(encoding='utf-8')
            except Exception:
                return None
        return None