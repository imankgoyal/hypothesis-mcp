import asyncio

import httpx
from mcp.server.fastmcp import FastMCP, Context

from hypothesis_mcp.pdf.fetcher import resolve_pdf_url, fetch_pdf
from hypothesis_mcp.pdf.extractor import extract_text


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def read_pdf(
        ctx: Context,
        url: str,
        page_start: int = 1,
        page_end: int | None = None,
        max_chars: int = 80_000,
    ) -> dict:
        """Read and extract text from a PDF.

        Accepts direct PDF URLs or Chrome extension viewer URLs:
          - https://arxiv.org/pdf/2507.05331
          - chrome-extension://bjfhmglciegochdpefhhlphglcehbmek/pdfjs/web/viewer.html?file=https%3A%2F%2F...

        Args:
            url: PDF URL in any supported format.
            page_start: First page to read, 1-indexed (default: 1).
            page_end: Last page to read, 1-indexed (default: read until max_chars is reached).
            max_chars: Maximum characters to return (default 80,000). If the PDF is larger,
                       call again with page_start set to the next unread page.
        """
        resolved_url = resolve_pdf_url(url)

        try:
            pdf_bytes = await fetch_pdf(resolved_url)
        except httpx.HTTPStatusError as e:
            return {
                "error": True,
                "message": f"HTTP {e.response.status_code} fetching PDF: {e.response.reason_phrase}",
                "url": resolved_url,
            }
        except httpx.RequestError as e:
            return {
                "error": True,
                "message": f"Network error fetching PDF: {e}",
                "url": resolved_url,
            }
        except ValueError as e:
            return {
                "error": True,
                "message": str(e),
                "url": resolved_url,
            }

        try:
            # extract_text is CPU-bound (pdfplumber) — run off the event loop.
            # 60 s timeout prevents a malicious PDF from hanging a thread indefinitely.
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    extract_text,
                    pdf_bytes,
                    page_start - 1,                                    # convert to 0-indexed
                    (page_end - 1) if page_end is not None else None,  # convert to 0-indexed
                    max_chars,
                ),
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            return {
                "error": True,
                "message": "PDF parsing timed out after 60 seconds. The file may be malformed.",
                "url": resolved_url,
            }
        except Exception as e:
            return {
                "error": True,
                "message": f"Failed to extract text from PDF: {e}",
                "url": resolved_url,
            }

        return {
            "url": url,
            "resolved_url": resolved_url,
            **result,
        }
