import re
import httpx
from typing import Any
from urllib.parse import urlparse

_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_MAX_ERROR_BODY = 200  # chars to include from API error responses


def _validate_id(value: str, label: str = "ID") -> None:
    """Reject IDs that contain path characters, preventing URL path traversal."""
    if not _ID_RE.match(value):
        raise ValueError(f"Invalid {label}: must contain only letters, digits, hyphens, underscores")


class HypothesisAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        # Truncate body to avoid leaking large/sensitive API responses into logs
        self.body = body[:_MAX_ERROR_BODY] + ("…" if len(body) > _MAX_ERROR_BODY else "")
        super().__init__(f"Hypothesis API error {status_code}: {self.body}")


class HypothesisClient:
    def __init__(self, api_key: str, base_url: str = "https://api.hypothes.is/api"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def __aenter__(self) -> "HypothesisClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        response = await self._client.request(method, url, **kwargs)
        if not response.is_success:
            raise HypothesisAPIError(response.status_code, response.text)
        if response.content:
            return response.json()
        return {}

    # --- Annotations ---

    async def search_annotations(self, **params: Any) -> dict:
        """Search annotations. Pass filter kwargs directly; None values are dropped."""
        clean = {k: v for k, v in params.items() if v is not None}
        return await self._request("GET", "/search", params=clean)

    async def get_annotation(self, annotation_id: str) -> dict:
        _validate_id(annotation_id, "annotation ID")
        return await self._request("GET", f"/annotations/{annotation_id}")

    async def create_annotation(self, body: dict) -> dict:
        return await self._request("POST", "/annotations", json=body)

    async def update_annotation(self, annotation_id: str, body: dict) -> dict:
        _validate_id(annotation_id, "annotation ID")
        return await self._request("PATCH", f"/annotations/{annotation_id}", json=body)

    async def delete_annotation(self, annotation_id: str) -> dict:
        _validate_id(annotation_id, "annotation ID")
        return await self._request("DELETE", f"/annotations/{annotation_id}")

    async def flag_annotation(self, annotation_id: str) -> dict:
        _validate_id(annotation_id, "annotation ID")
        return await self._request("PUT", f"/annotations/{annotation_id}/flag")

    async def hide_annotation(self, annotation_id: str) -> dict:
        _validate_id(annotation_id, "annotation ID")
        return await self._request("PUT", f"/annotations/{annotation_id}/hide")

    async def unhide_annotation(self, annotation_id: str) -> dict:
        _validate_id(annotation_id, "annotation ID")
        return await self._request("DELETE", f"/annotations/{annotation_id}/hide")

    # --- Groups ---

    async def list_groups(
        self,
        document_uri: str | None = None,
        expand: list[str] | None = None,
    ) -> list:
        params: dict[str, Any] = {}
        if document_uri:
            params["document_uri"] = document_uri
        if expand:
            params["expand"] = expand
        return await self._request("GET", "/groups", params=params)

    async def get_group(
        self,
        group_id: str,
        expand: list[str] | None = None,
    ) -> dict:
        _validate_id(group_id, "group ID")
        params: dict[str, Any] = {}
        if expand:
            params["expand"] = expand
        return await self._request("GET", f"/groups/{group_id}", params=params)

    # --- Profile ---

    async def get_profile(self) -> dict:
        return await self._request("GET", "/profile")
