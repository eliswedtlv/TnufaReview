import os

# app.py resolves the API key at import time; provide one so the module imports.
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
# Model defaults to deepseek/deepseek-v4-pro when unset — leave OPEN_ROUTER_MODEL alone.
