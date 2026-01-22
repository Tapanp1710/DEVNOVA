# devnova/state/api.py
"""
Project State API

Single source of truth for project data.
Exposes:
- Architecture facts
- Dependency queries
- Change diffs

No LLM logic here - purely data access layer.

INVARIANTS:
- All queries return consistent data from memory
- Architecture facts are computed from current memory state
- Dependencies are derived from graph edges
- State is refreshed atomically (ingestion -> analysis -> memory update)
- Cached data is invalidated on refresh

TODO:
- Implement change diffing between states
- Add query caching for performance
- Implement state validation and consistency checks
- Add support for partial state updates
- Implement state export/import for sharing
"""

import json
import os
from typing import Dict, List, Any, Optional
from devnova.ingestion.engine import ProjectIngestionEngine
from devnova.analysis.analyzer import StaticAnalysisLayer
from devnova.memory.memory import ProjectMemory


class ProjectStateAPI:
    """
    Unified API for accessing project state.

    INVARIANTS:
    - Memory is loaded on initialization
    - refresh_state() updates all components atomically
    - Query methods return data from memory, falling back to cache
    - File paths are normalized to forward slashes
    - Language detection is consistent across queries
    """

    def __init__(self, project_path: str, state_dir: str = '.devnova'):
        self.project_path = project_path
        self.state_dir = os.path.join(project_path, state_dir)
        os.makedirs(self.state_dir, exist_ok=True)

        self.memory = ProjectMemory(self.state_dir)
        self._load_state()

    def _load_state(self):
        """Load or initialize project state."""
        self.memory.load()
        # TODO: Load cached ingestion and analysis results

    def refresh_state(self):
        """
        Re-ingest and re-analyze the project.
        """
        # Ingestion
        ingestion_engine = ProjectIngestionEngine(self.project_path)
        project_state = ingestion_engine.scan_project()

        # Analysis
        analysis_layer = StaticAnalysisLayer(project_state)
        analysis_results = analysis_layer.analyze_all_python_files()

        # Update memory
        self.memory.update_from_analysis(analysis_results)
        self.memory.save()

        # Cache results (convert dataclasses to dicts)
        self._save_cached_data('ingestion', {
            'files': [vars(f) for f in project_state.files],
            'tree': project_state.tree,
            'metadata': vars(project_state.metadata)
        })
        self._save_cached_data('analysis', analysis_results)

    def _save_cached_data(self, name: str, data):
        """Save data to cache file."""
        path = os.path.join(self.state_dir, f'{name}_cache.json')
        
        def serialize(obj):
            """Recursively serialize dataclasses to dicts."""
            if hasattr(obj, '__dict__'):
                return vars(obj)
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            else:
                return obj
        
        serializable_data = serialize(data)
            
        with open(path, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def _load_cached_data(self, name: str) -> Optional[Dict[str, Any]]:
        """Load data from cache file."""
        path = os.path.join(self.state_dir, f'{name}_cache.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None

    # Query methods

    def get_file_tree(self) -> Dict[str, Any]:
        """
        Get the project file tree.
        """
        cached = self._load_cached_data('ingestion')
        return cached.get('tree', {}) if cached else {}

    def get_files(self, language: str = None) -> List[Dict[str, Any]]:
        """
        Get list of files, optionally filtered by language.
        """
        cached = self._load_cached_data('ingestion')
        if not cached:
            return []

        files = cached.get('files', [])
        if language:
            files = [f for f in files if f.get('language') == language]
        return files

    def get_functions(self, file_path: str = None) -> List[Dict[str, Any]]:
        """
        Get functions, optionally for a specific file.
        """
        functions = self.memory.graph_memory.query_nodes('function')
        if file_path:
            functions = [f for f in functions if f['id'].startswith(file_path)]
        return functions

    def get_classes(self, file_path: str = None) -> List[Dict[str, Any]]:
        """
        Get classes, optionally for a specific file.
        """
        classes = self.memory.graph_memory.query_nodes('class')
        if file_path:
            classes = [c for c in classes if c['id'].startswith(file_path)]
        return classes

    def get_dependencies(self, file_path: str) -> List[str]:
        """
        Get files that the given file depends on (imports).
        """
        imports = self.memory.graph_memory.query_edges('imports', source=file_path)
        return [imp['target'] for imp in imports]

    def get_dependents(self, file_path: str) -> List[str]:
        """
        Get files that depend on the given file.
        """
        # Reverse lookup for imports
        all_imports = self.memory.graph_memory.query_edges('imports')
        dependents = [imp['source'] for imp in all_imports if imp['target'].startswith(file_path)]
        return list(set(dependents))  # Unique

    def get_call_graph(self, function_id: str) -> Dict[str, List[str]]:
        """
        Get functions called by and calling the given function.
        """
        calls_out = self.memory.graph_memory.query_edges('calls', source=function_id)
        calls_in = self.memory.graph_memory.query_edges('calls', target=function_id)

        return {
            'calls': [c['target'] for c in calls_out],
            'called_by': [c['source'] for c in calls_in],
        }

    def search_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search in project content.
        """
        return self.memory.semantic_memory.search_similar(query, top_k)

    def get_architecture_facts(self) -> Dict[str, Any]:
        """
        Get high-level architecture facts.
        """
        cached_ingestion = self._load_cached_data('ingestion')
        if not cached_ingestion:
            return {}

        metadata = cached_ingestion.get('metadata', {})
        functions = self.memory.graph_memory.query_nodes('function')
        classes = self.memory.graph_memory.query_nodes('class')

        return {
            'total_files': metadata.get('total_files', 0),
            'languages': metadata.get('languages', []),
            'total_functions': len(functions),
            'total_classes': len(classes),
            'files_by_language': self._count_by_language(),
        }

    def _count_by_language(self) -> Dict[str, int]:
        """Count files by language."""
        cached = self._load_cached_data('ingestion')
        if not cached:
            return {}

        counts = {}
        for file in cached.get('files', []):
            lang = file.get('language', 'unknown')
            counts[lang] = counts.get(lang, 0) + 1
        return counts

    def get_change_diffs(self, previous_state: 'ProjectStateAPI') -> Dict[str, Any]:
        """
        Compare with previous state to find changes.
        TODO: Implement diff logic for files, functions, etc.
        """
        # Placeholder
        return {
            'new_files': [],
            'modified_files': [],
            'deleted_files': [],
            'new_functions': [],
            'modified_functions': [],
            'deleted_functions': [],
        }


# CLI interface for testing
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m devnova.state.api <project_path>")
        sys.exit(1)

    api = ProjectStateAPI(sys.argv[1])
    api.refresh_state()

    facts = api.get_architecture_facts()
    print("Architecture Facts:")
    print(json.dumps(facts, indent=2))

    files = api.get_files('python')[:5]  # First 5 Python files
    print(f"\nFirst 5 Python files: {[f['path'] for f in files]}")