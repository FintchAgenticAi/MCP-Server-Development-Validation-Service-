"""HTTP client for the Silver Zone Validation REST API.

Paths match the running Validation Rules Service (prefix ``/api/v1``).
This process never opens the database and never imports validation business logic.
"""

from __future__ import annotations

from typing import Any

import httpx


class ValidationApiError(Exception):
    """API returned an error response."""

    def __init__(self, status_code: int, message: str, body: Any | None = None):
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {message}")


class ValidationApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 60.0,
        api_key: str = "",
        bearer_token: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds
        self.headers: dict[str, str] = {}
        if api_key:
            self.headers["X-API-Key"] = api_key
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"

    def _url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.request(
                method,
                self._url(path),
                params=params,
                json=json_body,
            )
        if response.status_code >= 400:
            try:
                body = response.json()
                detail = body.get("detail", body) if isinstance(body, dict) else body
                if isinstance(detail, dict):
                    message = detail.get("message") or detail.get("error") or str(detail)
                else:
                    message = str(detail)
            except Exception:
                message = response.text or response.reason_phrase
                body = None
            raise ValidationApiError(response.status_code, message, body)
        if response.status_code == 204:
            return None
        return response.json()

    async def health_check(self) -> Any:
        """GET /health."""
        return await self._request("GET", "/health")

    async def list_validation_rules(self) -> Any:
        """GET /api/v1/validation/rules. Returns an array of rules."""
        return await self._request("GET", "/api/v1/validation/rules")

    async def get_validation_rule(self, rule_id: str) -> Any:
        """GET /api/v1/validation/rules/{rule_id}. Returns one rule."""
        rule_id = (rule_id or "").strip()
        return await self._request("GET", f"/api/v1/validation/rules/{rule_id}")

    async def validate_record(self, payload: dict[str, Any]) -> Any:
        """POST /api/v1/validation/execute.

        Body is ValidationRequest: required ``records`` array. Omit
        ``rule_pipeline`` to run the active rules loaded by the service.
        """
        return await self._request("POST", "/api/v1/validation/execute", json_body=payload)

    async def validate_batch(self, payload: dict[str, Any]) -> Any:
        """POST /api/v1/validation/batch.

        Body is BatchValidationRequest: ``records`` and a non-empty ``check_ids``.
        """
        return await self._request("POST", "/api/v1/validation/batch", json_body=payload)

    async def list_validation_logs(self, *, limit: int = 20) -> Any:
        """GET /api/v1/validation/logs?limit=. Returns an array of log entries."""
        return await self._request("GET", "/api/v1/validation/logs", params={"limit": limit})
