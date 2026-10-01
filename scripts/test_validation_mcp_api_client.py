"""
Smoke test: Validation MCP HTTP client (no MCP host required).

Requires the Validation FastAPI at VALIDATION_API_BASE_URL.
Paths match the running service: /health and /api/v1/validation/*.

Usage:
  python scripts/test_validation_mcp_api_client.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_validation.client import ValidationApiClient
from mcp_validation.config import get_settings

SAMPLE_RECORD = {
    "records": [
        {
            "email": "bob@example.com",
            "age": 42,
            "country": "US",
        }
    ]
}


async def main() -> None:
    settings = get_settings()
    client = ValidationApiClient(
        settings.validation_api_base_url,
        timeout_seconds=settings.validation_api_timeout,
        api_key=settings.validation_api_key,
        bearer_token=settings.validation_bearer_token,
    )
    try:
        health = await client.health_check()
        print("health_check:", health)
        rules = await client.list_validation_rules()
        if not isinstance(rules, list):
            raise RuntimeError("list_validation_rules did not return a JSON array")
        print("list_validation_rules:", len(rules))
        if rules:
            rule_id = rules[0].get("id")
            if not rule_id:
                raise RuntimeError("catalog entry is missing id")
            detail = await client.get_validation_rule(str(rule_id))
            print("get_validation_rule:", detail.get("id"), detail.get("name"))
        result = await client.validate_record(SAMPLE_RECORD)
        print("validate_record:", json.dumps(result, indent=2, default=str))
        logs = await client.list_validation_logs(limit=5)
        if not isinstance(logs, list):
            raise RuntimeError("list_validation_logs did not return a JSON array")
        print("list_validation_logs:", len(logs))
        print("Validation MCP API client smoke test PASSED")
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        print("Validation MCP API client smoke test FAILED")
        print(f"Start validation API first at {settings.validation_api_base_url}")
        print(exc)
        sys.exit(1)
    except Exception as exc:
        print("Validation MCP API client smoke test FAILED")
        print(exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
