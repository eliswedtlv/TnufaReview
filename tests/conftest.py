import os

# app.py resolves the API key at import time; provide one so the module imports.
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
# Model defaults to google/gemini-3.1-flash-lite when unset — leave OPEN_ROUTER_MODEL alone.
