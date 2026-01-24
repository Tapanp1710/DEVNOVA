# DEVNOVA Backend Verification Checklist

# Checklist for backend startup and API wiring

- [x] No hardcoded secrets exist in the codebase
- [x] All API calls (LLM + Web IDE) are wired end-to-end
- [x] FastAPI endpoints `/api/ide/status` and `/api/ide/task` exist and invoke orchestrator/agents
- [x] LLM provider uses real HTTP calls and reads config from environment variables only
- [x] No API keys, tokens, or secrets are hardcoded
- [x] LLM calls pass through post-LLM validation
- [x] Backend starts cleanly using `python -m web_platform.backend.run`
- [x] .env.example contains all required variables and no secrets
- [x] No `uvicorn.run` in main.py; only in run.py entrypoint
- [x] No hyphenated package names; all imports use `web_platform`

# To start the backend:
#   python -m web_platform.backend.run
