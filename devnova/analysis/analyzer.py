# devnova/analysis/analyzer.py
"""
Static Analysis Layer

Parses Python code using AST to extract:
- Functions
- Classes
- Imports
- Call relationships (best-effort)

Currently Python-only. No LLM usage - purely static analysis.
"""

import ast
import os
from typing import Dict, List, Any, Set
from dataclasses import dataclass
from devnova.ingestion.engine import ProjectState, FileInfo


@dataclass
class FunctionInfo:
    """Represents a function definition."""
    name: str
    line: int
    args: List[str]
    returns: str = None  # Placeholder for return type


@dataclass
class ClassInfo:
    """Represents a class definition."""
    name: str
    line: int
    methods: List[str]
    bases: List[str]


@dataclass
class ImportInfo:
    """Represents an import statement."""
    module: str
    names: List[str]
    line: int


class PythonAnalyzer:
    """
    AST-based analyzer for Python code.
    """

    def __init__(self, source_code: str, filename: str = None):
        self.source_code = source_code
        self.filename = filename
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[ImportInfo] = []
        self.calls: Set[str] = set()  # Function calls found

    def analyze(self) -> Dict[str, Any]:
        """
        Parse the source code and extract structured information.
        """
        try:
            tree = ast.parse(self.source_code)
            analyzer = ASTVisitor(self)
            analyzer.visit(tree)

            return {
                'filename': self.filename,
                'functions': [f.__dict__ for f in self.functions],
                'classes': [c.__dict__ for c in self.classes],
                'imports': [i.__dict__ for i in self.imports],
                'calls': list(self.calls),
            }
        except SyntaxError as e:
            return {
                'filename': self.filename,
                'error': f"Syntax error: {e}",
                'functions': [],
                'classes': [],
                'imports': [],
                'calls': [],
            }


class ASTVisitor(ast.NodeVisitor):
    """
    AST visitor to extract code elements.
    """

    def __init__(self, analyzer: PythonAnalyzer):
        self.analyzer = analyzer

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function definitions."""
        args = [arg.arg for arg in node.args.args]
        func_info = FunctionInfo(
            name=node.name,
            line=node.lineno,
            args=args,
        )
        self.analyzer.functions.append(func_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definitions."""
        methods = []
        bases = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]

        # Find methods in class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        class_info = ClassInfo(
            name=node.name,
            line=node.lineno,
            methods=methods,
            bases=bases,
        )
        self.analyzer.classes.append(class_info)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Extract import statements."""
        names = [alias.name for alias in node.names]
        import_info = ImportInfo(
            module='',  # Standard import
            names=names,
            line=node.lineno,
        )
        self.analyzer.imports.append(import_info)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Extract from import statements."""
        module = node.module or ''
        names = [alias.name for alias in node.names]
        import_info = ImportInfo(
            module=module,
            names=names,
            line=node.lineno,
        )
        self.analyzer.imports.append(import_info)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Extract function calls (best-effort)."""
        if isinstance(node.func, ast.Name):
            self.analyzer.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # For method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                call_name = f"{node.func.value.id}.{node.func.attr}"
                self.analyzer.calls.add(call_name)
        self.generic_visit(node)


class StaticAnalysisLayer:
    """
    Orchestrates static analysis across multiple files.
    """

    def __init__(self, project_state: ProjectState):
        self.project_state = project_state

    def analyze_all_python_files(self) -> Dict[str, Any]:
        """
        Analyze all Python files in the project.
        """
        results = {}
        root_path = self.project_state.metadata.root_path

        for file_info in self.project_state.files:
            if file_info.language == 'python':
                filepath = os.path.join(root_path, file_info.path)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        source = f.read()

                    analyzer = PythonAnalyzer(source, file_info.path)
                    results[file_info.path] = analyzer.analyze()
                except Exception as e:
                    results[file_info.path] = {
                        'filename': file_info.path,
                        'error': str(e),
                    }

        return {
            'analysis_results': results,
            'summary': {
                'total_files_analyzed': len(results),
                'files_with_errors': len([r for r in results.values() if 'error' in r]),
            }
        }


# CLI interface for testing
if __name__ == '__main__':
    import json
    import sys
    from devnova.ingestion.engine import ProjectIngestionEngine

    if len(sys.argv) != 2:
        print("Usage: python -m devnova.analysis.analyzer <project_path>")
        sys.exit(1)

    # First ingest the project
    ingestion_engine = ProjectIngestionEngine(sys.argv[1])
    project_state = ingestion_engine.scan_project()

    # Then analyze
    analyzer = StaticAnalysisLayer(project_state)
    results = analyzer.analyze_all_python_files()
    print(json.dumps(results, indent=2))