from __future__ import annotations

import os


class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514").strip()
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip()


settings = Settings()
