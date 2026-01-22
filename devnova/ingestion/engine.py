# devnova/ingestion/engine.py
"""
Project Ingestion Engine

Scans a local codebase and extracts:
- File tree structure
- Basic metadata (size, mtime)
- Language detection by file extensions

Outputs structured project state as a dictionary.
No LLM usage here - purely deterministic extraction.
"""

import os
import json
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Data model for file information."""
    path: str
    size: int
    mtime: float
    language: str


@dataclass
class ProjectMetadata:
    """Data model for project-level metadata."""
    root_path: str
    total_files: int
    languages: List[str]


@dataclass
class ProjectState:
    """Data model for complete project state."""
    files: List[FileInfo]
    tree: Dict[str, Any]
    metadata: ProjectMetadata


class ProjectIngestionEngine:
    """
    Handles ingestion of project files into structured state.
    """

    # Supported languages and their file extensions
    LANGUAGE_EXTENSIONS = {
        'python': ['.py', '.pyw', '.pyc'],
        'javascript': ['.js', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'java': ['.java'],
        'cpp': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hxx'],
        'c': ['.c', '.h'],
        'csharp': ['.cs'],
        'go': ['.go'],
        'rust': ['.rs'],
        'ruby': ['.rb'],
        'php': ['.php'],
        'html': ['.html', '.htm'],
        'css': ['.css'],
        'markdown': ['.md'],
        'yaml': ['.yml', '.yaml'],
        'json': ['.json'],
        'xml': ['.xml'],
        'shell': ['.sh', '.bash', '.zsh'],
        'sql': ['.sql'],
    }

    def __init__(self, root_path: str):
        """
        Initialize with project root path.
        """
        self.root_path = os.path.abspath(root_path)
        if not os.path.exists(self.root_path):
            raise ValueError(f"Path does not exist: {self.root_path}")

    def scan_project(self) -> ProjectState:
        """
        Scan the project and return structured state.

        Returns:
            ProjectState containing files, tree, and metadata
        """
        files = []
        tree = {}

        for root, dirs, filenames in os.walk(self.root_path):
            # Skip hidden directories and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]

            rel_root = os.path.relpath(root, self.root_path)

            for filename in filenames:
                if filename.startswith('.'):
                    continue  # Skip hidden files

                filepath = os.path.join(root, filename)
                rel_filepath = os.path.relpath(filepath, self.root_path)

                # Get file metadata
                stat = os.stat(filepath)
                language = self._detect_language(filename)

                file_info = FileInfo(
                    path=rel_filepath.replace(os.sep, '/'),  # Normalize to forward slashes
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                    language=language
                )
                files.append(file_info)

                # Build tree structure
                self._add_to_tree(tree, rel_filepath.split(os.sep))

        # Project metadata
        languages = list(set(f.language for f in files))
        metadata = ProjectMetadata(
            root_path=self.root_path,
            total_files=len(files),
            languages=languages
        )

        return ProjectState(
            files=files,
            tree=tree,
            metadata=metadata
        )

    def _detect_language(self, filename: str) -> str:
        """
        Detect programming language from file extension.
        """
        _, ext = os.path.splitext(filename.lower())
        for lang, exts in self.LANGUAGE_EXTENSIONS.items():
            if ext in exts:
                return lang
        return 'unknown'

    def _add_to_tree(self, tree: Dict, path_parts: List[str]):
        """
        Recursively build nested dict tree structure.
        """
        if not path_parts:
            return

        current = path_parts[0]
        if current not in tree:
            tree[current] = {}

        if len(path_parts) > 1:
            self._add_to_tree(tree[current], path_parts[1:])

    def save_state(self, state: ProjectState, output_path: str):
        """
        Save project state to JSON file.
        """
        # Convert dataclasses to dicts for JSON serialization
        state_dict = {
            'files': [vars(f) for f in state.files],
            'tree': state.tree,
            'metadata': vars(state.metadata)
        }
        with open(output_path, 'w') as f:
            json.dump(state_dict, f, indent=2)


# CLI interface for testing
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m devnova.ingestion.engine <project_path>")
        sys.exit(1)

    engine = ProjectIngestionEngine(sys.argv[1])
    state = engine.scan_project()

    # Print summary
    print(f"Project: {state.metadata.root_path}")
    print(f"Total files: {state.metadata.total_files}")
    print(f"Languages: {', '.join(state.metadata.languages)}")
    print(f"Files: {[f.path for f in state.files[:5]]}")  # First 5 files