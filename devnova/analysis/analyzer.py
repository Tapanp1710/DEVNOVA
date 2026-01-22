"""
Analysis Engine - Static code analysis layer

This module provides static analysis capabilities for Python code,
extracting functions, classes, imports, and call relationships.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class AnalyzedFunction:
    """Represents an analyzed function."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    parameters: List[str]
    docstring: Optional[str] = None
    complexity: int = 0
    is_method: bool = False
    class_name: Optional[str] = None


@dataclass
class AnalyzedClass:
    """Represents an analyzed class."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    methods: List[str]
    inherits_from: List[str]
    docstring: Optional[str] = None


@dataclass
class AnalyzedImport:
    """Represents an analyzed import."""
    module: str
    file_path: str
    line_number: int
    import_type: str  # 'import' or 'from'
    alias: Optional[str] = None


class CodeAnalyzer(ast.NodeVisitor):
    """
    AST-based code analyzer for Python files.

    This visitor extracts functions, classes, imports, and other
    code elements from Python source code.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions: List[AnalyzedFunction] = []
        self.classes: List[AnalyzedClass] = []
        self.imports: List[AnalyzedImport] = []
        self.current_class: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        parameters = [arg.arg for arg in node.args.args]
        if node.args.vararg:
            parameters.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            parameters.append(f"**{node.args.kwarg.arg}")

        docstring = None
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            docstring = node.body[0].value.s

        complexity = self._calculate_complexity(node)

        func = AnalyzedFunction(
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
            parameters=parameters,
            docstring=docstring,
            complexity=complexity,
            is_method=self.current_class is not None,
            class_name=self.current_class
        )

        self.functions.append(func)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definition."""
        # Treat async functions same as regular functions for now
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definition."""
        methods = []
        inherits_from = []

        # Get inherited classes
        for base in node.bases:
            if isinstance(base, ast.Name):
                inherits_from.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle qualified names like module.Class
                inherits_from.append(self._get_full_name(base))

        # Get methods (functions defined in this class)
        old_class = self.current_class
        self.current_class = node.name

        # Visit class body to find methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        self.current_class = old_class

        docstring = None
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
            docstring = node.body[0].value.s

        cls = AnalyzedClass(
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
            methods=methods,
            inherits_from=inherits_from,
            docstring=docstring
        )

        self.classes.append(cls)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Visit import statement."""
        for alias in node.names:
            imp = AnalyzedImport(
                module=alias.name,
                file_path=self.file_path,
                line_number=node.lineno,
                import_type='import',
                alias=alias.asname
            )
            self.imports.append(imp)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from import statement."""
        module = node.module or ''
        for alias in node.names:
            imp = AnalyzedImport(
                module=f"{module}.{alias.name}" if module else alias.name,
                file_path=self.file_path,
                line_number=node.lineno,
                import_type='from',
                alias=alias.asname
            )
            self.imports.append(imp)

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Assert)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and len(child.values) > 1:
                complexity += len(child.values) - 1

        return complexity

    def _get_full_name(self, node: ast.AST) -> str:
        """Get full name from AST node (for qualified names)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_full_name(node.value)}.{node.attr}"
        else:
            return str(node)


class AnalysisEngine:
    """
    Static analysis engine for codebases.

    This engine analyzes Python code to extract structural information
    about functions, classes, imports, and relationships.
    """

    def __init__(self):
        self.analyzer_cache: Dict[str, CodeAnalyzer] = {}

    def analyze_file(self, file_path: str) -> Optional[CodeAnalyzer]:
        """
        Analyze a single Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            CodeAnalyzer with analysis results, or None if analysis failed
        """
        if not file_path.endswith('.py'):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=file_path)
            analyzer = CodeAnalyzer(file_path)
            analyzer.visit(tree)

            self.analyzer_cache[file_path] = analyzer
            return analyzer

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not analyze {file_path}: {e}")
            return None

    def analyze_directory(self, directory_path: str) -> Dict[str, CodeAnalyzer]:
        """
        Analyze all Python files in a directory recursively.

        Args:
            directory_path: Root directory to analyze

        Returns:
            Dictionary mapping file paths to their analyzers
        """
        results = {}
        directory = Path(directory_path)

        for py_file in directory.rglob("*.py"):
            analyzer = self.analyze_file(str(py_file))
            if analyzer:
                results[str(py_file)] = analyzer

        return results

    def get_all_functions(self, analyzers: Dict[str, CodeAnalyzer]) -> List[AnalyzedFunction]:
        """Get all functions from analyzed files."""
        functions = []
        for analyzer in analyzers.values():
            functions.extend(analyzer.functions)
        return functions

    def get_all_classes(self, analyzers: Dict[str, CodeAnalyzer]) -> List[AnalyzedClass]:
        """Get all classes from analyzed files."""
        classes = []
        for analyzer in analyzers.values():
            classes.extend(analyzer.classes)
        return classes

    def get_all_imports(self, analyzers: Dict[str, CodeAnalyzer]) -> List[AnalyzedImport]:
        """Get all imports from analyzed files."""
        imports = []
        for analyzer in analyzers.values():
            imports.extend(analyzer.imports)
        return imports

    def build_call_graph(self, analyzers: Dict[str, CodeAnalyzer]) -> Dict[str, List[str]]:
        """
        Build a call graph from the analyzed code.

        This is a simplified call graph based on function names found in code.
        A full call graph would require more sophisticated analysis.
        """
        call_graph = {}

        for analyzer in analyzers.values():
            for func in analyzer.functions:
                func_id = f"{func.file_path}::{func.name}"
                calls = self._extract_function_calls(analyzer, func)
                if calls:
                    call_graph[func_id] = calls

        return call_graph

    def _extract_function_calls(self, analyzer: CodeAnalyzer, func: AnalyzedFunction) -> List[str]:
        """Extract function calls from a function's source code."""
        # This is a simplified implementation
        # A full implementation would require more sophisticated AST analysis
        calls = []

        # For now, return empty list - this would need more implementation
        # to actually parse function calls from the AST

        return calls