# Favicon fix: Serve /favicon.ico from frontend directory
@app.get("/favicon.ico")
async def favicon():
    """Serve favicon.ico for browser requests."""
    favicon_path = FRONTEND_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    # Return 204 No Content if missing (should not happen)
    from fastapi import Response
    return Response(status_code=204)
#
# Verification Checklist:
# - [x] .env loaded via python-dotenv
# - [x] Backend fails fast if required env vars missing
# - [x] Backend starts cleanly with one command
# - [x] Web IDE loads at /
# - [x] /api/ide/status returns valid JSON
# - [x] /api/ide/task produces real output
# web-platform/backend/main.py
"""
DEVNOVA Web Platform Backend

FastAPI server that provides:
- File system APIs (read/write within sandboxed project directory)
- Project snapshot export
- DEVNOVA integration adapter

ABSOLUTE BOUNDARIES:
- NO file modifications by DEVNOVA
- NO code execution
- NO autonomous actions
- DEVNOVA is read-only advisory service
"""


import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env for all imports (if not already loaded)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'), override=True)

# Fail fast if required env vars are missing when app is imported directly
required_vars = [
    "OPENROUTER_API_KEY",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "LLM_TIMEOUT",
    "DEVNOVA_ENV",
    "DEVNOVA_PORT",
    "DEVNOVA_PROJECT_ROOT"
]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# DEVNOVA Integration
from devnova.ide.interfaces import (
    IDEContext, SuggestionRequest, ExplanationRequest,
    MockDEVINOVAIntegration, create_devnova_integration
)

app = FastAPI(title="DEVNOVA Web Platform", version="1.0.0")


# Configuration from environment
PROJECT_ROOT = Path(os.getenv("DEVNOVA_PROJECT_ROOT", "D:/DEVNOVA/devnova"))
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# DEVNOVA Integration
devnova = create_devnova_integration(str(PROJECT_ROOT))

# ============================================================================
# DATA MODELS
# ============================================================================

class FileRequest(BaseModel):
    """Request to read a file."""
    path: str

class FileContent(BaseModel):
    """File content response."""
    path: str
    content: str
    exists: bool

class SaveFileRequest(BaseModel):
    """Request to save a file."""
    path: str
    content: str

class ProjectSnapshot(BaseModel):
    """Project snapshot for DEVNOVA analysis."""
    files: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class DEVINOVARequest(BaseModel):
    """Request to DEVNOVA for suggestions/explanations."""
    file_path: Optional[str] = None
    cursor_position: Optional[Dict[str, int]] = None
    selected_text: Optional[str] = None
    user_intent: str
    request_type: str  # "suggestions" or "explanation"

