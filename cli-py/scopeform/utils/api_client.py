from __future__ import annotations

from typing import Any

import httpx
from rich.console import Console

console = Console(stderr=True)


class ScopeformClientError(Exception):
    """Base exception for CLI API client failures."""


class ScopeformAuthError(ScopeformClientError):
    """Raised for authentication failures."""


class ScopeformForbiddenError(ScopeformClientError):
    """Raised for forbidden actions."""


class ScopeformNotFoundError(ScopeformClientError):
    """Raised when a resource does not exist."""


class ScopeformConflictError(ScopeformClientError):
    """Raised when the API reports a conflict."""


class ScopeformAPIError(ScopeformClientError):
    """Raised for all other API failures."""


class ScopeformClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ScopeformClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _extract_detail(self, response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return "The API returned an unexpected response."

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, dict):
                return str(detail.get("detail") or detail.get("title") or "Request failed.")
            if isinstance(detail, str):
                return detail
            if "title" in payload:
                return str(payload["title"])

        return "Request failed."

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        detail = self._extract_detail(response)
        if response.status_code == 401:
            console.print(f"[bold red]Authentication failed:[/bold red] {detail}")
            raise ScopeformAuthError(detail)
        if response.status_code == 403:
            console.print(f"[bold red]Permission denied:[/bold red] {detail}")
            raise ScopeformForbiddenError(detail)
        if response.status_code == 404:
            console.print(f"[bold red]Not found:[/bold red] {detail}")
            raise ScopeformNotFoundError(detail)
        if response.status_code == 409:
            console.print(f"[bold yellow]Conflict:[/bold yellow] {detail}")
            raise ScopeformConflictError(detail)

        console.print(f"[bold red]API request failed ({response.status_code}):[/bold red] {detail}")
        raise ScopeformAPIError(detail)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, path, headers=self._headers(), **kwargs)
        self._raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def exchange_auth_token(self, clerk_session_token: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/auth/token",
            json={"clerk_session_token": clerk_session_token},
        )

    def register_agent(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/agents", json=payload)

    def list_agents(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/agents")

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/agents/{agent_id}")

    def issue_token(self, agent_id: str, ttl: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/api/v1/tokens/issue",
            json={"agent_id": agent_id, "ttl": ttl},
        )

    def revoke_token(self, *, jti: str | None = None, agent_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if jti is not None:
            payload["jti"] = jti
        if agent_id is not None:
            payload["agent_id"] = agent_id
        return self._request("POST", "/api/v1/tokens/revoke", json=payload)

    def get_logs(
        self,
        *,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        allowed: bool | None = None,
        service: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if allowed is not None:
            params["allowed"] = str(allowed).lower()
        if service:
            params["service"] = service

        if agent_id:
            return self._request("GET", f"/api/v1/agents/{agent_id}/logs", params=params)
        return self._request("GET", "/api/v1/logs", params=params)
