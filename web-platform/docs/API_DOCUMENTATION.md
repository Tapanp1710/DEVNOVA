# DEVNOVA Web Platform API Documentation

## Overview

The DEVNOVA Web Platform provides a REST API that serves as the bridge between a web-based code editor and the DEVNOVA AI analysis system. This API enforces strict boundaries to ensure DEVNOVA remains an advisory system only.

## Architecture Boundaries

### What the Web Platform Does
- ✅ File system operations (read/write within sandboxed directory)
- ✅ User interface management
- ✅ Manual code editing
- ✅ DEVNOVA request/response handling
- ✅ Project snapshot generation

### What DEVNOVA Does
- ✅ Code analysis and suggestions
- ✅ Architecture recommendations
- ✅ Code explanations
- ✅ Risk assessment

### What DEVNOVA Does NOT Do
- ❌ File modifications
- ❌ Code execution
- ❌ UI state management
- ❌ Autonomous actions

## API Endpoints

### File System Operations

#### GET /api/files
List files and directories in a path.

**Query Parameters:**
- `path` (string, optional): Relative path within project (default: root)

**Response:**
```json
{
  "items": [
    {
      "name": "main.py",
      "path": "main.py",
      "type": "file",
      "size": 1024
    }
  ],
  "path": ""
}
```

#### POST /api/files/read
Read file contents.

**Request Body:**
```json
{
  "path": "main.py"
}
```

**Response:**
```json
{
  "path": "main.py",
  "content": "print('Hello World')",
  "exists": true
}
```

#### POST /api/files/save
Save file contents.

**Request Body:**
```json
{
  "path": "main.py",
  "content": "print('Hello World')"
}
```

**Response:**
```json
{
  "success": true,
  "path": "main.py",
  "message": "File saved successfully"
}
```

### Project Operations

#### GET /api/project/snapshot
Get project snapshot for DEVNOVA analysis.

**Response:**
```json
{
  "files": [
    {
      "path": "main.py",
      "size": 1024,
      "mtime": 1640995200.0,
      "language": "python"
    }
  ],
  "metadata": {
    "project_root": "/path/to/project",
    "total_files": 1,
    "snapshot_time": "1640995200.0"
  }
}
```

### DEVNOVA Integration

#### POST /api/devnova/analyze
Send analysis request to DEVNOVA.

**Request Body:**
```json
{
  "file_path": "main.py",
  "cursor_position": {"line": 10, "column": 5},
  "selected_text": "print('Hello')",
  "user_intent": "Add error handling",
  "request_type": "suggestions"
}
```

**Response for suggestions:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "type": "refactor",
        "content": "Consider adding try-except block",
        "confidence": 0.85,
        "metadata": {}
      }
    ],
    "confidence": 0.8,
    "agent_used": "DebugAgent",
    "warnings": []
  }
}
```

**Response for explanations:**
```json
{
  "success": true,
  "data": {
    "explanation": "This code prints 'Hello' to the console...",
    "code_references": [
      {
        "file": "main.py",
        "line": 10,
        "code": "print('Hello')",
        "explanation": "Prints the string 'Hello'"
      }
    ],
    "confidence": 0.9,
    "agent_used": "DocsAgent",
    "warnings": []
  }
}
```

## Security & Sandboxing

### Path Validation
All file operations are validated to ensure they remain within the sandboxed project directory (`D:/DEVNOVA/devnova`). Directory traversal attacks are prevented through path resolution and boundary checking.

### DEVNOVA Isolation
DEVNOVA has no direct access to file system operations. All interactions go through the web platform's controlled API endpoints.

## Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad request (invalid path, malformed data)
- `403`: Forbidden (path outside sandbox)
- `404`: Not found (file/directory doesn't exist)
- `500`: Internal server error

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

## Data Flow

### User Edit Flow
1. User selects file in file tree
2. Frontend requests file content via `/api/files/read`
3. User edits code in Monaco editor
4. User clicks "Save" → `/api/files/save`
5. File is saved to disk

### DEVNOVA Analysis Flow
1. User enters intent in input field
2. User clicks "Get AI Suggestions" or "Explain Code"
3. Frontend sends request to `/api/devnova/analyze`
4. Backend creates IDEContext and calls DEVNOVA interface
5. DEVNOVA returns analysis results
6. Frontend displays results in suggestions/explanations panel
7. **User must manually apply any changes**

## Integration Points

### DEVNOVA Interface Usage
The backend uses the existing DEVNOVA IDE Integration Interfaces:

```python
from devnova.ide.interfaces import create_devnova_integration

devnova = create_devnova_integration()

# For suggestions
response = devnova.get_suggestions(SuggestionRequest(...))

# For explanations
response = devnova.get_explanation(ExplanationRequest(...))
```

### Context Creation
IDEContext is created from web request data:

```python
context = IDEContext(
    workspace_path=str(PROJECT_ROOT),
    active_file=request.file_path,
    cursor_position=request.cursor_position,
    selected_text=request.selected_text
)
```

## Limitations

### Current Constraints
1. **Single Project**: Only operates within the sandboxed DEVNOVA project directory
2. **No Real LLM**: Uses mock responses for demonstration
3. **Manual Application**: All suggestions require explicit user action
4. **No Collaboration**: Single-user interface
5. **No Version Control**: No git integration

### Safety Guarantees
1. **No Autonomous Actions**: DEVNOVA cannot modify files or execute code
2. **Sandboxed Operations**: All file access is restricted to project directory
3. **User Consent Required**: All changes must be manually applied
4. **Read-Only Analysis**: DEVNOVA only analyzes and suggests

## Future Extensions

### Potential Enhancements
- Multi-project support
- Real-time collaboration
- Git integration
- Advanced file operations (create, delete, rename)
- Plugin architecture for additional tools
- Enhanced security (authentication, authorization)
- Performance optimizations (caching, incremental analysis)

## Development

### Running the Backend
```bash
cd web-platform/backend
pip install -r requirements.txt
python main.py
```

### Accessing the Frontend
Navigate to `http://127.0.0.1:8000` in your browser.

### Testing the API
Use tools like curl, Postman, or the browser's developer console to test API endpoints.