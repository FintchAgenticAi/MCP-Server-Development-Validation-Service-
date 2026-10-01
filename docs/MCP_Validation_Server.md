# Validation Service MCP Server

Thin **MCP adapter** that exposes the external Silver Zone Validation FastAPI as MCP tools. Same shape as the Transformation Rules MCP (`mcp_server` in `ai-financial-platform`).

## Architecture

```text
AI host (Cursor)  --stdio MCP-->  mcp_validation  --HTTP-->  Validation FastAPI (not this repo)
```

The MCP process does **not** connect to PostgreSQL and does **not** import validation business logic. Tools are wrappers over REST endpoints.

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `VALIDATION_API_BASE_URL` | `http://127.0.0.1:8001` | Validation FastAPI base URL (no trailing slash) |
| `VALIDATION_API_TIMEOUT` | `60` | HTTP timeout (seconds) |
| `VALIDATION_API_KEY` | empty | Optional `X-API-Key` header (`ApiKeyAuth`) |
| `VALIDATION_BEARER_TOKEN` | empty | Optional `Authorization: Bearer …` header (`BearerAuth`) |
| `MCP_TRANSPORT` | `stdio` | `stdio` (default), `sse`, or `streamable-http` |
| `MCP_PORT` | `8030` | Listen port when `MCP_TRANSPORT` is not stdio |

Copy `.env.example` to `.env` for local values. `python-dotenv` loads `.env` from the working directory.

## Install

```powershell
cd "d:\3rd year 1st sem\industrial_project\MCP server(Validation)"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`mcp` 1.30.x already depends on `uvicorn` and Starlette, so optional HTTP transport does not need extra packages.

## Run order

Terminal 1 — Validation FastAPI (their repo, not this adapter). It must listen on `VALIDATION_API_BASE_URL` (default `http://127.0.0.1:8001`, the server URL in `openapi.json`). Set `VALIDATION_API_KEY` or `VALIDATION_BEARER_TOKEN` when that deployment requires auth.

Terminal 2 — smoke test (HTTP client only, no Cursor):

```powershell
.\venv\Scripts\Activate.ps1
python scripts\test_validation_mcp_api_client.py
```

Success prints `Validation MCP API client smoke test PASSED`. If nothing is listening, the script prints `Start validation API first at` plus the base URL.

Cursor — enable `validation-service` from `docs/mcp_cursor_config_validation.example.json`. Leave the Validation API running. Cursor launches `python -m mcp_validation` over stdio.

Optional manual stdio server (blocks, waiting for an MCP host):

```powershell
python -m mcp_validation
```

## Tools

Source of truth: `openapi.json` (Silver-Zone Validation Service 1.0.0).

| MCP tool | HTTP | Purpose |
|----------|------|---------|
| `health_check` | `GET /health` | Liveness (`status`, optional `timestamp`) |
| `list_validation_rules` | `GET /validation/rules` | Catalog: `id`, `name`, `description` |
| `get_validation_rule` | `GET /validation/rules/{rule_id}` | One check: parameters, `example_payload` |
| `validate_record` | `POST /validation/execute` | One record |
| `validate_batch` | `POST /validation/batch` | Array of the same record body; results stay in order |
| `list_validation_logs` | `GET /validation/logs?limit=` | Recent runs (default limit 20) |

### `validate_record` body

`payload_json` is a JSON string. `data` is required. `check_ids` is optional; an empty list runs every configured check.

```json
{
  "data": {
    "email": "bob@example.com",
    "age": 42,
    "country": "US"
  },
  "check_ids": ["email-format", "age-range"]
}
```

Success body:

```json
{
  "record_id": "abc-123",
  "passed": false,
  "errors": [
    { "rule_id": "email-format", "message": "Invalid email address" }
  ]
}
```

The HTTP client returns that JSON unchanged. Local mistakes (bad JSON, missing `data`) come back as `{"error":"invalid_input","message":"..."}`. API errors come back as `{"error","status_code","body"}`.

## Sample curl

API key:

```bash
curl -X POST "http://127.0.0.1:8001/validation/execute" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: YOUR_API_KEY_HERE" \
     -d "{\"data\":{\"email\":\"bob@example.com\",\"age\":42,\"country\":\"US\"},\"check_ids\":[\"email-format\",\"age-range\"]}"
```

Bearer token. Empty `check_ids` runs every check:

```bash
curl -X POST "http://127.0.0.1:8001/validation/execute" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_BEARER_TOKEN_HERE" \
     -d "{\"data\":{\"email\":\"bob@example.com\",\"age\":42,\"country\":\"US\"},\"check_ids\":[]}"
```

## Cursor configuration

Copy `docs/mcp_cursor_config_validation.example.json` into Cursor MCP settings and fix the `command` / `cwd` paths if this folder moves.

- Command: `...\venv\Scripts\python.exe`
- Args: `-m`, `mcp_validation`
- Cwd: this project root
- Env: `VALIDATION_API_BASE_URL=http://127.0.0.1:8001`

## Example agent flow

1. `list_validation_rules` — read check ids
2. `get_validation_rule` — one id
3. `validate_record` with `payload_json` for one row
4. `list_validation_logs` — debug the run

## Optional HTTP transport (demo)

Stdio stays the default. FastMCP 1.30 supports Streamable HTTP and SSE with the same tools and the same HTTP client. No extra install.

```powershell
$env:MCP_TRANSPORT = "streamable-http"
$env:MCP_PORT = "8030"
python -m mcp_validation
```

Listens on `http://127.0.0.1:8030` (Streamable HTTP path is `/mcp`). `MCP_TRANSPORT=sse` uses the SSE app on the same host and port. `MCP_TRANSPORT=http` is accepted as an alias for `streamable-http`.
