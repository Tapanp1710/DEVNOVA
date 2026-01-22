"""
Ingestion Engine - Project scanning and metadata extraction

This module scans local codebases, extracts file tree information,
detects programming languages, and prepares project state for analysis.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from ..state.api import FileInfo


class IngestionEngine:
    """
    Project ingestion engine.

    This engine scans a local codebase and extracts basic metadata
    about files, languages, and project structure without performing
    deep code analysis.
    """

    def __init__(self):
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }

        self.exclude_patterns = {
            '.git',
            '__pycache__',
            'node_modules',
            '.venv',
            'venv',
            'env',
            'build',
            'dist',
            '.next',
            '.nuxt',
            'target',  # Maven
            'bin',
            'obj',     # .NET
            '.DS_Store',
            'Thumbs.db'
        }

    def scan_project(self, project_root: str) -> Dict[str, Any]:
        """
        Scan a project directory and extract basic metadata.

        Args:
            project_root: Root directory of the project

        Returns:
            Dictionary containing project metadata
        """
        project_path = Path(project_root)

        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"Project root {project_root} does not exist or is not a directory")

        # Scan all files
        all_files = self._scan_directory(project_path)

        # Categorize files
        file_info = []
        languages = set()

        for file_path in all_files:
            relative_path = file_path.relative_to(project_path)
            file_info_item = self._analyze_file(file_path, relative_path)
            if file_info_item:
                file_info.append(file_info_item)
                languages.add(file_info_item.language)

        # Build project metadata
        project_metadata = {
            "project_root": str(project_path.absolute()),
            "scan_time": datetime.now().isoformat(),
            "total_files": len(file_info),
            "languages": list(languages),
            "files": [self._file_info_to_dict(f) for f in file_info],
            "language_breakdown": self._calculate_language_breakdown(file_info)
        }

        return project_metadata

    def _scan_directory(self, directory: Path) -> List[Path]:
        """
        Recursively scan directory for files.

        Args:
            directory: Directory to scan

        Returns:
            List of file paths
        """
        files = []

        try:
            for item in directory.rglob('*'):
                if item.is_file() and self._should_include_file(item):
                    files.append(item)
        except PermissionError as e:
            print(f"Warning: Permission denied accessing {directory}: {e}")

        return files

    def _should_include_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be included in the scan.

        Args:
            file_path: File path to check

        Returns:
            True if file should be included
        """
        # Check if any part of the path matches exclude patterns
        parts = file_path.parts
        for part in parts:
            if part in self.exclude_patterns:
                return False

        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                return False
        except OSError:
            return False

        return True

    def _analyze_file(self, file_path: Path, relative_path: Path) -> Optional[FileInfo]:
        """
        Analyze a single file and extract metadata.

        Args:
            file_path: Absolute path to the file
            relative_path: Relative path from project root

        Returns:
            FileInfo object or None if file should be skipped
        """
        try:
            stat = file_path.stat()

            # Determine language
            language = self._detect_language(file_path)

            # Basic binary detection
            is_binary = self._is_binary_file(file_path)

            return FileInfo(
                path=str(relative_path),
                language=language,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                is_binary=is_binary
            )

        except OSError as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")
            return None

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect programming language from file extension.

        Args:
            file_path: File path

        Returns:
            Language name or 'unknown'
        """
        suffix = file_path.suffix.lower()
        return self.supported_languages.get(suffix, 'unknown')

    def _is_binary_file(self, file_path: Path) -> bool:
        """
        Determine if a file is binary.

        Args:
            file_path: File path

        Returns:
            True if file appears to be binary
        """
        try:
            # Read first 1024 bytes
            with open(file_path, 'rb') as f:
                data = f.read(1024)

            # Check for null bytes (common in binary files)
            if b'\x00' in data:
                return True

            # Try to decode as UTF-8
            try:
                data.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True

        except (OSError, IOError):
            return True

    def _calculate_language_breakdown(self, files: List[FileInfo]) -> Dict[str, int]:
        """
        Calculate breakdown of files by language.

        Args:
            files: List of FileInfo objects

        Returns:
            Dictionary mapping language to count
        """
        breakdown = {}
        for file_info in files:
            lang = file_info.language
            breakdown[lang] = breakdown.get(lang, 0) + 1
        return breakdown

    def _file_info_to_dict(self, file_info: FileInfo) -> Dict[str, Any]:
        """
        Convert FileInfo to dictionary.

        Args:
            file_info: FileInfo object

        Returns:
            Dictionary representation
        """
        return {
            "path": file_info.path,
            "language": file_info.language,
            "size": file_info.size,
            "last_modified": file_info.last_modified.isoformat(),
            "is_binary": file_info.is_binary
        }

    def detect_project_type(self, project_metadata: Dict[str, Any]) -> str:
        """
        Detect the type of project based on metadata.

        Args:
            project_metadata: Project metadata from scan

        Returns:
            Project type string
        """
        languages = set(project_metadata.get("languages", []))

        # Python project detection
        if "python" in languages:
            # Check for common Python project files
            files = [f["path"] for f in project_metadata.get("files", [])]

            if any("requirements.txt" in f for f in files):
                return "python"
            if any("setup.py" in f for f in files):
                return "python"
            if any("pyproject.toml" in f for f in files):
                return "python"

        # JavaScript/Node.js project
        if "javascript" in languages or "typescript" in languages:
            files = [f["path"] for f in project_metadata.get("files", [])]

            if any("package.json" in f for f in files):
                return "nodejs"
            if any("tsconfig.json" in f for f in files):
                return "nodejs"

        # Java project
        if "java" in languages:
            files = [f["path"] for f in project_metadata.get("files", [])]

            if any("pom.xml" in f for f in files):
                return "maven"
            if any("build.gradle" in f for f in files):
                return "gradle"

        return "unknown"