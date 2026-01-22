# DEVNOVA – AI Developer Operating Environment

## Overview

DEVNOVA is a research-grade AI-native development environment designed to provide deterministic project understanding, persistent memory, and multi-agent reasoning using an LLM as a reasoning layer only. All understanding, memory, and truth reside outside the LLM to ensure reliability and explainability.

## Architecture

The system is composed of the following core subsystems:

### 1. Project Ingestion Engine (`ingestion/`)
- Scans a local codebase
- Extracts file tree, basic metadata, and detects programming languages
- Outputs structured project state
- **No LLM usage**

### 2. Static Analysis Layer (`analysis/`)
- Parses code using AST (currently Python only)
- Extracts functions, classes, imports, and call relationships (best-effort)
- **No LLM usage**

### 3. Project Memory (`memory/`)
- Graph-based memory (nodes + edges)
- Vector-based semantic memory (placeholders for now)
- Persists across runs

### 4. Project State API (`state/`)
- Single source of truth for project data
- Exposes architecture facts, dependency queries, change diffs
- **No LLM logic**

### 5. Multi-Agent System (`agents/`)
- Defines agents with strict roles: ArchitectAgent, FeatureAgent, DebugAgent, TestAgent, DocsAgent
- Each agent reads from Project State and calls LLM only for reasoning
- Outputs structured actions or plans

### 6. LLM Reasoning Layer (`llm/`)
- Centralized interface for LLM interactions
- Enforces role prompts, input constraints, structured JSON outputs
- **Never stores memory**

### 7. Orchestrator (`orchestrator/`)
- Assigns tasks to agents
- Validates outputs
- Rejects unsafe or invalid actions

### 8. IDE Integration Placeholder (`ide/`)
- Defines interfaces for context loading, suggestions, explanations
- No actual VS Code extension implemented yet

## Implementation Notes

- **Language Focus**: Starting with Python support only
- **Persistence**: Uses file-based storage for simplicity (research-grade, not production)
- **LLM Integration**: Assumes external LLM API (e.g., OpenAI); not included
- **Testing**: Minimal unit tests provided; focus on integration
- **Limitations**: 
  - No advanced semantic analysis
  - Basic graph memory (no optimization)
  - Stub implementations for complex features
  - No UI/IDE integration yet

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run ingestion: `python -m devnova.ingestion.engine /path/to/project`
3. Analyze: `python -m devnova.analysis.analyzer`
4. Query state: `python -m devnova.state.api`

## Development

- Code must be modular, testable, and readable
- Prefer stubs with TODOs over incomplete features
- All reasoning boundaries clearly commented
- No magic: everything explicit and explainable

## Future Work

- Expand language support
- Implement full vector semantic memory
- Add IDE extensions
- Enhance static analysis with type inference
- Integrate with version control for diffs