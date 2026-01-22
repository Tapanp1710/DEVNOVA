# DEVNOVA Web Platform

A web-based coding platform that integrates with DEVNOVA AI for intelligent code analysis and suggestions.

## Overview

This web platform provides:
- **Code Editor**: Monaco-based editor for editing code files
- **File Browser**: Navigate and manage project files
- **AI Integration**: Connects to DEVNOVA for intelligent suggestions and explanations
- **Manual Control**: All changes require explicit user action

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │────│  Web Platform    │────│    DEVNOVA      │
│                 │    │  (FastAPI)       │    │  AI System      │
│ • Monaco Editor │    │                  │    │                 │
│ • File Tree     │    │ • File APIs       │    │ • Code Analysis │
│ • Intent Input  │    │ • DEVNOVA Client  │    │ • Suggestions   │
│ • Results Panel │    │ • Sandboxing      │    │ • Explanations  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Safety Boundaries

### ✅ What This Platform Does
- File editing (user-driven only)
- Code display and navigation
- DEVNOVA request/response handling
- Project visualization

### ❌ What This Platform Does NOT Do
- Autonomous code modifications
- Code execution
- Direct file system access outside sandbox
- AI-driven automatic changes

### 🔒 DEVNOVA Boundaries
DEVNOVA provides analysis and suggestions but:
- Cannot modify files
- Cannot execute code
- Cannot make UI decisions
- Requires explicit user consent for all actions

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js (for Monaco Editor - served via CDN)
- DEVNOVA system installed

### Installation

1. **Install Backend Dependencies**
   ```bash
   cd web-platform/backend
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```bash
   python main.py
   ```

3. **Open in Browser**
   ```
   http://127.0.0.1:8000
   ```

## Usage

### Basic Workflow

1. **Browse Files**
   - Use the file tree on the left to navigate
   - Click on files to load them in the editor

2. **Edit Code**
   - Use the Monaco editor for syntax-highlighted editing
   - Click "Save" to persist changes

3. **Get AI Assistance**
   - Enter your intent in the input field (e.g., "Add error handling")
   - Click "Get AI Suggestions" for code improvement suggestions
   - Click "Explain Code" for detailed code explanations

4. **Apply Changes Manually**
   - Review suggestions in the results panel
   - Manually apply changes in the editor
   - Save your modifications

### Example Session

1. Open `main.py`
2. Enter intent: "Add input validation"
3. Click "Get AI Suggestions"
4. Review suggestions in the panel
5. Manually edit the code to add validation
6. Save the file

## API Reference

See [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) for detailed API documentation.

## Configuration

### Project Directory
The platform is sandboxed to the DEVNOVA project directory:
```
PROJECT_ROOT = Path("D:/DEVNOVA/devnova")
```

### Server Settings
- Host: `127.0.0.1`
- Port: `8000`
- Auto-reload: Enabled for development

## Development

### Project Structure
```
web-platform/
├── backend/
│   ├── main.py              # FastAPI server
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html           # Single-page application
└── docs/
    ├── API_DOCUMENTATION.md # API reference
    └── README.md           # This file
```

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Modify `index.html` (JavaScript and CSS)
3. **API**: Update `API_DOCUMENTATION.md`

### Testing

```bash
# Test file operations
curl http://127.0.0.1:8000/api/files

# Test DEVNOVA integration
curl -X POST http://127.0.0.1:8000/api/devnova/analyze \
  -H "Content-Type: application/json" \
  -d '{"request_type": "suggestions", "user_intent": "test"}'
```

## Limitations

### Current Constraints
1. **Single Project**: Only works within the sandboxed DEVNOVA directory
2. **Mock AI**: Uses mock DEVNOVA responses for demonstration
3. **Manual Only**: No automatic code application
4. **No Collaboration**: Single-user interface
5. **No Version Control**: No git integration

### Safety Features
1. **Path Sandboxing**: All file operations restricted to project directory
2. **User Consent**: All changes require manual application
3. **Read-Only AI**: DEVNOVA can only analyze and suggest
4. **No Execution**: No code execution capabilities

## Troubleshooting

### Common Issues

**"Module not found" errors**
- Ensure DEVNOVA is properly installed
- Check Python path includes DEVNOVA directory

**File operations failing**
- Verify files exist within the sandboxed directory
- Check file permissions

**DEVNOVA not responding**
- Ensure DEVNOVA system is running
- Check mock vs real integration settings

**Monaco Editor not loading**
- Check internet connection (CDN hosted)
- Verify browser compatibility

### Logs
Server logs are displayed in the terminal. Check for:
- File operation errors
- DEVNOVA integration issues
- Path validation warnings

## Future Roadmap

### Phase 1: Enhanced Editing
- Multiple file tabs
- Find/replace functionality
- Syntax validation
- Auto-save options

### Phase 2: Advanced AI Integration
- Real DEVNOVA LLM integration
- Context-aware suggestions
- Multi-file analysis
- Performance metrics

### Phase 3: Collaboration Features
- Real-time collaboration
- Code review tools
- Comment system
- Team analytics

### Phase 4: Enterprise Features
- Authentication and authorization
- Audit logging
- Compliance checking
- Advanced security

## Contributing

1. Follow the established architecture boundaries
2. Maintain safety guarantees
3. Add comprehensive documentation
4. Test thoroughly before submitting

## License

This web platform is part of the DEVNOVA project. See main project license for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Examine server logs
4. Create an issue in the main DEVNOVA repository