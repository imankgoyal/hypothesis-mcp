import io
import pdfplumber


def extract_text(
    pdf_bytes: bytes,
    page_start: int = 0,
    page_end: int | None = None,
    max_chars: int = 80_000,
) -> dict:
    """Extract text from PDF bytes.

    Args:
        pdf_bytes: Raw PDF content.
        page_start: First page to extract (0-indexed).
        page_end: Last page to extract, inclusive (0-indexed). None means read to end or max_chars.
        max_chars: Hard cap on returned characters. Extraction stops when reached.

    Returns:
        {
            total_pages: int,
            extracted_pages: [first, last],  # 1-indexed
            text: str,
            char_count: int,
            truncated: bool,
        }
    """
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)

        if total_pages == 0:
            return {
                "total_pages": 0,
                "extracted_pages": [0, 0],
                "text": "",
                "char_count": 0,
                "truncated": False,
            }

        # Clamp page range to valid bounds
        page_start = max(0, min(page_start, total_pages - 1))
        if page_end is None:
            page_end = total_pages - 1
        page_end = max(page_start, min(page_end, total_pages - 1))

        parts: list[str] = []
        chars_used = 0
        last_page_extracted = page_start
        truncated = False
        has_content = False  # tracks whether any page yielded actual text

        for i in range(page_start, page_end + 1):
            page_text = pdf.pages[i].extract_text() or ""
            if page_text.strip():
                has_content = True
            segment = f"\n\n--- Page {i + 1} ---\n\n{page_text}"
            remaining = max_chars - chars_used

            if len(segment) > remaining:
                parts.append(segment[:remaining])
                chars_used += remaining
                last_page_extracted = i
                truncated = True
                break

            parts.append(segment)
            chars_used += len(segment)
            last_page_extracted = i

        text = "".join(parts).strip()

        if not has_content and total_pages > 0:
            text = (
                "[No selectable text found. The PDF may be a scanned image. "
                "OCR would be required to extract text.]"
            )

        return {
            "total_pages": total_pages,
            "extracted_pages": [page_start + 1, last_page_extracted + 1],  # 1-indexed
            "text": text,
            "char_count": chars_used,
            "truncated": truncated,
        }
