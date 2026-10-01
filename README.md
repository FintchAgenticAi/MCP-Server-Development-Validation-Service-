# Validation Service MCP Adapter

Thin **FastMCP** wrapper that exposes the external Silver Zone Validation Service to Cursor. It mirrors the Transformation Rules MCP: stdio tools, an async HTTP client, and no database.

```text
Cursor  --stdio MCP-->  mcp_validation  --HTTP-->  Validation FastAPI
```

## Quick start

```powershell
cd "d:\3rd year 1st sem\industrial_project\MCP server(Validation)"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

1. Start the Validation FastAPI on `http://127.0.0.1:8001` (see `openapi.json`). Set `VALIDATION_API_KEY` or `VALIDATION_BEARER_TOKEN` if that server requires auth.
2. Smoke-test the HTTP client (no Cursor):

```powershell
python scripts\test_validation_mcp_api_client.py
```

3. Run the MCP server (stdio; Cursor uses this):

```powershell
python -m mcp_validation
```

## How Cursor connects

Add the block from `docs/mcp_cursor_config_validation.example.json` to Cursor MCP settings. Cursor launches `python -m mcp_validation` and talks over stdio. The Validation API must stay running.

## Environment

| Variable | Default |
|----------|---------|
| `VALIDATION_API_BASE_URL` | `http://127.0.0.1:8001` |
| `VALIDATION_API_TIMEOUT` | `60` |
| `VALIDATION_API_KEY` | empty (`X-API-Key`) |
| `VALIDATION_BEARER_TOKEN` | empty (`Authorization: Bearer`) |

## HTTP paths

Wired from `openapi.json`. Full tool table and sample curl: `docs/MCP_Validation_Server.md`.

| Tool | HTTP |
|------|------|
| `health_check` | `GET /health` |
| `list_validation_rules` | `GET /validation/rules` |
| `get_validation_rule` | `GET /validation/rules/{rule_id}` |
| `validate_record` | `POST /validation/execute` |
| `validate_batch` | `POST /validation/batch` |
| `list_validation_logs` | `GET /validation/logs?limit=` |

## Optional HTTP transport

Stdio is the default. For a demo listener, `mcp` 1.30 already includes uvicorn:

```powershell
$env:MCP_TRANSPORT = "streamable-http"
$env:MCP_PORT = "8030"
python -m mcp_validation
```

Same tools and same client. Details are in `docs/MCP_Validation_Server.md`.
