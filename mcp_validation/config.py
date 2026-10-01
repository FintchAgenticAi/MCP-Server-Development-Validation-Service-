"""MCP server configuration (env-based; no DB access from MCP)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    validation_api_base_url: str
    validation_api_timeout: float
    validation_api_key: str
    validation_bearer_token: str


def get_settings() -> Settings:
    base = os.getenv("VALIDATION_API_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
    timeout = float(os.getenv("VALIDATION_API_TIMEOUT", "60"))
    api_key = os.getenv("VALIDATION_API_KEY", "").strip()
    bearer = os.getenv("VALIDATION_BEARER_TOKEN", "").strip()
    return Settings(
        validation_api_base_url=base,
        validation_api_timeout=timeout,
        validation_api_key=api_key,
        validation_bearer_token=bearer,
    )
