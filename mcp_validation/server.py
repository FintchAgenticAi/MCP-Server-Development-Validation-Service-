"""
MCP server — exposes Validation Service REST APIs as MCP tools (stdio).

Start the Validation FastAPI first, then: python -m mcp_validation
"""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_validation.client import ValidationApiClient, ValidationApiError
from mcp_validation.config import get_settings

INSTRUCTIONS = """
You are connected to the Silver Zone Validation service.

Workflow:
1. Call list_validation_rules to discover checks.
2. Call get_validation_rule for one check by numeric id or rule code.
3. Call validate_record.
   payload_json: {"records": [{ ...row... }]}
   Optional request_id. Omit rule_pipeline to run the active rules from the service.
4. Call list_validation_logs to debug recent runs.
5. Call validate_batch with records and at least one check id.

Each item in records is one row. Nested payloads are JSON strings.
""".strip()


def _http_port() -> int:
    raw = os.getenv("MCP_PORT", "8030")
    try:
        return int(raw)
    except ValueError:
        return 8030


mcp = FastMCP(
    "validation-service",
    instructions=INSTRUCTIONS,
    host="127.0.0.1",
    port=_http_port(),
)


def _client() -> ValidationApiClient:
    settings = get_settings()
    return ValidationApiClient(
        settings.validation_api_base_url,
        timeout_seconds=settings.validation_api_timeout,
        api_key=settings.validation_api_key,
        bearer_token=settings.validation_bearer_token,
    )


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


def _require_records(payload: Any) -> dict[str, Any]:
    """ValidationRequest: records is a non-empty array of row objects."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    records = payload.get("records")
    if (
        not isinstance(records, list)
        or not records
        or not all(isinstance(item, dict) for item in records)
    ):
        raise ValueError("records is required and must be a non-empty array of objects")
    return payload


def _require_batch(payload: Any) -> dict[str, Any]:
    """BatchValidationRequest: records plus a non-empty check_ids array."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    records = payload.get("records")
    if not isinstance(records, list) or not all(
        isinstance(item, dict) and isinstance(item.get("data"), dict) and item.get("record_id")
        for item in records
    ):
        raise ValueError(
            "records must be an array of objects with record_id and data"
        )
    check_ids = payload.get("check_ids")
    if (
        not isinstance(check_ids, list)
        or not check_ids
        or not all(isinstance(item, str) for item in check_ids)
    ):
        raise ValueError("check_ids must be a non-empty array of rule ids")
    return payload


@mcp.tool()
async def health_check() -> str:
    """GET /health. Returns status (and timestamp when the service sends one)."""
    try:
        result = await _client().health_check()
        return _json(result)
    except ValidationApiError as e:
        return _json({"error": str(e), "status_code": e.status_code, "body": e.body})


@mcp.tool()
async def list_validation_rules() -> str:
    """
    GET /api/v1/validation/rules. Catalog of active checks.

    Use each rule id or rule code with get_validation_rule.
    """
    try:
        result = await _client().list_validation_rules()
        return _json(result)
    except ValidationApiError as e:
        return _json({"error": str(e), "status_code": e.status_code, "body": e.body})


@mcp.tool()
async def get_validation_rule(rule_id: str) -> str:
    """
    GET /api/v1/validation/rules/{rule_id}. One active check.

    Args:
        rule_id: numeric id or rule code from list_validation_rules
    """
    try:
        rule_id = (rule_id or "").strip()
        if not rule_id:
            raise ValueError("rule_id is required")
        result = await _client().get_validation_rule(rule_id)
        return _json(result)
    except ValueError as e:
        return _json({"error": "invalid_input", "message": str(e)})
    except ValidationApiError as e:
        return _json({"error": str(e), "status_code": e.status_code, "body": e.body})


@mcp.tool()
async def validate_record(payload_json: str) -> str:
    """
    POST /api/v1/validation/execute. Validate one or more records.

    Args:
        payload_json: JSON object.
            records (required): rows, e.g. [{"email":"bob@example.com","age":42,"country":"US"}]
            request_id (optional): caller id for this run
            rule_pipeline (optional): omit to run the active rules from the service

    Returns overall_status, passed_records, and quarantined_records.
    """
    try:
        payload = _require_records(json.loads(payload_json))
        result = await _client().validate_record(payload)
        return _json(result)
    except (json.JSONDecodeError, ValueError) as e:
        return _json({"error": "invalid_input", "message": str(e)})
    except ValidationApiError as e:
        return _json({"error": str(e), "status_code": e.status_code, "body": e.body})


@mcp.tool()
async def validate_batch(payload_json: str) -> str:
    """
    POST /api/v1/validation/batch. Validate many records against selected rules.

    Args:
        payload_json: JSON object.
            records: [{"record_id": "r1", "data": {"email": "bob@example.com"}}]
            check_ids: non-empty list of rule ids, e.g. ["VR_001_NULL_CHECK"]
    """
    try:
        payload = _require_batch(json.loads(payload_json))
        result = await _client().validate_batch(payload)
        return _json(result)
    except (json.JSONDecodeError, ValueError) as e:
        return _json({"error": "invalid_input", "message": str(e)})
    except ValidationApiError as e:
        return _json({"error": str(e), "status_code": e.status_code, "body": e.body})


@mcp.tool()
async def list_validation_logs(limit: int = 20) -> str:
    """
    GET /api/v1/validation/logs. Recent validation runs.

    Args:
        limit: maximum entries (default 20, minimum 1).
    """
    try:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        result = await _client().list_validation_logs(limit=limit)
        return _json(result)
    except ValueError as e:
        return _json({"error": "invalid_input", "message": str(e)})
    except ValidationApiError as e:
        return _json({"error": str(e), "status_code": e.status_code, "body": e.body})


def main() -> None:
    """Run MCP server. Default transport is stdio (Cursor / Claude Desktop)."""
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower() or "stdio"
    if transport == "http":
        transport = "streamable-http"
    if transport not in ("stdio", "sse", "streamable-http"):
        raise SystemExit(
            f"Unknown MCP_TRANSPORT={transport!r}. Use stdio, sse, or streamable-http."
        )
    mcp.run(transport=transport)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
