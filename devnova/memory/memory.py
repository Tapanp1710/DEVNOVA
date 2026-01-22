"""
Memory System - Graph-based and semantic memory

This module implements persistent memory for DEVNOVA, including
graph-based memory for relationships and semantic memory for concepts.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import networkx as nx


class GraphMemory:
    """
    Graph-based memory for storing relationships between code elements.

    This stores nodes (functions, classes, files) and edges (calls, inherits, imports)
    to maintain a persistent understanding of code relationships.
    """

    def __init__(self, storage_path: str = ".devnova/graph_memory.json"):
        self.storage_path = Path(storage_path)
        self.graph = nx.DiGraph()
        self._load_memory()

    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any]):
        """
        Add a node to the graph memory.

        Args:
            node_id: Unique identifier for the node
            node_type: Type of node (function, class, file, etc.)
            properties: Additional properties for the node
        """
        self.graph.add_node(node_id, type=node_type, **properties)

    def add_edge(self, source_id: str, target_id: str, edge_type: str, properties: Optional[Dict[str, Any]] = None):
        """
        Add an edge between nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of relationship (calls, inherits, imports, etc.)
            properties: Additional properties for the edge
        """
        if properties:
            self.graph.add_edge(source_id, target_id, type=edge_type, **properties)
        else:
            self.graph.add_edge(source_id, target_id, type=edge_type)

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node data by ID."""
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[str]:
        """Get neighboring nodes."""
        if node_id not in self.graph:
            return []

        if edge_type:
            return [n for n in self.graph.neighbors(node_id)
                   if self.graph.edges[node_id, n].get('type') == edge_type]
        else:
            return list(self.graph.neighbors(node_id))

    def find_paths(self, source_id: str, target_id: str, max_length: int = 5) -> List[List[str]]:
        """Find paths between two nodes."""
        try:
            return list(nx.all_simple_paths(self.graph, source_id, target_id, cutoff=max_length))
        except nx.NetworkXNoPath:
            return []

    def query_by_type(self, node_type: str) -> List[str]:
        """Get all nodes of a specific type."""
        return [node for node, data in self.graph.nodes(data=True)
               if data.get('type') == node_type]

    def save_memory(self):
        """Persist memory to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert graph to serializable format
        data = {
            "nodes": [
                {"id": node_id, "data": dict(data)}
                for node_id, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": source, "target": target, "data": dict(data)}
                for source, target, data in self.graph.edges(data=True)
            ],
            "saved_at": datetime.now().isoformat()
        }

        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_memory(self):
        """Load memory from disk."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            # Rebuild graph
            for node in data.get("nodes", []):
                self.graph.add_node(node["id"], **node["data"])

            for edge in data.get("edges", []):
                self.graph.add_edge(edge["source"], edge["target"], **edge["data"])

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load graph memory: {e}")


class SemanticMemory:
    """
    Semantic memory for storing conceptual relationships.

    This provides vector-based semantic search capabilities for
    understanding concepts and relationships in the codebase.
    """

    def __init__(self, storage_path: str = ".devnova/semantic_memory.json"):
        self.storage_path = Path(storage_path)
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self._load_memory()

    def add_concept(self, concept_id: str, concept_data: Dict[str, Any]):
        """
        Add a concept to semantic memory.

        Args:
            concept_id: Unique identifier for the concept
            concept_data: Concept data including description, related concepts, etc.
        """
        self.concepts[concept_id] = {
            **concept_data,
            "added_at": datetime.now().isoformat()
        }

    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Get concept data by ID."""
        return self.concepts.get(concept_id)

    def find_related_concepts(self, concept_id: str) -> List[str]:
        """Find concepts related to the given concept."""
        if concept_id not in self.concepts:
            return []

        concept = self.concepts[concept_id]
        related = concept.get("related_concepts", [])
        return related

    def search_concepts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search concepts by text similarity.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching concepts with scores
        """
        # Simple text-based search (placeholder for vector search)
        results = []
        query_lower = query.lower()

        for concept_id, concept_data in self.concepts.items():
            score = 0
            description = concept_data.get("description", "").lower()
            name = concept_data.get("name", "").lower()

            # Simple scoring based on word matches
            query_words = set(query_lower.split())
            desc_words = set(description.split())
            name_words = set(name.split())

            score += len(query_words & desc_words) * 2  # Description matches worth more
            score += len(query_words & name_words) * 3  # Name matches worth most

            if score > 0:
                results.append({
                    "concept_id": concept_id,
                    "score": score,
                    "data": concept_data
                })

        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def save_memory(self):
        """Persist semantic memory to disk."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.storage_path, 'w') as f:
            json.dump(self.concepts, f, indent=2)

    def _load_memory(self):
        """Load semantic memory from disk."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r') as f:
                self.concepts = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not load semantic memory: {e}")


class MemorySystem:
    """
    Unified memory system combining graph and semantic memory.

    This provides a single interface to both types of memory for
    comprehensive code understanding and relationship tracking.
    """

    def __init__(self, base_path: str = ".devnova"):
        self.graph_memory = GraphMemory(f"{base_path}/graph_memory.json")
        self.semantic_memory = SemanticMemory(f"{base_path}/semantic_memory.json")

    def save_all(self):
        """Save all memory components."""
        self.graph_memory.save_memory()
        self.semantic_memory.save_memory()

    def get_code_context(self, element_id: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a code element.

        Args:
            element_id: ID of the code element

        Returns:
            Context including relationships and semantic information
        """
        # Get graph relationships
        node_data = self.graph_memory.get_node(element_id)
        neighbors = self.graph_memory.get_neighbors(element_id)

        # Get semantic information
        semantic_info = self.semantic_memory.get_concept(element_id)

        return {
            "element_id": element_id,
            "node_data": node_data,
            "relationships": neighbors,
            "semantic_info": semantic_info
        }