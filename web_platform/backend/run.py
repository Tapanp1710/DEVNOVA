"""
DEVNOVA Backend Entrypoint

Starts the FastAPI server using Uvicorn with reload enabled.

Verification Checklist:
# - [x] .env loaded via python-dotenv
# - [x] Backend fails fast if required env vars missing
# - [x] Backend starts cleanly with one command
# - [x] Web IDE loads at /
# - [x] /api/ide/status returns valid JSON
# - [x] /api/ide/task produces real output
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load .env before any env validation
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'), override=True)

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
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    port = int(os.getenv("DEVNOVA_PORT"))
    print("🚀 Starting DEVNOVA Web Platform Backend")
    print(f"🌐 http://localhost:{port}/")
    uvicorn.run(
        "web_platform.backend.main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        log_level="info"
    )