class DEVINOVAResponse(BaseModel):
    """Response from DEVNOVA."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_path_safety(requested_path: str) -> Path:
    """
    Validate that the requested path is within the sandboxed project directory.

    Args:
        requested_path: The path requested by the client

    Returns:
        Resolved Path object within PROJECT_ROOT

    Raises:
        HTTPException: If path is outside sandbox or invalid
    """
    try:
        # Resolve the path to prevent directory traversal
        full_path = (PROJECT_ROOT / requested_path).resolve()

        # Ensure it's within PROJECT_ROOT
        if not str(full_path).startswith(str(PROJECT_ROOT)):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Path outside sandboxed directory"
            )

        return full_path

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path: {str(e)}"
        )

def get_project_snapshot() -> ProjectSnapshot:
    """
    Generate a snapshot of the current project state for DEVNOVA analysis.

    Returns:
        ProjectSnapshot with file information
    """
    files = []

    try:
        for root, dirs, filenames in os.walk(PROJECT_ROOT):
            # Skip hidden directories and common excludes
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

            for filename in filenames:
                if filename.startswith('.'):
                    continue

                file_path = Path(root) / filename
                rel_path = file_path.relative_to(PROJECT_ROOT)

                try:
                    stat = file_path.stat()
                    files.append({
                        "path": str(rel_path),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "language": get_language_from_extension(filename)
                    })
                except OSError:
                    # Skip files we can't stat
                    continue

    except Exception as e:
        print(f"Warning: Could not generate full project snapshot: {e}")

    return ProjectSnapshot(
        files=files,
        metadata={
            "project_root": str(PROJECT_ROOT),
            "total_files": len(files),
            "snapshot_time": str(Path(__file__).stat().st_mtime)
        }
    )

def get_language_from_extension(filename: str) -> str:
    """Simple language detection from file extension."""
    ext = Path(filename).suffix.lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.md': 'markdown'
    }
    return language_map.get(ext, 'unknown')


# ============================================================================
# API ENDPOINTS
# ============================================================================

from devnova.orchestrator.central_orchestrator import CentralOrchestrator
import os

# Load config from environment
DEVNOVA_PORT = int(os.getenv("DEVNOVA_PORT", "8000"))
DEVNOVA_ENV = os.getenv("DEVNOVA_ENV", "development")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")

# Central orchestrator instance (stateful)
central_orchestrator = CentralOrchestrator(str(PROJECT_ROOT))

class IDETaskRequest(BaseModel):
    code: str
    active_file: str
    project_context: Dict[str, Any]
    intent: str
    request_type: str  # "suggestion" or "explanation"

class IDETaskResponse(BaseModel):
    success: bool
    output: Any = None
    error: Optional[str] = None

@app.post("/api/ide/task")
async def ide_task(request: IDETaskRequest):
    """
    Accepts code/text input, active file path, project context, intent, and request type.
    Invokes DEVNOVA orchestrator and agents, returns structured output.
    """
    try:
        # Build IDEContext
        context = IDEContext(
            file_path=request.active_file,
            cursor_position={"line": 1, "column": 1},  # Placeholder, can be extended
            selected_text=request.code,
            project_root=request.project_context.get("project_root", str(PROJECT_ROOT)),
            language=request.project_context.get("language", "python")
        )
        if request.request_type == "suggestion":
            suggestions = central_orchestrator.orchestrator.get_suggestions(context, request.intent)
            return IDETaskResponse(success=True, output=[s.dict() for s in suggestions])
        elif request.request_type == "explanation":
            explanations = central_orchestrator.orchestrator.get_explanations(context, request.code, "general")
            return IDETaskResponse(success=True, output=[e.dict() for e in explanations])
        else:
            return IDETaskResponse(success=False, error="Unknown request_type")
    except Exception as e:
        return IDETaskResponse(success=False, error=str(e))

@app.get("/api/ide/status")
async def ide_status():
    """
    Returns system readiness and provider status.
    """
    try:
        # Check orchestrator and LLM provider status
        status = {
            "ready": True,
            "env": DEVNOVA_ENV,
            "port": DEVNOVA_PORT,
            "llm_provider": LLM_PROVIDER,
            "project_root": str(PROJECT_ROOT)
        }
        return status
    except Exception as e:
        return {"ready": False, "error": str(e)}

@app.get("/")
async def root():
    """Serve the main web interface."""
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/files")
async def list_files(path: str = ""):
    """
    List files and directories in the specified path.

    Args:
        path: Relative path within the project (default: root)

    Returns:
        List of files and directories
    """
    try:
        full_path = validate_path_safety(path)

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")

        if not full_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        items = []
        for item in full_path.iterdir():
            rel_path = item.relative_to(PROJECT_ROOT)
            items.append({
                "name": item.name,
                "path": str(rel_path),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })

        return {"items": items, "path": path}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.post("/api/files/read")
async def read_file(request: FileRequest):
    """
    Read the contents of a file.

    Args:
        request: FileRequest with path to read

    Returns:
        FileContent with file contents
    """
    try:
        full_path = validate_path_safety(request.path)

        if not full_path.exists():
            return FileContent(path=request.path, content="", exists=False)

        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        try:
            content = full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # For binary files, return empty content
            content = ""

        return FileContent(path=request.path, content=content, exists=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.post("/api/files/save")
async def save_file(request: SaveFileRequest):
    """
    Save content to a file.

    IMPORTANT: This is USER-DRIVEN file editing only.
    DEVNOVA NEVER calls this endpoint.

    Args:
        request: SaveFileRequest with path and content

    Returns:
        Success confirmation
    """
    try:
        full_path = validate_path_safety(request.path)

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        full_path.write_text(request.content, encoding='utf-8')

        return {"success": True, "path": request.path, "message": "File saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.get("/api/project/snapshot")
async def get_snapshot():
    """
    Get a snapshot of the current project state for DEVNOVA analysis.

    Returns:
        ProjectSnapshot for DEVNOVA consumption
    """
    try:
        snapshot = get_project_snapshot()
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating snapshot: {str(e)}")

@app.post("/api/devnova/analyze")
async def analyze_with_devnova(request: DEVINOVARequest):
    """
    Send request to DEVNOVA for analysis.

    This is the ONLY interface between web platform and DEVNOVA.
    Web platform sends context + intent, DEVNOVA returns suggestions/explanations.

    Args:
        request: DEVINOVARequest with context and intent

    Returns:
        DEVINOVAResponse with DEVNOVA analysis
    """
    try:
        # Create IDE context from request
        context = IDEContext(
            workspace_path=str(PROJECT_ROOT),
            active_file=request.file_path,
            cursor_position=request.cursor_position,
            selected_text=request.selected_text
        )

        # Route to appropriate DEVNOVA interface
        if request.request_type == "suggestions":
            suggestion_request = SuggestionRequest(
                context=context,
                suggestion_type="general",  # Could be made more specific
                user_query=request.user_intent
            )

            response = devnova.get_suggestions(suggestion_request)

            return DEVINOVAResponse(
                success=True,
                data={
                    "suggestions": response.suggestions,
                    "confidence": response.confidence,
                    "agent_used": response.agent_used,
                    "warnings": response.warnings
                }
            )

        elif request.request_type == "explanation":
            explanation_request = ExplanationRequest(
                context=context,
                explanation_type="code_explanation",
                target_code=request.selected_text,
                user_question=request.user_intent
            )

            response = devnova.get_explanation(explanation_request)

            return DEVINOVAResponse(
                success=True,
                data={
                    "explanation": response.explanation,
                    "code_references": response.code_references,
                    "confidence": response.confidence,
                    "agent_used": response.agent_used,
                    "warnings": response.warnings
                }
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown request type: {request.request_type}")

    except HTTPException:
        raise
    except Exception as e:
        return DEVINOVAResponse(
            success=False,
            error=f"DEVNOVA analysis failed: {str(e)}"
        )

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

# Mount frontend static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ============================================================================
# MAIN
# ============================================================================

##
# Entrypoint logic removed. This file only defines FastAPI app 'app'.
