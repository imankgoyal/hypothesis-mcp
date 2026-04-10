from mcp.server.fastmcp import FastMCP, Context
from hypothesis_mcp.client import HypothesisAPIError
from hypothesis_mcp.context import AppContext


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def search_annotations(
        ctx: Context,
        url: str | None = None,
        user: str | None = None,
        group: str | None = None,
        tag: str | None = None,
        text: str | None = None,
        any_field: str | None = None,
        quote: str | None = None,
        limit: int = 20,
        offset: int = 0,
        sort: str = "updated",
        order: str = "desc",
    ) -> dict:
        """Search Hypothesis annotations with optional filters.

        Args:
            url: Filter by document URL.
            user: Filter by username (e.g. 'acct:user@hypothes.is').
            group: Filter by group ID. Use '__world__' for public annotations.
            tag: Filter by a single tag.
            text: Full-text search within annotation body.
            any_field: Search across all annotation fields (text, tags, URL, etc).
            quote: Filter by the quoted text the annotation targets.
            limit: Number of results to return (max 200, default 20).
            offset: Pagination offset.
            sort: Sort field — one of: created, updated, group, id, user.
            order: Sort direction — 'asc' or 'desc'.
        """
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.search_annotations(
                url=url,
                user=user,
                group=group,
                tag=tag,
                text=text,
                any=any_field,
                quote=quote,
                limit=limit,
                offset=offset,
                sort=sort,
                order=order,
            )
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def get_annotation(ctx: Context, annotation_id: str) -> dict:
        """Fetch a single annotation by its ID."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.get_annotation(annotation_id)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def create_annotation(
        ctx: Context,
        uri: str,
        text: str = "",
        tags: list[str] | None = None,
        group: str = "__world__",
        quote: str | None = None,
        quote_prefix: str | None = None,
        quote_suffix: str | None = None,
    ) -> dict:
        """Create a new annotation on a document.

        Args:
            uri: URL of the document to annotate.
            text: Body text of the annotation (supports Markdown).
            tags: List of tags to attach.
            group: Group ID to post into. Defaults to public ('__world__').
            quote: Exact text being highlighted/quoted from the document.
            quote_prefix: Text immediately before the quote (for context).
            quote_suffix: Text immediately after the quote (for context).
        """
        app_ctx: AppContext = ctx.request_context.lifespan_context
        body: dict = {
            "uri": uri,
            "text": text,
            "tags": tags or [],
            "group": group,
        }
        if quote:
            selector: dict = {"type": "TextQuoteSelector", "exact": quote}
            if quote_prefix:
                selector["prefix"] = quote_prefix
            if quote_suffix:
                selector["suffix"] = quote_suffix
            body["target"] = [{"source": uri, "selector": [selector]}]
        try:
            return await app_ctx.hypothesis_client.create_annotation(body)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def update_annotation(
        ctx: Context,
        annotation_id: str,
        text: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Update an existing annotation's text and/or tags.

        Args:
            annotation_id: ID of the annotation to update.
            text: New body text (replaces existing).
            tags: New tag list (replaces existing).
        """
        app_ctx: AppContext = ctx.request_context.lifespan_context
        body: dict = {}
        if text is not None:
            body["text"] = text
        if tags is not None:
            body["tags"] = tags
        if not body:
            return {"error": True, "message": "Provide at least one of: text, tags"}
        try:
            return await app_ctx.hypothesis_client.update_annotation(annotation_id, body)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def delete_annotation(ctx: Context, annotation_id: str) -> dict:
        """Delete an annotation by its ID."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.delete_annotation(annotation_id)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def flag_annotation(ctx: Context, annotation_id: str) -> dict:
        """Flag an annotation for moderator review."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.flag_annotation(annotation_id)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def hide_annotation(ctx: Context, annotation_id: str) -> dict:
        """Hide an annotation from other users (moderator action)."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.hide_annotation(annotation_id)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def unhide_annotation(ctx: Context, annotation_id: str) -> dict:
        """Unhide a previously hidden annotation."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.unhide_annotation(annotation_id)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}
