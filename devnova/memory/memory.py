# devnova/memory/memory.py
"""
Project Memory

Implements:
- Graph-based memory (nodes + edges)
- Vector-based semantic memory (placeholders)

Memory persists across runs using file storage.

INVARIANTS:
- Graph nodes have unique IDs
- All edges have a 'relation' attribute
- Node types: 'file', 'function', 'class', 'method', 'import'
- Edge relations: 'contains', 'imports', 'calls'
- Memory is the single source of truth for structural relationships
- No LLM logic or reasoning stored here

TODO:
- Implement actual vector embeddings for semantic memory
- Add graph optimization for large codebases
- Implement incremental updates instead of full rebuilds
- Add memory compression for persistence
- Implement memory versioning for change tracking
"""

import json
import os
from typing import Dict, List, Any, Optional
import networkx as nx


class GraphMemory:
    """
    Graph-based memory using NetworkX.
    Nodes represent entities (files, functions, classes).
    Edges represent relationships (contains, imports, calls).

    INVARIANTS:
    - Each node has a unique string ID
    - Each node has a 'type' attribute
    - Each edge has a 'relation' attribute
    - Node IDs follow format: filepath::entity_name for contained entities
    - Import nodes follow format: import::module::name
    """

    def __init__(self, storage_path: str = None):
        self.graph = nx.DiGraph()
        self.storage_path = storage_path or 'devnova_memory.json'

    def add_node(self, node_id: str, node_type: str, **attributes):
        """
        Add a node to the graph.
        """
        self.graph.add_node(node_id, type=node_type, **attributes)

    def add_edge(self, source: str, target: str, relation: str, **attributes):
        """
        Add an edge between nodes.
        """
        self.graph.add_edge(source, target, relation=relation, **attributes)

    def query_nodes(self, node_type: str = None, **filters) -> List[Dict[str, Any]]:
        """
        Query nodes by type and attributes.
        """
        results = []
        for node, data in self.graph.nodes(data=True):
            if node_type and data.get('type') != node_type:
                continue
            if all(data.get(k) == v for k, v in filters.items()):
                results.append({'id': node, **data})
        return results

    def query_edges(self, relation: str = None, source: str = None, target: str = None) -> List[Dict[str, Any]]:
        """
        Query edges by relation and nodes.
        """
        results = []
        for u, v, data in self.graph.edges(data=True):
            if relation and data.get('relation') != relation:
                continue
            if source and u != source:
                continue
            if target and v != target:
                continue
            results.append({'source': u, 'target': v, **data})
        return results

    def get_neighbors(self, node_id: str, relation: str = None) -> List[str]:
        """
        Get neighboring nodes, optionally filtered by relation.
        """
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            if relation:
                edge_data = self.graph.get_edge_data(node_id, neighbor)
                if edge_data and edge_data.get('relation') == relation:
                    neighbors.append(neighbor)
            else:
                neighbors.append(neighbor)
        return neighbors

    def save(self):
        """
        Save graph to JSON file.
        """
        data = {
            'nodes': [{'id': n, **d} for n, d in self.graph.nodes(data=True)],
            'edges': [{'source': u, 'target': v, **d} for u, v, d in self.graph.edges(data=True)],
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        """
        Load graph from JSON file.
        """
        if not os.path.exists(self.storage_path):
            return

        with open(self.storage_path, 'r') as f:
            data = json.load(f)

        self.graph.clear()
        for node in data.get('nodes', []):
            node_id = node.pop('id')
            self.graph.add_node(node_id, **node)

        for edge in data.get('edges', []):
            source = edge.pop('source')
            target = edge.pop('target')
            self.graph.add_edge(source, target, **edge)


class SemanticMemory:
    """
    Vector-based semantic memory (placeholder implementation).

    TODO: Implement actual vector embeddings and similarity search.
    Currently stores text snippets with dummy vectors.
    """

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or 'devnova_semantic_memory.json'
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self.load()

    def add_text(self, text_id: str, text: str, metadata: Dict[str, Any] = None):
        """
        Add text to semantic memory with dummy vector.
        """
        # TODO: Generate actual embeddings using a model like BERT or Sentence Transformers
        dummy_vector = [0.0] * 384  # Placeholder 384-dim vector

        self.vectors[text_id] = {
            'text': text,
            'vector': dummy_vector,
            'metadata': metadata or {},
        }

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar texts (placeholder: returns random results).
        """
        # TODO: Implement actual vector similarity search
        results = list(self.vectors.values())[:top_k]
        return [{'text': r['text'], 'metadata': r['metadata'], 'similarity': 0.5} for r in results]

    def save(self):
        """
        Save semantic memory to JSON.
        """
        with open(self.storage_path, 'w') as f:
            json.dump(self.vectors, f, indent=2)

    def load(self):
        """
        Load semantic memory from JSON.
        """
        if not os.path.exists(self.storage_path):
            return

        with open(self.storage_path, 'r') as f:
            self.vectors = json.load(f)


class ProjectMemory:
    """
    Unified memory interface combining graph and semantic memory.
    """

    def __init__(self, storage_dir: str = '.'):
        self.graph_memory = GraphMemory(os.path.join(storage_dir, 'graph_memory.json'))
        self.semantic_memory = SemanticMemory(os.path.join(storage_dir, 'semantic_memory.json'))

    def update_from_analysis(self, analysis_results: Dict[str, Any]):
        """
        Update memory from static analysis results.
        """
        # Add files as nodes
        for file_path, result in analysis_results['analysis_results'].items():
            self.graph_memory.add_node(file_path, 'file', language='python')

            # Add functions and classes
            for func in result.get('functions', []):
                func_id = f"{file_path}::{func['name']}"
                self.graph_memory.add_node(func_id, 'function', **func)
                self.graph_memory.add_edge(file_path, func_id, 'contains')

            for cls in result.get('classes', []):
                cls_id = f"{file_path}::{cls['name']}"
                self.graph_memory.add_node(cls_id, 'class', **cls)
                self.graph_memory.add_edge(file_path, cls_id, 'contains')

                # Add methods
                for method in cls['methods']:
                    method_id = f"{cls_id}::{method}"
                    self.graph_memory.add_node(method_id, 'method', name=method)
                    self.graph_memory.add_edge(cls_id, method_id, 'contains')

            # Add imports and calls as edges
            for imp in result.get('imports', []):
                for name in imp['names']:
                    # Create import target node if not exists
                    import_id = f"import::{imp['module']}::{name}"
                    self.graph_memory.add_node(import_id, 'import', module=imp['module'], name=name)
                    self.graph_memory.add_edge(file_path, import_id, 'imports')

            for call in result.get('calls', []):
                # Best-effort: assume calls are to functions in same file or known
                call_target = f"{file_path}::{call}"
                if self.graph_memory.graph.has_node(call_target):
                    self.graph_memory.add_edge(f"{file_path}::(caller)", call_target, 'calls')

        # Add semantic snippets (placeholder)
        for file_path, result in analysis_results['analysis_results'].items():
            for func in result.get('functions', []):
                text = f"Function {func['name']} with args {func['args']}"
                self.semantic_memory.add_text(f"func_{file_path}_{func['name']}", text, {'type': 'function', 'file': file_path})

    def save(self):
        """Save all memory components."""
        self.graph_memory.save()
        self.semantic_memory.save()

    def load(self):
        """Load all memory components."""
        self.graph_memory.load()
        self.semantic_memory.load()


# CLI interface for testing
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python -m devnova.memory.memory <analysis_results.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        analysis_results = json.load(f)

    memory = ProjectMemory()
    memory.update_from_analysis(analysis_results)
    memory.save()
    print("Memory updated and saved.")