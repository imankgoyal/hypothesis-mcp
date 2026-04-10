from mcp.server.fastmcp import FastMCP, Context
from hypothesis_mcp.client import HypothesisAPIError
from hypothesis_mcp.context import AppContext


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_groups(
        ctx: Context,
        document_uri: str | None = None,
    ) -> dict:
        """List groups the current user is a member of.

        Args:
            document_uri: If provided, only return groups associated with this document URI.
        """
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            groups = await app_ctx.hypothesis_client.list_groups(document_uri=document_uri)
            return {"groups": groups}
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}

    @mcp.tool()
    async def get_group(ctx: Context, group_id: str) -> dict:
        """Fetch details for a specific group by ID.

        Args:
            group_id: The group's ID (e.g. 'hLkFsDnb').
        """
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.get_group(group_id)
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}
