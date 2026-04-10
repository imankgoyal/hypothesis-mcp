import httpx
from urllib.parse import urlparse, parse_qs, unquote

MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB
_ALLOWED_SCHEMES = {"http", "https"}


def _assert_safe_url(url: str) -> None:
    """Raise ValueError if the URL scheme is not http or https.

    Prevents SSRF via file://, ftp://, gopher://, etc.
    """
    scheme = urlparse(url).scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"Unsafe URL scheme {scheme!r}. Only http:// and https:// are allowed."
        )


def resolve_pdf_url(raw_url: str) -> str:
    """Return the real PDF URL from a chrome-extension:// viewer URL, or the URL unchanged."""
    if raw_url.startswith("chrome-extension://"):
        parsed = urlparse(raw_url)
        params = parse_qs(parsed.query)
        file_param = params.get("file", [None])[0]
        if file_param:
            resolved = unquote(file_param)
            _assert_safe_url(resolved)
            return resolved
    return raw_url


def _redirect_hook(request: httpx.Request, response: httpx.Response) -> None:
    """Block redirects to non-HTTP/HTTPS targets (redirect-based SSRF)."""
    if response.is_redirect:
        location = response.headers.get("location", "")
        if location:
            scheme = urlparse(location).scheme.lower()
            if scheme and scheme not in _ALLOWED_SCHEMES:
                raise ValueError(
                    f"Redirect to unsafe scheme {scheme!r} blocked."
                )


async def fetch_pdf(url: str) -> bytes:
    """Download a PDF from the given URL and return raw bytes.

    Raises:
        ValueError: If the URL scheme is unsafe, file exceeds MAX_PDF_BYTES,
                    or the server returns non-PDF content.
        httpx.HTTPStatusError: On 4xx/5xx responses.
    """
    _assert_safe_url(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; hypothesis-mcp/0.1)",
        "Accept": "application/pdf,*/*",
    }
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=60.0,
        event_hooks={"response": [_redirect_hook]},
    ) as client:
        async with client.stream("GET", url, headers=headers) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            # Only reject types that are definitively not PDFs.
            if "text/html" in content_type:
                raise ValueError(
                    f"Server returned HTML instead of a PDF (content-type: {content_type}). "
                    "The URL may require authentication or does not point to a PDF."
                )

            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes(chunk_size=65536):
                total += len(chunk)
                if total > MAX_PDF_BYTES:
                    raise ValueError(
                        f"PDF exceeds the {MAX_PDF_BYTES // (1024 * 1024)} MB size limit."
                    )
                chunks.append(chunk)

    return b"".join(chunks)
