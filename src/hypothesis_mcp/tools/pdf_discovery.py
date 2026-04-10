import asyncio
import re

from mcp.server.fastmcp import FastMCP, Context

from hypothesis_mcp.client import HypothesisAPIError
from hypothesis_mcp.context import AppContext
from hypothesis_mcp.pdf.fetcher import fetch_pdf
from hypothesis_mcp.pdf.extractor import extract_text


# URL patterns that reliably indicate a PDF document
_PDF_PATTERNS = [
    r"\.pdf($|\?|#)",
    r"arxiv\.org/pdf/",
    r"openreview\.net/pdf",
    r"biorxiv\.org/.+\.full\.pdf",
    r"medrxiv\.org/.+\.full\.pdf",
    r"ncbi\.nlm\.nih\.gov/.+/pdf",
    r"semanticscholar\.org/.+/pdf",
    r"dl\.acm\.org/doi/pdf/",
    r"ieeexplore\.ieee\.org/stamp/",
    r"proceedings\.mlr\.press/.+\.pdf",
    r"papers\.nips\.cc/.+\.pdf",
    r"aclanthology\.org/.+\.pdf",
    r"aclweb\.org/.+\.pdf",
]


def _unwrap_via(url: str) -> str:
    """Strip the via.hypothes.is proxy prefix if present.

    Annotations on PDFs opened through the Hypothesis proxy store the URI as
    'https://via.hypothes.is/https://arxiv.org/pdf/...' — we need the inner
    URL to fetch the actual PDF.
    """
    for prefix in ("https://via.hypothes.is/", "http://via.hypothes.is/"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return url


def _is_pdf_url(url: str) -> bool:
    return any(re.search(p, url, re.IGNORECASE) for p in _PDF_PATTERNS)


def _score(query: str, text: str, url: str = "", title: str = "") -> tuple[float, str]:
    """Return (relevance_score, excerpt). Score is 0 if no terms match."""
    terms = re.findall(r"\w+", query.lower())
    if not terms:
        return 0.0, ""

    text_lower = text.lower()
    score = 0.0
    first_pos = -1

    for term in terms:
        pattern = r"\b" + re.escape(term) + r"\b"
        hits = [m.start() for m in re.finditer(pattern, text_lower)]
        score += len(hits)
        if hits and first_pos == -1:
            first_pos = hits[0]
        if re.search(pattern, url.lower()):
            score += 5
        if re.search(pattern, title.lower()):
            score += 10

    excerpt = ""
    if first_pos >= 0:
        start = max(0, first_pos - 200)
        end = min(len(text), first_pos + 300)
        excerpt = text[start:end].strip()

    return score, excerpt


async def _collect_pdf_urls(client, max_annotations: int = 1000) -> dict[str, dict]:
    """Page through the authenticated user's annotations and return a map of PDF URL → metadata."""
    # Resolve the authenticated user's ID so we only scan their own annotations,
    # not all public annotations on Hypothesis.
    userid: str | None = None
    try:
        profile = await client.get_profile()
        userid = profile.get("userid")
    except HypothesisAPIError:
        pass  # Fall back to unfiltered search if profile fetch fails

    pdf_map: dict[str, dict] = {}
    limit = 200
    offset = 0

    while offset < max_annotations:
        try:
            result = await client.search_annotations(
                user=userid, limit=limit, offset=offset, order="asc"
            )
        except HypothesisAPIError:
            break

        rows = result.get("rows", [])
        if not rows:
            break

        for ann in rows:
            uri = _unwrap_via(ann.get("uri", ""))
            if not uri or not _is_pdf_url(uri):
                continue
            if uri not in pdf_map:
                titles = ann.get("document", {}).get("title", [])
                pdf_map[uri] = {
                    "title": titles[0] if titles else "",
                    "annotation_count": 0,
                }
            pdf_map[uri]["annotation_count"] += 1

        offset += len(rows)
        if len(rows) < limit:
            break

    return pdf_map


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def discover_pdfs(
        ctx: Context,
        query: str,
        max_pdfs: int = 20,
        max_chars_per_pdf: int = 20_000,
    ) -> dict:
        """Find which of your annotated PDFs discuss a given topic.

        Scans the full text of every PDF you've annotated in Hypothesis,
        scores each for relevance to your query, and returns the best matches
        with a short excerpt showing where the topic appears.

        Args:
            query: Topic or keywords to search for (e.g. 'attention mechanism transformer').
            max_pdfs: Maximum number of PDFs to scan (default 20, sorted by annotation count).
            max_chars_per_pdf: Characters to read per PDF for scoring (default 20,000 ≈ 15 pages).
        """
        # Clamp parameters to safe limits
        if len(query) > 500:
            return {"error": True, "message": "Query must be 500 characters or fewer."}
        max_pdfs = min(max_pdfs, 50)
        max_chars_per_pdf = min(max_chars_per_pdf, 50_000)

        app_ctx: AppContext = ctx.request_context.lifespan_context

        # 1. Collect all annotated PDF URLs
        pdf_map = await _collect_pdf_urls(app_ctx.hypothesis_client)

        if not pdf_map:
            return {
                "query": query,
                "pdfs_found": 0,
                "pdfs_scanned": 0,
                "results": [],
                "message": "No PDF annotations found in your Hypothesis account.",
            }

        # Prioritise PDFs with more annotations (likely more important to the user)
        candidates = sorted(
            pdf_map.items(),
            key=lambda kv: kv[1]["annotation_count"],
            reverse=True,
        )[:max_pdfs]

        # 2. Fetch + score in parallel, at most 5 concurrent downloads
        semaphore = asyncio.Semaphore(5)

        async def _process(url: str, meta: dict) -> dict | None:
            async with semaphore:
                try:
                    pdf_bytes = await fetch_pdf(url)
                    result = await asyncio.wait_for(
                        asyncio.to_thread(extract_text, pdf_bytes, 0, None, max_chars_per_pdf),
                        timeout=60.0,
                    )
                    score, excerpt = _score(
                        query, result["text"], url=url, title=meta["title"]
                    )
                    return {
                        "url": url,
                        "title": meta["title"],
                        "annotation_count": meta["annotation_count"],
                        "total_pages": result["total_pages"],
                        "relevance_score": score,
                        "excerpt": excerpt,
                    }
                except Exception:
                    return None  # skip failed PDFs silently

        gathered = await asyncio.gather(*[_process(url, meta) for url, meta in candidates])

        # 3. Filter to matches, sort by score
        results = sorted(
            [r for r in gathered if r and r["relevance_score"] > 0],
            key=lambda r: r["relevance_score"],
            reverse=True,
        )

        return {
            "query": query,
            "pdfs_found": len(pdf_map),
            "pdfs_scanned": len(candidates),
            "pdfs_matched": len(results),
            "results": results,
            **(
                {"message": "No PDFs matched the query. Try broader keywords."}
                if not results
                else {}
            ),
        }
