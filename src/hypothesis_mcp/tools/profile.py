from mcp.server.fastmcp import FastMCP, Context
from hypothesis_mcp.client import HypothesisAPIError
from hypothesis_mcp.context import AppContext


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def get_user_profile(ctx: Context) -> dict:
        """Fetch the profile of the currently authenticated user,
        including their userid, display name, and group memberships."""
        app_ctx: AppContext = ctx.request_context.lifespan_context
        try:
            return await app_ctx.hypothesis_client.get_profile()
        except HypothesisAPIError as e:
            return {"error": True, "status_code": e.status_code, "message": str(e)}
